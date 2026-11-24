"""Tests for fairdm/contrib/import_export/plugins.py, the pages of an import.

Pages are read for their structure: the status they answer with, the rows they list,
the elements their states need and what they write. Wording and look are never asserted.
"""

import io
from unittest import mock

import pytest
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from import_export.formats.base_formats import XLSX
from openpyxl import load_workbook

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from demo.models import RockSample, XRFMeasurement
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.import_export import tasks
from fairdm.contrib.import_export.definitions import import_definitions
from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.contrib.import_export.plugins import import_chooser
from fairdm.contrib.import_export.reader import FileReader
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.contrib.import_export.undo import ImportUndo
from fairdm.contrib.plugins import reverse
from fairdm.factories import ContributionFactory, DatasetFactory, PersonFactory
from fairdm.registry import registry
from tests.factories import ImportJobFactory, ImportRowFactory

pytestmark = pytest.mark.django_db

Status = ImportJob.Status
Outcome = ImportRow.Outcome

ROCK_HEADINGS = ["name", "rock_type", "collection_date"]


def parse(response):
    """Parse a response's page."""
    return BeautifulSoup(response.content, "html.parser")


@pytest.fixture
def person_at():
    """Return a function making a person who holds a level on a dataset."""

    def make(dataset, level):
        """Make the person.

        Args:
            dataset: The dataset the level is held on.
            level: A ``ContributionLevel``.

        Returns:
            The person.
        """
        person = PersonFactory()
        ContributionFactory(content_object=dataset, contributor=person, level=level)
        return person

    return make


@pytest.fixture
def editor(open_dataset, person_at):
    """A person who may import into the open dataset."""
    return person_at(open_dataset, ContributionLevel.EDIT)


@pytest.fixture
def editor_client(client, editor):
    """A client signed in as the editor."""
    client.force_login(editor)
    return client


@pytest.fixture
def start_url(open_dataset):
    """The import page of rock samples in the open dataset."""
    return reverse(open_dataset, "import", type="rocksample")


@pytest.fixture
def job_url(open_dataset):
    """Return a function giving the address of one of a job's pages."""

    def build(job, page="job", dataset=None):
        """Find the address.

        Args:
            job: The import job.
            page: ``job``, ``columns``, ``status`` or ``problems``.
            dataset: The dataset whose address is used. Defaults to the open dataset.

        Returns:
            The address.
        """
        return reverse(dataset or open_dataset, f"imports-{page}", job=job.pk)

    return build


@pytest.fixture
def queued():
    """Replace ``tasks.start`` and return the mock that records what is queued."""
    with mock.patch.object(tasks, "start") as start:
        yield start


@pytest.fixture
def upload(editor_client, start_url):
    """Return a function posting a file to the import page of rock samples."""

    def post(name, body, **options):
        """Post the file.

        Args:
            name: The file's name.
            body: The file's bytes.
            **options: Further form fields.

        Returns:
            The response.
        """
        return editor_client.post(
            start_url, {"file": SimpleUploadedFile(name, body), **options}
        )

    return post


@pytest.fixture
def rock_csv():
    """The bytes of a clean file of two new rocks."""
    return (
        b"name,rock_type,collection_date\n"
        b"Granite A,granite,2024-06-30\n"
        b"Basalt A,basalt,2024-06-30\n"
    )


class TestPermission:
    """Every page answers a person who may not import with a 404 (FR-001)."""

    @pytest.fixture
    def pages(self, open_dataset, job_url):
        """Every address of the import pages of the open dataset."""
        job = ImportJobFactory(
            dataset=open_dataset, status=Status.PROBLEMS, with_file=True
        )
        return [
            reverse(open_dataset, "import", type="rocksample"),
            reverse(open_dataset, "import-template", type="rocksample", fmt="csv"),
            reverse(open_dataset, "imports"),
            job_url(job),
            job_url(job, "columns"),
            job_url(job, "status"),
            job_url(job, "problems"),
        ]

    def test_an_editor_is_let_in_everywhere(self, editor_client, pages):
        assert [editor_client.get(a).status_code for a in pages] == [200] * len(pages)

    def test_a_visitor_gets_a_404_everywhere(self, client, pages):
        assert [client.get(a).status_code for a in pages] == [404] * len(pages)

    def test_a_person_who_may_only_view_gets_a_404_everywhere(
        self, client, open_dataset, person_at, pages
    ):
        client.force_login(person_at(open_dataset, ContributionLevel.VIEW))
        assert [client.get(a).status_code for a in pages] == [404] * len(pages)

    def test_an_editor_of_another_dataset_gets_a_404_everywhere(
        self, client, person_at, pages
    ):
        other = DatasetFactory()
        client.force_login(person_at(other, ContributionLevel.EDIT))
        assert [client.get(a).status_code for a in pages] == [404] * len(pages)

    @pytest.mark.parametrize("page", ["job", "columns", "status", "problems"])
    def test_another_datasets_job_is_a_404_under_this_datasets_address(
        self, editor_client, job_url, page
    ):
        foreign = ImportJobFactory(dataset=DatasetFactory(), status=Status.PROBLEMS)
        assert editor_client.get(job_url(foreign, page)).status_code == 404

    @pytest.mark.parametrize("page", ["job", "columns"])
    def test_a_post_for_another_datasets_job_writes_nothing(
        self, editor_client, job_url, queued, page
    ):
        foreign = ImportJobFactory(dataset=DatasetFactory(), status=Status.CHECKED)
        response = editor_client.post(job_url(foreign, page), {"action": "discard"})
        assert response.status_code == 404
        foreign.refresh_from_db()
        assert foreign.status == Status.CHECKED
        queued.assert_not_called()


class TestImportStart:
    """The page of one type takes the options and a file."""

    def test_it_offers_the_templates_and_the_guide(self, editor_client, start_url):
        page = parse(editor_client.get(start_url))
        links = [a["href"] for a in page.select("a[download]")]
        assert any(link.endswith("template.xlsx/") for link in links)
        assert any(link.endswith("template.csv/") for link in links)
        assert page.select("table.ie-guide__table")
        assert page.select("form[data-ie-upload] input[type=file]")

    def test_downloads_of_the_current_records_appear_only_with_records(
        self, editor_client, start_url, open_dataset
    ):
        before = parse(editor_client.get(start_url))
        assert not any("scope=all" in a["href"] for a in before.select("a[download]"))
        RockSampleFactory(dataset=open_dataset)
        after = parse(editor_client.get(start_url))
        assert any("scope=all" in a["href"] for a in after.select("a[download]"))

    def test_only_the_columns_panel_counts_and_it_counts_columns(
        self, editor_client, start_url, open_dataset
    ):
        RockSampleFactory.create_batch(3, dataset=open_dataset)
        page = parse(editor_client.get(start_url))
        counts = {
            panel.select_one(".ie-panel__title").get_text(strip=True): panel.select_one(
                ".ie-count"
            )
            for panel in page.select("section.ie-panel")
        }
        schema = import_definitions.get("rocksample").table_schema()
        columns = [c for c in counts.items() if c[1] is not None]
        assert len(columns) == 1
        assert int(columns[0][1].get_text()) == len(schema.columns)

    def test_the_type_of_a_measurement_has_a_page_too(
        self, editor_client, open_dataset
    ):
        address = reverse(open_dataset, "import", type="xrfmeasurement")
        assert editor_client.get(address).status_code == 200

    def test_a_type_the_portal_lacks_is_a_404(self, editor_client, open_dataset):
        address = reverse(open_dataset, "import", type="nosuchtype")
        assert editor_client.get(address).status_code == 404

    def test_the_csv_template_holds_the_headings_only(
        self, editor_client, open_dataset
    ):
        address = reverse(open_dataset, "import-template", type="rocksample", fmt="csv")
        response = editor_client.get(address)
        lines = response.content.decode("utf-8-sig").splitlines()
        schema = import_definitions.get("rocksample").table_schema()
        assert len(lines) == 1
        assert lines[0].split(",")[0] == schema.headings[0]

    def test_the_excel_template_opens(self, editor_client, open_dataset):
        address = reverse(
            open_dataset, "import-template", type="rocksample", fmt="xlsx"
        )
        book = load_workbook(io.BytesIO(editor_client.get(address).content))
        assert book.sheetnames

    def test_a_format_the_type_lacks_is_a_404(self, editor_client, open_dataset):
        address = reverse(
            open_dataset, "import-template", type="rocksample", fmt="json"
        )
        assert editor_client.get(address).status_code == 404

    def test_a_template_in_a_format_the_portal_does_not_read_is_a_404(
        self, editor_client, open_dataset, settings
    ):
        settings.IMPORT_FORMATS = [XLSX]
        address = reverse(open_dataset, "import-template", type="rocksample", fmt="csv")
        assert editor_client.get(address).status_code == 404

    def test_the_step_bar_marks_the_first_step(self, editor_client, start_url):
        page = parse(editor_client.get(start_url))
        steps = page.select("ol.ie-steps > li")
        assert len(steps) == 4
        assert [bool(step.get("aria-current")) for step in steps] == [
            True,
            False,
            False,
            False,
        ]

    def test_the_upload_form_posts_a_file_with_the_options(
        self, editor_client, start_url
    ):
        form = parse(editor_client.get(start_url)).select_one("form[data-ie-upload]")
        assert form["method"] == "post"
        assert form["enctype"] == "multipart/form-data"
        assert form.select_one("input[type=file][required]")
        assert form.select_one("input[name=mode]")
        assert form.select_one("input[name=empty]")
        assert form.select_one("input[name=csrfmiddlewaretoken]")

    def test_recent_imports_are_of_this_type_and_at_most_five(
        self, editor_client, start_url, open_dataset, job_url
    ):
        rocks = [ImportJobFactory(dataset=open_dataset) for _ in range(6)]
        other = ImportJobFactory(dataset=open_dataset, definition_name="xrfmeasurement")
        page = parse(editor_client.get(start_url))
        links = [a["href"] for a in page.select(".ie-side [data-ie-job] a")]
        assert len(links) == 5
        assert job_url(other) not in links
        assert set(links) <= {job_url(job) for job in rocks}

    def test_no_recent_imports_draws_no_list(self, editor_client, start_url):
        page = parse(editor_client.get(start_url))
        assert not page.select("[data-ie-job]")


class TestUpload:
    """A file is read before any job is saved."""

    @pytest.mark.parametrize(
        ("name", "body"),
        [
            pytest.param("rocks.json", b"[]", id="format"),
            pytest.param("rocks.txt", b"a,b\n1,2\n", id="text"),
            pytest.param("rocks.csv", b"", id="empty"),
            pytest.param("rocks.csv", b"name,rock_type\n", id="no_rows"),
            pytest.param("rocks.xlsx", b"not a workbook", id="unreadable"),
        ],
    )
    def test_a_refused_file_saves_no_job(self, upload, queued, name, body):
        response = upload(name, body)
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0
        queued.assert_not_called()

    def test_no_file_saves_no_job(self, editor_client, start_url, queued):
        response = editor_client.post(start_url, {})
        assert response.status_code == 200
        assert ImportJob.objects.count() == 0

    def test_a_file_over_the_size_limit_saves_no_job(self, upload, rock_csv, queued):
        with mock.patch.object(FileReader, "MAX_BYTES", 10):
            response = upload("rocks.csv", rock_csv)
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0

    def test_a_file_with_too_many_rows_saves_no_job(self, upload, rock_csv, queued):
        with mock.patch.object(FileReader, "MAX_ROWS", 1):
            response = upload("rocks.csv", rock_csv)
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0

    def test_a_workbook_too_large_once_unpacked_saves_no_job(
        self, upload, file_of, queued
    ):
        body = file_of("xlsx", [ROCK_HEADINGS, ["A", "granite", "2024-06-30"]])
        with mock.patch.object(FileReader, "MAX_UNCOMPRESSED", 10):
            response = upload("rocks.xlsx", body)
        assert response.status_code == 200
        assert ImportJob.objects.count() == 0

    def test_a_clean_file_goes_to_the_check(
        self, upload, rock_csv, queued, open_dataset, editor
    ):
        response = upload("rocks.csv", rock_csv)
        job = ImportJob.objects.get()
        assert response.status_code == 302
        assert response.url == job.get_absolute_url()
        assert job.status == Status.CHECKING
        assert job.dataset == open_dataset
        assert job.created_by == editor
        assert job.definition_name == "rocksample"
        assert job.headers == ROCK_HEADINGS
        assert job.column_map == {h: h for h in ROCK_HEADINGS}
        assert job.row_count == 2
        assert job.file
        queued.assert_called_once_with(tasks.check_job, job.pk)

    def test_the_options_are_kept_on_the_job(self, upload, rock_csv, queued):
        upload("rocks.csv", rock_csv, mode="add", empty="clear")
        job = ImportJob.objects.get()
        assert job.mode == ImportJob.Mode.ADD
        assert job.empty_cells == ImportJob.Empty.CLEAR

    def test_example_values_are_kept_for_matching(self, upload, rock_csv, queued):
        upload("rocks.csv", rock_csv)
        job = ImportJob.objects.get()
        assert job.samples["name"] == ["Granite A", "Basalt A"]

    def test_the_examples_are_four_cut_values_and_skip_empty_cells(
        self, upload, queued
    ):
        long = "A" * 50
        rows = [long, "", "B", "C", "D", "E"]
        body = "name,rock_type,collection_date\n" + "".join(
            f"{name},granite,2024-06-30\n" for name in rows
        )
        upload("rocks.csv", body.encode())
        job = ImportJob.objects.get()
        assert job.samples["name"] == ["A" * 40, "B", "C", "D"]

    def test_two_columns_with_one_heading_save_no_job(self, upload, queued):
        response = upload("rocks.csv", b"name,name,rock_type\nA,B,granite\n")
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0

    def test_a_format_the_portal_does_not_read_saves_no_job(
        self, upload, rock_csv, queued, settings
    ):
        settings.IMPORT_FORMATS = [XLSX]
        response = upload("rocks.csv", rock_csv)
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0

    def test_an_unmatched_heading_goes_to_matching(self, upload, queued, job_url):
        body = b"name,rock_type,collection_date,mystery\nA,granite,2024-06-30,x\n"
        response = upload("rocks.csv", body)
        job = ImportJob.objects.get()
        assert response.status_code == 302
        assert response.url == job_url(job, "columns")
        assert job.status == Status.MATCHING
        assert job.column_map["mystery"] == ""
        queued.assert_not_called()

    def test_a_file_missing_a_required_column_goes_to_matching(
        self, upload, queued, job_url
    ):
        response = upload("rocks.csv", b"name,rock_type\nA,granite\n")
        job = ImportJob.objects.get()
        assert response.url == job_url(job, "columns")
        assert job.status == Status.MATCHING

    def test_a_second_upload_of_the_same_file_is_its_own_job(
        self, upload, rock_csv, queued
    ):
        upload("rocks.csv", rock_csv)
        upload("rocks.csv", rock_csv)
        assert ImportJob.objects.count() == 2


@pytest.fixture
def matching_job(make_job):
    """A job waiting for its columns to be matched."""
    return make_job(
        [{"name": "A", "kind": "granite", "collection_date": "2024-06-30"}],
        status=Status.MATCHING,
        column_map={"name": "name", "kind": "", "collection_date": "collection_date"},
        samples={"kind": ["granite"]},
    )


class TestJobColumns:
    """The matching page, one select for each heading of the file."""

    def test_it_has_a_select_for_each_heading(
        self, editor_client, job_url, matching_job
    ):
        page = parse(editor_client.get(job_url(matching_job, "columns")))
        selects = page.select("table select[name^=col-]")
        assert len(selects) == len(matching_job.headers)
        assert page.select("table thead th")

    def test_the_chosen_column_is_selected(self, editor_client, job_url, matching_job):
        page = parse(editor_client.get(job_url(matching_job, "columns")))
        chosen = page.select_one("select[name=col-0] option[selected]")
        assert chosen["value"] == "name"

    def test_a_choice_starts_the_check(
        self, editor_client, job_url, matching_job, queued
    ):
        response = editor_client.post(
            job_url(matching_job, "columns"),
            {
                "col-0": "name",
                "col-1": "rock_type",
                "col-2": "collection_date",
                "mode": "both",
                "empty": "keep",
            },
        )
        matching_job.refresh_from_db()
        assert response.status_code == 302
        assert matching_job.status == Status.CHECKING
        assert matching_job.column_map == {
            "name": "name",
            "kind": "rock_type",
            "collection_date": "collection_date",
        }
        queued.assert_called_once_with(tasks.check_job, matching_job.pk)

    def test_a_column_a_value_cannot_name_is_left_out(
        self, editor_client, job_url, matching_job, queued
    ):
        editor_client.post(
            job_url(matching_job, "columns"),
            {"col-0": "name", "col-1": "no_such_column", "col-2": "collection_date"},
        )
        matching_job.refresh_from_db()
        assert matching_job.column_map["kind"] == ""

    def test_two_headings_for_one_column_start_nothing(
        self, editor_client, job_url, matching_job, queued
    ):
        response = editor_client.post(
            job_url(matching_job, "columns"),
            {"col-0": "name", "col-1": "name", "col-2": "collection_date"},
        )
        matching_job.refresh_from_db()
        assert response.status_code == 200
        assert matching_job.status == Status.MATCHING
        queued.assert_not_called()

    def test_a_missing_required_column_starts_nothing(
        self, editor_client, job_url, matching_job, queued
    ):
        response = editor_client.post(
            job_url(matching_job, "columns"), {"col-0": "name"}
        )
        matching_job.refresh_from_db()
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert matching_job.status == Status.MATCHING
        queued.assert_not_called()

    @pytest.mark.parametrize(
        "status",
        [Status.CHECKING, Status.IMPORTING, Status.IMPORTED, Status.DISCARDED],
    )
    def test_a_job_past_the_check_cannot_be_matched_again(
        self, editor_client, job_url, matching_job, queued, status
    ):
        ImportJob.objects.filter(pk=matching_job.pk).update(status=status)
        editor_client.post(
            job_url(matching_job, "columns"),
            {"col-0": "name", "col-1": "rock_type", "col-2": "collection_date"},
        )
        matching_job.refresh_from_db()
        assert matching_job.status == status
        queued.assert_not_called()

    def test_a_job_past_the_check_is_not_shown_problems_with_a_new_match(
        self, editor_client, job_url, matching_job, queued
    ):
        ImportJob.objects.filter(pk=matching_job.pk).update(status=Status.IMPORTED)
        response = editor_client.post(
            job_url(matching_job, "columns"), {"col-0": "name"}
        )
        assert response.status_code == 302
        assert response.url == matching_job.get_absolute_url()

    def test_the_form_carries_a_csrf_token(self, editor_client, job_url, matching_job):
        page = parse(editor_client.get(job_url(matching_job, "columns")))
        assert page.select_one("form.ie-stack input[name=csrfmiddlewaretoken]")

    def test_a_double_post_queues_one_check(
        self, editor_client, job_url, matching_job, queued
    ):
        data = {"col-0": "name", "col-1": "rock_type", "col-2": "collection_date"}
        editor_client.post(job_url(matching_job, "columns"), data)
        editor_client.post(job_url(matching_job, "columns"), data)
        assert queued.call_count == 1


@pytest.fixture
def checked_job(make_job, open_dataset):
    """A checked job that would add two records."""
    job = make_job(
        [{"name": "A", "rock_type": "granite", "collection_date": "2024-06-30"}],
        status=Status.CHECKED,
    )
    ImportJob.objects.filter(pk=job.pk).update(
        summary={"new": 2}, row_count=2, status=Status.CHECKED
    )
    job.refresh_from_db()
    return job


def add_rows(job, outcome, count, start=1):
    """Store ``count`` rows of one outcome for a job, numbered from ``start``."""
    return [
        ImportRowFactory(
            job=job,
            number=start + n,
            line=start + n + 1,
            outcome=outcome,
            label=f"r{n}",
        )
        for n in range(count)
    ]


class TestJobDetail:
    """The check and its outcome, with the actions that move a job on."""

    def rows_on(self, response):
        """Return the row elements of a page."""
        return parse(response).select("[data-ie-row]")

    def test_rows_are_listed_by_outcome_a_page_at_a_time(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 150)
        add_rows(checked_job, Outcome.UPDATE, 3, start=151)
        address = job_url(checked_job)
        assert len(self.rows_on(editor_client.get(address + "?show=new"))) == 100
        assert len(self.rows_on(editor_client.get(address + "?show=new&page=2"))) == 50
        assert len(self.rows_on(editor_client.get(address + "?show=update"))) == 3

    def test_problems_are_shown_first_when_there_are_any(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 5)
        add_rows(checked_job, Outcome.PROBLEM, 2, start=6)
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.PROBLEMS, summary={"new": 5, "problem": 2}
        )
        rows = self.rows_on(editor_client.get(job_url(checked_job)))
        assert len(rows) == 2

    def test_every_row_is_listed_for_show_all(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 4)
        add_rows(checked_job, Outcome.UNCHANGED, 3, start=5)
        rows = self.rows_on(editor_client.get(job_url(checked_job) + "?show=all"))
        assert len(rows) == 7

    def test_a_page_past_the_last_is_empty_not_an_error(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 3)
        response = editor_client.get(job_url(checked_job) + "?show=new&page=9")
        assert response.status_code == 200
        assert not self.rows_on(response)

    def test_a_page_number_below_one_reads_as_the_first(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 3)
        response = editor_client.get(job_url(checked_job) + "?show=new&page=-2")
        assert len(self.rows_on(response)) == 3

    def test_the_pager_links_to_the_pages_either_side(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 250)
        address = job_url(checked_job) + "?show=new"
        first = parse(editor_client.get(address)).select("nav.ie-pager a")
        middle = parse(editor_client.get(address + "&page=2")).select("nav.ie-pager a")
        last = parse(editor_client.get(address + "&page=3")).select("nav.ie-pager a")
        assert [a["href"] for a in first] == ["?show=new&page=2"]
        assert [a["href"] for a in middle] == ["?show=new&page=1", "?show=new&page=3"]
        assert [a["href"] for a in last] == ["?show=new&page=2"]

    def test_a_job_on_one_page_has_no_pager(self, editor_client, job_url, checked_job):
        add_rows(checked_job, Outcome.NEW, 3)
        page = parse(editor_client.get(job_url(checked_job) + "?show=new"))
        assert not page.select("nav.ie-pager")

    def test_new_and_changed_rows_have_a_tile_even_with_none(
        self, editor_client, job_url, checked_job
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.NOTHING, summary={"unchanged": 3}
        )
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select_one(".ie-tile--new.ie-tile--zero")
        assert page.select_one(".ie-tile--update.ie-tile--zero")
        assert page.select_one(".ie-tile--unchanged")
        assert not page.select(".ie-tile--skipped")
        assert not page.select(".ie-tile--problem")

    @pytest.mark.parametrize(
        ("status", "current"),
        [
            (Status.CHECKING, 2),
            (Status.CHECKED, 2),
            (Status.PROBLEMS, 2),
            (Status.IMPORTING, 3),
            (Status.IMPORTED, 3),
            (Status.UNDONE, 3),
        ],
    )
    def test_the_step_bar_follows_the_job(
        self, editor_client, job_url, checked_job, status, current
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        page = parse(editor_client.get(job_url(checked_job)))
        steps = page.select("ol.ie-steps > li")
        assert [i for i, step in enumerate(steps) if step.get("aria-current")] == [
            current
        ]

    @pytest.mark.parametrize(
        "status", [Status.CHECKED, Status.PROBLEMS, Status.NOTHING]
    )
    def test_a_job_that_may_be_matched_again_offers_to_do_so_or_to_check_again(
        self, editor_client, job_url, checked_job, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select(f'a[href="{job_url(checked_job, "columns")}"]')
        assert page.select('form button[name=action][value="recheck"]')

    @pytest.mark.parametrize(
        "status", [Status.IMPORTED, Status.FAILED, Status.DISCARDED]
    )
    def test_a_job_past_the_check_offers_neither(
        self, editor_client, job_url, checked_job, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        page = parse(editor_client.get(job_url(checked_job)))
        assert not page.select(f'a[href="{job_url(checked_job, "columns")}"]')
        assert not page.select('button[value="recheck"]')

    def test_a_problem_job_without_its_file_offers_no_download(
        self, editor_client, job_url, checked_job
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.PROBLEMS, summary={"problem": 1}, file=""
        )
        page = parse(editor_client.get(job_url(checked_job)))
        assert not page.select(f'a[href="{job_url(checked_job, "problems")}"]')

    def test_a_running_job_lists_no_rows_even_when_it_has_some(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 2)
        ImportJob.objects.filter(pk=checked_job.pk).update(status=Status.IMPORTING)
        page = parse(editor_client.get(job_url(checked_job)))
        assert not page.select(".ie-tiles")
        assert not page.select("[data-ie-row]")

    def test_a_page_number_that_is_not_a_number_reads_as_the_first(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 3)
        response = editor_client.get(job_url(checked_job) + "?show=new&page=x")
        assert len(self.rows_on(response)) == 3

    def test_a_problem_row_lists_each_problem_and_a_change_row_each_change(
        self, editor_client, job_url, checked_job
    ):
        ImportRowFactory(
            job=checked_job,
            outcome=Outcome.PROBLEM,
            problems=[
                {"column": "name", "message": "one"},
                {"column": "rock_type", "message": "two"},
            ],
        )
        ImportRowFactory(
            job=checked_job,
            outcome=Outcome.UPDATE,
            changes=[{"label": "Name", "old": "a", "new": "b"}],
        )
        problems = parse(editor_client.get(job_url(checked_job) + "?show=problem"))
        assert len(problems.select("[data-ie-row] [data-ie-problem]")) == 2
        changes = parse(editor_client.get(job_url(checked_job) + "?show=update"))
        assert len(changes.select("[data-ie-row] [data-ie-change]")) == 1

    def test_a_job_still_matching_goes_to_the_matching_page(
        self, editor_client, job_url, matching_job
    ):
        response = editor_client.get(job_url(matching_job))
        assert response.status_code == 302
        assert response.url == job_url(matching_job, "columns")

    def test_a_job_that_is_running_shows_the_progress_component(
        self, editor_client, job_url, checked_job
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=Status.CHECKING)
        page = parse(editor_client.get(job_url(checked_job)))
        bar = page.select_one("[data-ie-progress]")
        assert bar["hx-get"] == job_url(checked_job, "status")
        assert bar["hx-trigger"] == "every 1s"
        assert not page.select("[data-ie-row]")

    def test_an_imported_job_shows_what_it_imported(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 2)
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.IMPORTED, summary={"new": 2}
        )
        rows = self.rows_on(editor_client.get(job_url(checked_job) + "?show=new"))
        assert len(rows) == 2

    def test_a_failed_job_shows_a_way_to_upload_another(
        self, editor_client, job_url, checked_job, start_url
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.FAILED, error="x"
        )
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select(f'a[href="{start_url}"]')

    def test_a_problem_job_links_to_the_download_of_its_problems(
        self, editor_client, job_url, checked_job
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.PROBLEMS, summary={"problem": 1}
        )
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select(f'a[href="{job_url(checked_job, "problems")}"]')

    def test_the_import_form_is_guarded_against_a_second_submit(
        self, editor_client, job_url, checked_job
    ):
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select('form[data-ie-once] button[value="import"]')


class TestJobActions:
    """Each action moves a job with one conditional update and queues one task."""

    def post(self, client, address, action):
        """Post an action to a job's page."""
        return client.post(address, {"action": action})

    def test_import_moves_a_checked_job_and_queues_the_import(
        self, editor_client, editor, job_url, checked_job, queued
    ):
        response = self.post(editor_client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert response.status_code == 302
        assert checked_job.status == Status.IMPORTING
        queued.assert_called_once_with(tasks.import_job, checked_job.pk, editor.pk)

    def test_a_double_post_of_import_queues_one_task(
        self, editor_client, job_url, checked_job, queued
    ):
        self.post(editor_client, job_url(checked_job), "import")
        self.post(editor_client, job_url(checked_job), "import")
        assert queued.call_count == 1

    @pytest.mark.parametrize(
        "status",
        [
            Status.PROBLEMS,
            Status.NOTHING,
            Status.MATCHING,
            Status.CHECKING,
            Status.IMPORTING,
            Status.IMPORTED,
            Status.UNDONE,
            Status.DISCARDED,
            Status.FAILED,
        ],
    )
    def test_import_is_refused_in_any_other_status_and_writes_nothing(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        queued.assert_not_called()

    def test_import_is_refused_for_a_checked_job_with_nothing_to_write(
        self, editor_client, job_url, checked_job, queued
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(summary={"unchanged": 2})
        self.post(editor_client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKED
        queued.assert_not_called()

    @pytest.mark.parametrize(
        "status", [Status.CHECKED, Status.PROBLEMS, Status.NOTHING]
    )
    def test_recheck_queues_a_new_check(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "recheck")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKING
        queued.assert_called_once_with(tasks.check_job, checked_job.pk)

    @pytest.mark.parametrize(
        "status", [Status.IMPORTED, Status.IMPORTING, Status.CHECKING, Status.FAILED]
    )
    def test_recheck_is_refused_in_any_other_status(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "recheck")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        queued.assert_not_called()

    @pytest.mark.parametrize("status", [Status.CHECKED, Status.PROBLEMS])
    def test_discard_sets_the_job_aside_and_deletes_its_file(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        stored = checked_job.file.name
        self.post(editor_client, job_url(checked_job), "discard")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.DISCARDED
        assert not checked_job.file
        assert stored
        queued.assert_not_called()

    @pytest.mark.parametrize(
        "status", [Status.IMPORTED, Status.IMPORTING, Status.UNDONE, Status.FAILED]
    )
    def test_discard_is_refused_in_any_other_status(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "discard")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        assert checked_job.file

    def test_an_action_the_page_does_not_know_changes_nothing(
        self, editor_client, job_url, checked_job, queued
    ):
        self.post(editor_client, job_url(checked_job), "explode")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKED
        queued.assert_not_called()

    def test_a_person_who_may_not_import_cannot_post_an_action(
        self, client, open_dataset, person_at, job_url, checked_job, queued
    ):
        client.force_login(person_at(open_dataset, ContributionLevel.VIEW))
        response = self.post(client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert response.status_code == 404
        assert checked_job.status == Status.CHECKED
        queued.assert_not_called()


class TestJobStatus:
    """The progress component, asked for every second while a job runs."""

    @pytest.fixture
    def running(self, checked_job, settings):
        """A job being checked, two hundred rows long, with a cache that keeps it."""
        settings.CACHES = {
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
        }
        ImportJob.objects.filter(pk=checked_job.pk).update(
            status=Status.CHECKING, row_count=200
        )
        checked_job.refresh_from_db()
        cache.delete(ImportRun(checked_job).progress_key)
        return checked_job

    def test_a_running_job_answers_the_component_with_its_progress(
        self, editor_client, job_url, running
    ):
        cache.set(ImportRun(running).progress_key, 50)
        response = editor_client.get(job_url(running, "status"))
        page = parse(response)
        bar = page.select_one("[role=progressbar]")
        assert response.status_code == 200
        assert "HX-Refresh" not in response.headers
        assert bar["aria-valuenow"] == "50"
        assert bar["aria-valuemax"] == "200"
        root = page.select_one("[data-ie-progress]")
        assert root["hx-trigger"] == "every 1s"
        assert root["hx-get"] == job_url(running, "status")

    def test_an_import_is_labelled_apart_from_a_check(
        self, editor_client, job_url, running
    ):
        def label():
            page = parse(editor_client.get(job_url(running, "status")))
            return page.select_one("[role=progressbar]")["aria-label"]

        checking = label()
        ImportJob.objects.filter(pk=running.pk).update(status=Status.IMPORTING)
        assert label() != checking

    def test_an_undo_is_labelled_apart_from_a_check_and_an_import(
        self, editor_client, job_url, running
    ):
        def label(status):
            ImportJob.objects.filter(pk=running.pk).update(status=status)
            page = parse(editor_client.get(job_url(running, "status")))
            return page.select_one("[role=progressbar]")["aria-label"]

        assert label(Status.UNDOING) not in {
            label(Status.CHECKING),
            label(Status.IMPORTING),
        }

    def test_an_undoing_job_counts_its_progress_against_the_records_it_writes(
        self, editor_client, job_url, running
    ):
        ImportJob.objects.filter(pk=running.pk).update(
            status=Status.UNDOING, summary={"new": 30, "update": 10}
        )
        cache.set(ImportRun(running).progress_key, 20)
        page = parse(editor_client.get(job_url(running, "status")))
        bar = page.select_one("[role=progressbar]")
        assert bar["aria-valuenow"] == "20"
        assert bar["aria-valuemax"] == "40"

    def test_a_job_with_no_progress_yet_reads_as_none_done(
        self, editor_client, job_url, running
    ):
        page = parse(editor_client.get(job_url(running, "status")))
        assert page.select_one("[role=progressbar]")["aria-valuenow"] == "0"

    @pytest.mark.parametrize(
        "status",
        [
            Status.CHECKED,
            Status.PROBLEMS,
            Status.NOTHING,
            Status.IMPORTED,
            Status.FAILED,
        ],
    )
    def test_a_job_that_is_over_answers_with_a_refresh(
        self, editor_client, job_url, running, status
    ):
        ImportJob.objects.filter(pk=running.pk).update(status=status)
        response = editor_client.get(job_url(running, "status"))
        assert response.status_code == 200
        assert response.headers["HX-Refresh"] == "true"
        assert response.content == b""


class TestJobProblems:
    """The file back with each problem written beside its row."""

    @pytest.fixture
    def problem_job(self, make_job):
        """A job whose second row has a problem, with a formula in a cell."""
        job = make_job(
            [
                {
                    "name": "=1+1",
                    "rock_type": "granite",
                    "collection_date": "2024-06-30",
                },
                {"name": "B", "rock_type": "nonsense", "collection_date": "2024-06-30"},
                {
                    "name": "C\x07",
                    "rock_type": "basalt",
                    "collection_date": "2024-06-30",
                },
            ],
            status=Status.PROBLEMS,
        )
        ImportRowFactory(
            job=job,
            number=2,
            line=3,
            outcome=Outcome.PROBLEM,
            problems=[{"column": "", "message": "=SUM(1,1) is not a rock"}],
        )
        return job

    def sheet_of(self, response):
        """Open the workbook a response holds and return its first sheet."""
        return load_workbook(io.BytesIO(response.content)).worksheets[0]

    def test_it_is_a_workbook_download(self, editor_client, job_url, problem_job):
        response = editor_client.get(job_url(problem_job, "problems"))
        assert response.status_code == 200
        assert "attachment" in response["Content-Disposition"]
        assert self.sheet_of(response).max_row == 4

    def test_each_problem_sits_beside_its_row(
        self, editor_client, job_url, problem_job
    ):
        sheet = self.sheet_of(editor_client.get(job_url(problem_job, "problems")))
        problems = [row[0].value for row in sheet.iter_rows(min_row=2)]
        assert problems[0] in (None, "")
        assert "not a rock" in problems[1]
        assert problems[2] in (None, "")

    def test_the_cells_of_the_file_come_back_as_text(
        self, editor_client, job_url, problem_job
    ):
        sheet = self.sheet_of(editor_client.get(job_url(problem_job, "problems")))
        formula = next(
            cell
            for row in sheet.iter_rows(min_row=2)
            for cell in row
            if cell.value == "=1+1"
        )
        assert formula.data_type == "s"

    def test_a_message_that_looks_like_a_formula_comes_back_as_text(
        self, editor_client, job_url, problem_job
    ):
        sheet = self.sheet_of(editor_client.get(job_url(problem_job, "problems")))
        message = sheet.cell(row=3, column=1)
        assert message.data_type == "s"
        assert message.value.startswith("=SUM")

    def test_a_control_character_in_the_file_still_downloads(
        self, editor_client, job_url, problem_job
    ):
        response = editor_client.get(job_url(problem_job, "problems"))
        assert response.status_code == 200
        values = [
            cell.value for row in self.sheet_of(response).iter_rows() for cell in row
        ]
        assert not any("\x07" in str(value) for value in values if value)

    @pytest.mark.parametrize(
        "status",
        [Status.CHECKED, Status.NOTHING, Status.IMPORTED, Status.CHECKING],
    )
    def test_it_is_a_404_outside_the_problems_status(
        self, editor_client, job_url, problem_job, status
    ):
        ImportJob.objects.filter(pk=problem_job.pk).update(status=status)
        assert editor_client.get(job_url(problem_job, "problems")).status_code == 404

    def test_a_problem_row_is_marked_and_the_others_are_not(
        self, editor_client, job_url, problem_job
    ):
        sheet = self.sheet_of(editor_client.get(job_url(problem_job, "problems")))
        marked = [row[0].fill.fill_type for row in sheet.iter_rows(min_row=2)]
        assert [bool(kind) for kind in marked] == [False, True, False]

    def test_a_problem_names_its_column_by_label(
        self, editor_client, job_url, problem_job
    ):
        ImportRow.objects.filter(job=problem_job).update(
            problems=[{"column": "rock_type", "message": "not a rock"}]
        )
        schema = import_definitions.get("rocksample").table_schema()
        label = str(schema.get("rock_type").label)
        sheet = self.sheet_of(editor_client.get(job_url(problem_job, "problems")))
        assert sheet.cell(row=3, column=1).value == f"{label}: not a rock"

    def test_it_is_a_404_when_the_stored_file_has_gone_from_storage(
        self, editor_client, job_url, problem_job
    ):
        problem_job.file.storage.delete(problem_job.file.name)
        assert editor_client.get(job_url(problem_job, "problems")).status_code == 404

    def test_it_is_a_404_once_the_file_is_gone(
        self, editor_client, job_url, problem_job
    ):
        problem_job.file.delete(save=True)
        assert editor_client.get(job_url(problem_job, "problems")).status_code == 404


class TestChooser:
    """The data of the dialog that lists the types a file can be imported as."""

    def test_samples_only(self, open_dataset):
        chooser = import_chooser(open_dataset, "sample")
        assert [group["kind"] for group in chooser["groups"]] == ["sample"]
        names = [d.name for d in import_definitions.all("sample")]
        urls = [e["url"] for e in chooser["groups"][0]["entries"]]
        assert urls == [reverse(open_dataset, "import", type=n) for n in names]

    def test_measurements_only(self, open_dataset):
        chooser = import_chooser(open_dataset, "measurement")
        assert [group["kind"] for group in chooser["groups"]] == ["measurement"]
        names = [d.name for d in import_definitions.all("measurement")]
        urls = [e["url"] for e in chooser["groups"][0]["entries"]]
        assert urls == [reverse(open_dataset, "import", type=n) for n in names]

    def test_both(self, open_dataset):
        chooser = import_chooser(open_dataset)
        assert [group["kind"] for group in chooser["groups"]] == [
            "sample",
            "measurement",
        ]

    def test_each_kind_has_its_own_dialog_id(self, open_dataset):
        ids = {
            import_chooser(open_dataset, kind)["id"]
            for kind in (None, "sample", "measurement")
        }
        assert len(ids) == 3

    def test_each_entry_counts_the_records_the_dataset_holds(self, open_dataset):
        RockSampleFactory.create_batch(3, dataset=open_dataset)
        RockSampleFactory(dataset=DatasetFactory())
        XRFMeasurementFactory(
            dataset=open_dataset, sample=RockSampleFactory(dataset=open_dataset)
        )
        entries = {
            e["url"]: e
            for group in import_chooser(open_dataset)["groups"]
            for e in group["entries"]
        }
        rocks = entries[reverse(open_dataset, "import", type="rocksample")]
        xrf = entries[reverse(open_dataset, "import", type="xrfmeasurement")]
        assert rocks["count"] == RockSample.objects.filter(dataset=open_dataset).count()
        assert (
            xrf["count"] == XRFMeasurement.objects.filter(dataset=open_dataset).count()
        )

    def test_each_entry_names_what_a_new_record_needs(self, open_dataset):
        entry = next(
            e
            for e in import_chooser(open_dataset, "sample")["groups"][0]["entries"]
            if e["url"] == reverse(open_dataset, "import", type="rocksample")
        )
        schema = registry.get_for_model(RockSample).get_table_schema()
        assert entry["required"] == [str(c.label) for c in schema.required]
        assert entry["columns"] == len(schema.importable) - 1


class TestImportsList:
    """The page that lists every import into the dataset."""

    def test_it_lists_the_jobs_of_the_dataset_only(
        self, editor_client, open_dataset, job_url
    ):
        mine = [ImportJobFactory(dataset=open_dataset) for _ in range(3)]
        ImportJobFactory(dataset=DatasetFactory())
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        links = {a["href"] for a in page.select("[data-ie-job] a")}
        assert links == {job_url(job) for job in mine}

    def test_each_job_names_its_type(self, editor_client, open_dataset):
        job = ImportJobFactory(dataset=open_dataset)
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        meta = page.select_one("[data-ie-job] .ie-job__meta").get_text().lower()
        assert job.type_name.lower() in meta

    def test_an_empty_dataset_says_so(self, editor_client, open_dataset):
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        assert not page.select("[data-ie-job]")

    def test_the_import_menu_sits_in_the_page_head(self, editor_client, open_dataset):
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        menu = page.select_one("button[aria-haspopup=dialog]")
        assert menu is not None
        assert menu.find_parent(class_="ie-page") is None
        assert len(page.select("dialog[id^=ie-import-]")) == 1

    def test_an_empty_dataset_offers_the_import_menu_in_the_empty_state(
        self, editor_client, open_dataset
    ):
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        empty = page.select_one(".ie-empty-block")
        assert empty.select_one("button[aria-haspopup=dialog]") is not None


@pytest.fixture
def imported_job(make_job, open_dataset, editor):
    """An imported job that added one rock and changed another.

    Returns:
        The job, the added rock and the changed rock.
    """
    changed = RockSampleFactory(
        dataset=open_dataset, local_id="OLD", hardness_mohs="7.0", rock_type="granite"
    )
    job = make_job(
        [
            {
                "name": "Brand new",
                "local_id": "NEW",
                "rock_type": "basalt",
                "collection_date": "2024-06-30",
            },
            {
                "name": changed.name,
                "local_id": "OLD",
                "rock_type": "granite",
                "collection_date": "2024-06-30",
                "hardness_mohs": "6.5",
            },
        ]
    )
    ImportRun(job).check()
    ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
    ImportRun(job).perform(editor)
    job.refresh_from_db()
    added = RockSample.objects.get(dataset=open_dataset, local_id="NEW")
    return job, added, RockSample.objects.get(pk=changed.pk)


class TestJobUndo:
    """The undo action: claimed in the request, done by a task."""

    def post(self, client, address):
        """Post the undo action to a job's page."""
        return client.post(address, {"action": "undo"})

    def test_undo_claims_the_job_and_queues_the_task_at_once(
        self, editor_client, editor, job_url, imported_job, queued
    ):
        job, added, changed = imported_job
        response = self.post(editor_client, job_url(job))
        job.refresh_from_db()
        assert response.status_code == 302
        assert response["Location"] == job_url(job)
        assert job.status == Status.UNDOING
        queued.assert_called_once_with(tasks.undo_job, job.pk, editor.pk)
        assert RockSample.objects.filter(pk=added.pk).exists()
        assert str(RockSample.objects.get(pk=changed.pk).hardness_mohs) == "6.5"

    def test_the_task_undoes_what_was_added_and_restores_what_was_changed(
        self, editor_client, editor, job_url, imported_job, queued
    ):
        job, added, changed = imported_job
        self.post(editor_client, job_url(job))
        tasks.undo_job(*queued.call_args.args[1:])
        job.refresh_from_db()
        changed.refresh_from_db()
        assert job.status == Status.UNDONE
        assert job.undone_by == editor
        assert not RockSample.objects.filter(pk=added.pk).exists()
        assert str(changed.hardness_mohs) == "7.0"

    def test_anyone_with_the_edit_level_may_undo_not_only_who_imported(
        self, client, open_dataset, person_at, job_url, imported_job, queued
    ):
        job, _added, _changed = imported_job
        other = person_at(open_dataset, ContributionLevel.EDIT)
        client.force_login(other)
        self.post(client, job_url(job))
        job.refresh_from_db()
        assert job.status == Status.UNDOING
        queued.assert_called_once_with(tasks.undo_job, job.pk, other.pk)

    def test_a_person_who_may_not_import_gets_a_404_and_nothing_changes(
        self, client, open_dataset, person_at, job_url, imported_job, queued
    ):
        job, added, _changed = imported_job
        client.force_login(person_at(open_dataset, ContributionLevel.VIEW))
        response = self.post(client, job_url(job))
        job.refresh_from_db()
        assert response.status_code == 404
        assert job.status == Status.IMPORTED
        assert RockSample.objects.filter(pk=added.pk).exists()
        queued.assert_not_called()

    def test_a_double_post_queues_one_task(
        self, editor_client, job_url, imported_job, queued
    ):
        job, _added, _changed = imported_job
        self.post(editor_client, job_url(job))
        self.post(editor_client, job_url(job))
        assert queued.call_count == 1

    @pytest.mark.parametrize(
        "status",
        [
            Status.CHECKED,
            Status.PROBLEMS,
            Status.UNDOING,
            Status.UNDONE,
            Status.DISCARDED,
            Status.FAILED,
        ],
    )
    def test_undo_is_refused_in_any_other_status(
        self, editor_client, job_url, imported_job, queued, status
    ):
        job, added, _changed = imported_job
        ImportJob.objects.filter(pk=job.pk).update(status=status)
        self.post(editor_client, job_url(job))
        job.refresh_from_db()
        assert job.status == status
        assert RockSample.objects.filter(pk=added.pk).exists()
        queued.assert_not_called()

    def test_a_refusal_after_the_task_names_the_records_on_the_job_page(
        self, editor_client, editor, job_url, imported_job, queued
    ):
        job, added, changed = imported_job
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        self.post(editor_client, job_url(job))
        tasks.undo_job(job.pk, editor.pk)
        label = job.rows.get(record_pk=changed.pk).label
        page = parse(editor_client.get(job_url(job)))
        listed = [item.get_text() for item in page.select("[data-ie-refusal] li")]
        job.refresh_from_db()
        assert job.status == Status.IMPORTED
        assert RockSample.objects.filter(pk=added.pk).exists()
        assert [text for text in listed if label in text]

    def test_a_refusal_shows_twenty_records_and_counts_the_rest(
        self, editor_client, editor, job_url, imported_job, queued
    ):
        job, _added, _changed = imported_job
        ImportRow.objects.bulk_create(
            ImportRow(job=job, number=100 + n, line=n, outcome="new", record_pk=n)
            for n in range(1, 31)
        )
        self.post(editor_client, job_url(job))
        tasks.undo_job(job.pk, editor.pk)
        page = parse(editor_client.get(job_url(job)))
        assert len(page.select("[data-ie-refusal] li")) == 21

    def test_an_imported_job_with_no_refusal_shows_no_refusal(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        page = parse(editor_client.get(job_url(job)))
        assert not page.select("[data-ie-refusal]")

    def test_the_undo_button_shows_on_an_imported_job(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        page = parse(editor_client.get(job_url(job)))
        assert page.select('form button[name="action"][value="undo"]')

    def test_the_undo_button_shows_even_when_a_record_changed(
        self, editor_client, job_url, imported_job
    ):
        job, _added, changed = imported_job
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        page = parse(editor_client.get(job_url(job)))
        assert page.select('form button[name="action"][value="undo"]')

    def test_undo_is_asked_for_in_a_dialog_before_it_is_posted(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        page = parse(editor_client.get(job_url(job)))
        dialog = page.select_one("dialog#ie-undo")
        assert dialog.select_one('form[method="post"] button[value="undo"]')
        opener = page.select_one('button[aria-haspopup="dialog"][type="button"]')
        assert opener is not None
        assert not page.select('form:not(dialog form) button[value="undo"]')

    def test_an_undoing_job_shows_the_progress_and_no_undo_button(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        ImportJob.objects.filter(pk=job.pk).update(status=Status.UNDOING)
        page = parse(editor_client.get(job_url(job)))
        assert page.select_one("[data-ie-progress]")["hx-get"] == job_url(job, "status")
        assert not page.select('button[value="undo"]')

    def test_the_job_page_of_an_imported_job_runs_the_same_queries_for_50_and_500_rows(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job

        def add(first, last):
            ImportRow.objects.bulk_create(
                ImportRow(
                    job=job,
                    number=100 + n,
                    line=n,
                    outcome="new",
                    record_pk=n,
                    digest="x",
                )
                for n in range(first, last)
            )

        def count():
            editor_client.get(job_url(job))
            with CaptureQueriesContext(connection) as queries:
                editor_client.get(job_url(job))
            return len(queries)

        add(0, 50)
        few = count()
        add(50, 500)
        assert count() == few

    def test_the_job_page_of_an_imported_job_looks_for_no_conflicts(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        with mock.patch.object(ImportUndo, "conflicts") as looked:
            editor_client.get(job_url(job))
        looked.assert_not_called()

    def test_another_datasets_job_cannot_be_undone_through_this_one(
        self, editor_client, open_dataset, job_url, imported_job, queued
    ):
        job, _added, _changed = imported_job
        other = DatasetFactory()
        response = self.post(editor_client, job_url(job, dataset=other))
        job.refresh_from_db()
        assert response.status_code == 404
        assert job.status == Status.IMPORTED
        queued.assert_not_called()


class TestPastImports:
    """The dataset's list of imports, newest first."""

    @pytest.fixture
    def past_url(self, open_dataset):
        """The past imports address."""
        return reverse(open_dataset, "imports")

    def test_it_lists_the_datasets_imports_newest_first(
        self, editor_client, open_dataset, past_url
    ):
        older = ImportJobFactory(dataset=open_dataset, filename="older.csv")
        newer = ImportJobFactory(dataset=open_dataset, filename="newer.csv")
        ImportJobFactory(filename="elsewhere.csv")
        page = parse(editor_client.get(past_url))
        links = [a["href"] for a in page.select("[data-ie-job] a.ie-job__link")]
        assert links == [newer.get_absolute_url(), older.get_absolute_url()]

    def test_an_empty_dataset_says_so_and_offers_the_import_dialog(
        self, editor_client, past_url
    ):
        page = parse(editor_client.get(past_url))
        assert not page.select("[data-ie-job]")
        assert page.select_one(".ie-empty")
        assert page.select('button[aria-haspopup="dialog"]')
        assert page.select("dialog")

    def test_a_dataset_with_imports_offers_the_dialog_too(
        self, editor_client, open_dataset, past_url
    ):
        ImportJobFactory(dataset=open_dataset)
        page = parse(editor_client.get(past_url))
        assert page.select('button[aria-haspopup="dialog"]')
        assert page.select("dialog")

    def test_a_person_who_may_not_import_gets_a_404(
        self, client, open_dataset, person_at, past_url
    ):
        client.force_login(person_at(open_dataset, ContributionLevel.VIEW))
        assert client.get(past_url).status_code == 404

"""Tests for fairdm/contrib/import_export/plugins.py, the pages of an import.

Pages are read for their structure: the status they answer with, the rows they list,
the elements their states need and what they write. Wording and look are never asserted.
"""

import io

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
from fairdm.contrib.import_export.plugins import JobDetail, import_chooser
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
def queued(monkeypatch):
    """Stand in for the task queue and return the list of ``(task, args)`` it took."""
    taken = []
    monkeypatch.setattr(tasks, "start", lambda task, *args: taken.append((task, args)))
    return taken


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

    @pytest.mark.parametrize("page", ["job", "problems"])
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
        assert not queued


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
        RockSampleFactory(dataset=open_dataset)
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
            pytest.param("rocks.xlsx", b"not a workbook", id="unreadable"),
        ],
    )
    def test_a_refused_file_saves_no_job(self, upload, queued, name, body):
        response = upload(name, body)
        assert response.status_code == 200
        assert parse(response).select("[role=alert]")
        assert ImportJob.objects.count() == 0
        assert not queued

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
        assert queued == [(tasks.check_job, (job.pk,))]

    def test_the_options_are_kept_on_the_job(self, upload, rock_csv, queued):
        upload("rocks.csv", rock_csv, mode="add", empty="clear")
        job = ImportJob.objects.get()
        assert job.mode == ImportJob.Mode.ADD
        assert job.empty_cells == ImportJob.Empty.CLEAR

    def test_the_examples_are_cut_and_skip_empty_cells(self, upload, queued):
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
        assert not queued

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
        assert queued == [(tasks.check_job, (matching_job.pk,))]

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
        assert not queued

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
        assert not queued

    @pytest.mark.parametrize("status", [Status.CHECKING, Status.IMPORTED])
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
        assert not queued

    def test_a_job_past_the_check_is_not_shown_problems_with_a_new_match(
        self, editor_client, job_url, matching_job, queued
    ):
        ImportJob.objects.filter(pk=matching_job.pk).update(status=Status.IMPORTED)
        response = editor_client.post(
            job_url(matching_job, "columns"), {"col-0": "name"}
        )
        assert response.status_code == 302
        assert response.url == matching_job.get_absolute_url()


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
    return ImportRow.objects.bulk_create(
        ImportRow(
            job=job,
            number=start + n,
            line=start + n + 1,
            outcome=outcome,
            label=f"r{n}",
        )
        for n in range(count)
    )


@pytest.fixture
def small_pages(monkeypatch):
    """List two rows to a page of a job."""
    monkeypatch.setattr(JobDetail, "per_page", 2)


class TestJobDetail:
    """The check and its outcome, with the actions that move a job on."""

    def test_a_warning_about_the_columns_is_on_the_page_after_an_upload(
        self, upload, editor_client, rock_csv, queued
    ):
        upload("rocks.csv", rock_csv, mode="both")
        job = ImportJob.objects.get()
        response = editor_client.get(job.get_absolute_url())
        assert job.status == Status.CHECKING
        assert len(parse(response).select("[data-ie-warning]")) == 1

    def test_no_warning_is_shown_when_the_columns_hold_none(
        self, upload, editor_client, queued
    ):
        upload(
            "rocks.csv",
            b"name,rock_type,collection_date,local_id\nA,granite,2024-06-30,R-1\n",
            mode="both",
        )
        job = ImportJob.objects.get()
        response = editor_client.get(job.get_absolute_url())
        assert not parse(response).select("[data-ie-warning]")

    def rows_on(self, response):
        """Return the row elements of a page."""
        return parse(response).select("[data-ie-row]")

    def test_rows_are_listed_by_outcome_a_page_at_a_time(
        self, editor_client, job_url, checked_job, small_pages
    ):
        add_rows(checked_job, Outcome.NEW, 3)
        add_rows(checked_job, Outcome.UPDATE, 1, start=4)
        address = job_url(checked_job)
        assert len(self.rows_on(editor_client.get(address + "?show=new"))) == 2
        assert len(self.rows_on(editor_client.get(address + "?show=new&page=2"))) == 1
        assert len(self.rows_on(editor_client.get(address + "?show=update"))) == 1

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

    def test_a_page_number_out_of_range_or_not_a_number_is_not_an_error(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 3)
        shown = {}
        for page in ("9", "-2", "x"):
            response = editor_client.get(
                job_url(checked_job) + f"?show=new&page={page}"
            )
            shown[page] = (response.status_code, len(self.rows_on(response)))
        assert shown == {"9": (200, 0), "-2": (200, 3), "x": (200, 3)}

    def test_the_pager_links_to_the_pages_either_side(
        self, editor_client, job_url, checked_job, small_pages
    ):
        add_rows(checked_job, Outcome.NEW, 5)
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

    @pytest.mark.parametrize(
        ("status", "current"),
        [(Status.CHECKED, 2), (Status.IMPORTED, 3)],
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

    @pytest.mark.parametrize("status", [Status.PROBLEMS, Status.NOTHING])
    def test_a_job_that_may_be_matched_again_offers_to_do_so_or_to_check_again(
        self, editor_client, job_url, checked_job, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        page = parse(editor_client.get(job_url(checked_job)))
        assert page.select(f'a[href="{job_url(checked_job, "columns")}"]')
        assert page.select('form button[name=action][value="recheck"]')

    @pytest.mark.parametrize("status", [Status.IMPORTED, Status.FAILED])
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

    @pytest.fixture
    def read_job(self, make_job):
        """A job whose file is read: one new rock, one rock with a problem."""
        job = make_job(
            [
                {
                    "name": "Granite A",
                    "rock_type": "granite",
                    "collection_date": "2024-06-30",
                },
                {
                    "name": "Bad date",
                    "rock_type": "basalt",
                    "collection_date": "not a date",
                },
            ],
            status=Status.PROBLEMS,
        )
        ImportRowFactory(job=job, number=1, line=2, outcome=Outcome.NEW)
        ImportRowFactory(
            job=job,
            number=2,
            line=3,
            outcome=Outcome.PROBLEM,
            label="Row 2",
            problems=[{"column": "collection_date", "message": "not a date"}],
        )
        ImportJob.objects.filter(pk=job.pk).update(
            summary={"new": 1, "problem": 1}, row_count=2
        )
        job.refresh_from_db()
        return job

    def labels_on(self, response):
        """Return the label of each row on a page."""
        return [
            item.get_text(strip=True)
            for item in parse(response).select("[data-ie-row] .ie-row__label")
        ]

    def test_a_problem_row_is_named_by_its_name_in_the_file(
        self, editor_client, job_url, read_job
    ):
        response = editor_client.get(job_url(read_job))
        assert self.labels_on(response) == ["Bad date"]

    def test_a_new_row_lists_the_values_the_file_gives_it(
        self, editor_client, job_url, read_job
    ):
        page = parse(editor_client.get(job_url(read_job) + "?show=new"))
        cells = page.select_one("[data-ie-row] .ie-cells").get_text(" ", strip=True)
        assert "granite" in cells
        assert "2024-06-30" in cells
        assert "Granite A" not in cells

    def test_a_problem_row_without_its_stored_file_is_named_by_its_number(
        self, editor_client, job_url, read_job
    ):
        ImportRun(read_job).delete_file()
        response = editor_client.get(job_url(read_job))
        assert self.labels_on(response) == ["Row 2"]

    def test_a_new_row_without_its_stored_file_lists_no_cell(
        self, editor_client, job_url, read_job
    ):
        ImportRun(read_job).delete_file()
        response = editor_client.get(job_url(read_job) + "?show=new")
        assert not parse(response).select("[data-ie-row] .ie-cells")

    def test_an_imported_row_is_named_by_its_record_and_lists_no_cell(
        self, editor_client, job_url, imported_job
    ):
        job, added, _changed = imported_job
        response = editor_client.get(job_url(job) + "?show=new")
        assert self.labels_on(response) == [added.name]
        assert not parse(response).select("[data-ie-row] .ie-cells")

    def test_a_job_still_matching_goes_to_the_matching_page(
        self, editor_client, job_url, matching_job
    ):
        response = editor_client.get(job_url(matching_job))
        assert response.status_code == 302
        assert response.url == job_url(matching_job, "columns")

    def test_a_job_that_is_running_shows_the_progress_component(
        self, editor_client, job_url, checked_job
    ):
        add_rows(checked_job, Outcome.NEW, 2)
        ImportJob.objects.filter(pk=checked_job.pk).update(status=Status.CHECKING)
        page = parse(editor_client.get(job_url(checked_job)))
        bar = page.select_one("[data-ie-progress]")
        assert bar["hx-get"] == job_url(checked_job, "status")
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
        assert queued == [(tasks.import_job, (checked_job.pk, editor.pk))]

    def test_a_double_post_of_import_queues_one_task(
        self, editor_client, job_url, checked_job, queued
    ):
        self.post(editor_client, job_url(checked_job), "import")
        self.post(editor_client, job_url(checked_job), "import")
        assert len(queued) == 1

    @pytest.mark.parametrize(
        "status", [Status.PROBLEMS, Status.IMPORTING, Status.IMPORTED]
    )
    def test_import_is_refused_in_any_other_status_and_writes_nothing(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        assert not queued

    def test_import_is_refused_for_a_checked_job_with_nothing_to_write(
        self, editor_client, job_url, checked_job, queued
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(summary={"unchanged": 2})
        self.post(editor_client, job_url(checked_job), "import")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKED
        assert not queued

    @pytest.mark.parametrize("status", [Status.CHECKED, Status.NOTHING])
    def test_recheck_queues_a_new_check(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "recheck")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKING
        assert queued == [(tasks.check_job, (checked_job.pk,))]

    @pytest.mark.parametrize("status", [Status.IMPORTED, Status.CHECKING])
    def test_recheck_is_refused_in_any_other_status(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "recheck")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        assert not queued

    @pytest.mark.parametrize("status", [Status.PROBLEMS, Status.NOTHING])
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
        assert not queued

    def test_discard_leaves_the_rows_no_changed_cell(
        self, editor_client, job_url, checked_job, queued
    ):
        ImportRowFactory(
            job=checked_job,
            outcome=Outcome.UPDATE,
            changes=[{"column": "name", "label": "Name", "old": "A", "new": "B"}],
        )
        self.post(editor_client, job_url(checked_job), "discard")
        assert not checked_job.rows.exclude(changes=[]).exists()
        assert checked_job.rows.count() == 1

    @pytest.mark.parametrize("status", [Status.IMPORTED, Status.IMPORTING])
    def test_discard_is_refused_in_any_other_status(
        self, editor_client, job_url, checked_job, queued, status
    ):
        ImportJob.objects.filter(pk=checked_job.pk).update(status=status)
        self.post(editor_client, job_url(checked_job), "discard")
        checked_job.refresh_from_db()
        assert checked_job.status == status
        assert checked_job.file
        assert not queued

    def test_an_action_the_page_does_not_know_changes_nothing(
        self, editor_client, job_url, checked_job, queued
    ):
        self.post(editor_client, job_url(checked_job), "explode")
        checked_job.refresh_from_db()
        assert checked_job.status == Status.CHECKED
        assert not queued


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
        cache.clear()
        yield checked_job
        cache.clear()

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
        assert root["hx-get"] == job_url(running, "status")

    def test_each_kind_of_work_is_labelled_apart(self, editor_client, job_url, running):
        labels = {}
        for status in (Status.CHECKING, Status.IMPORTING, Status.UNDOING):
            ImportJob.objects.filter(pk=running.pk).update(status=status)
            page = parse(editor_client.get(job_url(running, "status")))
            labels[status] = page.select_one("[role=progressbar]")["aria-label"]
        assert len(set(labels.values())) == 3

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

    @pytest.mark.parametrize("status", [Status.CHECKED, Status.FAILED])
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

    @pytest.mark.parametrize("status", [Status.CHECKED, Status.CHECKING])
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

    @pytest.mark.parametrize("kind", ["sample", "measurement"])
    def test_one_kind_lists_its_types_only(self, open_dataset, kind):
        chooser = import_chooser(open_dataset, kind)
        names = [d.name for d in import_definitions.all(kind)]
        urls = [e["url"] for e in chooser["groups"][0]["entries"]]
        assert [group["kind"] for group in chooser["groups"]] == [kind]
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
        RockSampleFactory.create_batch(2, dataset=open_dataset)
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

    def test_each_job_names_its_type(self, editor_client, open_dataset):
        job = ImportJobFactory(dataset=open_dataset)
        page = parse(editor_client.get(reverse(open_dataset, "imports")))
        meta = page.select_one("[data-ie-job] .ie-job__meta").get_text().lower()
        assert job.type_name.lower() in meta


def import_row_for(job, record, outcome, number, **overrides):
    """Store the row an import of the record would have left on the job."""
    fresh = type(record).objects.get(pk=record.pk)
    return ImportRowFactory(
        job=job,
        number=number,
        outcome=outcome,
        record_pk=record.pk,
        label=record.name,
        digest=ImportUndo(job).digest(fresh),
        changes=[{"column": "name", "label": "Name", "old": "a", "new": "b"}],
        **overrides,
    )


@pytest.fixture
def imported_job(open_dataset):
    """An imported job that added one rock and changed another.

    Returns:
        The job, the added rock and the changed rock.
    """
    job = ImportJobFactory(dataset=open_dataset, status=Status.IMPORTED)
    added = RockSampleFactory(
        dataset=open_dataset, name="Brand new", local_id="NEW", rock_type="basalt"
    )
    changed = RockSampleFactory(
        dataset=open_dataset, local_id="OLD", hardness_mohs="6.5", rock_type="granite"
    )
    import_row_for(job, added, Outcome.NEW, 1)
    import_row_for(job, changed, Outcome.UPDATE, 2, before={"hardness_mohs": "7.0"})
    return (
        job,
        RockSample.objects.get(pk=added.pk),
        RockSample.objects.get(pk=changed.pk),
    )


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
        assert queued == [(tasks.undo_job, (job.pk, editor.pk))]
        assert RockSample.objects.filter(pk=added.pk).exists()
        assert str(RockSample.objects.get(pk=changed.pk).hardness_mohs) == "6.5"

    def test_anyone_with_the_edit_level_may_undo_not_only_who_imported(
        self, client, open_dataset, person_at, job_url, imported_job, queued
    ):
        job, _added, _changed = imported_job
        other = person_at(open_dataset, ContributionLevel.EDIT)
        client.force_login(other)
        self.post(client, job_url(job))
        job.refresh_from_db()
        assert job.status == Status.UNDOING
        assert queued == [(tasks.undo_job, (job.pk, other.pk))]

    @pytest.mark.parametrize("status", [Status.CHECKED, Status.UNDOING])
    def test_undo_is_refused_in_any_other_status(
        self, editor_client, job_url, imported_job, queued, status
    ):
        job, added, _changed = imported_job
        ImportJob.objects.filter(pk=job.pk).update(status=status)
        self.post(editor_client, job_url(job))
        job.refresh_from_db()
        assert job.status == status
        assert RockSample.objects.filter(pk=added.pk).exists()
        assert not queued

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

    def test_a_changed_record_replaces_the_undo_button_with_a_note_naming_it(
        self, editor_client, job_url, imported_job
    ):
        job, _added, changed = imported_job
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        page = parse(editor_client.get(job_url(job)))
        note = page.select_one("[data-ie-no-undo]")
        assert note is not None
        assert job.rows.get(record_pk=changed.pk).label in note.get_text()
        assert not page.select('button[value="undo"]')
        assert not page.select("dialog#ie-undo")

    def test_the_note_names_three_records_and_counts_the_rest(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        ImportRow.objects.bulk_create(
            ImportRow(job=job, number=100 + n, line=n, outcome="new", record_pk=n)
            for n in range(1, 6)
        )
        page = parse(editor_client.get(job_url(job)))
        assert len(page.select("[data-ie-no-undo] [data-ie-in-the-way]")) == 3
        assert page.select_one("[data-ie-no-undo] [data-ie-more]") is not None

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
        assert not page.select("[data-ie-no-undo], [data-ie-refusal]")

    def test_an_undoing_job_shows_the_progress_and_no_undo_button(
        self, editor_client, job_url, imported_job
    ):
        job, _added, _changed = imported_job
        ImportJob.objects.filter(pk=job.pk).update(status=Status.UNDOING)
        page = parse(editor_client.get(job_url(job)))
        assert page.select_one("[data-ie-progress]")["hx-get"] == job_url(job, "status")
        assert not page.select('button[value="undo"]')

    def test_the_job_page_of_an_imported_job_runs_the_same_queries_for_more_rows(
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

        add(0, 1)
        few = count()
        add(1, 4)
        assert count() == few


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

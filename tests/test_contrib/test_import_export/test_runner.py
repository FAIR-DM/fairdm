"""Tests for fairdm/contrib/import_export/runner.py."""

import json
from pathlib import Path
from unittest import mock

import pytest
from django.core.files.base import ContentFile
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.factories import RockSampleFactory
from demo.models import ICP_MS_Measurement, RockSample
from fairdm.contrib.import_export.exports import TableExport
from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.contrib.import_export.undo import ImportUndo
from fairdm.core.dataset.models import Dataset
from fairdm.factories import DatasetFactory, UserFactory
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db

Status = ImportJob.Status
Outcome = ImportRow.Outcome


def rock(name="Granite", **overrides):
    """Return the cells of a new rock with every required column filled."""
    row = {"name": name, "rock_type": "granite", "collection_date": "2024-06-30"}
    row.update(overrides)
    return row


def outcomes(job):
    """Return the outcome of each of the job's rows, in the file's order."""
    return list(job.rows.order_by("number").values_list("outcome", flat=True))


def checked(job):
    """Run the check on a job and return the job as stored."""
    ImportRun(job).check()
    job.refresh_from_db()
    return job


def importing(job, user=None):
    """Check a job, then run its import as the person who started it."""
    checked(job)
    assert job.status == Status.CHECKED
    ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
    ImportRun(job).perform(user)
    job.refresh_from_db()
    return job


class TestCheck:
    """The check reads the file and keeps the outcome of every row."""

    def test_writes_nothing_to_the_dataset(self, make_job, open_dataset):
        job = make_job([rock("A"), rock("B")])
        before = RockSample.objects.count()
        checked(job)
        assert RockSample.objects.count() == before
        assert job.status == Status.CHECKED
        assert job.row_count == 2
        assert job.summary == {"new": 2}
        assert job.checked_at is not None
        assert job.error == ""

    def test_keeps_every_outcome(self, make_job, open_dataset):
        same = RockSampleFactory(
            dataset=open_dataset,
            local_id="SAME",
            name="Same",
            rock_type="granite",
            collection_date="2024-06-30",
            weight_grams=None,
            mineral_content="",
            hardness_mohs=None,
        )
        old = RockSampleFactory(
            dataset=open_dataset,
            local_id="OLD",
            name="Old",
            rock_type="granite",
            collection_date="2024-06-30",
        )
        job = make_job(
            [
                rock("New"),
                rock("Old", local_id="OLD", rock_type="basalt"),
                rock("Same", local_id=same.local_id),
                rock("", local_id="BAD"),
                rock("Bad date", collection_date="not a date"),
            ]
        )
        checked(job)
        assert outcomes(job) == [
            Outcome.NEW,
            Outcome.UPDATE,
            Outcome.UNCHANGED,
            Outcome.PROBLEM,
            Outcome.PROBLEM,
        ]
        assert job.status == Status.PROBLEMS
        assert job.summary == {"new": 1, "update": 1, "unchanged": 1, "problem": 2}
        rows = {row.number: row for row in job.rows.all()}
        assert [change["column"] for change in rows[2].changes] == ["rock_type"]
        assert rows[2].changes[0]["old"] == "granite"
        assert rows[2].changes[0]["new"] == "basalt"
        assert rows[2].portal_id == old.uuid
        assert rows[2].record_pk is None
        assert rows[4].problems[0]["column"] == "name"
        assert rows[5].problems[0]["column"] == "collection_date"
        assert rows[1].line == 2
        assert rows[5].line == 6

    def test_a_row_left_out_keeps_its_reason(self, make_job, open_dataset):
        RockSampleFactory(dataset=open_dataset, local_id="HERE")
        job = make_job([rock("Again", local_id="HERE")], mode="add")
        checked(job)
        row = job.rows.get()
        assert row.outcome == Outcome.SKIPPED
        assert row.note
        assert job.status == Status.NOTHING

    def test_a_file_of_unchanged_rows_has_nothing_to_import(
        self, make_job, open_dataset
    ):
        record = RockSampleFactory(
            dataset=open_dataset,
            name="Same",
            rock_type="granite",
            collection_date="2024-06-30",
            weight_grams=None,
            mineral_content="",
            hardness_mohs=None,
        )
        job = make_job([rock("Same", portal_id=record.uuid)])
        checked(job)
        assert job.status == Status.NOTHING

    def test_a_second_check_replaces_the_rows(self, make_job):
        job = make_job([rock("A"), rock("B")])
        checked(job)
        checked(job)
        assert job.rows.count() == 2

    def test_ignored_headings_are_not_read(self, make_job):
        job = make_job(
            [{**rock("A"), "Notes": "zzsentinel"}],
            column_map={
                "name": "name",
                "rock_type": "rock_type",
                "collection_date": "collection_date",
                "Notes": "",
            },
        )
        checked(job)
        assert job.status == Status.CHECKED

    def test_progress_is_written_every_ten_rows(self, make_job, recorded_cache):
        job = make_job([rock(f"Rock {number}") for number in range(25)])

        checked(job)

        written = [
            value
            for key, value in recorded_cache.written
            if key == ImportRun(job).progress_key
        ]
        assert written[:2] == [10, 20]
        assert ImportRun(job).progress() is None


class TestDuplicateRecords:
    """Two rows about one record both need changes."""

    def test_two_rows_with_one_local_id_are_problems(self, make_job):
        job = make_job([rock("A", local_id="L1"), rock("B", local_id="L1")])
        checked(job)
        assert outcomes(job) == [Outcome.PROBLEM, Outcome.PROBLEM]

    def test_a_portal_id_and_a_local_id_of_one_record(self, make_job, open_dataset):
        record = RockSampleFactory(dataset=open_dataset, local_id="L2")
        job = make_job(
            [
                rock("A", portal_id=record.uuid, rock_type="basalt"),
                rock("B", local_id="L2", rock_type="slate"),
                rock("Other"),
            ]
        )
        checked(job)
        assert outcomes(job) == [Outcome.PROBLEM, Outcome.PROBLEM, Outcome.NEW]
        assert job.status == Status.PROBLEMS

    def test_the_record_two_rows_share_is_never_written(self, make_job, open_dataset):
        record = RockSampleFactory(dataset=open_dataset, local_id="L3", name="Keep")
        job = make_job(
            [
                rock("A", portal_id=record.uuid),
                rock("B", local_id="L3", rock_type="slate"),
            ]
        )
        checked(job)
        record.refresh_from_db()
        assert record.name == "Keep"


class TestPerform:
    """The import writes what the check showed, once, inside one transaction."""

    def test_writes_what_the_check_showed(self, make_job, open_dataset):
        user = UserFactory()
        old = RockSampleFactory(
            dataset=open_dataset,
            local_id="OLD",
            name="Old",
            rock_type="granite",
            collection_date="2024-06-30",
        )
        job = make_job(
            [
                rock("Fresh", local_id="FRESH"),
                rock("Old", local_id="OLD", rock_type="x"),
            ]
        )
        importing(job, user)
        assert job.status == Status.IMPORTED
        assert job.imported_by == user
        assert job.imported_at is not None
        fresh = RockSample.objects.get(local_id="FRESH")
        old.refresh_from_db()
        assert old.rock_type == "x"
        rows = {row.number: row for row in job.rows.all()}
        assert rows[1].record_pk == fresh.pk
        assert rows[1].portal_id == fresh.uuid
        assert rows[1].digest == ImportUndo(job).digest(fresh)
        assert rows[2].record_pk == old.pk
        assert rows[2].digest == ImportUndo(job).digest(old)
        assert rows[2].before == {"rock_type": "granite"}
        assert rows[1].before == {}

    def test_the_before_values_use_the_stored_encoding(self, make_job, open_dataset):
        old = RockSampleFactory(
            dataset=open_dataset, local_id="OLD", hardness_mohs="7.0", weight_grams=2.5
        )
        job = make_job(
            [rock(old.name, local_id="OLD", hardness_mohs="6.5", weight_grams="3")]
        )
        importing(job)
        row = job.rows.get()
        assert row.before["hardness_mohs"] == "7.0"
        assert row.before["weight_grams"] == "2.5"
        json.dumps(row.before)

    def test_a_failure_while_recording_writes_nothing(self, make_job):
        job = make_job([rock("A"), rock("B")])
        checked(job)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        with (
            mock.patch.object(
                ImportRun, "record_outcomes", side_effect=RuntimeError("boom")
            ),
            pytest.raises(RuntimeError),
        ):
            ImportRun(job).perform(None)
        assert RockSample.objects.count() == 0

    def test_the_second_of_two_imports_is_checked_again(self, make_job):
        first = make_job([rock("A", local_id="TWICE")])
        second = make_job([rock("A", local_id="TWICE")])
        checked(first)
        checked(second)
        assert outcomes(second) == [Outcome.NEW]
        for job in (first, second):
            ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
            ImportRun(job).perform(None)
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.status == Status.IMPORTED
        assert RockSample.objects.filter(local_id="TWICE").count() == 1
        assert second.status == Status.NOTHING
        assert second.error
        assert outcomes(second) == [Outcome.UNCHANGED]

    def test_a_changed_dataset_returns_to_the_check(self, make_job, open_dataset):
        record = RockSampleFactory(
            dataset=open_dataset,
            local_id="CH",
            name="Was",
            rock_type="granite",
            collection_date="2024-06-30",
            weight_grams=None,
            mineral_content="",
            hardness_mohs=None,
        )
        job = make_job([rock("Was", local_id="CH", rock_type="basalt")])
        checked(job)
        RockSample.objects.filter(pk=record.pk).update(rock_type="basalt")
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        ImportRun(job).perform(None)
        job.refresh_from_db()
        assert job.status == Status.NOTHING
        assert job.error
        assert job.imported_at is None
        assert outcomes(job) == [Outcome.UNCHANGED]
        assert job.rows.get().record_pk is None

    def test_a_deleted_record_returns_to_the_check_and_saves_nothing(
        self, make_job, open_dataset
    ):
        record = RockSampleFactory(dataset=open_dataset, local_id="GONE")
        job = make_job([rock("Gone", local_id="GONE", rock_type="basalt")])
        checked(job)
        assert outcomes(job) == [Outcome.UPDATE]
        record.delete()
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        ImportRun(job).perform(None)
        job.refresh_from_db()
        assert job.status == Status.CHECKED
        assert job.error
        assert outcomes(job) == [Outcome.NEW]
        assert RockSample.objects.count() == 0

    def test_a_file_that_gains_a_problem_returns_to_the_check(self, make_job):
        record = RockSampleFactory(local_id="P")
        job = make_job([rock("A", local_id="P")], dataset=record.dataset)
        checked(job)
        other = RockSampleFactory(dataset=record.dataset, local_id="P2")
        RockSample.objects.filter(pk=other.pk).update(local_id="P")
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        ImportRun(job).perform(None)
        job.refresh_from_db()
        assert job.status == Status.PROBLEMS
        assert job.error

    def test_a_file_with_problems_writes_nothing(self, make_job):
        job = make_job([rock("A"), rock("", local_id="BAD")])
        checked(job)
        assert job.status == Status.PROBLEMS
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        ImportRun(job).perform(None)
        job.refresh_from_db()
        assert job.status == Status.PROBLEMS
        assert job.error
        assert job.imported_at is None
        assert RockSample.objects.count() == 0

    def test_a_private_dataset_imports(self, make_job):
        private = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        assert not Dataset.objects.filter(pk=private.pk).exists()
        job = make_job([rock("Secret")], dataset=private)
        importing(job)
        assert job.status == Status.IMPORTED
        assert RockSample.objects.filter(dataset=private).count() == 1

    def test_the_dataset_is_locked_before_anything_is_written(self, make_job):
        job = make_job([rock("A")])
        checked(job)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        with CaptureQueriesContext(connection) as queries:
            ImportRun(job).perform(None)
        sql = [query["sql"] for query in queries.captured_queries]
        table = Dataset._meta.db_table
        locks = [
            i
            for i, text in enumerate(sql)
            if "FOR UPDATE" in text and f'"{table}"' in text
        ]
        writes = [
            i
            for i, text in enumerate(sql)
            if text.startswith(("INSERT", "UPDATE", "DELETE"))
        ]
        assert locks
        assert writes
        assert min(locks) < min(writes)

    def test_a_job_not_importing_is_left_alone(self, make_job):
        job = make_job([rock("A")])
        checked(job)
        ImportRun(job).perform(None)
        job.refresh_from_db()
        assert job.status == Status.CHECKED
        assert RockSample.objects.count() == 0
        assert job.rows.get().record_pk is None
        assert job.file

    def test_the_status_is_read_again_under_the_lock(self, make_job):
        job = make_job([rock("A")])
        checked(job)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.IMPORTING)
        stale = ImportJob.objects.get(pk=job.pk)
        ImportJob.objects.filter(pk=job.pk).update(status=Status.DISCARDED)
        ImportRun(stale).perform(None)
        assert RockSample.objects.count() == 0


class TestFileDeleted:
    """No end state leaves the file or a cell of it behind."""

    SENTINEL = "zzsentinel"

    @pytest.fixture
    def job(self, make_job):
        """A job whose file and example values both hold a cell of the file."""
        return make_job(
            [{**rock("A"), "Notes": self.SENTINEL}],
            column_map={
                "name": "name",
                "rock_type": "rock_type",
                "collection_date": "collection_date",
                "Notes": "",
            },
            samples={"Notes": [self.SENTINEL]},
        )

    def assert_no_trace(self, job, path):
        """Check the file is gone and no field of the job or its rows holds a cell."""
        job.refresh_from_db()
        assert not job.file
        assert not Path(path).exists()
        assert job.samples == {}
        text = json.dumps(
            [
                job.headers,
                job.samples,
                job.summary,
                job.file_problems,
                job.error,
                list(
                    job.rows.values(
                        "label", "portal_id", "changes", "problems", "note", "before"
                    )
                ),
            ],
            default=str,
        )
        assert self.SENTINEL not in text

    def test_imported(self, job):
        path = job.file.path
        importing(job)
        assert job.status == Status.IMPORTED
        self.assert_no_trace(job, path)

    def test_failed(self, job):
        job.file.save("records.csv", ContentFile(b""))
        job.save()
        path = job.file.path
        checked(job)
        assert job.status == Status.FAILED
        assert job.error
        self.assert_no_trace(job, path)

    def test_discarded(self, job):
        path = job.file.path
        ImportJob.objects.filter(pk=job.pk).update(status=Status.DISCARDED)
        ImportRun(job).delete_file()
        self.assert_no_trace(job, path)


class TestRoundTrip:
    """A file exported from a records table and imported back changes nothing."""

    @pytest.mark.parametrize("model", [RockSample, ICP_MS_Measurement], ids=str)
    def test_every_row_is_unchanged(self, model, make_record, open_dataset):
        records = [make_record(model) for _ in range(2)]
        schema = registry.get_for_model(model).get_table_schema()
        response = TableExport(schema).response(
            model.objects.filter(pk__in=[r.pk for r in records]), "csv", "records"
        )
        job = ImportJob.objects.create(
            dataset=open_dataset,
            definition_name=model._meta.model_name,
            file=ContentFile(response.content, name="records.csv"),
            filename="records.csv",
            file_format="csv",
            status=Status.CHECKING,
            column_map={heading: heading for heading in schema.headings},
        )
        checked(job)
        assert outcomes(job) == [Outcome.UNCHANGED] * 2, [
            (row.problems, row.changes) for row in job.rows.all()
        ]
        assert job.status == Status.NOTHING


class TestLongLabel:
    """A name as long as the name field allows is still checked."""

    def test_a_280_character_name_reaches_checked(self, make_job, open_dataset):
        job = make_job([rock("N" * 280, local_id="LONG")])

        ImportRun(job).check()

        job.refresh_from_db()
        assert job.status == Status.CHECKED
        row = job.rows.get()
        assert len(row.label) <= ImportRow._meta.get_field("label").max_length
        assert row.label.startswith("N" * 100)

"""Tests for fairdm/contrib/import_export/undo.py."""

from datetime import timedelta
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from demo.models import RockSample
from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.contrib.import_export.undo import ImportUndo
from fairdm.core.dataset.models import Dataset
from fairdm.factories import ContributionFactory, SampleDescriptionFactory
from tests.factories import ImportJobFactory, ImportRowFactory

pytestmark = pytest.mark.django_db

CHANGES = [{"column": "hardness_mohs", "label": "Hardness", "old": "7.0", "new": "6.5"}]


class TestImportUndo:
    """What an undo keeps and compares."""

    class TestDigest:
        """The digest describes the record as the database holds it."""

        def test_changes_with_any_stored_value(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset, rock_type="granite")
            before = ImportUndo(import_job).digest(record)
            RockSample.objects.filter(pk=record.pk).update(rock_type="basalt")
            record.refresh_from_db()
            assert ImportUndo(import_job).digest(record) != before

        def test_changes_with_the_modified_time_alone(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset)
            before = ImportUndo(import_job).digest(record)
            RockSample.objects.filter(pk=record.pk).update(
                modified=record.modified + timedelta(seconds=1)
            )
            record.refresh_from_db()
            assert ImportUndo(import_job).digest(record) != before

        def test_is_the_same_for_two_reads(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset)
            first = ImportUndo(import_job).digest(RockSample.objects.get(pk=record.pk))
            second = ImportUndo(import_job).digest(RockSample.objects.get(pk=record.pk))
            assert first == second

        def test_equal_at_import_and_at_a_later_read(
            self, make_job, open_dataset, settings
        ):
            settings.TIME_ZONE = "Asia/Tokyo"
            record = RockSampleFactory(
                dataset=open_dataset, local_id="DEC", hardness_mohs="7.0"
            )
            job = make_job(
                [
                    {
                        "name": record.name,
                        "local_id": "DEC",
                        "rock_type": record.rock_type,
                        "collection_date": "2024-06-30",
                        "hardness_mohs": "6.5",
                    }
                ]
            )
            ImportRun(job).check()
            ImportJob.objects.filter(pk=job.pk).update(status="importing")
            ImportRun(job).perform(None)
            row = job.rows.get()
            later = RockSample.objects.get(pk=row.record_pk)
            assert str(later.hardness_mohs) == "6.5"
            assert row.digest == ImportUndo(job).digest(later)


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
        changes=CHANGES,
        **overrides,
    )


@pytest.fixture
def imported(open_dataset):
    """An imported job that added one rock and changed another.

    Returns:
        The job, the added rock and the changed rock, read back from the database.
    """
    job = ImportJobFactory(dataset=open_dataset, status=ImportJob.Status.IMPORTED)
    added = RockSampleFactory(
        dataset=open_dataset, name="Brand new", local_id="NEW", rock_type="basalt"
    )
    changed = RockSampleFactory(
        dataset=open_dataset, local_id="OLD", hardness_mohs="6.5", rock_type="granite"
    )
    import_row_for(job, added, ImportRow.Outcome.NEW, 1)
    import_row_for(
        job, changed, ImportRow.Outcome.UPDATE, 2, before={"hardness_mohs": "7.0"}
    )
    return (
        job,
        RockSample.objects.get(pk=added.pk),
        RockSample.objects.get(pk=changed.pk),
    )


@pytest.fixture
def editor_for_undo():
    """The person who undoes."""
    from fairdm.factories import PersonFactory

    return PersonFactory()


class TestConflicts:
    """What stands in the way of an undo."""

    def test_a_fresh_import_has_none(self, imported):
        job, _added, _changed = imported
        found = ImportUndo(job).conflicts()
        assert found["entries"] == []
        assert found["more"] == 0

    def test_an_edit_by_save_is_one(self, imported):
        job, added, _changed = imported
        added.refresh_from_db()
        added.save()
        found = ImportUndo(job).conflicts()
        assert [entry["pk"] for entry in found["entries"]] == [added.pk]

    def test_a_queryset_update_that_skips_modified_is_one(self, imported):
        job, _added, changed = imported
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        found = ImportUndo(job).conflicts()
        assert [entry["pk"] for entry in found["entries"]] == [changed.pk]

    def test_a_deleted_record_is_one(self, imported):
        job, added, _changed = imported
        pk = added.pk
        added.delete()
        found = ImportUndo(job).conflicts()
        assert [entry["pk"] for entry in found["entries"]] == [pk]

    def test_a_measurement_on_an_added_sample_is_one(self, imported):
        job, added, _changed = imported
        XRFMeasurementFactory(sample=added, dataset=added.dataset)
        found = ImportUndo(job).conflicts()
        assert [entry["pk"] for entry in found["entries"]] == [added.pk]

    def test_a_description_added_to_an_added_sample_is_one(self, imported):
        job, added, _changed = imported
        SampleDescriptionFactory(related=added)
        found = ImportUndo(job).conflicts()
        assert [(e["pk"], e["reason"]) for e in found["entries"]] == [
            (added.pk, "changed")
        ]

    def test_a_contributor_added_to_an_added_sample_is_one(self, imported):
        job, added, _changed = imported
        ContributionFactory(content_object=added)
        found = ImportUndo(job).conflicts()
        assert [(e["pk"], e["reason"]) for e in found["entries"]] == [
            (added.pk, "changed")
        ]

    def test_a_description_added_to_a_changed_sample_is_not_one(self, imported):
        job, _added, changed = imported
        SampleDescriptionFactory(related=changed)
        assert ImportUndo(job).conflicts()["entries"] == []

    def test_the_queries_do_not_grow_with_the_rows(self, open_dataset):
        def added_rows(how_many):
            job = ImportJobFactory(dataset=open_dataset, status="imported")
            for number in range(how_many):
                record = RockSampleFactory(dataset=open_dataset)
                import_row_for(job, record, ImportRow.Outcome.NEW, number + 1)
            return job

        def count(job):
            ImportUndo(job).conflicts()
            with CaptureQueriesContext(connection) as queries:
                ImportUndo(job).conflicts()
            return len(queries)

        assert count(added_rows(1)) == count(added_rows(3))

    def test_the_list_stops_at_the_limit_and_counts_the_rest(self, imported):
        job, added, changed = imported
        RockSample.objects.filter(pk__in=[added.pk, changed.pk]).update(
            rock_type="gabbro"
        )
        found = ImportUndo(job).conflicts(limit=1)
        assert len(found["entries"]) == 1
        assert found["more"] == 1


class TestUndo:
    """Putting a dataset back as the import found it."""

    @pytest.fixture
    def undoing(self, imported):
        """The imported job after the request has claimed it for the task."""
        job, added, changed = imported
        ImportJob.objects.filter(pk=job.pk).update(status=ImportJob.Status.UNDOING)
        job.refresh_from_db()
        return job, added, changed

    def test_the_added_record_is_deleted_and_the_changed_one_restored(self, undoing):
        job, added, changed = undoing
        assert str(changed.hardness_mohs) == "6.5"
        found = ImportUndo(job).undo(None)
        assert found["entries"] == []
        assert not RockSample.objects.filter(pk=added.pk).exists()
        changed.refresh_from_db()
        assert str(changed.hardness_mohs) == "7.0"

    def test_the_progress_counts_the_records_undone(self, undoing, recorded_cache):
        job, _added, _changed = undoing
        ImportUndo(job).undo(None)
        written = [
            value
            for key, value in recorded_cache.written
            if key == ImportRun(job).progress_key
        ]
        assert written[-1] == 2

    def test_the_job_moves_from_undoing_to_undone_with_who_and_when(
        self, undoing, editor_for_undo
    ):
        job, _added, _changed = undoing
        ImportUndo(job).undo(editor_for_undo)
        job.refresh_from_db()
        assert job.status == ImportJob.Status.UNDONE
        assert job.undone_by == editor_for_undo
        assert job.undone_at is not None
        assert not job.file
        assert job.rows.count() == 2

    def test_the_rows_keep_no_changed_cell_once_undone(self, undoing):
        job, _added, _changed = undoing
        assert job.rows.exclude(changes=[]).exists()
        ImportUndo(job).undo(None)
        assert not job.rows.exclude(changes=[]).exists()

    def test_a_refused_undo_keeps_the_changed_cells(self, undoing):
        job, added, _changed = undoing
        added.save()
        ImportUndo(job).undo(None)
        assert job.rows.exclude(changes=[]).exists()

    def test_the_dataset_is_locked_before_anything_is_written(self, undoing):
        job, _added, _changed = undoing
        with CaptureQueriesContext(connection) as queries:
            ImportUndo(job).undo(None)
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

    def test_the_records_read_for_the_conflicts_are_locked(self, undoing):
        job, _added, _changed = undoing
        with CaptureQueriesContext(connection) as queries:
            ImportUndo(job).undo(None)
        table = RockSample._meta.db_table
        locked = [
            q["sql"]
            for q in queries.captured_queries
            if "FOR UPDATE" in q["sql"] and f'"{table}"' in q["sql"]
        ]
        assert locked

    def test_a_failure_part_way_changes_nothing(self, undoing):
        job, added, changed = undoing
        with (
            mock.patch.object(ImportUndo, "restore_updated", side_effect=RuntimeError),
            pytest.raises(RuntimeError),
        ):
            ImportUndo(job).undo(None)
        job.refresh_from_db()
        assert job.status == ImportJob.Status.UNDOING
        assert RockSample.objects.filter(pk=added.pk).exists()
        changed.refresh_from_db()
        assert str(changed.hardness_mohs) == "6.5"

    def test_a_refused_undo_changes_no_record_and_returns_the_job_to_imported(
        self, undoing
    ):
        job, added, changed = undoing
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        found = ImportUndo(job).undo(None)
        assert [entry["pk"] for entry in found["entries"]] == [changed.pk]
        job.refresh_from_db()
        assert job.status == ImportJob.Status.IMPORTED
        assert job.undone_at is None
        assert RockSample.objects.filter(pk=added.pk).exists()
        changed.refresh_from_db()
        assert changed.rock_type == "gabbro"
        assert str(changed.hardness_mohs) == "6.5"

    def test_a_refusal_is_kept_on_the_job_naming_twenty_records_and_counting_the_rest(
        self, undoing
    ):
        job, _added, _changed = undoing
        ImportRow.objects.bulk_create(
            ImportRow(
                job=job,
                number=100 + n,
                line=n,
                outcome="new",
                record_pk=n,
                label=f"L{n}",
            )
            for n in range(1, 31)
        )
        ImportUndo(job).undo(None)
        job.refresh_from_db()
        lines = job.error.splitlines()
        assert len(lines) == 21
        assert lines[0].startswith("L1")
        assert "10" in lines[-1]

    @pytest.mark.parametrize(
        "status", [ImportJob.Status.IMPORTED, ImportJob.Status.UNDONE]
    )
    def test_a_job_that_is_not_undoing_is_left_alone(self, imported, status):
        job, added, _changed = imported
        ImportJob.objects.filter(pk=job.pk).update(status=status)
        assert ImportUndo(job).undo(None) is None
        assert RockSample.objects.filter(pk=added.pk).exists()

    def test_the_job_returns_to_imported_with_the_message_when_released(self, undoing):
        job, added, _changed = undoing
        ImportUndo(job).release("It broke.")
        job.refresh_from_db()
        assert job.status == ImportJob.Status.IMPORTED
        assert job.error == "It broke."
        assert RockSample.objects.filter(pk=added.pk).exists()

    def test_a_release_leaves_a_job_that_is_not_undoing_alone(self, imported):
        job, _added, _changed = imported
        ImportUndo(job).release("It broke.")
        job.refresh_from_db()
        assert job.error == ""


class TestUndoOfEmptyValues:
    """An import that filled fields that were empty is undone to empty fields."""

    def test_fields_that_were_empty_are_empty_again(
        self, make_job, open_dataset, editor_for_undo
    ):
        record = RockSampleFactory(
            dataset=open_dataset,
            local_id="EMPTY",
            hardness_mohs=None,
            weight_grams=None,
            location=None,
        )
        job = make_job(
            [
                {
                    "name": record.name,
                    "local_id": "EMPTY",
                    "rock_type": record.rock_type,
                    "collection_date": "2024-06-30",
                    "hardness_mohs": "6.5",
                    "weight_grams": "12",
                    "latitude": "10",
                    "longitude": "20",
                }
            ]
        )
        ImportRun(job).check()
        ImportJob.objects.filter(pk=job.pk).update(status=ImportJob.Status.IMPORTING)
        ImportRun(job).perform(editor_for_undo)
        job.refresh_from_db()
        filled = RockSample.objects.get(pk=record.pk)
        assert filled.hardness_mohs is not None
        assert filled.weight_grams is not None
        assert filled.location is not None
        ImportJob.objects.filter(pk=job.pk).update(status=ImportJob.Status.UNDOING)
        job.refresh_from_db()

        found = ImportUndo(job).undo(None)

        assert found["entries"] == []
        job.refresh_from_db()
        assert job.status == ImportJob.Status.UNDONE
        restored = RockSample.objects.get(pk=record.pk)
        assert restored.hardness_mohs is None
        assert restored.weight_grams is None
        assert restored.location is None

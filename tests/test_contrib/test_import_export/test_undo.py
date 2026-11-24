"""Tests for fairdm/contrib/import_export/undo.py."""

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

pytestmark = pytest.mark.django_db


class TestImportUndo:
    """What an undo keeps and compares."""

    class TestDigest:
        """The digest describes the record as the database holds it."""

        def test_is_a_sha256_hex_string(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset)
            digest = ImportUndo(import_job).digest(record)
            assert len(digest) == 64
            int(digest, 16)

        def test_changes_with_any_stored_value(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset, rock_type="granite")
            before = ImportUndo(import_job).digest(record)
            RockSample.objects.filter(pk=record.pk).update(rock_type="basalt")
            record.refresh_from_db()
            assert ImportUndo(import_job).digest(record) != before

        def test_changes_with_the_modified_time_alone(self, import_job, open_dataset):
            record = RockSampleFactory(dataset=open_dataset)
            before = ImportUndo(import_job).digest(record)
            record.save()
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


@pytest.fixture
def imported(make_job, open_dataset, editor_for_undo):
    """An imported job that added one rock and changed another.

    Returns:
        The job, the added rock and the changed rock, read back from the database.
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
    ImportJob.objects.filter(pk=job.pk).update(status=ImportJob.Status.IMPORTING)
    ImportRun(job).perform(editor_for_undo)
    job.refresh_from_db()
    assert job.status == ImportJob.Status.IMPORTED
    added = RockSample.objects.get(dataset=open_dataset, local_id="NEW")
    return job, added, RockSample.objects.get(pk=changed.pk)


@pytest.fixture
def editor_for_undo():
    """The person who undoes."""
    from fairdm.factories import PersonFactory

    return PersonFactory()


class TestConflicts:
    """What stands in the way of an undo."""

    def test_a_fresh_import_has_none(self, imported):
        job, _added, _changed = imported
        found = ImportUndo(job).conflicts(None)
        assert found["entries"] == []
        assert found["more"] == 0

    def test_an_edit_by_save_is_one(self, imported):
        job, added, _changed = imported
        added.refresh_from_db()
        added.save()
        found = ImportUndo(job).conflicts(None)
        assert [entry["pk"] for entry in found["entries"]] == [added.pk]

    def test_a_queryset_update_that_skips_modified_is_one(self, imported):
        job, _added, changed = imported
        RockSample.objects.filter(pk=changed.pk).update(rock_type="gabbro")
        found = ImportUndo(job).conflicts(None)
        assert [entry["pk"] for entry in found["entries"]] == [changed.pk]

    def test_a_deleted_record_is_one(self, imported):
        job, added, _changed = imported
        pk = added.pk
        added.delete()
        found = ImportUndo(job).conflicts(None)
        assert [entry["pk"] for entry in found["entries"]] == [pk]

    def test_a_measurement_on_an_added_sample_is_one(self, imported):
        job, added, _changed = imported
        XRFMeasurementFactory(sample=added, dataset=added.dataset)
        found = ImportUndo(job).conflicts(None)
        assert [entry["pk"] for entry in found["entries"]] == [added.pk]

    def test_the_list_stops_at_the_limit_and_counts_the_rest(self, imported):
        job, added, changed = imported
        RockSample.objects.filter(pk__in=[added.pk, changed.pk]).update(
            rock_type="gabbro"
        )
        found = ImportUndo(job).conflicts(None, limit=1)
        assert len(found["entries"]) == 1
        assert found["more"] == 1

    def test_the_default_limit_is_twenty(self, imported, open_dataset):
        job, _added, _changed = imported
        rows = [
            ImportRow(job=job, number=100 + n, line=n, outcome="new", record_pk=n)
            for n in range(1, 31)
        ]
        ImportRow.objects.bulk_create(rows)
        found = ImportUndo(job).conflicts(None)
        assert len(found["entries"]) == 20
        assert found["more"] == 10


class TestUndo:
    """Putting a dataset back as the import found it."""

    def test_the_added_record_is_deleted_and_the_changed_one_restored(self, imported):
        job, added, changed = imported
        assert str(changed.hardness_mohs) == "6.5"
        found = ImportUndo(job).undo(None)
        assert found["entries"] == []
        assert not RockSample.objects.filter(pk=added.pk).exists()
        changed.refresh_from_db()
        assert str(changed.hardness_mohs) == "7.0"

    def test_the_job_records_who_and_when(self, imported, editor_for_undo):
        job, _added, _changed = imported
        ImportUndo(job).undo(editor_for_undo)
        job.refresh_from_db()
        assert job.status == ImportJob.Status.UNDONE
        assert job.undone_by == editor_for_undo
        assert job.undone_at is not None
        assert not job.file
        assert job.rows.count() == 2

    def test_the_dataset_is_locked_before_anything_is_written(self, imported):
        job, _added, _changed = imported
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

    def test_a_failure_part_way_changes_nothing(self, imported):
        job, added, changed = imported
        with (
            mock.patch.object(ImportUndo, "restore_updated", side_effect=RuntimeError),
            pytest.raises(RuntimeError),
        ):
            ImportUndo(job).undo(None)
        job.refresh_from_db()
        assert job.status == ImportJob.Status.IMPORTED
        assert RockSample.objects.filter(pk=added.pk).exists()
        changed.refresh_from_db()
        assert str(changed.hardness_mohs) == "6.5"

    def test_a_refused_undo_changes_nothing(self, imported):
        job, added, changed = imported
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

    def test_a_job_that_is_not_imported_is_left_alone(self, imported):
        job, added, _changed = imported
        ImportJob.objects.filter(pk=job.pk).update(status=ImportJob.Status.UNDONE)
        assert ImportUndo(job).undo(None) is None
        assert RockSample.objects.filter(pk=added.pk).exists()

    def test_a_second_undo_does_nothing(self, imported):
        job, _added, _changed = imported
        ImportUndo(job).undo(None)
        with mock.patch.object(ImportUndo, "delete_created") as deleted:
            assert ImportUndo(job).undo(None) is None
        deleted.assert_not_called()

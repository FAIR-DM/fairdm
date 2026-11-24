"""Tests for fairdm/contrib/import_export/undo.py."""

import pytest
from fairdm.contrib.import_export.runner import ImportRun
from fairdm.contrib.import_export.undo import ImportUndo

from demo.factories import RockSampleFactory
from demo.models import RockSample
from fairdm.contrib.import_export.models import ImportJob

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

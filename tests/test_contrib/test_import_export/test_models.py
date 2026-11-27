"""Tests for fairdm/contrib/import_export/models.py."""

import datetime
import re

import pytest
from django.db import models

from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.core.dataset.models import Dataset
from fairdm.factories import DatasetFactory
from tests.factories import ImportJobFactory, ImportRowFactory

RUNNING = {"checking", "importing", "undoing"}
FINISHED = {"imported", "undone", "discarded", "failed"}


@pytest.fixture
def media(settings, tmp_path):
    """Store uploaded files in a folder of the test's own."""
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


class TestImportJobProperties:
    """What a job reports about itself without being stored."""

    def test_a_new_job_waits_for_column_matching(self):
        assert ImportJob().status == ImportJob.Status.MATCHING

    def test_a_job_is_running_only_while_checking_importing_or_undoing(self):
        running = {
            status
            for status in ImportJob.Status.values
            if ImportJob(status=status).is_running
        }

        assert running == RUNNING

    def test_a_job_is_finished_once_it_has_an_outcome(self):
        finished = {
            status
            for status in ImportJob.Status.values
            if ImportJob(status=status).is_finished
        }

        assert finished == FINISHED

    def test_writes_counts_the_rows_added_and_updated(self):
        job = ImportJob(summary={"new": 3, "update": 2, "unchanged": 9, "problem": 1})

        assert job.writes == 5

    def test_writes_is_zero_before_the_check(self):
        assert ImportJob(summary={}).writes == 0


@pytest.mark.django_db
class TestImportJob:
    """The record of one file, from upload to outcome."""

    def test_the_definition_is_found_by_name(self, import_job):
        assert import_job.definition.name == "rocksample"
        assert import_job.model._meta.model_name == "rocksample"

    def test_type_name_is_the_plural_name_of_the_type(self, import_job):
        assert import_job.type_name == str(import_job.model._meta.verbose_name_plural)

    def test_jobs_are_listed_newest_first(self):
        dataset = DatasetFactory()
        older = ImportJobFactory(dataset=dataset)
        newer = ImportJobFactory(dataset=dataset)
        ImportJob.objects.filter(pk=older.pk).update(
            created=newer.created - datetime.timedelta(days=1)
        )

        assert list(dataset.import_jobs.all()) == [newer, older]

    def test_deleting_a_job_deletes_its_stored_file(self, media):
        job = ImportJobFactory(with_file=True)
        storage, name = job.file.storage, job.file.name
        assert storage.exists(name)

        job.delete()

        assert not storage.exists(name)

    def test_deleting_a_job_whose_file_is_gone_does_not_fail(self):
        job = ImportJobFactory()

        job.delete()

        assert not ImportJob.objects.filter(pk=job.pk).exists()

    def test_deleting_a_dataset_deletes_its_jobs_and_their_files(self, media):
        job = ImportJobFactory(with_file=True)
        storage, name = job.file.storage, job.file.name

        job.dataset.delete()

        assert not ImportJob.objects.filter(pk=job.pk).exists()
        assert not storage.exists(name)

    def test_deleting_a_job_leaves_its_dataset(self, import_job):
        import_job.delete()

        assert Dataset.all_objects.filter(pk=import_job.dataset_id).exists()


@pytest.mark.django_db
class TestImportRow:
    """One row of a file as the check saw it."""

    def test_rows_come_in_the_order_of_the_file(self, import_job):
        third = ImportRowFactory(job=import_job, number=3)
        first = ImportRowFactory(job=import_job, number=1)
        second = ImportRowFactory(job=import_job, number=2)

        assert list(import_job.rows.all()) == [first, second, third]


class TestFieldDocumentation:
    """Every field of both models has a name and an explanation."""

    def test_every_field_has_a_verbose_name_and_help_text(self):
        undocumented = [
            f"{model.__name__}.{field.name}"
            for model in (ImportJob, ImportRow)
            for field in model._meta.get_fields()
            if isinstance(field, models.Field)
            and not field.auto_created
            and not (str(field.help_text) and field._verbose_name is not None)
        ]

        assert not undocumented


@pytest.mark.django_db
class TestStoredFileName:
    """An uploaded file is stored under a name nobody can guess."""

    def test_the_stored_name_holds_neither_the_upload_nor_a_date(self, make_job, media):
        from django.core.files.base import ContentFile

        job = make_job([{"name": "a", "local_id": "A"}])
        job.file.save("Rock-Sample-Template.XLSX", ContentFile(b"x"), save=False)

        assert re.fullmatch(r"imports/[0-9a-f]{32}\.xlsx", job.file.name)

    def test_two_uploads_of_one_name_are_stored_apart(self, make_job, media):
        from django.core.files.base import ContentFile

        job = make_job([{"name": "a", "local_id": "A"}])
        job.file.save("same.csv", ContentFile(b"x"), save=False)
        first = job.file.name
        job.file.save("same.csv", ContentFile(b"x"), save=False)

        assert job.file.name != first

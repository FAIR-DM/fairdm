"""Tests for fairdm/contrib/import_export/models.py."""

import datetime

import pytest
from django.db import models

from fairdm.contrib.import_export.models import ImportJob, ImportRow
from fairdm.core.dataset.models import Dataset
from fairdm.factories import DatasetFactory
from tests.factories import ImportJobFactory, ImportRowFactory

pytestmark = pytest.mark.django_db

RUNNING = {"checking", "importing", "undoing"}
FINISHED = {"imported", "undone", "discarded", "failed"}


class TestImportJob:
    """The record of one file, from upload to outcome."""

    def test_a_new_job_waits_for_column_matching(self):
        assert ImportJob().status == ImportJob.Status.MATCHING

    @pytest.mark.parametrize("status", ImportJob.Status.values)
    def test_a_job_is_running_only_while_checking_or_importing(self, status):
        job = ImportJob(status=status)

        assert job.is_running is (status in RUNNING)

    @pytest.mark.parametrize("status", ImportJob.Status.values)
    def test_a_job_is_finished_once_it_has_an_outcome(self, status):
        job = ImportJob(status=status)

        assert job.is_finished is (status in FINISHED)

    def test_writes_counts_the_rows_added_and_updated(self):
        job = ImportJob(summary={"new": 3, "update": 2, "unchanged": 9, "problem": 1})

        assert job.writes == 5

    def test_writes_is_zero_before_the_check(self):
        assert ImportJob(summary={}).writes == 0

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

    def test_a_job_keeps_the_dataset_and_definition_listing_index(self):
        indexed = [index.fields for index in ImportJob._meta.indexes]

        assert ["dataset", "definition_name", "created"] in indexed

    def test_a_factory_stores_no_file_unless_asked(self, import_job):
        assert not import_job.file

    def test_deleting_a_job_deletes_its_stored_file(self):
        job = ImportJobFactory(with_file=True)
        storage, name = job.file.storage, job.file.name
        assert storage.exists(name)

        job.delete()

        assert not storage.exists(name)

    def test_deleting_a_job_whose_file_is_gone_does_not_fail(self):
        job = ImportJobFactory()

        job.delete()

        assert not ImportJob.objects.filter(pk=job.pk).exists()

    def test_deleting_a_dataset_deletes_its_jobs_and_their_files(self):
        job = ImportJobFactory(with_file=True)
        ImportRowFactory(job=job)
        storage, name = job.file.storage, job.file.name

        job.dataset.delete()

        assert not ImportJob.objects.filter(pk=job.pk).exists()
        assert not ImportRow.objects.filter(job_id=job.pk).exists()
        assert not storage.exists(name)

    def test_deleting_a_job_leaves_its_dataset(self, import_job):
        import_job.delete()

        assert Dataset.all_objects.filter(pk=import_job.dataset_id).exists()


class TestImportRow:
    """One row of a file as the check saw it."""

    def test_rows_come_in_the_order_of_the_file(self, import_job):
        third = ImportRowFactory(job=import_job, number=3)
        first = ImportRowFactory(job=import_job, number=1)
        second = ImportRowFactory(job=import_job, number=2)

        assert list(import_job.rows.all()) == [first, second, third]

    def test_rows_of_one_outcome_are_found_by_the_index(self):
        indexed = [index.fields for index in ImportRow._meta.indexes]

        assert ["job", "outcome", "number"] in indexed

    def test_a_row_starts_as_a_new_record(self, import_row):
        assert import_row.outcome == ImportRow.Outcome.NEW
        assert import_row.record_pk is None

    def test_a_row_holds_no_cell_of_the_file(self):
        names = {field.name for field in ImportRow._meta.get_fields()}

        assert names.isdisjoint({"values", "cells", "data", "raw"})

    def test_deleting_a_job_deletes_its_rows(self, import_job):
        row = ImportRowFactory(job=import_job)

        import_job.delete()

        assert not ImportRow.objects.filter(pk=row.pk).exists()


class TestFieldDocumentation:
    """Every field of both models has a name and an explanation."""

    FIELDS = [
        field
        for model in (ImportJob, ImportRow)
        for field in model._meta.get_fields()
        if isinstance(field, models.Field) and not field.auto_created
    ]

    @pytest.mark.parametrize(
        "field", FIELDS, ids=lambda field: f"{field.model.__name__}.{field.name}"
    )
    def test_field_has_verbose_name_and_help_text(self, field):
        assert str(field.help_text)
        assert field._verbose_name is not None

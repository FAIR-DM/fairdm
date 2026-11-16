"""Tests for fairdm/contrib/activity/receivers.py."""

from unittest import mock

import pytest
from actstream import action
from actstream.models import Action
from django.contrib.contenttypes.models import ContentType

from fairdm.contrib.activity import receivers
from fairdm.contrib.activity.receivers import EDITED, JOINED, PUBLISHED
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.factories import (
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteSampleFactory

pytestmark = pytest.mark.django_db


def recorded(verb):
    """Return the actions of one verb, oldest first."""
    return list(Action.objects.filter(verb=verb).order_by("pk"))


def refetch(record):
    """Return the record as a fresh query reads it, with nothing remembered about it."""
    model = type(record)
    manager = getattr(model, "all_objects", model.objects)
    return manager.get(pk=record.pk)


def is_actor(action_row, record):
    """Say whether the record is the actor of the action."""
    return action_row.actor_content_type_id == ContentType.objects.get_for_model(
        record
    ).pk and action_row.actor_object_id == str(record.pk)


RECORD_FACTORIES = [ProjectFactory, DatasetFactory]
RELATED_FACTORIES = [
    (ProjectFactory, ProjectDescriptionFactory),
    (ProjectFactory, ProjectDateFactory),
    (ProjectFactory, ProjectIdentifierFactory),
    (DatasetFactory, DatasetDescriptionFactory),
    (DatasetFactory, DatasetDateFactory),
    (DatasetFactory, DatasetIdentifierFactory),
]


class TestRecordEdits:
    @pytest.mark.parametrize("factory", RECORD_FACTORIES)
    def test_a_new_name_records_one_edit_by_the_record(self, factory, clean_slate):
        record = factory()
        clean_slate()

        record.name = "A new name"
        record.save()

        (edit,) = recorded(EDITED)
        assert is_actor(edit, record)
        assert edit.public is False

    @pytest.mark.parametrize("factory", RECORD_FACTORIES)
    def test_a_fetched_record_records_one_edit_then_none_unchanged(
        self, factory, clean_slate
    ):
        record = factory()
        clean_slate()

        fetched = refetch(record)
        fetched.name = "Renamed after a fetch"
        fetched.save()
        fetched.save()

        assert len(recorded(EDITED)) == 1

    @pytest.mark.parametrize("factory", RECORD_FACTORIES)
    def test_a_save_that_changes_nothing_records_none(self, factory, clean_slate):
        record = refetch(factory())
        clean_slate()

        record.save()

        assert recorded(EDITED) == []

    @pytest.mark.parametrize("factory", RECORD_FACTORIES)
    def test_a_visibility_change_alone_records_none(self, factory, clean_slate):
        record = refetch(factory(visibility=Visibility.PRIVATE))
        clean_slate()

        record.visibility = Visibility.PUBLIC
        record.save()

        assert recorded(EDITED) == []

    @pytest.mark.parametrize(("record_factory", "related_factory"), RELATED_FACTORIES)
    def test_saving_a_related_record_records_an_edit_on_its_record(
        self, record_factory, related_factory, clean_slate
    ):
        record = record_factory()
        clean_slate()

        related_factory(related=record)

        (edit,) = recorded(EDITED)
        assert is_actor(edit, record)
        assert edit.public is False

    @pytest.mark.parametrize(("record_factory", "related_factory"), RELATED_FACTORIES)
    def test_deleting_a_related_record_records_an_edit_on_its_record(
        self, record_factory, related_factory, clean_slate
    ):
        record = record_factory()
        related = related_factory(related=record)
        clean_slate()

        related.delete()

        (edit,) = recorded(EDITED)
        assert is_actor(edit, record)

    @pytest.mark.parametrize(("record_factory", "related_factory"), RELATED_FACTORIES)
    def test_deleting_the_record_records_nothing_new(
        self, record_factory, related_factory, clean_slate
    ):
        record = record_factory()
        related_factory(related=record)
        clean_slate()

        record.delete()

        assert Action.objects.count() == 0


class TestRecordPublished:
    def test_publishing_records_published_and_not_edited(self, clean_slate):
        dataset = refetch(DatasetFactory(published=False))
        clean_slate()

        dataset.published = True
        dataset.save()

        (published,) = recorded(PUBLISHED)
        assert is_actor(published, dataset)
        assert published.public is False
        assert recorded(EDITED) == []

    def test_a_dataset_created_published_records_published(self, clean_slate):
        clean_slate()

        dataset = DatasetFactory(published=True)

        (published,) = recorded(PUBLISHED)
        assert is_actor(published, dataset)

    def test_saving_an_already_published_dataset_records_nothing(self, clean_slate):
        dataset = refetch(DatasetFactory(published=True))
        clean_slate()

        dataset.save()

        assert Action.objects.count() == 0


class TestRecordJoined:
    @pytest.mark.parametrize("factory", RECORD_FACTORIES)
    def test_crediting_a_person_records_joined(self, factory, clean_slate):
        record = factory()
        person = PersonFactory()
        clean_slate()

        Crediting(record).add(person)

        (joined,) = recorded(JOINED)
        assert is_actor(joined, person)
        assert joined.target_content_type_id == (
            ContentType.objects.get_for_model(record).pk
        )
        assert joined.target_object_id == str(record.pk)
        assert joined.public is False

    def test_crediting_an_organization_records_joined(self, clean_slate):
        dataset = DatasetFactory()
        organization = OrganizationFactory()
        clean_slate()

        Crediting(dataset).add(organization)

        (joined,) = recorded(JOINED)
        assert is_actor(joined, organization)

    def test_crediting_on_a_sample_records_nothing(self, clean_slate):
        sample = ConcreteSampleFactory(dataset=DatasetFactory())
        person = PersonFactory()
        clean_slate()

        Crediting(sample).add(person)

        assert Action.objects.count() == 0


class TestRecordingNeverFails:
    def test_a_failing_send_does_not_stop_the_save_and_is_logged(self):
        record = refetch(ProjectFactory())

        with (
            mock.patch.object(action, "send", side_effect=RuntimeError("down")),
            mock.patch.object(receivers.logger, "exception") as logged,
        ):
            record.name = "Saved all the same"
            record.save()

        assert Project.objects.get(pk=record.pk).name == "Saved all the same"
        logged.assert_called_once()

    def test_a_failing_send_does_not_stop_a_dataset_being_published(self):
        dataset = refetch(DatasetFactory(published=False))

        with (
            mock.patch.object(action, "send", side_effect=RuntimeError("down")),
            mock.patch.object(receivers.logger, "exception") as logged,
        ):
            dataset.published = True
            dataset.save()

        assert Dataset.all_objects.get(pk=dataset.pk).published is True
        logged.assert_called()

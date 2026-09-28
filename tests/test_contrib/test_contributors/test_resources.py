"""Tests for PersonResource (fairdm.contrib.contributors.resources) — bulk import."""

import pytest
import tablib
from django.core.exceptions import ValidationError
from import_export.instance_loaders import ModelInstanceLoader

from fairdm.contrib.contributors.models import ContributorIdentifier, Person
from fairdm.contrib.contributors.resources import PersonResource
from fairdm.factories import PersonFactory

ORCID_ID = "0000-0002-1111-2222"


@pytest.fixture
def resource():
    return PersonResource()


@pytest.fixture
def instance_loader(resource):
    return ModelInstanceLoader(resource)


@pytest.fixture
def stub_orcid_creation(monkeypatch):

    def fake_update_or_create_from_orcid(orcid, **kwargs):
        person = Person(name="New Import Person", first_name="New", last_name="Person")
        person.save()
        return person, True

    monkeypatch.setattr(
        "fairdm.contrib.contributors.resources.update_or_create_from_orcid",
        fake_update_or_create_from_orcid,
    )
    return fake_update_or_create_from_orcid


@pytest.fixture
def stub_orcid_match(monkeypatch):

    def make(person):
        def fake_update_or_create_from_orcid(orcid, **kwargs):
            return person, False

        monkeypatch.setattr(
            "fairdm.contrib.contributors.resources.update_or_create_from_orcid",
            fake_update_or_create_from_orcid,
        )

    return make


@pytest.mark.django_db
class TestGetInstanceCreatesGhostShapedPerson:
    def test_matches_create_unclaimed_on_all_four_points(
        self, resource, instance_loader, stub_orcid_creation
    ):
        row = {"orcid": ORCID_ID, "name": "New Import Person"}

        person = resource.get_instance(instance_loader, row)

        reference = Person.objects.create_unclaimed(
            first_name="Ghost", last_name="Person"
        )

        assert person.is_active is True
        assert person.is_claimed is False
        assert person.email is None
        assert person.has_usable_password() is False

        assert person.is_active == reference.is_active
        assert person.is_claimed == reference.is_claimed
        assert person.email == reference.email
        assert person.has_usable_password() == reference.has_usable_password()


@pytest.mark.django_db
class TestGetInstanceRefusesClaimedPerson:
    def test_orcid_match_on_claimed_person_is_refused(self, resource, instance_loader):
        claimed = PersonFactory(
            email="claimed-import@example.com", is_active=True, is_claimed=True
        )
        ContributorIdentifier.objects.create(
            related=claimed, value=ORCID_ID, type="ORCID"
        )
        original_name = claimed.name
        original_email = claimed.email

        row = {"orcid": ORCID_ID, "name": "Someone Else Entirely"}

        with pytest.raises(ValidationError):
            resource.get_instance(instance_loader, row)

        claimed.refresh_from_db()
        assert claimed.name == original_name
        assert claimed.email == original_email
        assert claimed.is_claimed is True

    def test_uuid_match_on_claimed_person_is_refused(self, resource, instance_loader):
        claimed = PersonFactory(
            email="claimed-uuid-import@example.com", is_active=True, is_claimed=True
        )
        original_name = claimed.name

        row = {"uuid": claimed.uuid, "name": "Someone Else Entirely"}

        with pytest.raises(ValidationError):
            resource.get_instance(instance_loader, row)

        claimed.refresh_from_db()
        assert claimed.name == original_name
        assert claimed.is_claimed is True


@pytest.mark.django_db
class TestGetInstanceDoesNotResolveByName:
    def test_name_collision_does_not_resolve_to_existing_person(
        self, resource, instance_loader
    ):
        existing = PersonFactory(
            name="Common Name",
            first_name="Common",
            last_name="Name",
            email="common.name@example.com",
        )

        row = {"name": "Common Name", "first_name": "Common", "last_name": "Name"}

        result = resource.get_instance(instance_loader, row)

        assert result is None
        assert result != existing


@pytest.mark.django_db
class TestImportInstanceDoesNotOverwriteUuid:
    def test_orcid_matched_row_does_not_change_the_matched_persons_uuid(
        self, resource, stub_orcid_match
    ):
        existing = PersonFactory(is_claimed=False)
        original_uuid = existing.uuid
        stub_orcid_match(existing)

        dataset = tablib.Dataset(
            headers=["uuid", "orcid", "name", "first_name", "last_name"]
        )
        dataset.append(
            ["", ORCID_ID, existing.name, existing.first_name, existing.last_name]
        )

        result = resource.import_data(dataset, dry_run=False)

        assert not result.has_errors(), [
            [e.error for e in row.errors] for row in result.rows
        ]
        existing.refresh_from_db()
        assert existing.uuid == original_uuid


@pytest.mark.django_db
class TestImportDataDoesNotPoisonTheBatch:
    def test_a_failing_row_does_not_poison_a_later_rows_outcome(
        self, resource, stub_orcid_match
    ):
        colliding_uuid_holder = PersonFactory(
            is_claimed=True, email="holds-the-uuid@example.com"
        )
        matched_by_orcid = PersonFactory(is_claimed=False)
        stub_orcid_match(matched_by_orcid)

        dataset = tablib.Dataset(
            headers=["uuid", "orcid", "name", "first_name", "last_name"]
        )
        # Row 0: resolved via ORCID, but its uploaded uuid cell collides with
        # a different, unrelated Person's real uuid.
        dataset.append(
            [
                colliding_uuid_holder.uuid,
                ORCID_ID,
                matched_by_orcid.name,
                matched_by_orcid.first_name,
                matched_by_orcid.last_name,
            ]
        )
        # Row 1: an entirely unrelated, valid new row with nothing wrong
        # with it on its own.
        dataset.append(["", "", "Fresh New Person", "Fresh", "Person"])

        result = resource.import_data(dataset, dry_run=False)

        row_zero_errors = [e.error for e in result.rows[0].errors]
        row_one_errors = [e.error for e in result.rows[1].errors]
        assert not row_one_errors, (
            "row 1 has nothing wrong with it and must report its own "
            f"outcome, not row 0's failure: {row_one_errors!r}"
        )
        assert Person.objects.filter(name="Fresh New Person").exists()

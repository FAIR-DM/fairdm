"""Tests for PersonResource (fairdm.contrib.contributors.resources) — bulk import.

An uploaded spreadsheet is untrusted input. These tests cover:

  - A newly-created (Ghost-state) Person produced from an ORCID import row
    matches ``UserManager.create_unclaimed()``'s shape exactly: active,
    unclaimed, no email, no usable password — never the old "is_active=False"
    (banned) shape that made a freshly imported profile indistinguishable
    from someone who had been deactivated.
  - ``get_instance()`` refuses to resolve to — and thereby modify — an
    already-claimed Person, whether the match comes from the row's ORCID
    identifier or its uuid, raising a ``ValidationError`` naming the row
    instead of silently overwriting it.
  - ``get_instance()`` no longer resolves rows by display name — a free-text
    ``name`` collision with an existing Person is not an identity match, now
    that ``import_id_fields`` is ``["uuid"]``.
"""

import pytest
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
    """Stand in for ``update_or_create_from_orcid`` so tests never hit the
    real ORCID API.

    Mirrors what ``ORCIDTransform.update_or_create`` does when nothing
    matches yet: builds a bare, saved Person from the row's name and reports
    it as newly created — leaving email, is_claimed, is_active and password
    entirely at ``Person()``'s own defaults, exactly what ``get_instance``
    receives before it applies its own fix-up.
    """

    def fake_update_or_create_from_orcid(orcid, **kwargs):
        person = Person(name="New Import Person", first_name="New", last_name="Person")
        person.save()
        return person, True

    monkeypatch.setattr(
        "fairdm.contrib.contributors.resources.update_or_create_from_orcid",
        fake_update_or_create_from_orcid,
    )
    return fake_update_or_create_from_orcid


@pytest.mark.django_db
class TestGetInstanceCreatesGhostShapedPerson:
    """A row that creates a new Person (via its ORCID) gets the same shape
    ``UserManager.create_unclaimed`` produces.
    """

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
    """An import row must never resolve to — and thereby modify — an
    already-claimed Person, whichever way it is matched.
    """

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
    """``import_id_fields`` is ``["uuid"]`` — a display name collision never
    resolves to an existing Person.
    """

    def test_name_collision_does_not_resolve_to_existing_person(
        self, resource, instance_loader
    ):
        existing = PersonFactory(
            name="Common Name",
            first_name="Common",
            last_name="Name",
            email="common.name@example.com",
        )

        # No "uuid" column in the row at all — the old "name" resolution is gone.
        row = {"name": "Common Name", "first_name": "Common", "last_name": "Name"}

        result = resource.get_instance(instance_loader, row)

        assert result is None
        assert result != existing

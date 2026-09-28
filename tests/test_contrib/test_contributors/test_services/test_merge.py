"""Tests for the merge_persons service."""

import pytest


@pytest.fixture
def keep_person(db):
    from fairdm.factories import PersonFactory

    return PersonFactory(
        first_name="Keep", last_name="Person", is_claimed=True, is_active=True
    )


@pytest.fixture
def discard_person(db):
    from fairdm.contrib.contributors.models import Person

    return Person.objects.create_unclaimed(first_name="Discard", last_name="Person")


class TestMergePersonsHappyPath:
    def test_discard_is_deleted_after_merge(self, keep_person, discard_person):
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.services.merge import merge_persons

        discard_pk = discard_person.pk
        merge_persons(keep_person, discard_person)
        assert not Person.objects.filter(pk=discard_pk).exists()

    def test_keep_person_is_claimed_after_merge(self, keep_person, discard_person):
        from fairdm.contrib.contributors.services.merge import merge_persons

        result = merge_persons(keep_person, discard_person)
        result.refresh_from_db()
        assert result.is_claimed is True
        assert result.is_active is True

    def test_returns_updated_keep_person(self, keep_person, discard_person):
        from fairdm.contrib.contributors.services.merge import merge_persons

        result = merge_persons(keep_person, discard_person)
        assert result.pk == keep_person.pk

    def test_audit_log_written_on_success(self, keep_person, discard_person):
        from fairdm.contrib.contributors.models import ClaimingAuditLog, ClaimMethod
        from fairdm.contrib.contributors.services.merge import merge_persons

        merge_persons(keep_person, discard_person)
        log = ClaimingAuditLog.objects.filter(method=ClaimMethod.ADMIN_MERGE).first()
        assert log is not None
        assert log.success is True


class TestMergeContributions:
    def test_contributions_reassigned_to_keep(self, db, keep_person, discard_person):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        Contribution.add_to(discard_person, project)

        merge_persons(keep_person, discard_person)
        assert Contribution.objects.filter(contributor=keep_person).exists()

    def test_duplicate_contributions_not_duplicated(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        Contribution.add_to(keep_person, project)
        Contribution.add_to(discard_person, project)

        merge_persons(keep_person, discard_person)
        count = Contribution.objects.filter(contributor=keep_person).count()
        assert count == 1

        from fairdm.contrib.contributors.models import Person

        assert not Person.objects.filter(pk=discard_person.pk).exists()


class TestMergeIdentifiers:
    def test_identifiers_reassigned_to_keep(self, db, keep_person, discard_person):
        from fairdm.contrib.contributors.models import ContributorIdentifier
        from fairdm.contrib.contributors.services.merge import merge_persons

        ContributorIdentifier.objects.create(
            related=discard_person, type="ORCID", value="0000-0000-0000-0001"
        )
        merge_persons(keep_person, discard_person)
        assert ContributorIdentifier.objects.filter(
            related=keep_person, type="ORCID"
        ).exists()

    def test_duplicate_identifiers_not_duplicated(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import ContributorIdentifier
        from fairdm.contrib.contributors.services.merge import merge_persons

        ContributorIdentifier.objects.create(
            related=discard_person, type="ORCID", value="0000-0000-0000-9999"
        )
        merge_persons(keep_person, discard_person)
        assert ContributorIdentifier.objects.filter(
            related=keep_person, value="0000-0000-0000-9999"
        ).exists()


class TestMergeAffiliations:
    def test_affiliations_reassigned_to_keep(self, db, keep_person, discard_person):
        from fairdm.contrib.contributors.models import Affiliation
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import OrganizationFactory

        org = OrganizationFactory()
        Affiliation.objects.create(person=discard_person, organization=org)
        merge_persons(keep_person, discard_person)
        assert Affiliation.objects.filter(person=keep_person, organization=org).exists()


class TestMergeGuards:
    def test_merge_with_self_raises(self, db, keep_person):
        from fairdm.contrib.contributors.exceptions import ClaimingError
        from fairdm.contrib.contributors.services.merge import merge_persons

        with pytest.raises(ClaimingError):
            merge_persons(keep_person, keep_person)

    def test_atomic_rollback_on_error(
        self, db, keep_person, discard_person, monkeypatch
    ):
        from fairdm.contrib.contributors.models import Person
        from fairdm.contrib.contributors.services import merge as merge_module

        def _raise(*args, **kwargs):
            raise RuntimeError("Simulated error")

        monkeypatch.setattr(merge_module, "_reassign_contributions", _raise)

        with pytest.raises(RuntimeError):
            merge_module.merge_persons(keep_person, discard_person)

        assert Person.objects.filter(pk=discard_person.pk).exists()

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


class TestMergeLevels:
    @pytest.mark.parametrize(
        ("kept", "discarded", "expected"),
        [
            (1, 3, 3),
            (3, 1, 3),
            (2, 2, 2),
            (1, 2, 2),
        ],
    )
    def test_the_higher_level_is_kept(
        self, db, keep_person, discard_person, kept, discarded, expected
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ContributionFactory, ProjectFactory

        project = ProjectFactory()
        ContributionFactory(content_object=project, contributor=keep_person, level=kept)
        ContributionFactory(
            content_object=project, contributor=discard_person, level=discarded
        )

        merge_persons(keep_person, discard_person)

        entry = Contribution.objects.get(
            object_id=str(project.pk), contributor=keep_person
        )
        assert entry.level == expected
        assert Contribution.objects.filter(object_id=str(project.pk)).count() == 1

    def test_the_kept_organization_is_left_as_it_is(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import (
            ContributionFactory,
            OrganizationFactory,
            ProjectFactory,
        )

        project = ProjectFactory()
        kept_from, discarded_from = OrganizationFactory(), OrganizationFactory()
        ContributionFactory(
            content_object=project,
            contributor=keep_person,
            level=1,
            affiliation=kept_from,
        )
        ContributionFactory(
            content_object=project,
            contributor=discard_person,
            level=3,
            affiliation=discarded_from,
        )

        merge_persons(keep_person, discard_person)

        entry = Contribution.objects.get(
            object_id=str(project.pk), contributor=keep_person
        )
        assert entry.level == 3
        assert entry.affiliation == kept_from

    def test_a_kept_entry_with_no_organization_stays_without_one(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import (
            ContributionFactory,
            OrganizationFactory,
            ProjectFactory,
        )

        project = ProjectFactory()
        ContributionFactory(content_object=project, contributor=keep_person, level=1)
        ContributionFactory(
            content_object=project,
            contributor=discard_person,
            level=3,
            affiliation=OrganizationFactory(),
        )

        merge_persons(keep_person, discard_person)

        entry = Contribution.objects.get(
            object_id=str(project.pk), contributor=keep_person
        )
        assert entry.affiliation is None

    def test_a_contribution_only_the_discarded_person_held_moves_with_its_level(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ContributionFactory, ProjectFactory

        project = ProjectFactory()
        ContributionFactory(content_object=project, contributor=discard_person, level=3)

        merge_persons(keep_person, discard_person)

        entry = Contribution.objects.get(
            object_id=str(project.pk), contributor=keep_person
        )
        assert entry.level == 3

    def test_a_contribution_only_the_kept_person_held_is_untouched(
        self, db, keep_person, discard_person
    ):
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ContributionFactory, ProjectFactory

        project = ProjectFactory()
        ContributionFactory(content_object=project, contributor=keep_person, level=2)

        merge_persons(keep_person, discard_person)

        entry = Contribution.objects.get(
            object_id=str(project.pk), contributor=keep_person
        )
        assert entry.level == 2


class TestMergePermissions:
    def test_a_stored_row_on_a_core_record_is_not_copied(
        self, db, keep_person, discard_person
    ):
        from guardian.models import UserObjectPermission
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        assign_perm("change_project", discard_person, project)

        merge_persons(keep_person, discard_person)

        assert not UserObjectPermission.objects.filter(user=keep_person).exists()

    def test_a_stored_row_on_another_object_is_copied(
        self, db, keep_person, discard_person
    ):
        from guardian.models import UserObjectPermission
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.services.merge import merge_persons
        from fairdm.factories import OrganizationFactory

        organization = OrganizationFactory()
        assign_perm("change_organization", discard_person, organization)

        merge_persons(keep_person, discard_person)

        assert UserObjectPermission.objects.filter(
            user=keep_person, object_pk=str(organization.pk)
        ).exists()


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

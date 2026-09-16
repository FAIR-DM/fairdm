"""Tests for the four roles FairDM ships and installs into every portal.

See CONTEXT.md for how a *portal role* differs from a *contribution role* and
what a *rights-carrying role* is.
"""

import pytest
from django.contrib.auth.models import Group, Permission

from fairdm.factories import PersonFactory
from fairdm.portal_roles import PortalRoles

#: The Data Curator's declared rights: view/add/change/delete over Project,
#: Dataset, Sample and Measurement and their attached description, date and
#: contribution records, plus the two permissions the import and publish
#: plugin checks read directly (research R1, R9).
DATA_CURATOR_PERMISSIONS = {
    # Project
    "project.view_project",
    "project.add_project",
    "project.change_project",
    "project.delete_project",
    "project.view_projectdescription",
    "project.add_projectdescription",
    "project.change_projectdescription",
    "project.delete_projectdescription",
    "project.view_projectdate",
    "project.add_projectdate",
    "project.change_projectdate",
    "project.delete_projectdate",
    # Dataset
    "dataset.view_dataset",
    "dataset.add_dataset",
    "dataset.change_dataset",
    "dataset.delete_dataset",
    "dataset.view_datasetdescription",
    "dataset.add_datasetdescription",
    "dataset.change_datasetdescription",
    "dataset.delete_datasetdescription",
    "dataset.view_datasetdate",
    "dataset.add_datasetdate",
    "dataset.change_datasetdate",
    "dataset.delete_datasetdate",
    "dataset.import_data",
    "dataset.can_publish",
    # Sample
    "sample.view_sample",
    "sample.add_sample",
    "sample.change_sample",
    "sample.delete_sample",
    "sample.view_sampledescription",
    "sample.add_sampledescription",
    "sample.change_sampledescription",
    "sample.delete_sampledescription",
    "sample.view_sampledate",
    "sample.add_sampledate",
    "sample.change_sampledate",
    "sample.delete_sampledate",
    # Measurement
    "measurement.view_measurement",
    "measurement.add_measurement",
    "measurement.change_measurement",
    "measurement.delete_measurement",
    "measurement.view_measurementdescription",
    "measurement.add_measurementdescription",
    "measurement.change_measurementdescription",
    "measurement.delete_measurementdescription",
    "measurement.view_measurementdate",
    "measurement.add_measurementdate",
    "measurement.change_measurementdate",
    "measurement.delete_measurementdate",
    # Contribution
    "contributors.view_contribution",
    "contributors.add_contribution",
    "contributors.change_contribution",
    "contributors.delete_contribution",
}

COMMUNITY_MANAGER_PERMISSIONS = {
    "contributors.view_person",
    "contributors.change_person",
    "contributors.view_organization",
    "contributors.change_organization",
    "contributors.view_affiliation",
    "contributors.change_affiliation",
    "contributors.view_contribution",
    "contributors.change_contribution",
}


class TestDeclarations:
    """FR-001 to FR-005: exactly four roles, named and scoped as the spec requires."""

    def test_exactly_four_roles_with_the_shipped_names_in_order(self):
        assert PortalRoles.shipped_names() == [
            "Portal Administrator",
            "Data Curator",
            "Community Manager",
            "Developer",
        ]

    def test_portal_administrator_permissions_match_exactly(self):
        assert set(PortalRoles.PORTAL_ADMINISTRATOR.permissions) == {
            "auth.view_group",
            "contributors.view_person",
            "contributors.change_person",
            "identity.change_identity",
        }

    def test_portal_administrator_cannot_edit_a_group(self):
        """D15: the role that assigns roles must not be able to rewrite what any role may do."""
        assert not {
            "auth.add_group",
            "auth.change_group",
            "auth.delete_group",
        } & set(PortalRoles.PORTAL_ADMINISTRATOR.permissions)

    def test_data_curator_permissions_match_exactly(self):
        assert set(PortalRoles.DATA_CURATOR.permissions) == DATA_CURATOR_PERMISSIONS

    def test_community_manager_permissions_match_exactly(self):
        assert (
            set(PortalRoles.COMMUNITY_MANAGER.permissions)
            == COMMUNITY_MANAGER_PERMISSIONS
        )

    def test_community_manager_cannot_delete_a_person(self):
        """FR-004: the role must not hold the right to delete a person record."""
        assert (
            "contributors.delete_person"
            not in PortalRoles.COMMUNITY_MANAGER.permissions
        )

    def test_developer_holds_no_permissions(self):
        assert PortalRoles.DEVELOPER.permissions == ()

    def test_every_permission_is_an_explicit_app_label_codename(self):
        for role in PortalRoles.ROLES:
            for permission in role.permissions:
                assert permission.count(".") == 1, (
                    f"{role.name}'s {permission!r} is not an app_label.codename string"
                )


def _permission_strings(group):
    """A group's permissions as ``app_label.codename`` strings, for comparison against a
    ``PortalRole.permissions`` declaration."""
    return {
        f"{permission.content_type.app_label}.{permission.codename}"
        for permission in group.permissions.all()
    }


def _resolvable_permissions(role):
    """The subset of a role's declared permissions that exist as real ``Permission`` rows
    right now. ``dataset.can_publish`` does not - no model declares it - and ``reconcile()``
    must tolerate that rather than raise (D19, research R5)."""
    resolvable = set()
    for permission_name in role.permissions:
        app_label, codename = permission_name.split(".", 1)
        if Permission.objects.filter(
            content_type__app_label=app_label, codename=codename
        ).exists():
            resolvable.add(permission_name)
    return resolvable


@pytest.mark.django_db
class TestReconcile:
    """FR-009 to FR-011, US-1 AC3, SC-002: installation and repair on every update."""

    def test_installs_all_four_roles_with_their_declared_rights(self):
        Group.objects.all().delete()

        PortalRoles.reconcile()

        for role in PortalRoles.ROLES:
            group = Group.objects.get(name=role.name)
            assert _permission_strings(group) == _resolvable_permissions(role)

    def test_a_second_run_changes_nothing_and_duplicates_nothing(self):
        Group.objects.all().delete()
        PortalRoles.reconcile()

        PortalRoles.reconcile()

        assert Group.objects.filter(name__in=PortalRoles.shipped_names()).count() == 4
        for role in PortalRoles.ROLES:
            group = Group.objects.get(name=role.name)
            assert _permission_strings(group) == _resolvable_permissions(role)

    def test_permissions_edited_by_hand_are_restored(self):
        Group.objects.all().delete()
        PortalRoles.reconcile()
        group = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)
        group.permissions.clear()
        assert group.permissions.count() == 0

        PortalRoles.reconcile()

        group.refresh_from_db()
        assert _permission_strings(group) == _resolvable_permissions(
            PortalRoles.DATA_CURATOR
        )

    def test_the_people_in_a_role_are_untouched(self):
        Group.objects.all().delete()
        PortalRoles.reconcile()
        curator_group = Group.objects.get(name=PortalRoles.DATA_CURATOR.name)
        curator = PersonFactory()
        curator.groups.add(curator_group)

        PortalRoles.reconcile()

        assert curator in curator_group.user_set.all()

    def test_a_group_the_portal_created_itself_is_left_alone(self):
        custom_group = Group.objects.create(name="Project Alpha Team")
        view_dataset = Permission.objects.get(
            content_type__app_label="dataset", codename="view_dataset"
        )
        custom_group.permissions.add(view_dataset)

        PortalRoles.reconcile()

        custom_group.refresh_from_db()
        assert custom_group.name == "Project Alpha Team"
        assert list(custom_group.permissions.all()) == [view_dataset]

    def test_legacy_groups_with_members_end_up_in_the_corresponding_new_roles(self):
        """R10, D10: a rename carries the membership rows across; a fresh create does not."""
        Group.objects.all().delete()
        legacy = {}
        for legacy_name in PortalRoles.LEGACY_NAMES:
            group = Group.objects.create(name=legacy_name)
            member = PersonFactory()
            member.groups.add(group)
            legacy[legacy_name] = (group.pk, member)

        PortalRoles.reconcile()

        for legacy_name, shipped_name in PortalRoles.LEGACY_NAMES.items():
            assert not Group.objects.filter(name=legacy_name).exists()
            renamed = Group.objects.get(name=shipped_name)
            pk, member = legacy[legacy_name]
            assert renamed.pk == pk
            assert member in renamed.user_set.all()


@pytest.mark.django_db
class TestDeclaredPermissionsExist:
    """Every permission named in any role's declaration resolves to a real ``Permission``
    row once the database is up to date.

    ``reconcile()`` skips a permission with no matching row yet, which is right for the
    ordering ``INSTALLED_APPS`` runs migrations in and wrong as a permanent state: without
    this test, a typo, or a right nobody declares, is silently absent from the role forever
    - exactly what happened to ``dataset.can_publish`` in US-1 (T017b).
    """

    def test_every_declared_permission_resolves_to_a_real_permission_row(self):
        missing = []
        for role in PortalRoles.ROLES:
            resolvable = _resolvable_permissions(role)
            missing.extend(
                f"{role.name}: {permission_name}"
                for permission_name in role.permissions
                if permission_name not in resolvable
            )
        assert not missing, f"declared but not a real Permission row: {missing}"

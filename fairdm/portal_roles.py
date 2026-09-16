"""The four roles FairDM ships, declared once, and their installation into every portal.

The module is named ``portal_roles``, not ``roles``: this codebase already spends the bare
word "role" on a :class:`~fairdm.contrib.contributors.models.Contribution`'s role, and the two
are distinct terms (see CONTEXT.md).
"""

from typing import NamedTuple

from django.contrib.auth.models import Group, Permission
from django.utils.translation import gettext_lazy as _


class PortalRole(NamedTuple):
    """One shipped role: its stored name, its display label, and the exact
    permissions it holds, each an explicit ``app_label.codename``."""

    name: str
    label: str
    permissions: tuple[str, ...] = ()


class PortalRoles:
    """The roles FairDM ships, and the methods that read and install them (Article XI)."""

    PORTAL_ADMINISTRATOR = PortalRole(
        name="Portal Administrator",
        label=_("Portal Administrator"),
        permissions=(
            "auth.view_group",
            "contributors.view_person",
            "contributors.change_person",
            "identity.change_identity",
        ),
    )

    DATA_CURATOR = PortalRole(
        name="Data Curator",
        label=_("Data Curator"),
        permissions=(
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
        ),
    )

    COMMUNITY_MANAGER = PortalRole(
        name="Community Manager",
        label=_("Community Manager"),
        permissions=(
            "contributors.view_person",
            "contributors.change_person",
            "contributors.view_organization",
            "contributors.change_organization",
            "contributors.view_affiliation",
            "contributors.change_affiliation",
            "contributors.view_contribution",
            "contributors.change_contribution",
        ),
    )

    DEVELOPER = PortalRole(name="Developer", label=_("Developer"), permissions=())

    #: Declaration order. Every method below reads this, so the order named here is the
    #: order the whole feature presents the roles in.
    ROLES: tuple[PortalRole, ...] = (
        PORTAL_ADMINISTRATOR,
        DATA_CURATOR,
        COMMUNITY_MANAGER,
        DEVELOPER,
    )

    #: The three pre-existing `auth.Group` rows a portal set up before this feature already
    #: has, mapped to the shipped role each becomes. Renamed in place rather than replaced, so
    #: their membership carries across (D10, research R10).
    LEGACY_NAMES = {
        "Portal Administrators": "Portal Administrator",
        "Data Administrators": "Data Curator",
        "Developers": "Developer",
    }

    @classmethod
    def shipped_names(cls) -> list[str]:
        """The stored name of every role FairDM ships, in declaration order."""
        return [role.name for role in cls.ROLES]

    @classmethod
    def rights_carrying(cls) -> list[str]:
        """The stored names of the roles that hold at least one permission.

        Holding any of these gives access to the administration interface (FR-006, FR-008);
        holding only a role absent from this list does not.
        """
        return [role.name for role in cls.ROLES if role.permissions]

    @classmethod
    def _rename_legacy_groups(cls) -> None:
        """Rename a legacy group row in place, and only when its target name is free.

        A rename carries the membership rows across; a fresh create does not (D10). Renaming
        onto a name already taken would raise `IntegrityError` on `Group.name`'s uniqueness,
        so a legacy row is left alone once its target already exists.
        """
        existing = set(Group.objects.values_list("name", flat=True))
        for legacy_name, shipped_name in cls.LEGACY_NAMES.items():
            if legacy_name in existing and shipped_name not in existing:
                Group.objects.filter(name=legacy_name).update(name=shipped_name)
                existing.discard(legacy_name)
                existing.add(shipped_name)

    @classmethod
    def _permissions_for(cls, role: PortalRole) -> list[Permission]:
        """The `Permission` rows a role's declaration resolves to right now.

        A declared permission that has no matching row yet is skipped rather than raised on:
        `INSTALLED_APPS` lists `fairdm` before the apps whose permissions these roles need, so
        an early `post_migrate` pass sees an incomplete set, and a later pass converges
        (research R5). `dataset.can_publish` currently has no model declaring it at all and is
        skipped the same way, for the same reason: nothing here may raise on a missing right.
        """
        permissions = []
        for permission_name in role.permissions:
            app_label, codename = permission_name.split(".", 1)
            permission = Permission.objects.filter(
                content_type__app_label=app_label, codename=codename
            ).first()
            if permission is not None:
                permissions.append(permission)
        return permissions

    @classmethod
    def reconcile(cls) -> None:
        """Install the four roles into the database (FR-009 to FR-011).

        Renames the legacy rows first, so their membership carries across, then creates
        whatever role is still missing and sets each role's permissions to exactly its
        declaration - restoring a permission removed by hand and removing one added by hand.
        Membership is never touched, and a group this method did not create or rename is never
        looked at.
        """
        cls._rename_legacy_groups()

        for role in cls.ROLES:
            group, _created = Group.objects.get_or_create(name=role.name)
            group.permissions.set(cls._permissions_for(role))

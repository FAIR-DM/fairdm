"""The four roles FairDM ships, declared once, and their installation into every portal.

The module is named ``portal_roles``, not ``roles``, because the bare word "role" already
names a :class:`~fairdm.contrib.contributors.models.Contribution`'s role (see CONTEXT.md).
"""

from typing import NamedTuple

from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _


class PortalRole(NamedTuple):
    """One shipped role: its stored name, its display label, and the exact permissions it holds.

    Attributes:
        name: The stored name of the role's group.
        label: The role's display label.
        permissions: The permissions the role holds, each an explicit ``app_label.codename``.
        covers_registered_types: Whether the role also holds the permissions of every
            registered sample and measurement type, which differ per portal.
    """

    name: str
    label: str | Promise
    permissions: tuple[str, ...] = ()
    covers_registered_types: bool = False


class PortalRoles:
    """The roles FairDM ships, and the methods that read and install them."""

    PORTAL_ADMINISTRATOR = PortalRole(
        name="Portal Administrator",
        label=_("Portal Administrator"),
        permissions=(
            "auth.view_group",
            "contributors.view_person",
            "contributors.change_person",
            "identity.change_identity",
            "identity.view_authority",
            "identity.change_authority",
        ),
    )

    DATA_CURATOR = PortalRole(
        name="Data Curator",
        label=_("Data Curator"),
        permissions=(
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
            "project.view_projectidentifier",
            "project.add_projectidentifier",
            "project.change_projectidentifier",
            "project.delete_projectidentifier",
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
            "dataset.view_datasetidentifier",
            "dataset.add_datasetidentifier",
            "dataset.change_datasetidentifier",
            "dataset.delete_datasetidentifier",
            "dataset.import_data",
            "dataset.can_publish",
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
            "sample.view_sampleidentifier",
            "sample.add_sampleidentifier",
            "sample.change_sampleidentifier",
            "sample.delete_sampleidentifier",
            "sample.view_samplerelation",
            "sample.add_samplerelation",
            "sample.change_samplerelation",
            "sample.delete_samplerelation",
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
            "measurement.view_measurementidentifier",
            "measurement.add_measurementidentifier",
            "measurement.change_measurementidentifier",
            "measurement.delete_measurementidentifier",
            "contributors.view_contribution",
            "contributors.add_contribution",
            "contributors.change_contribution",
            "contributors.delete_contribution",
            "literature.view_item",
            "literature.add_item",
            "literature.change_item",
            "literature.delete_item",
        ),
        covers_registered_types=True,
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

    #: Declaration order, which every method below follows.
    ROLES: tuple[PortalRole, ...] = (
        PORTAL_ADMINISTRATOR,
        DATA_CURATOR,
        COMMUNITY_MANAGER,
        DEVELOPER,
    )

    #: Legacy `auth.Group` names mapped to the shipped role each becomes. Renamed in place
    #: rather than replaced, so their membership carries across.
    LEGACY_NAMES = {
        "Portal Administrators": "Portal Administrator",
        "Data Administrators": "Data Curator",
        "Developers": "Developer",
    }

    @classmethod
    def shipped_names(cls) -> list[str]:
        """Return the stored name of every role FairDM ships, in declaration order.

        Returns:
            The role names.
        """
        return [role.name for role in cls.ROLES]

    @classmethod
    def is_held_by(cls, user, role: PortalRole) -> bool:
        """Say whether a user is an active member of a role's group.

        The check reads the group, never a Django permission: a Portal Administrator holds
        ``contributors.change_person`` and does not hold the Community Manager role. A superuser
        in no group holds no role.

        Args:
            user: The user, or an anonymous user for a visitor.
            role: The role to look for.

        Returns:
            True when the user is authenticated, active and in the group named ``role.name``.
        """
        if not (user.is_authenticated and user.is_active):
            return False
        return bool(user.groups.filter(name=role.name).exists())

    @classmethod
    def rights_carrying(cls) -> list[str]:
        """Return the stored names of the roles that hold at least one permission.

        Holding any of these gives access to the administration interface. Holding only a role
        absent from this list does not.

        Returns:
            The names of the roles with at least one permission.
        """
        return [role.name for role in cls.ROLES if role.permissions]

    @classmethod
    def reaches_every_record(cls, user, permission: str) -> bool:
        """Say whether a permission applies to every record for a user, listed on it or not.

        It does for an active superuser, and for someone who holds it through a shipped role. A
        permission granted straight to a person, or held through a group the portal made up
        itself, does not.

        Args:
            user: The user, or an anonymous user for a visitor.
            permission: The permission, as ``app_label.codename``.

        Returns:
            True when the permission reaches every record.
        """
        if not user.has_perm(permission):
            return False
        if user.is_superuser:
            return True
        app_label, codename = permission.split(".", 1)
        return bool(
            user.groups.filter(
                name__in=cls.shipped_names(),
                permissions__content_type__app_label=app_label,
                permissions__codename=codename,
            ).exists()
        )

    @classmethod
    def permissions_of(cls, role: PortalRole) -> tuple[str, ...]:
        """Return every permission a role holds in this portal.

        That is its declaration, and for a role that covers them the permissions of every
        registered sample and measurement type. Those are read from the registry because each
        portal registers its own types, and the polymorphic administration hands a record to
        the admin of its type, which asks for that type's own permissions.

        Args:
            role: The role.

        Returns:
            The permissions, each an explicit ``app_label.codename``.
        """
        if not role.covers_registered_types:
            return role.permissions
        from fairdm.registry import registry

        return role.permissions + tuple(
            f"{model._meta.app_label}.{action}_{model._meta.model_name}"
            for model in (*registry.samples, *registry.measurements)
            for action in model._meta.default_permissions
        )

    @classmethod
    def _rename_legacy_groups(cls) -> None:
        """Rename a legacy group row in place, and only when its target name is free.

        A rename carries the membership rows across, a fresh create does not. Renaming onto a name
        already taken would raise `IntegrityError` on `Group.name`'s uniqueness, so a legacy row is
        left alone once its target already exists.
        """
        existing = set(Group.objects.values_list("name", flat=True))
        for legacy_name, shipped_name in cls.LEGACY_NAMES.items():
            if legacy_name in existing and shipped_name not in existing:
                Group.objects.filter(name=legacy_name).update(name=shipped_name)
                existing.discard(legacy_name)
                existing.add(shipped_name)

    @classmethod
    def _permissions_for(cls, role: PortalRole) -> list[Permission]:
        """Return the `Permission` rows a role's declaration resolves to right now, in one query.

        A declared permission with no matching row yet is skipped rather than raised on:
        `INSTALLED_APPS` lists `fairdm` before the apps whose permissions these roles need, so an
        early `post_migrate` pass sees an incomplete set and a later pass converges.
        `dataset.can_publish` currently has no model declaring it and is skipped the same way.

        A role with no declared permissions (the Developer) returns early, because an empty `Q()`
        matches every `Permission` row rather than none.

        Args:
            role: The role whose permissions to resolve.

        Returns:
            The existing permissions the role declares.
        """
        permissions = cls.permissions_of(role)
        if not permissions:
            return []
        query = Q()
        for permission_name in permissions:
            app_label, codename = permission_name.split(".", 1)
            query |= Q(content_type__app_label=app_label, codename=codename)
        return list(Permission.objects.filter(query))

    @classmethod
    def reconcile(cls) -> None:
        """Install the four roles into the database.

        Renames the legacy rows first, so their membership carries across, then creates whatever
        role is still missing and sets each role's permissions to exactly ``permissions_of``,
        restoring a permission removed by hand and removing one added by hand. Membership is never
        touched, and a group this method did not create or rename is never looked at.
        """
        cls._rename_legacy_groups()

        for role in cls.ROLES:
            group, _created = Group.objects.get_or_create(name=role.name)
            group.permissions.set(cls._permissions_for(role))

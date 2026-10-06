"""Signal receivers that keep credit roles and shipped portal roles consistent."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def refuse_off_vocabulary_role(sender, action, reverse, model, pk_set, **kwargs):
    """Refuse a role from any vocabulary other than the roles vocabulary before it is written."""
    # `pre_add` covers `roles.add()` and the add half of `roles.set()`. Forms narrow their querysets
    # first, so this backstops fixtures, commands and direct calls. Reverse writes have no accessor.
    if action != "pre_add" or reverse or not pk_set:
        return

    from .models import CONTRIBUTION_ROLES_VOCABULARY_MESSAGE

    if (
        model.objects.filter(pk__in=pk_set)
        .exclude(vocabulary__name="fairdm-roles")
        .exists()
    ):
        raise ValidationError(CONTRIBUTION_ROLES_VOCABULARY_MESSAGE)


def refuse_shipped_role_deletion(sender, instance, **kwargs):
    """Refuse to delete a shipped portal role, including through a queryset delete."""
    from fairdm.portal_roles import PortalRoles

    if instance.name in PortalRoles.shipped_names():
        raise ValidationError(
            _('FairDM requires the "%(name)s" role and refuses to delete it.')
            % {"name": instance.name}
        )


def refuse_shipped_role_rename(sender, instance, **kwargs):
    """Refuse to rename a shipped portal role."""
    # New groups, including those `PortalRoles.reconcile()` creates, must pass.
    if instance._state.adding:
        return

    from django.contrib.auth.models import Group

    from fairdm.portal_roles import PortalRoles

    # Compare the stored name: the incoming one would miss a rename away from a shipped name.
    try:
        stored_name = Group.objects.get(pk=instance.pk).name
    except Group.DoesNotExist:
        return

    if stored_name in PortalRoles.shipped_names() and instance.name != stored_name:
        raise ValidationError(
            _('FairDM requires the "%(name)s" role and refuses to rename it.')
            % {"name": stored_name}
        )

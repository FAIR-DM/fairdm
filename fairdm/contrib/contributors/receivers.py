"""Signal receivers that keep the shipped portal roles in place."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


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

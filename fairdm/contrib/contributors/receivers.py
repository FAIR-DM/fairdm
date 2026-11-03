"""Signal receivers that keep the shipped portal roles in place and schedule the profile refresh."""

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


REFRESH_TASK = "fairdm.contrib.contributors.tasks.refresh_all_contributors"
"""The task path of the weekly refresh of profiles from ORCID and ROR."""


def seed_refresh_task(**kwargs):
    """Create the weekly refresh of profiles from ORCID and ROR, Monday at 03:00, if missing.

    A refresh task that exists is never touched, so a portal that changed its schedule,
    switched it off or renamed it keeps its choice. The task is found by its task path.

    Args:
        **kwargs: The signal's arguments, unused.
    """
    from django.conf import settings
    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    if PeriodicTask.objects.filter(task=REFRESH_TASK).exists():
        return
    crontab, created = CrontabSchedule.objects.get_or_create(
        minute="0",
        hour="3",
        day_of_week="1",
        day_of_month="*",
        month_of_year="*",
        timezone=settings.TIME_ZONE,
    )
    PeriodicTask.objects.create(
        name="Refresh profiles from ORCID and ROR",
        task=REFRESH_TASK,
        crontab=crontab,
        enabled=True,
    )

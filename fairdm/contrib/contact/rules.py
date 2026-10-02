"""Who may send, who receives, and how many a day.

Prototype code for specification 027: the answers are plausible, not proven.
"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from fairdm.contrib.contributors.models import Affiliation, Contributor, Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility

from .models import ContactMessage, ProblemReport

#: How many Contact messages and reports one account may send in a day, unless the portal says otherwise.
DEFAULT_DAILY_LIMIT = 10


def daily_limit():
    """Return the portal's daily limit per account."""
    return getattr(settings, "FAIRDM_CONTACT_DAILY_LIMIT", DEFAULT_DAILY_LIMIT)


def sent_today(user):
    """Count the Contact messages and reports the user sent in the last day."""
    since = timezone.now() - timedelta(days=1)
    return (
        ContactMessage.objects.filter(sender=user, sent__gte=since).count()
        + ProblemReport.objects.filter(reporter=user, created__gte=since).count()
    )


def at_limit(user):
    """Return whether the user has used up the day's allowance."""
    return sent_today(user) >= daily_limit()


def email_is_verified(user):
    """Return whether the user has a verified email address."""
    from allauth.account.models import EmailAddress

    return EmailAddress.objects.filter(user=user, verified=True).exists()


def change_permission(obj):
    """Return the permission that lets someone edit the record."""
    for model, permission in (
        (Project, "project.change_project"),
        (Dataset, "dataset.change_dataset"),
        (Sample, "sample.change_sample"),
        (Measurement, "measurement.change_measurement"),
    ):
        if isinstance(obj, model):
            return permission
    return None


def may_edit(user, obj):
    """Return whether the user may edit the record."""
    permission = change_permission(obj)
    if not permission or not user.is_authenticated:
        return False
    return user.has_perm(permission) or user.has_perm(permission, obj)


def is_visible(user, obj):
    """Return whether the user may open the record."""
    if isinstance(obj, Contributor):
        return True
    if isinstance(obj, Sample):
        return Sample.objects.visible_to(user).filter(pk=obj.pk).exists()
    if isinstance(obj, Measurement):
        return Measurement.objects.visible_to(user).filter(pk=obj.pk).exists()
    if obj.visibility == Visibility.PUBLIC:
        return True
    view = f"{obj._meta.app_label}.view_{obj._meta.model_name}"
    return user.is_authenticated and (user.has_perm(view) or user.has_perm(view, obj))


def active(people):
    """Keep the people who have an account they can sign in to."""
    return [p for p in people if p.is_active and p.is_claimed and p.email]


def editors(obj):
    """Return the people the record's own grants let edit it, portal roles aside."""
    from guardian.shortcuts import get_users_with_perms

    permission = change_permission(obj)
    if not permission:
        return []
    codename = permission.split(".")[1]
    target = obj
    if isinstance(obj, (Sample, Measurement)) and not get_users_with_perms(
        obj, only_with_perms_in=[codename]
    ):
        # A sample or measurement with no grants of its own follows its dataset's team.
        target, codename = obj.dataset, "change_dataset"
    return active(
        get_users_with_perms(
            target, only_with_perms_in=[codename], with_group_users=False
        )
    )


def data_curators():
    """Return the people holding the Data Curator portal role."""
    return active(
        get_user_model().objects.filter(groups__name=PortalRoles.DATA_CURATOR.name)
    )


def contact_recipients(obj, sender=None):
    """Return who a Contact message about the record goes to, and which rule chose them.

    Returns:
        The recipients and one of ``"contact"``, ``"editors"``, ``"curators"``, ``"person"``,
        ``"organization"``.
    """
    if isinstance(obj, Contributor):
        if obj.is_organization:
            people = Person.objects.filter(
                affiliations__organization=obj,
                affiliations__type__gte=Affiliation.MembershipType.ADMIN,
                affiliations__end_date__isnull=True,
            )
            found, rule = active(people), "organization"
        else:
            found, rule = active([Person.objects.get(pk=obj.pk)]), "person"
    else:
        contacts = Person.objects.filter(
            pk__in=obj.contributors.filter(roles__name="ContactPerson").values(
                "contributor"
            )
        )
        found, rule = active(contacts), "contact"
        if not found:
            found, rule = editors(obj), "editors"
        if not found:
            found, rule = data_curators(), "curators"
    if sender is not None and sender.is_authenticated:
        found = [p for p in found if p.pk != sender.pk]
    return found, rule


def report_recipients(obj):
    """Return who is told about a problem reported on the record."""
    return editors(obj) or data_curators()


def dataset_of(obj):
    """Return the dataset whose list a report on the record appears in."""
    return obj if isinstance(obj, Dataset) else obj.dataset


def reports_for(obj):
    """Return the reports a record's list shows: its own, and for a dataset those on its records too."""
    from django.contrib.contenttypes.models import ContentType

    if isinstance(obj, Dataset):
        return ProblemReport.objects.filter(dataset=obj)
    base = Sample if isinstance(obj, Sample) else Measurement
    types = [
        ContentType.objects.get_for_model(model, for_concrete_model=True)
        for model in (base, type(obj))
    ]
    return ProblemReport.objects.filter(content_type__in=types, object_id=obj.pk)

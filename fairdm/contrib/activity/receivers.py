"""Record what happens to a project or dataset as actions of django-activity-stream.

Every action is recorded not public: the panels read them back through the access rules of the
record they name, and no other feed exposes them. A failure to record is logged and never reaches
the save that caused it.
"""

import logging

from actstream import action
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from fairdm.contrib.contributors.models import Contribution
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
)
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)

logger = logging.getLogger(__name__)

EDITED = "edited"
PUBLISHED = "published"
JOINED = "joined"

UNREPORTED_FIELDS = frozenset({"modified", "visibility", "published"})
"""Fields whose change is not an edit: a timestamp, and two changes that read otherwise."""

RELATED_MODELS = (
    ProjectDescription,
    ProjectDate,
    ProjectIdentifier,
    DatasetDescription,
    DatasetDate,
    DatasetIdentifier,
)


def record(actor, verb, target=None):
    """Record one action, not public, and never raise.

    Args:
        actor: The object the action is about.
        verb: One of ``EDITED``, ``PUBLISHED`` or ``JOINED``.
        target: The object the action was done to, if any.
    """
    try:
        with transaction.atomic():
            action.send(actor, verb=verb, target=target, public=False)
    except Exception:
        logger.exception("Could not record %r for %r", verb, actor)


def record_edit(sender, instance, created, **kwargs):
    """Record an edit of a project or dataset when a field other than the quiet ones changed."""
    if created:
        return
    if set(instance.tracker.changed()) - UNREPORTED_FIELDS:
        record(instance, EDITED)


def record_published(sender, instance, created, **kwargs):
    """Record that a dataset was published, on creation or when the flag is first set."""
    if instance.published and (created or "published" in instance.tracker.changed()):
        record(instance, PUBLISHED)


def record_related_saved(sender, instance, **kwargs):
    """Record an edit of the record a description, date or identifier belongs to."""
    record(instance.related, EDITED)


def record_related_deleted(sender, instance, origin=None, **kwargs):
    """Record an edit of the record a related row belonged to, unless it went with the record."""
    if isinstance(origin, models.Model):
        cascaded = origin is not instance
    elif isinstance(origin, models.QuerySet):
        cascaded = origin.model is not sender
    else:
        cascaded = False
    if not cascaded:
        record(instance.related, EDITED)


def record_joined(sender, instance, created, **kwargs):
    """Record a contributor being added to a project or dataset."""
    if not created or instance.contributor_id is None:
        return
    credited = {
        ContentType.objects.get_for_model(Project).pk,
        ContentType.objects.get_for_model(Dataset).pk,
    }
    if instance.content_type_id not in credited:
        return
    target = instance.content_object
    if target is not None:
        record(instance.contributor.get_real_instance(), JOINED, target=target)


def connect():
    """Connect every receiver of this module to the signals it listens to."""
    post_save = models.signals.post_save
    post_delete = models.signals.post_delete
    post_save.connect(
        record_edit, sender=Project, dispatch_uid="activity.record_edit.project"
    )
    post_save.connect(
        record_edit, sender=Dataset, dispatch_uid="activity.record_edit.dataset"
    )
    post_save.connect(
        record_published, sender=Dataset, dispatch_uid="activity.record_published"
    )
    for model in RELATED_MODELS:
        post_save.connect(
            record_related_saved,
            sender=model,
            dispatch_uid=f"activity.record_related_saved.{model.__name__}",
        )
        post_delete.connect(
            record_related_deleted,
            sender=model,
            dispatch_uid=f"activity.record_related_deleted.{model.__name__}",
        )
    post_save.connect(
        record_joined, sender=Contribution, dispatch_uid="activity.record_joined"
    )

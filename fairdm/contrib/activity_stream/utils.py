"""
Activity Stream Utilities

Helper functions for creating and managing activities in FairDM.
"""

from actstream import action as actstream_action
from actstream import actions
from actstream.models import Follow
from django.contrib.auth.models import User
from django.db.models import Model


def create_activity(actor: User, verb: str, target: Model = None, action_object: Model = None, description: str = ""):
    """
    Create an activity in the activity stream.

    Args:
        actor: The user performing the action
        verb: The action verb (e.g., "created", "updated", "deleted")
        target: The primary object being acted upon
        action_object: An optional related object
        description: Optional human-readable description

    Returns:
        The created Action instance
    """
    return actstream_action.send(
        actor,
        verb=verb,
        target=target,
        action_object=action_object,
        description=description,
    )


def follow(user: User, obj: Model):
    """
    Make a user follow an object.

    Args:
        user: The user who will follow the object
        obj: The object to follow
    """
    actions.follow(user, obj)


def unfollow(user: User, obj: Model):
    """
    Make a user unfollow an object.

    Args:
        user: The user who will unfollow the object
        obj: The object to unfollow
    """
    actions.unfollow(user, obj)


def is_following(user: User, obj: Model) -> bool:
    """
    Check if a user is following an object.

    Args:
        user: The user to check
        obj: The object to check

    Returns:
        True if the user is following the object, False otherwise
    """
    return Follow.objects.is_following(user, obj)


def get_object_activities(obj: Model, limit: int = None):
    """
    Get all activities related to an object.

    Args:
        obj: The object to get activities for
        limit: Optional limit on number of activities to return

    Returns:
        QuerySet of Action objects
    """
    from actstream.models import Action
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(obj)

    # Get all actions where obj is the target or action_object
    activities = Action.objects.filter(
        target_object_id=obj.pk,
        target_content_type=content_type,
    ) | Action.objects.filter(
        action_object_object_id=obj.pk,
        action_object_content_type=content_type,
    )

    # Order by most recent first and prefetch related objects
    activities = (
        activities.select_related(
            "actor_content_type",
            "target_content_type",
            "action_object_content_type",
        )
        .prefetch_related("actor", "target", "action_object")
        .order_by("-timestamp")
    )

    if limit:
        activities = activities[:limit]

    return activities

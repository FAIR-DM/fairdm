"""Helpers for contributor avatars, role checks and contributions."""

from django.templatetags.static import static
from easy_thumbnails.files import get_thumbnailer
from research_vocabs.models import Concept


def get_contributor_avatar(contributor):
    """Return the URL of a contributor's avatar thumbnail.

    Args:
        contributor: The contributor.

    Returns:
        The thumbnail URL, or the default user icon when there is no image.
    """
    if not contributor.image:
        return static("icons/user.svg")

    return get_thumbnailer(contributor.image)["thumb"].url


def avatar_url(contributor, size=None):
    """Resolve a contributor's avatar for django-mvp's ``c-avatar``.

    Wired as ``MVP_CONFIG["brand"]["avatar_resolver"]``, so ``<c-mvp.avatar :for="contributor">``
    draws the contributor's photo or logo anywhere it is used.

    Args:
        contributor: A person, an organization, or None.
        size: The ``c-avatar`` size token; lg and above get the larger image.

    Returns:
        The thumbnail URL, or None so ``c-avatar`` falls back to its placeholder.
    """
    image = getattr(contributor, "image", None)
    if not image:
        return None
    alias = "medium" if size in ("lg", "xl", "xxl") else "small"
    try:
        return get_thumbnailer(image)[alias].url
    except Exception:  # A missing file draws the placeholder, never a server error.
        return None


def current_user_has_role(request, obj, role):
    """Check whether the signed-in user holds any of the roles on an object.

    Args:
        request: The current request.
        obj: A project, dataset or sample with contributors.
        role: A role name or a list of role names.

    Returns:
        True when the user's contribution to the object includes any of the roles.
    """
    current_user = request.user
    if not current_user.is_authenticated:
        return False

    if not isinstance(role, list):
        role = [role]

    if contribution_obj := obj.contributors.filter(contributor=current_user).first():
        return any(role in contribution_obj.roles for role in role)

    return False


def update_or_create_contribution(contributor, obj, roles=None):
    """Add a contributor to an object and add the given roles to their contribution.

    Args:
        contributor: The contributor to add.
        obj: The object to add them to. Needs a ``contributors`` manager and ``DEFAULT_ROLES``.
        roles: Role names to add. Defaults to ``obj.DEFAULT_ROLES``.

    Returns:
        A ``(contribution, created)`` pair, where ``created`` is False when the contributor
        was already on the object.
    """
    contribution, created = obj.contributors.get_or_create(
        contributor=contributor,
    )
    roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
    if not roles:
        roles = obj.DEFAULT_ROLES

    contribution.roles.add(*roles_qs.filter(name__in=roles))

    return contribution, created

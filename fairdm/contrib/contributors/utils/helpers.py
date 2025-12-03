"""
Helper utilities for contributors.

This module provides helper functions for working with contributors,
including avatar retrieval, role checking, and contribution management.
"""

from django.templatetags.static import static
from easy_thumbnails.files import get_thumbnailer
from research_vocabs.models import Concept


def get_contributor_avatar(contributor):
    """
    Returns the avatar URL for a given contributor.

    Args:
        contributor (Contributor): A Contributor object.

    Returns:
        str: The URL of the contributor's avatar.
    """
    if not contributor.image:
        return static("icons/user.svg")

    return get_thumbnailer(contributor.image)["thumb"].url


def current_user_has_role(request, obj, role):
    """
    Returns True if the current user has the specified role for the given object.

    Args:
        request (Request): The request object.
        obj (Project, Dataset, Sample): A database object containing a list of contributors.
        role (str, list): The role/s to check for.

    Returns:
        bool: True if the contributor has the specified roles.
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
    """
    Adds a contributor to the given object with specified roles.

    Behavior:
    - If the contributor already exists on the object and roles are provided, the roles are updated and the Contribution
      object is returned.
    - If the contributor already exists on the object and roles *are not* provided, the existing roles are retained and
      the Contribution object is returned unchanged.
    - If the contributor does not already exist on the object and roles are provided, a new Contribution object is created
      with the provided roles and returned.
    - If the contributor does not already exist on the object and roles are not provided, a new Contribution object is
      created with the object's DEFAULT_ROLES and returned.

    Args:
        contributor: The contributor instance to add.
        obj: The object to which the contributor is being added. Must have a 'contributors' manager and 'DEFAULT_ROLES' attribute.
        roles (optional): The roles to assign to the contributor. If not provided, uses obj.DEFAULT_ROLES.

    Returns:
        tuple: (contribution, created)
            contribution: The contribution instance.
            created (bool): True if a new contribution was created, False if it already existed.
    """
    contribution, created = obj.contributors.get_or_create(
        contributor=contributor,
    )
    roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
    if not roles:
        roles = obj.DEFAULT_ROLES

    contribution.roles.add(*roles_qs.filter(name__in=roles))

    return contribution, created

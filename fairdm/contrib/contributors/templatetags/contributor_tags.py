"""Template filters for contributions and roles."""

from django import template

register = template.Library()


@register.filter
def by_role(contributions, roles=None):
    """Filter contributions to those holding any of the roles.

    Args:
        contributions: The contributions queryset.
        roles: A comma-separated string or a list of role names. Empty returns all.

    Returns:
        The filtered contributions.
    """
    if not roles:
        return contributions
    if isinstance(roles, str):
        roles = roles.split(",")
    return contributions.filter(roles__name__in=roles)


@register.filter
def has_role(contribution, roles=None):
    """Check whether the contribution holds any of the roles.

    Args:
        contribution: The contribution.
        roles: A comma-separated string or a list of role names.

    Returns:
        True when a role matches. With no roles the contribution itself is returned.
    """
    if not roles:
        return contribution
    if isinstance(roles, str):
        roles = roles.split(",")
    return contribution.roles.filter(name__in=roles).exists()

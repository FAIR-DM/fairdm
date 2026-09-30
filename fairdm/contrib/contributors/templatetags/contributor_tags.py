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


@register.filter
def as_contributor(value):
    """Return the contributor behind a contribution, or the value itself if it is one.

    Args:
        value: A ``Contribution``, a ``Contributor`` or None.

    Returns:
        The contributor, or None when a contribution's contributor was deleted.
    """
    if value is None:
        return None
    if hasattr(value, "content_object") and hasattr(value, "roles"):
        value = value.contributor
    # A foreign key to the polymorphic base returns a plain Contributor; the display needs to
    # know whether it is a person or an organization.
    if (
        value is not None
        and type(value).__name__ == "Contributor"
        and hasattr(value, "get_real_instance")
    ):
        value = value.get_real_instance()
    return value


@register.filter
def as_contributors(values):
    """Turn a list of contributions or contributors into a list of contributors.

    Contributions whose contributor was deleted are dropped rather than drawn as a blank.
    """
    if values is None:
        return []
    return [c for c in (as_contributor(v) for v in values) if c is not None]


@register.simple_tag
def contributor_name(contributor, name_format=""):
    """The contributor's name in the requested format.

    The preferred ``name`` unless a person's name is asked for family-first, for citations.
    """
    if contributor is None:
        return ""
    if name_format and hasattr(contributor, "get_full_name_display"):
        return contributor.get_full_name_display(name_format)
    return contributor.name


@register.simple_tag
def split_contributors(values, limit=0, total=None):
    """Split a list of contributors into those shown and a count of the rest.

    Args:
        values: Contributions or contributors.
        limit: How many to show; 0 shows everyone.
        total: The real total when ``values`` was already cut short by the caller.

    Returns:
        ``{"shown", "more", "total"}``.
    """
    contributors = as_contributors(values)
    count = int(total) if total not in (None, "") else len(contributors)
    limit = int(limit or 0)
    # Counting one hidden contributor takes as much room as naming them, so name them.
    if limit and len(contributors) == limit + 1 and count == len(contributors):
        limit += 1
    shown = contributors[:limit] if limit else contributors
    return {"shown": shown, "more": max(count - len(shown), 0), "total": count}

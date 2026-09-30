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


# The six fallback tints an avatar without an image can take. Mixed from theme colours in
# `fairdm.css`, so they follow the theme; status colours are left out on purpose.
AVATAR_TINTS = 6

# Image alias per avatar size. The `contributors` aliases are not cropped, so the component
# crops with `object-fit` and a 2x source keeps a face sharp on a high-density screen.
AVATAR_IMAGE_ALIAS = {"xs": "small", "sm": "small", "md": "small", "lg": "small", "xl": "medium"}


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
    if value is not None and type(value).__name__ == "Contributor" and hasattr(value, "get_real_instance"):
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


@register.filter
def is_organization(contributor):
    """Whether the contributor is an organization."""
    from fairdm.contrib.contributors.models import Organization

    return isinstance(contributor, Organization)


@register.simple_tag
def contributor_avatar(contributor, size="md"):
    """Everything an avatar needs to draw one contributor.

    Returns:
        A dict with ``src`` (image URL or None), ``initials``, ``tint`` (0-5) and
        ``organization`` (bool).
    """
    import hashlib

    from easy_thumbnails.files import get_thumbnailer

    src = None
    if contributor is not None and contributor.image:
        try:
            src = get_thumbnailer(contributor.image)[AVATAR_IMAGE_ALIAS.get(size, "small")].url
        except Exception:  # A missing or unreadable file falls back to initials, never a 500.
            src = None

    organization = is_organization(contributor)
    initials = ""
    if contributor is not None and not organization:
        first = (getattr(contributor, "first_name", "") or "").strip()
        last = (getattr(contributor, "last_name", "") or "").strip()
        if first or last:
            initials = (first[:1] + last[:1]).upper()
        else:
            words = (contributor.name or "").split()
            if words:
                initials = (words[0][:1] + (words[-1][:1] if len(words) > 1 else "")).upper()

    key = str(getattr(contributor, "uuid", "") or getattr(contributor, "pk", ""))
    tint = int(hashlib.md5(key.encode(), usedforsecurity=False).hexdigest(), 16) % AVATAR_TINTS
    return {"src": src, "initials": initials, "tint": tint, "organization": organization}


@register.simple_tag
def contributor_orcid(contributor):
    """The person's ORCID identifier and whether it is authenticated, or None.

    Returns:
        ``{"value", "url", "authenticated"}``, or None for an organization or a person
        without an ORCID iD.
    """
    if contributor is None or is_organization(contributor):
        return None
    identifier = contributor.identifiers.filter(type="ORCID").first()
    if identifier is None:
        return None
    return {
        "value": identifier.value,
        "url": f"https://orcid.org/{identifier.value}",
        "authenticated": contributor.orcid_is_authenticated,
    }


@register.simple_tag
def contributor_ror(contributor):
    """The organization's ROR identifier, or None."""
    if contributor is None or not is_organization(contributor):
        return None
    identifier = contributor.identifiers.filter(type="ROR").first()
    if identifier is None:
        return None
    return {"value": identifier.value, "url": f"https://ror.org/{identifier.value}"}


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
def contributor_secondary(contributor, contribution=None):
    """The one line that tells two contributors of the same name apart.

    A person: their affiliation on this credit, else their primary affiliation. An organization:
    its type and location.
    """
    if contributor is None:
        return ""
    if is_organization(contributor):
        parts = [contributor.get_type_display() if contributor.type else "", contributor.get_location_display() or ""]
        return " · ".join(p for p in parts if p)
    if getattr(contribution, "affiliation_id", None):
        return contribution.affiliation.name
    primary = contributor.primary_affiliation()
    return primary.organization.name if primary else ""


@register.simple_tag
def contribution_roles(contribution):
    """A contribution's role labels, in vocabulary order."""
    if contribution is None or not hasattr(contribution, "roles"):
        return []
    return [role.label for role in contribution.roles.all()]


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

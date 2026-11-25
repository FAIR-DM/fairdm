"""Tells the dock which of its items holds the page being shown."""

from django import template

register = template.Library()

#: Each dock section and the views it holds: whole URL namespaces, then single view names.
SECTIONS = {
    "home": {"namespaces": set(), "views": {"home"}},
    "projects": {"namespaces": {"project"}, "views": {"project-list", "project-create"}},
    "datasets": {"namespaces": {"dataset"}, "views": {"dataset-list", "dataset-create"}},
    "search": {"namespaces": set(), "views": {"mvp-search"}},
}


@register.simple_tag(takes_context=True)
def dock_section(context):
    """Return the dock item the current page belongs to.

    A project's or a dataset's own pages (its overview, contributors, samples, edit form) belong
    to Projects or Datasets, so the dock keeps showing where the reader is while they move
    through a record's tabs. A page only the sidebar reaches belongs to Menu.

    Returns:
        One of ``home``, ``projects``, ``datasets``, ``search`` or ``menu``.
    """
    request = context.get("request")
    match = getattr(request, "resolver_match", None)
    if match is None:
        return "menu"
    for section, holds in SECTIONS.items():
        if match.view_name in holds["views"] or match.namespace in holds["namespaces"]:
            return section
    return "menu"

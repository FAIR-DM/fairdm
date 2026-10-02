"""Template tags the overview pages use to offer the two page actions.

Stands in for the page actions dropdown that specification 021 (#401) delivers.
"""

from django import template
from django.urls import NoReverseMatch
from django.utils.translation import gettext as _

from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins import reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

from .. import rules
from ..models import ProblemReport

register = template.Library()


@register.simple_tag(takes_context=True)
def page_actions(context, record):
    """Return the page actions this feature offers on the record, for the visitor looking at it."""
    request = context["request"]
    actions = []
    try:
        if isinstance(record, (Project, Dataset, Contributor)):
            recipients, _rule = rules.contact_recipients(record, request.user)
            if recipients:
                actions.append(
                    {
                        "label": _("Contact"),
                        "icon": "email",
                        "href": reverse(record, "contact"),
                    }
                )
        if isinstance(record, (Dataset, Sample, Measurement)):
            actions.append(
                {
                    "label": _("Report a problem"),
                    "icon": "warning",
                    "href": reverse(record, "report-problem"),
                }
            )
    except NoReverseMatch:
        return []
    return actions


@register.simple_tag(takes_context=True)
def reported_problems(context, record):
    """Return the list's address and the open count, or nothing for someone who may not edit the record."""
    request = context["request"]
    if not isinstance(record, (Dataset, Sample, Measurement)):
        return None
    if not rules.may_edit(request.user, record):
        return None
    return {
        "url": reverse(record, "reported-problems"),
        "open": rules.reports_for(record)
        .filter(state=ProblemReport.State.OPEN)
        .count(),
    }

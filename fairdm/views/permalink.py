"""A record's permalink: the portal's root followed by the record's portal ID."""

from django.urls import reverse
from django.views.generic import RedirectView
from shortuuid import ShortUUID

from fairdm.contrib.contributors.models import Contributor
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

UUID_FIELDS = [
    model._meta.get_field("uuid")
    for model in (Project, Dataset, Sample, Measurement, Contributor)
]

# One letter, then the alphabet the uuid fields generate from, at their shared length.
PORTAL_ID_PATTERN = (
    f"[{''.join(field.prefix for field in UUID_FIELDS)}]"
    f"[{ShortUUID(alphabet=UUID_FIELDS[0].alphabet).get_alphabet()}]"
    f"{{{UUID_FIELDS[0].length}}}"
)

OVERVIEW_URL_NAMES = {
    "p": "project:overview",
    "d": "dataset:overview",
    "s": "sample:overview",
    "m": "measurement:overview",
    "c": "contributor:overview",
}


def get_permalink(record, request=None) -> str:
    """Return a record's permalink.

    Args:
        record: Any record with a portal ID in its ``uuid`` field.
        request: When given, the link is absolute for this request's host.

    Returns:
        The path of the permalink, or the absolute link when a request is given.
    """
    path = reverse("permalink", kwargs={"portal_id": record.uuid})
    return request.build_absolute_uri(path) if request else path


class PermalinkView(RedirectView):
    """Send a visitor from a record's permalink to the record's overview page.

    The redirect is temporary, so a browser asks again on every visit. The view looks
    nothing up: the overview page answers a record the visitor may not open exactly as it
    answers one that does not exist.
    """

    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        """Return the overview address for the letter the portal ID starts with."""
        portal_id = kwargs["portal_id"]
        self.pattern_name = OVERVIEW_URL_NAMES[portal_id[0]]
        return super().get_redirect_url(uuid=portal_id)

"""A record's permanent link: the portal's root followed by the record's portal ID."""

from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import RedirectView

PORTAL_ID_LETTERS = "pdsmc"
# shortuuid's default alphabet: digits and letters without 0, 1, I, O and l.
PORTAL_ID_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class PortalIDConverter:
    """Match exactly the shape of a portal ID: a record letter and 22 characters."""

    regex = f"[{PORTAL_ID_LETTERS}][{PORTAL_ID_ALPHABET}]{{22}}"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


def record_models():
    """Return the model each portal ID letter names."""
    from fairdm.contrib.contributors.models import Contributor
    from fairdm.core.dataset.models import Dataset
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.project.models import Project
    from fairdm.core.sample.models import Sample

    return {
        "p": Project.objects,
        "d": Dataset.all_objects,
        "s": Sample.objects,
        "m": Measurement.objects,
        "c": Contributor.objects,
    }


def record_link(record) -> str:
    """Return the path of a record's permanent link."""
    return reverse("record-link", kwargs={"portal_id": record.uuid})


class RecordLinkView(RedirectView):
    """Send a visitor from a record's permanent link to the record's page.

    The redirect is temporary, so a browser asks again on every visit and a later change to
    where a kind of record's pages live reaches everyone. The record's page decides who may
    see it.
    """

    permanent = False
    query_string = True

    def get_redirect_url(self, *args, **kwargs):
        portal_id = kwargs["portal_id"]
        manager = record_models()[portal_id[0]]
        record = get_object_or_404(manager, uuid=portal_id)
        return record.get_absolute_url()

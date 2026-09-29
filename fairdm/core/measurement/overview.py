"""What the measurement overview page draws, from the base ``Measurement`` model alone.

Everything here reads fields every measurement has, plus what the registry says about the
measurement's type. What a particular type adds (an element and its concentration, an isotope
ratio) is drawn by that type's own template, which extends
``measurement/measurement_overview.html`` and fills its blocks. See ``TypedOverviewPlugin``.

A reuser asks four things of a single measurement: what the result was, what it was measured
on, how it was measured, and whether they can cite and reuse it. The page answers them in that
order.
"""

from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from fairdm.core import overview as shared

#: Each step in how a measurement was made: its date type, the contributor role that performs
#: it, the description type that explains it, and what the page calls it. The measurement
#: vocabularies describe the same procedure three ways, so the page puts them back together.
PROCEDURE = [
    ("Setup", "MeasurementPreparation", "MeasurementSetup", gettext_lazy("Set up")),
    (None, "MeasurementCollection", "MeasurementConditions", gettext_lazy("Measured")),
    ("TearDown", None, "MeasurementTearDown", gettext_lazy("Taken down")),
]

#: Rows shown in the list of other measurements made on the same sample.
SIBLINGS = 8


def build(request, measurement, can_manage):
    from fairdm.core.project.plugins import project_is_visible
    from fairdm.core.sample.models import Sample

    user = request.user
    entries = shared.credits(measurement)
    descriptions = {d.type: d.value for d in measurement.descriptions.all()}
    dates = {d.type: d.value for d in measurement.dates.all()}
    sample = measurement.sample
    sample_visible = Sample.objects.filter(pk=sample.pk).visible_to(user).exists()
    project = measurement.dataset.project
    if project is not None and not project_is_visible(request, project):
        project = None
    measurement_type = str(type(measurement)._meta.verbose_name)
    identifiers = shared.identifiers(measurement)
    doi = next((i for i in identifiers if i["type"] == "DOI"), None)
    setup = dates.get("Setup")

    title = _("%(name)s [%(type)s] of %(sample)s") % {
        "name": measurement.name,
        "type": measurement_type,
        "sample": sample if sample_visible else _("an unpublished sample"),
    }
    citation = {
        "title": _("Citation"),
        "text": shared.citation(
            request,
            authors=shared.with_role(entries, "MeasurementCollection"),
            year=getattr(getattr(setup, "date", None), "year", None)
            or measurement.added.year,
            title=title,
            link=doi["link"]
            if doi
            else request.build_absolute_uri(measurement.get_absolute_url()),
        ),
    }
    if not doi:
        citation["note"] = _(
            "Most measurements are cited through their dataset. This citation points at this page."
        )
        citation["note_url"] = measurement.dataset.get_absolute_url() + "#cite"
        citation["note_link"] = _("Cite the dataset")

    parents = []
    if project is not None:
        parents.append({"label": _("Project"), "icon": "project", "record": project})
    parents.append(
        {"label": _("Dataset"), "icon": "dataset", "record": measurement.dataset}
    )
    parents.append(shared.license_row(measurement.dataset.license))

    return {
        "record": measurement,
        "overview_icon": "measurement",
        "can_manage": can_manage,
        "measurement_type": measurement_type,
        "result": result(measurement),
        "type_info": shared.type_info(measurement),
        "procedure": shared.timeline(PROCEDURE, dates, descriptions, entries),
        "notes": descriptions.get("Other"),
        "sample": sample,
        "sample_type": shared.sentence_case(type(sample)._meta.verbose_name),
        "sample_status": sample_status(sample),
        "sample_visible": sample_visible,
        "other_dataset": sample.dataset_id != measurement.dataset_id,
        "siblings": siblings(user, measurement),
        "project": project,
        "citation": citation,
        "identifiers": identifiers,
        "api_url": shared.safe_reverse("api:measurement-detail", uuid=measurement.uuid),
        "people": shared.people(entries),
        "details": parents
        + [
            {"label": _("Added"), "icon": "calendar", "date": measurement.added},
            {"label": _("Last updated"), "icon": "time", "date": measurement.modified},
        ],
    }


def result(measurement):
    """The value, when the measurement's type declares one.

    ``Measurement.get_value`` is part of the base model's contract: a type that defines ``value``
    (and optionally ``uncertainty``) gets its result shown here with no template of its own. A
    type that records its result some other way leaves this empty and fills the
    ``overview.result`` block itself.
    """
    if getattr(measurement, "value", None) is None:
        return None
    return {"text": measurement.print_value()}


def sample_status(sample):
    """The sample's status label and badge colour, as its own page shows them."""
    from fairdm.core.sample.overview import STATUS_VARIANTS

    status = getattr(sample.status, "name", sample.status)
    if not status:
        return None
    labels = dict(type(sample)._meta.get_field("status").choices)
    return {
        "label": labels.get(status, status),
        "variant": STATUS_VARIANTS.get(status, "neutral"),
    }


def siblings(user, measurement):
    """Other measurements made on the same sample, most recent first: the context a single value
    is read against. Each is shown only if the viewer may see its own dataset."""
    from .models import Measurement

    queryset = (
        Measurement.objects.filter(sample_id=measurement.sample_id)
        .exclude(pk=measurement.pk)
        .visible_to(user)
        .select_related("dataset")
        .order_by("-added")
    )
    total = queryset.count()
    rows = [
        {
            "measurement": m,
            "type": str(type(m)._meta.verbose_name),
            "same_type": type(m) is type(measurement),
        }
        for m in queryset[:SIBLINGS]
    ]
    return {"rows": rows, "more": max(total - SIBLINGS, 0), "total": total}

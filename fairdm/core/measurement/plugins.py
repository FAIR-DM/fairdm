"""Plugin pages for measurements.

A measurement has its own page at its permanent address, ``/measurement/<uuid>/``, in the same
tabbed detail view as projects, datasets and samples. The overview is its first tab, and a portal
adds further tabs by registering plugins against ``Measurement`` here or in its own app.
"""

from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from fairdm import plugins
from fairdm.contrib.plugins.access import has_perm
from fairdm.core.overview import safe_reverse, sentence_case
from fairdm.core.plugins import TypedOverviewPlugin

from .models import Measurement


@plugins.register(Measurement, label=_("Overview"), icon="view", order=0)
class Overview(TypedOverviewPlugin):
    """The measurement's own page, drawn from ``measurement/measurement_overview.html``, which
    reads only the base ``Measurement`` model and the registry's description of its type. A
    measurement type adds its own content with ``<app_label>/<model_name>_overview.html``; see
    :class:`TypedOverviewPlugin`.

    A reuser asks four things of a single measurement: what the result was, what it was measured
    on, how it was measured, and whether they can cite and reuse it. The page answers them in that
    order.

    Attributes:
        procedure_steps: Each step in how a measurement was made: its date type, the contributor
            role that performs it, the description type that explains it, and what the page calls
            it. The measurement vocabularies describe the same procedure three ways, so the page
            puts them back together.
        siblings_shown: Rows shown in the list of other measurements made on the same sample.
    """

    base_model = Measurement
    fallback_template = "measurement/measurement_overview.html"
    # The root of the measurement's address, as the project and dataset overviews are. Left unset
    # the plugin base would mount it at `overview/` and move the permanent address.
    url_path = None

    procedure_steps = [
        ("Setup", "MeasurementPreparation", "MeasurementSetup", _("Set up")),
        (None, "MeasurementCollection", "MeasurementConditions", _("Measured")),
        ("TearDown", None, "MeasurementTearDown", _("Taken down")),
    ]
    siblings_shown = 8

    def get_page_title(self):
        """Title the page with the measurement's name, or its portal ID when it has none."""
        return self.base_object.name or str(self.base_object.uuid)

    def get_breadcrumbs(self):
        """Name the measurement in the trail by its portal ID when it has no name.

        Returns:
            The trail, with the measurement's own entry reading as its portal ID when unnamed.
        """
        trail = super().get_breadcrumbs()
        measurement = self.base_object
        if measurement is not None and not measurement.name:
            own_address = measurement.get_absolute_url()
            for crumb in trail:
                if crumb.get("href") == own_address:
                    crumb["text"] = str(measurement.uuid)
        return trail

    def get_context_data(self, **kwargs):
        """Add the measurement and everything the overview page draws."""
        from fairdm.core.project.plugins import project_is_visible
        from fairdm.core.sample.models import Sample

        context = super().get_context_data(**kwargs)
        measurement = self.base_object
        entries = self.get_credits()
        descriptions = {d.type: d.value for d in measurement.descriptions.all()}
        dates = {d.type: d.value for d in measurement.dates.all()}
        sample = measurement.sample
        sample_visible = (
            Sample.objects.filter(pk=sample.pk).visible_to(self.request.user).exists()
        )
        project = measurement.dataset.project
        if project is not None and not project_is_visible(self.request, project):
            project = None
        identifiers = self.get_identifiers()

        context["measurement"] = measurement
        context.update(
            {
                "record": measurement,
                "record_title": self.get_page_title(),
                "overview_icon": "measurement",
                "can_manage": has_perm(
                    self.request, "dataset.change_dataset", measurement.dataset
                ),
                "measurement_type": str(type(measurement)._meta.verbose_name),
                "result": self.get_result(),
                "type_info": self.get_type_info(),
                "procedure": self.get_timeline(
                    self.procedure_steps, dates, descriptions, entries
                ),
                "notes": descriptions.get("Other"),
                "sample": sample,
                "sample_type": sentence_case(type(sample)._meta.verbose_name),
                "sample_status": self.get_sample_status(),
                "sample_visible": sample_visible,
                "other_dataset": sample.dataset_id != measurement.dataset_id,
                "siblings": self.get_siblings(),
                "project": project,
                "citation": self.get_citation_details(
                    entries, dates, identifiers, sample if sample_visible else None
                ),
                "identifiers": identifiers,
                "api_url": safe_reverse(
                    "api:measurement-detail", uuid=measurement.uuid
                ),
                "people": self.get_people(entries),
                "details": self.get_details(project),
            }
        )
        return context

    def get_result(self):
        """Read the value, when the measurement's type declares one.

        ``Measurement.get_value`` is part of the base model's contract: a type that defines
        ``value`` (and optionally ``uncertainty``) gets its result shown with no template of its
        own. A type that records its result some other way leaves this empty and fills the
        ``overview.result`` block itself.

        Returns:
            The result's text, or ``None`` when the type declares no value.
        """
        measurement = self.base_object
        if getattr(measurement, "value", None) is None:
            return None
        return {"text": measurement.print_value()}

    def get_sample_status(self):
        """Read the sample's status label and badge colour, as its own page shows them.

        Returns:
            The label and colour, or ``None`` when the sample records no status.
        """
        from fairdm.core.sample.plugins import Overview as SampleOverview

        sample = self.base_object.sample
        status = getattr(sample.status, "name", sample.status)
        if not status:
            return None
        labels = dict(type(sample)._meta.get_field("status").choices)
        return {
            "label": labels.get(status, status),
            "variant": SampleOverview.status_variants.get(status, "neutral"),
        }

    def get_siblings(self):
        """Read the other measurements made on the same sample, most recent first.

        They are the context a single value is read against. Each is shown only if the viewer may
        see its own dataset.

        Returns:
            The rows shown, how many are left over and how many the viewer may see.
        """
        measurement = self.base_object
        queryset = (
            Measurement.objects.filter(sample_id=measurement.sample_id)
            .exclude(pk=measurement.pk)
            .visible_to(self.request.user)
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
            for m in queryset[: self.siblings_shown]
        ]
        return {
            "rows": rows,
            "more": max(total - self.siblings_shown, 0),
            "total": total,
        }

    def get_citation_details(self, entries, dates, identifiers, sample):
        """Write the citation, and where the measurement has no DOI, a note pointing at its dataset.

        Args:
            entries: The record's credits, from :meth:`get_credits`.
            dates: The measurement's dates, by type.
            identifiers: The measurement's identifiers, from :meth:`get_identifiers`.
            sample: The sample it was made on, or ``None`` when the viewer may not see it.

        Returns:
            The card's title and text, with the note and its link when there is no DOI.
        """
        measurement = self.base_object
        doi = next((i for i in identifiers if i["type"] == "DOI"), None)
        setup = dates.get("Setup")
        title = gettext("%(name)s [%(type)s] of %(sample)s") % {
            "name": measurement.name,
            "type": str(type(measurement)._meta.verbose_name),
            "sample": sample
            if sample is not None
            else gettext("an unpublished sample"),
        }
        citation = {
            "title": gettext("Citation"),
            "text": self.get_citation(
                authors=self.get_contributors_with_role(
                    entries, "MeasurementCollection"
                ),
                year=getattr(getattr(setup, "date", None), "year", None)
                or measurement.added.year,
                title=title,
                link=doi["link"]
                if doi
                else self.request.build_absolute_uri(measurement.get_absolute_url()),
            ),
        }
        if not doi:
            citation["note"] = gettext(
                "Most measurements are cited through their dataset. This citation points at this page."
            )
            citation["note_url"] = measurement.dataset.get_absolute_url() + "#cite"
            citation["note_link"] = gettext("Cite the dataset")
        return citation

    def get_details(self, project):
        """Write the Details card's entries: where the measurement sits, its licence and dates.

        Args:
            project: The parent project, or ``None`` when there is none or the viewer may not see it.

        Returns:
            The entries for :class:`c-card.details`.
        """
        measurement = self.base_object
        parents = []
        if project is not None:
            parents.append(
                {"label": gettext("Project"), "icon": "project", "record": project}
            )
        parents.append(
            {
                "label": gettext("Dataset"),
                "icon": "dataset",
                "record": measurement.dataset,
            }
        )
        parents.append(self.get_license_entry(measurement.dataset.license))
        return [
            *parents,
            {"label": gettext("Added"), "icon": "calendar", "date": measurement.added},
            {
                "label": gettext("Last updated"),
                "icon": "time",
                "date": measurement.modified,
            },
        ]


# `fairdm.core` is not an installed app, so plugin discovery does not reach its modules. This is
# the last of the four record modules to load, so each record's overview stays first registered.
import fairdm.core.editing  # noqa: E402, F401

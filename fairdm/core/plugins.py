"""Reusable overview plugins for the core record pages."""

from collections import OrderedDict
from dataclasses import replace
from datetime import date
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import NoReverseMatch, reverse
from django.utils.formats import date_format
from django.utils.http import content_disposition_header
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views import View
from partial_dates import Precision
from pyecharts import options as opts
from pyecharts.charts import Line

from fairdm.contrib.contributors.models import Contribution, Contributor
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.core.citation import FORMATS, Citation, CitedName
from fairdm.core.overview import describe_coverage, format_authors, sentence_case
from fairdm.core.vocabularies import DOI, IGSN
from fairdm.views import FairDMTemplateView


class OverviewPlugin(Plugin, FairDMTemplateView):
    """Reusable overview plugin for displaying object details.

    This base class provides a standard overview/detail view for any model.
    Portal developers can inherit from this and customize:
    - menu: Configure tab label, icon, and order
    - template_name: Override the template (or use hierarchical resolution)
    - get_context_data(): Add custom context variables
    - permission: Set required permission for access

    Attributes:
        page_lead: The line under the page title.
        page_icon: The icon shown beside the page title.
        menu: The tab label, icon and order.

    Example:
        ```python
        from fairdm import plugins
        from fairdm.core.plugins import OverviewPlugin


        @plugins.register(Sample)
        class SampleOverview(OverviewPlugin):
            menu = {"label": "Overview", "icon": "eye", "order": 0}
            template_name = "samples/sample_overview.html"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["measurements"] = self.base_object.measurements.all()
                return context
        ```
    """

    page_lead = _("Overview")
    page_icon = "overview"
    menu = {"label": _("Overview"), "icon": "overview", "order": 0}

    def get_page_title(self):
        """Use the object's string representation as the page title."""
        return str(self.base_object)


class CitationFile(Plugin, View):
    """One format of a record's citation, as a file, at ``<record address>cite/<format>/``.

    The record's overview answers who may open it, and this view asks that overview, so a
    private record answers a stranger as its page does and an unknown record is not found. The
    file is the format's value on the overview's own context, so it is the one the Cite panel
    shows.

    A portal plugin that sets its own ``extra_views`` must list this class to keep the
    addresses.

    Attributes:
        name: The route's name, ``<namespace>:overview-citation``.
        url_path: The route's last part, ``cite/<format>``.
    """

    name = "citation"
    url_path = "cite/<str:format>"

    def setup(self, request, *args, **kwargs):
        """Build the overview that owns this address, set up for this request."""
        super().setup(request, *args, **kwargs)
        self.owner = self.plugin_class(
            registered_model=self.registered_model, menu=self.menu
        )
        self.owner.setup(request, *args, **kwargs)

    def has_permission(self):
        """Ask the owning overview, so the file opens for whom the page opens for."""
        return self.owner.has_permission()

    def handle_no_permission(self):
        """Answer as the owning overview answers."""
        return self.owner.handle_no_permission()

    def get(self, request, *args, **kwargs):
        """Answer with the citation in the format named by the address.

        Args:
            request: The request.
            *args: Positional URL arguments.
            **kwargs: Keyword URL arguments, the record's and the ``format``.

        Returns:
            The file, as an attachment named after the record.

        Raises:
            Http404: The format is not one of ``FORMATS``.
        """
        chosen = next((f for f in FORMATS if f.key == kwargs["format"]), None)
        if chosen is None:
            raise Http404(_("No such citation format."))
        citation = self.owner.get_context_data()["citation"]
        value = next(f["value"] for f in citation["formats"] if f["key"] == chosen.key)
        response = HttpResponse(value, content_type=chosen.content_type)
        response["Content-Disposition"] = content_disposition_header(
            True, citation["work"].filename(chosen.extension)
        )
        return response


class RecordOverviewPlugin(OverviewPlugin):
    """The overview of a project, dataset, sample or measurement.

    Holds what every one of those pages works out the same way: who is credited, the People
    panel, identifiers, citation, timeline, licence entry, records by type and the charts. A portal changes one
    piece of a page by subclassing that page's plugin and overriding one of these methods.

    Attributes:
        people_named: How many credits the People panel names, with their roles.
        people_faces: How many faces it draws after them before it counts the rest.
        resolvable_identifier_types: The identifier types that link to doi.org.
    """

    people_named = 6
    people_faces = 10
    resolvable_identifier_types = (DOI, IGSN)
    extra_views = [CitationFile]

    def get_context_data(self, **kwargs):
        """Add what the shared page reads on every record.

        The People panel's link to the Contributors tab, each panel's Edit link, the word for the
        record's kind, and the record's image, which fills the header's trailing side.
        """
        from fairdm.contrib.contributors.access import RecordAccess
        from fairdm.core.editing import edit_links

        record = self.base_object
        context = super().get_context_data(**kwargs)
        context["people_url"] = plugin_reverse(record, "contribution-list")
        context["edit"] = edit_links(self.request, record)
        context["record_kind"] = RecordAccess(record).kind
        context["cover_image"] = record.image or None
        return context

    def get_contributions(self) -> list[Contribution]:
        """List the record's credits, people first and then organizations, each in order.

        Everything an overview or a citation names comes from this list, so they follow the
        order the team set on the Contributors tab. ``select_related`` stops at the polymorphic
        base, which has neither a person's name parts nor a way to tell the two apart, so the
        real instances are fetched in one extra query.

        Returns:
            The record's contributions, each with its real contributor, roles prefetched.
        """
        listed = self.base_object.contributors
        contributions = [
            *listed.people().select_related("affiliation").prefetch_related("roles"),
            *listed.organizations()
            .select_related("affiliation")
            .prefetch_related("roles"),
        ]
        real = Contributor.objects.in_bulk([c.contributor_id for c in contributions])
        for contribution in contributions:
            contribution.contributor = real[contribution.contributor_id]
        return contributions

    @staticmethod
    def get_role_uris(contribution) -> set[str]:
        """Give the addresses of the roles held on one credit.

        Args:
            contribution: A contribution, from :meth:`get_contributions`.

        Returns:
            The addresses of its roles.
        """
        return {role.uri for role in contribution.roles.all()}

    @staticmethod
    def get_contributors_with_role(entries, role) -> list[Contributor]:
        """Pick out the contributors credited with one role.

        Args:
            entries: The record's credits, from :meth:`get_credits`.
            role: The address of the role.

        Returns:
            The contributors of every entry that holds it.
        """
        return [entry["contributor"] for entry in entries if role in entry["roles"]]

    def get_credits(self) -> list[dict[str, Any]]:
        """List everyone credited on the record.

        Each contributor is its own type (person or organisation). The affiliation is the one
        recorded on the credit itself, so a person credited with no organization has none.

        Returns:
            One ``{"contributor", "roles": {address: label}, "affiliation"}`` entry per credit, in
            the order of :meth:`get_contributions`.
        """
        return [
            {
                "contributor": credit.contributor,
                "roles": {
                    role.uri: role.display_label() for role in credit.roles.all()
                },
                "affiliation": credit.affiliation,
            }
            for credit in self.get_contributions()
        ]

    def get_people(self, entries=None) -> dict[str, Any]:
        """Work out what the People panel shows: names with roles first, then faces.

        Args:
            entries: The record's credits, when the caller already has them. Defaults to
                :meth:`get_credits`.

        Returns:
            ``named``: the first ``people_named`` credits, each with its ``contributor``, its
            first two ``roles``, how many ``more_roles`` it holds and its ``affiliation``.
            ``faces``: the next ``people_faces`` contributors. ``more``: how many are left after
            those. ``total``: everyone credited.
        """
        if entries is None:
            entries = self.get_credits()
        named = [
            {
                "contributor": entry["contributor"],
                "roles": [
                    sentence_case(label) for label in list(entry["roles"].values())[:2]
                ],
                "more_roles": max(len(entry["roles"]) - 2, 0),
                "affiliation": entry["affiliation"],
            }
            for entry in entries[: self.people_named]
        ]
        last_face = self.people_named + self.people_faces
        return {
            "named": named,
            "faces": [
                entry["contributor"] for entry in entries[self.people_named : last_face]
            ],
            "more": max(len(entries) - last_face, 0),
            "total": len(entries),
        }

    def get_identifiers(self) -> list[dict[str, Any]]:
        """List the record's identifiers for the fact sheet.

        A DOI or an IGSN links to doi.org, since an IGSN is a DataCite DOI since 2023. A legacy
        IGSN handle, which does not start with ``10.``, does not resolve there and stays unlinked.

        Returns:
            One ``{"type", "value", "link"}`` entry per identifier, ``type`` being the identifier
            type's concept. ``link`` is ``None`` for any other type.
        """
        return [
            {
                "type": identifier.type,
                "value": identifier.value,
                "link": f"https://doi.org/{identifier.value}"
                if identifier.type_id in self.resolvable_identifier_types
                and str(identifier.value).startswith("10.")
                else None,
            }
            for identifier in self.base_object.identifiers.select_related("type")
        ]

    @staticmethod
    def get_primary_identifier(identifiers) -> dict[str, Any] | None:
        """Pick the identifier a reader looks for first: the first one that resolves.

        Args:
            identifiers: The record's identifiers, from :meth:`get_identifiers`.

        Returns:
            The first identifier with a ``link``, or ``None`` when none resolves.
        """
        return next((i for i in identifiers if i["link"]), None)

    def get_publisher(self) -> str:
        """Name the publisher a citation gives: the site's name.

        Returns:
            The current site's name, or an empty string when the site has none.
        """
        return getattr(getattr(self.request, "site", None), "name", "") or ""

    @staticmethod
    def format_cited_names(names) -> str:
        """Write cited names as a citation lists them, like :func:`format_authors`.

        Args:
            names: The :class:`~fairdm.core.citation.CitedName` values, in order.

        Returns:
            "Keller, A., Oliveira, T. & Brandt, L.", or an empty string for no names.
        """
        written = [
            f"{name.family}, {name.given[0]}."
            if name.family and name.given
            else name.family or name.literal
            for name in names
        ]
        if len(written) > 1:
            return ", ".join(written[:-1]) + " & " + written[-1]
        return written[0] if written else ""

    def get_citation(self, *, authors, year, title, link, publisher=None) -> str:
        """Write the citation in DataCite's form: Creators (Year). Title. Publisher. Identifier.

        Args:
            authors: The creators to name, as contributors or as cited names.
            year: The year of publication.
            title: The record's title.
            link: Its DOI link, or the address of the page. ``None`` when it has none.
            publisher: The publisher to name. Defaults to :meth:`get_publisher`.

        Returns:
            The citation as plain text.
        """
        if publisher is None:
            publisher = self.get_publisher()
        if authors and all(isinstance(a, CitedName) for a in authors):
            names = self.format_cited_names(authors)
        else:
            names = format_authors(authors)
        year = gettext("n.d.") if year is None else year
        parts = [
            f"{names} ({year})." if names else f"({year}).",
            f"{title}.",
            f"{publisher}.",
            link,
        ]
        return " ".join(part for part in parts if part and part.strip(". "))

    def build_citation(
        self, *, authors, year, title, link, publisher=None, types=("misc", "GEN")
    ) -> Citation:
        """Gather the parts of the record's citation into the value the files are written from.

        Args:
            authors: The creators, as contributors or as cited names.
            year: The year of publication.
            title: The title.
            link: The link the text ends with, or ``None``.
            publisher: The publisher. Defaults to :meth:`get_publisher`.
            types: The BibTeX and RIS types.

        Returns:
            The citation, keyed by the record's portal ID. Its DOI is set when ``link`` is a
            doi.org link.
        """
        prefix = "https://doi.org/"
        bibtex_type, ris_type = types
        return Citation(
            key=str(self.base_object.uuid),
            authors=[
                a if isinstance(a, CitedName) else CitedName.from_contributor(a)
                for a in authors
            ],
            year=year,
            title=title,
            publisher=self.get_publisher() if publisher is None else publisher,
            doi=link.removeprefix(prefix) if link and link.startswith(prefix) else None,
            url=link,
            bibtex_type=bibtex_type,
            ris_type=ris_type,
        )

    def get_citation_formats(self, citation, text) -> list[dict[str, Any]]:
        """List the ways to take the citation, for the Cite panel and the files.

        Args:
            citation: The :class:`~fairdm.core.citation.Citation`.
            text: The citation as text.

        Returns:
            One ``{"key", "label", "value", "url", "download"}`` entry per format, in the
            order of ``FORMATS``. ``url`` is the format's address beside the record's page, or
            ``None`` where the portal's plugin does not mount :class:`CitationFile`.
        """
        values = {
            "text": text,
            "bibtex": citation.to_bibtex(),
            "ris": citation.to_ris(),
        }
        return [
            {
                "key": f.key,
                "label": f.label,
                "value": values[f.key],
                "url": self.get_citation_address(f.key),
                "download": f.downloadable,
            }
            for f in FORMATS
        ]

    def get_citation_address(self, key) -> str | None:
        """Give the address of one format of the record's citation.

        Args:
            key: The format's key, one of ``FORMATS``.

        Returns:
            The address, or ``None`` when the portal's plugin does not mount
            :class:`CitationFile`.
        """
        try:
            return plugin_reverse(self.base_object, "overview-citation", format=key)
        except NoReverseMatch:
            return None

    def get_cited_details(self, citation, text) -> dict[str, Any]:
        """Give the two keys every record's citation card adds to its text.

        Args:
            citation: The :class:`~fairdm.core.citation.Citation`.
            text: The citation as text.

        Returns:
            ``work``, the citation, and ``formats``, from :meth:`get_citation_formats`.
        """
        return {
            "work": citation,
            "formats": self.get_citation_formats(citation, text),
        }

    def get_timeline(self, steps, dates, descriptions, entries) -> list[dict[str, Any]]:
        """Join the three ways the vocabularies describe a step in a record's life.

        A step combines a date type, a contributor role and a description type. Dated steps come
        first in date order, undated ones after them in the order given. A date recorded only to
        the year or the month is shown as recorded, never padded out to a day.

        Args:
            steps: ``[(date_type, role, description_type, label)]``, each type and role
                given by its address.
            dates: The record's dates, keyed by the address of their type.
            descriptions: The record's descriptions, keyed by the address of their type.
            entries: The record's credits, from :meth:`get_credits`.

        Returns:
            One ``{"label", "date", "day", "people", "note"}`` entry per step with anything to
            show.
        """
        result = []
        for date_type, role, description_type, label in steps:
            when = dates.get(date_type) if date_type else None
            who = self.get_contributors_with_role(entries, role) if role else []
            note = descriptions.get(description_type) if description_type else None
            if when or who or note:
                result.append(
                    {
                        "label": label,
                        "date": when,
                        "day": when.start
                        if when is not None and when.precision is Precision.DAY
                        else None,
                        "people": who,
                        "note": note,
                    }
                )
        dated = sorted((s for s in result if s["date"]), key=lambda s: str(s["date"]))
        return dated + [s for s in result if not s["date"]]

    def get_license_entry(self, licence, note=None) -> dict[str, Any]:
        """Write the fact sheet's licence entry: the licence linked to its text, or a warning.

        Args:
            licence: The licence, or ``None`` when none is chosen.
            note: A line to show under the licence.

        Returns:
            An entry for :class:`c-overview.sheet`.
        """
        if licence is None:
            return {
                "label": gettext("Licence"),
                "icon": "license",
                "text": gettext("None chosen yet"),
                "warning": True,
                "note": gettext(
                    "Nobody can safely reuse this data until a licence is chosen."
                ),
            }
        return {
            "label": gettext("Licence"),
            "icon": "license",
            "text": licence.name,
            "url": licence.canonical_url or "",
            "note": note,
        }

    def get_type_mix(self, samples, measurements) -> dict[str, Any] | None:
        """Count the records by type for the bars in each type's colour.

        Args:
            samples: The samples to count.
            measurements: The measurements to count.

        Returns:
            ``samples`` and ``measurements``, each ``[(plural type name, count)]`` largest first,
            and ``max``, the largest count, which every bar is drawn against. ``None`` when there
            is nothing to count.
        """
        by_sample = self._type_counts(samples)
        by_measurement = self._type_counts(measurements)
        counts = [n for _label, n in by_sample + by_measurement]
        if not counts:
            return None
        return {
            "samples": by_sample,
            "measurements": by_measurement,
            "max": max(counts),
        }

    def get_sample_points(self, samples) -> dict[str, Any]:
        """Give the located samples as GeoJSON for the map to draw.

        The rows are read with ``values()``, never as model instances, so the answer
        costs one query however many samples there are.

        Args:
            samples: The samples to draw. Those without a location are left out.

        Returns:
            A ``FeatureCollection`` with one ``Point`` feature per located sample,
            ordered by name. Each feature's properties are ``name``, ``type`` (the
            sample type's name, empty when the type's model no longer exists),
            ``dataset`` (the dataset's name) and ``url`` (the sample's page).
        """
        rows = (
            samples.filter(location__isnull=False)
            .order_by("name", "uuid")
            .values("uuid", "name", "location", "polymorphic_ctype", "dataset__name")
        )
        labels: dict[int, str] = {}
        features = []
        for row in rows:
            ctype = row["polymorphic_ctype"]
            if ctype not in labels:
                model = ContentType.objects.get_for_id(ctype).model_class()
                labels[ctype] = (
                    sentence_case(model._meta.verbose_name) if model is not None else ""
                )
            point = row["location"]
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [round(point.x, 5), round(point.y, 5)],
                    },
                    "properties": {
                        "name": row["name"],
                        "type": labels[ctype],
                        "dataset": row["dataset__name"],
                        "url": reverse("sample:overview", kwargs={"uuid": row["uuid"]}),
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}

    def get_sample_map(
        self, samples, coverage, points_url, *, count_datasets=False
    ) -> dict[str, Any] | None:
        """Work out what the map panel shows: how many samples are located and where.

        One aggregate query counts the samples, no rows are read.

        Args:
            samples: The samples the page counts.
            coverage: The smallest box holding their locations, or ``None``.
            points_url: The address that answers the located samples as GeoJSON.
            count_datasets: Whether to count the datasets the located samples come from.

        Returns:
            ``located``, ``missing`` (the samples without a location), ``bounds`` (the
            coverage as ``[west, south, east, north]``, with ``east`` carried past 180
            when the box crosses the 180th meridian so MapLibre fits the narrow box),
            ``area`` (the coverage as text) and ``points_url``, plus ``datasets`` when
            asked. With no located sample, ``bounds`` and ``area`` are ``None``.
            ``None`` when ``samples`` is empty.
        """
        located_only = Q(location__isnull=False)
        counts = samples.aggregate(
            total=Count("pk"),
            located=Count("pk", filter=located_only),
            datasets=Count("dataset", distinct=True, filter=located_only),
        )
        if not counts["total"]:
            return None
        located = counts["located"]
        result = {
            "located": located,
            "missing": counts["total"] - located,
            "bounds": None,
            "area": None,
            "points_url": points_url,
        }
        if count_datasets:
            result["datasets"] = counts["datasets"]
        if located and coverage is not None:
            west, south, east, north = coverage
            result["bounds"] = [west, south, east + 360 if west > east else east, north]
            result["area"] = describe_coverage(coverage)
        return result

    def get_growth_chart(self, samples, measurements) -> dict[str, Any] | None:
        """Draw the cumulative samples and measurements by month, two series on one count axis.

        Args:
            samples: The samples to count.
            measurements: The measurements to count.

        Returns:
            The chart and its text alternative, or ``None`` when the records span fewer than two
            months.
        """
        by_sample, by_measurement = self._monthly(samples), self._monthly(measurements)
        months = sorted(set(by_sample) | set(by_measurement))
        if len(months) < 2:
            return None
        # Fill the gaps so a quiet month reads as flat, not as a missing point.
        first, last = months[0], months[-1]
        months, cursor = [], first
        while cursor <= last:
            months.append(cursor)
            cursor = date(cursor.year + cursor.month // 12, cursor.month % 12 + 1, 1)

        def cumulative(series):
            total, values = 0, []
            for month in months:
                total += series.get(month, 0)
                values.append(total)
            return values

        samples_line, measurements_line = (
            cumulative(by_sample),
            cumulative(by_measurement),
        )
        line_style = opts.LineStyleOpts(width=2)
        chart = (
            Line()
            .add_xaxis([date_format(month, "YEAR_MONTH_FORMAT") for month in months])
            .add_yaxis(
                gettext("Samples"),
                samples_line,
                is_symbol_show=False,
                linestyle_opts=line_style,
                label_opts=opts.LabelOpts(is_show=False),
            )
            .add_yaxis(
                gettext("Measurements"),
                measurements_line,
                is_symbol_show=False,
                linestyle_opts=line_style,
                label_opts=opts.LabelOpts(is_show=False),
            )
            .set_global_opts(
                legend_opts=opts.LegendOpts(pos_left="left", pos_top="top"),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                xaxis_opts=opts.AxisOpts(boundary_gap=False),
            )
        )
        chart.options["grid"] = {
            "left": 8,
            "right": 16,
            "top": 40,
            "bottom": 8,
            "containLabel": True,
        }
        return {
            "chart": chart,
            "description": gettext(
                "From %(first)s to %(last)s it grew to %(samples)s samples and "
                "%(measurements)s measurements."
            )
            % {
                "first": date_format(months[0], "YEAR_MONTH_FORMAT"),
                "last": date_format(months[-1], "YEAR_MONTH_FORMAT"),
                "samples": samples_line[-1],
                "measurements": measurements_line[-1],
            },
        }

    @staticmethod
    def _type_counts(queryset) -> list[tuple[str, int]]:
        """Count a queryset's records by type, largest first.

        A type the registry does not hold, and a content type whose model no longer exists, are
        left out.

        Args:
            queryset: The records to count.

        Returns:
            One ``(plural type name, count)`` pair per type.
        """
        from fairdm.registry import registry

        rows = (
            queryset.values("polymorphic_ctype").annotate(n=Count("pk")).order_by("-n")
        )
        result = []
        for row in rows:
            model = ContentType.objects.get_for_id(
                row["polymorphic_ctype"]
            ).model_class()
            if model is None or not registry.is_registered(model):
                continue
            result.append((sentence_case(model._meta.verbose_name_plural), row["n"]))
        return result

    @staticmethod
    def _monthly(queryset) -> "OrderedDict[date, int]":
        """Count a queryset's records by the month they were added.

        Args:
            queryset: The records to count.

        Returns:
            The count for each month that has records, oldest month first.
        """
        return OrderedDict(
            (
                row["month"].date() if hasattr(row["month"], "date") else row["month"],
                row["n"],
            )
            for row in queryset.annotate(month=TruncMonth("added"))
            .values("month")
            .annotate(n=Count("pk"))
            .order_by("month")
        )


class SamplePoints(Plugin):
    """Answer a record's located samples as GeoJSON, for its overview page's map.

    It decides nothing itself. The owning overview plugin says who may open the record
    and which of its samples the viewer sees, so this address answers exactly as the
    record's page does: a private record is "not found", and the points are the samples
    the page counts.

    The owner is built with this mount's model. A plugin built without it resolves no
    record, and a plugin that resolves none lets everyone in.

    Attributes:
        owner: The overview plugin that owns this address, set when access is decided.
    """

    name = "sample-points"
    url_path = "sample-points"
    owner = None

    def has_permission(self) -> bool:
        """Ask the owning overview plugin whether the viewer may open its record."""
        self.owner = self.plugin_class(
            registered_model=self.registered_model, menu=self.menu
        )
        self.owner.setup(self.request, *self.args, **self.kwargs)
        return self.owner.has_permission()

    def handle_no_permission(self):
        """Refuse as the overview does, so a private record answers "not found"."""
        return self.owner.handle_no_permission()

    def get(self, request, *args, **kwargs):
        """Give the samples the page counts that have a location, as GeoJSON."""
        return JsonResponse(self.owner.get_sample_points(self.owner.get_map_samples()))


def _visible_through(base_model):
    """Build a plugin ``check`` that asks the base model's manager whether the user may see a record.

    The subtype's own manager is never asked: a portal's type may declare a plain ``QuerySet``
    manager with no ``visible_to``.

    Args:
        base_model: The core model the records share, such as ``Sample``.

    Returns:
        A ``check(request, obj)`` predicate.
    """

    def check(request, obj):
        if obj is None:
            return True
        return base_model.objects.visible_to(request.user).filter(pk=obj.pk).exists()

    return check


class TypedOverviewPlugin(RecordOverviewPlugin):
    """The overview of a record portals subclass: a sample or a measurement.

    Two things differ from a project or dataset overview.

    **The template follows the record's type.** For each concrete class from the record's own
    type up to ``base_model``, it looks for ``<app_label>/<model_name>_overview.html``, then falls
    back to ``fallback_template``. A type gets its own page by providing that template, extending
    its record's template and filling the ``overview.*`` blocks it wants. A subtype inherits its
    parent type's page until it provides its own.

    **The record follows its dataset.** It opens for everyone once its own dataset is public and
    published, and otherwise only for people who hold a level on the record, or on its dataset or that dataset's
    project (``visible_to``). Anyone else gets a
    404, so the address never confirms the record exists. ``PrivateRecordNotFoundMixin`` can't be
    reused here: it reads ``obj.open_to_everyone``, which samples and measurements don't have.
    """

    base_model = None
    fallback_template = None

    @staticmethod
    def check(request, obj):
        # Fails closed: a subclass that names its ``base_model`` gets the real check from
        # ``__init_subclass__``. It is a staticmethod, not a classmethod, because registration
        # refuses a classmethod `check` (fairdm.contrib.plugins.access.check_is_valid).
        return obj is None

    def __init_subclass__(cls, **kwargs):
        """Give a subclass that names its ``base_model`` a visibility check that reads through it."""
        super().__init_subclass__(**kwargs)
        if cls.base_model is not None:
            cls.check = staticmethod(_visible_through(cls.base_model))

    def handle_no_permission(self):
        """Answer a viewer who may not open the record exactly as for a record that does not exist."""
        from django.http import Http404

        raise Http404(
            _("No %s matches the given query.") % self.base_model._meta.object_name
        )

    def get_template_names(self):
        """Offer the record's own type templates, most specific first, then the fallback."""
        names = []
        for cls in type(self.base_object).__mro__:
            if cls is self.base_model:
                break
            if (
                isinstance(cls, type)
                and issubclass(cls, self.base_model)
                and not cls._meta.abstract
            ):
                names.append(
                    f"{cls._meta.app_label}/{cls._meta.model_name}_overview.html"
                )
        return [*names, self.fallback_template]

    def get_type_info(self) -> dict[str, Any] | None:
        """Read what the registry says about the record's type and by whose rules it is recorded.

        Returns:
            The description, the maintaining authority, the protocol citation and the keywords,
            or ``None`` when the registry holds nothing to say.
        """
        from fairdm.registry import registry

        model = type(self.base_object)
        if not registry.is_registered(model):
            return None
        config = registry.get_for_model(model)
        metadata = config.metadata
        citation = metadata.citation
        if (
            citation
            and citation.doi
            and not citation.doi.startswith(("http://", "https://"))
        ):
            citation = replace(citation, doi=f"https://doi.org/{citation.doi}")
        info = {
            "description": metadata.description or config.description,
            "authority": metadata.authority,
            "citation": citation,
            "keywords": metadata.keywords,
        }
        return info if any(info.values()) else None

"""Reusable overview plugins for the core record pages."""

from collections import OrderedDict
from dataclasses import replace
from datetime import date
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils.formats import date_format
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from partial_dates import Precision
from pyecharts import options as opts
from pyecharts.charts import Line

from fairdm.contrib.contributors.models import Contribution, Contributor
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins import reverse as plugin_reverse
from fairdm.core.overview import format_authors, sentence_case
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

    def get_citation(self, *, authors, year, title, link) -> str:
        """Write the citation in DataCite's form: Creators (Year). Title. Publisher. Identifier.

        Args:
            authors: The creators to name.
            year: The year of publication.
            title: The record's title.
            link: Its DOI link, or the address of the page.

        Returns:
            The citation as plain text.
        """
        names = format_authors(authors)
        publisher = getattr(getattr(self.request, "site", None), "name", "") or ""
        parts = [
            f"{names} ({year})." if names else f"({year}).",
            f"{title}.",
            f"{publisher}.",
            link,
        ]
        return " ".join(part for part in parts if part.strip(". "))

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

"""Registered pages for a project: overview, delete, datasets and export."""

from collections import Counter

from django.db.models import Count
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext, ngettext
from django.utils.translation import gettext_lazy as _
from mvp.views.detail import CRUDDirectoryMixin

from fairdm import plugins
from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import has_perm
from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import (
    as_date,
    format_partial_date,
    json_ld,
    safe_reverse,
)
from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.core.sample.models import Sample
from fairdm.utils.choices import Visibility
from fairdm.views import FairDMDeleteView, FairDMTemplateView

from ..dataset.views import DatasetListView
from .models import Project, ProjectDescription, PublicDatasetsProtect
from .transforms import to_json_ld


def project_is_visible(request, obj):
    """Return whether the request's user may view a project.

    A public project is always visible, a private one only with ``project.view_project``.
    A registered page resolves its record past filtered managers and relies on the page to gate
    itself, so without this check a private project would be readable by anyone holding its
    address. It is set as ``Overview.check``.

    An additional view does not inherit this rule (the owner is read from ``plugin_class``, which
    exists only on the view instance, while ``has_permission`` passes the class). ``Delete``
    therefore states a visibility rule of its own (#284).

    Args:
        request: The current request.
        obj: The project, or ``None`` when no record has been resolved.

    Returns:
        True when the page may be shown.
    """
    if obj is None:
        return True
    if obj.visibility == Visibility.PUBLIC:
        return True
    return has_perm(request, "project.view_project", obj)


def visible_to_holder_of(permission):
    """Build a page check that also admits a holder of one record-level permission.

    Like :func:`project_is_visible`, except a private project also stays visible to a user
    holding ``permission`` on it. A level includes the ones below it, so anyone who holds the
    page's own permission on the project can also view it, and this check says so directly.

    A user holding ``permission`` only at the model level, granted to them directly or through
    a group the portal made up, still finds no grant here and is refused. With an object,
    ``has_perm`` answers from the contribution level, and from membership of one of the four
    shipped portal roles, which confers the object-level answer.

    Args:
        permission: The permission to accept at record level.

    Returns:
        A ``check(request, obj)`` callable.
    """

    def check(request, obj):
        if project_is_visible(request, obj):
            return True
        if obj is None:
            return False
        return request.user.has_perm(permission, obj)

    return check


class Delete(
    PrivateRecordNotFoundMixin, RecordOwnPageBackFallbackMixin, Plugin, FairDMDeleteView
):
    """Delete the project, confirmed by typing its name.

    An additional view of :class:`Overview`.
    """

    url_path = "delete"
    permission = "project.delete_project"
    check = staticmethod(visible_to_holder_of("project.delete_project"))
    page_title = _("Delete project")
    model = Project
    require_confirmation = True
    success_url = reverse_lazy("project-list")

    def get_confirmation_value(self):
        """Ask the user to type the project's name."""
        return self.base_object.name

    def get_context_data(self, **kwargs):
        """Report the project's public datasets as the objects protecting it from deletion."""
        # Set after `super()`, because passing these as keyword arguments would be overwritten.
        context = super().get_context_data(**kwargs)
        public_datasets = self.base_object.datasets.filter(visibility=Visibility.PUBLIC)
        if public_datasets.exists():
            context["is_protected"] = True
            context["protected_objects"] = list(public_datasets)
            # `cotton/form/index.html` renders any `form` in context, which would duplicate the
            # confirmation input the `is_protected` branch already withholds.
            context["form"] = None
        return context

    def form_valid(self, form):
        """Re-render the page when a public dataset blocks the deletion."""
        try:
            return super().form_valid(form)
        except PublicDatasetsProtect:
            return self.render_to_response(
                self.get_context_data(object=self.base_object)
            )


@plugins.register(Project, label=_("Overview"), icon="view", order=0)
class Overview(PrivateRecordNotFoundMixin, CRUDDirectoryMixin, RecordOverviewPlugin):
    """The project's own page and the root of its collection.

    Its ``extra_views`` are :class:`Delete`, and ``directory`` names the action link it needs.
    The editing pages are the shared ones in :mod:`fairdm.core.editing`, reached from the Manage
    menu.

    ``PrivateRecordNotFoundMixin`` makes a private project answer a stranger with a 404, since a
    403 or a sign-in redirect would confirm the record exists.

    The page is a landing page, read by someone deciding whether the data is usable to them,
    someone who has to cite the project and the team keeping the record complete. Everything on it
    is derived from the project's own records. A visitor's counts are taken over the project's
    public datasets only, and the samples and measurements beneath them; a member of the team sees
    everything, with the private share called out.

    Attributes:
        dataset_preview: How many datasets the page lists before it hands over to the Datasets
            page.
        lead_roles: The roles that name the people a visitor should see first, in this order.
    """

    url_path = None
    model = Project
    check = staticmethod(project_is_visible)
    template_name = "project/project_detail.html"
    extra_views = [Delete]

    directory = ["delete"]
    crud_views = {"delete": "project:overview-delete"}

    dataset_preview = 5
    lead_roles = ["ProjectLeader", "ProjectManager"]

    def show_delete_action(self, user):
        """Show the delete action to a user who may open the delete page."""
        return has_perm(self.request, Delete.permission, self.base_object)

    def get_context_data(self, **kwargs):
        """Add the project and everything the overview page draws.

        The datasets counted are the project's public ones for a visitor and every one for the
        team, and the samples and measurements are those beneath them.
        """
        context = super().get_context_data(**kwargs)
        project = self.base_object
        can_manage = has_perm(self.request, "project.change_project", project)

        datasets = Dataset.all_objects.filter(project=project)
        if not can_manage:
            datasets = datasets.filter(visibility=Visibility.PUBLIC)
        dataset_ids = list(datasets.values_list("pk", flat=True))
        samples = Sample.objects.filter(dataset_id__in=dataset_ids)
        measurements = Measurement.objects.filter(dataset_id__in=dataset_ids)

        page = {
            "can_manage": can_manage,
            "descriptions": self.get_descriptions(),
            "timeline": self.get_progress(),
            "team": self.get_team(),
            "funding": project.funding or [],
            "counts": self.get_counts(datasets, samples, measurements, can_manage),
            "datasets_preview": self.get_datasets_preview(datasets),
            "licenses": self.get_licenses(datasets),
            "composition_chart": self.get_composition_chart(samples, measurements),
            "growth_chart": self.get_growth_chart(samples, measurements),
            "citation": self.get_citation_details(),
            "json_ld": json_ld(to_json_ld(project)),
            "api_url": safe_reverse(
                f"api:{project._meta.model_name}-detail", uuid=project.uuid
            ),
            "urls": {
                "datasets": safe_reverse("project:dataset-list", uuid=project.uuid),
                "contributors": safe_reverse(
                    "project:contribution-list", uuid=project.uuid
                ),
                "update": safe_reverse("project:edit", uuid=project.uuid),
                "descriptions": safe_reverse("project:descriptions", uuid=project.uuid),
                "delete": safe_reverse("project:overview-delete", uuid=project.uuid),
                "add_dataset": safe_reverse("dataset-create"),
            },
        }
        if can_manage:
            page["readiness"] = self.get_readiness(page)
        page.update(self.get_shared_context(page))

        context["project"] = project
        context.update(page)
        return context

    def get_shared_context(self, page):
        """Provide the keys every overview page has, which the shared skeleton and cards read.

        Args:
            page: The page context gathered so far.

        Returns:
            The record, its icon, the header's people, the People, Identifiers and citation cards,
            the Details rows and, for the team, the readiness checklist.
        """
        leads = [entry["contributor"] for entry in page["team"]["leads"]]
        result = {
            "record": self.base_object,
            "overview_icon": "project",
            "has_charts": bool(page["composition_chart"] or page["growth_chart"]),
            "citation": {
                "title": gettext("Citation"),
                "text": page["citation"]["text"],
            },
            "identifiers": self.get_identifiers(),
            "people": self.get_people(),
            "people_url": page["urls"]["contributors"],
            "header_people": leads,
            "header_people_label": gettext("Project leaders"),
            "details": self.get_details(page["licenses"]),
        }
        if not page["citation"]["has_doi"]:
            result["citation"]["note"] = gettext(
                "This project has no DOI, so the citation points at this page."
            )
        if "readiness" in page:
            readiness = page["readiness"]
            readiness["title"] = gettext("Metadata readiness")
            readiness["summary"] = gettext("%(done)s of %(total)s in place") % readiness
            readiness["about"] = gettext(
                "What search engines, data repositories and other researchers look for before "
                "they trust and reuse a project."
            )
            result["readiness"] = readiness
        return result

    def get_descriptions(self):
        """List the project's descriptions in the vocabulary's own order, abstract first."""
        by_type = {d.type: d.value for d in self.base_object.descriptions.all()}
        labels = dict(ProjectDescription.VOCABULARY.choices)
        return [
            {"type": t, "label": labels.get(t, t), "value": by_type[t]}
            for t in ProjectDescription.VOCABULARY.values
            if by_type.get(t)
        ]

    def get_progress(self):
        """Work out the project's start, its end and how far through it today is, in whole years.

        Returns:
            The start and end as recorded and as dates, the percentage elapsed, the year the
            project is in and a label saying where it stands.
        """
        dates = {d.type: d.value for d in self.base_object.dates.all()}
        start, end = dates.get("Start"), dates.get("End")
        start_date, end_date = as_date(start), as_date(end)
        result = {
            "start": start,
            "end": end,
            "start_date": start_date,
            "end_date": end_date,
            "start_text": format_partial_date(start),
            "end_text": format_partial_date(end),
            "percent": None,
            "year": None,
            "years": None,
        }
        if start_date and end_date and end_date > start_date:
            today = timezone.localdate()
            total = (end_date - start_date).days
            elapsed = min(max((today - start_date).days, 0), total)
            result["percent"] = round(100 * elapsed / total)
            result["years"] = max(round(total / 365.25), 1)
            result["year"] = min(elapsed // 365 + 1, result["years"])
            result["finished"] = today > end_date
            result["not_started"] = today < start_date
            if result["finished"]:
                result["label"] = gettext("Finished")
            elif result["not_started"]:
                result["label"] = gettext("Not started yet")
            else:
                result["label"] = gettext("Year %(year)s of %(years)s") % result
        return result

    def get_team(self):
        """Name the leads and the contact person, and count everyone else.

        Returns:
            The leads, the contact person, the other contributors, the counts of people and
            organisations, and who a would-be collaborator writes to: the contact person, else the
            first lead.
        """
        contributions = self.get_contributions()
        ranked_leads, contact, others = [], None, []
        for contribution in contributions:
            roles = self.get_role_names(contribution)
            entry = {
                "contributor": contribution.contributor,
                "roles": [
                    r.label for r in contribution.roles.all() if r.name != "Creator"
                ],
            }
            if "ContactPerson" in roles and contact is None:
                contact = entry
            if roles & set(self.lead_roles):
                ranked_leads.append((0 if "ProjectLeader" in roles else 1, entry))
            elif "ContactPerson" not in roles:
                others.append(entry)
        leads = [entry for _rank, entry in sorted(ranked_leads, key=lambda t: t[0])]
        return {
            "leads": leads,
            "contact": contact if contact and contact not in leads else None,
            "contact_is_lead": bool(contact and contact in leads),
            "others": others,
            "total": len(contributions),
            "people": sum(1 for c in contributions if c.is_person()),
            "organizations": sum(1 for c in contributions if not c.is_person()),
            "has_contact": contact is not None,
            "reach": (contact or (leads[0] if leads else None) or {}).get(
                "contributor"
            ),
        }

    def get_counts(self, datasets, samples, measurements, can_manage):
        """Count the figures in the strip and describe each in a line.

        Args:
            datasets: The datasets the viewer may see.
            samples: The samples beneath them.
            measurements: The measurements beneath them.
            can_manage: Whether the viewer is on the project's team.

        Returns:
            The three counts, each with its description.
        """
        total = datasets.count()
        public = datasets.filter(visibility=Visibility.PUBLIC).count()
        published = datasets.filter(published=True).count()
        sample_types = samples.values("polymorphic_ctype").distinct().count()
        measurement_types = measurements.values("polymorphic_ctype").distinct().count()

        if can_manage and total != public:
            dataset_desc = gettext("%(public)s public · %(private)s private") % {
                "public": public,
                "private": total - public,
            }
        elif total:
            dataset_desc = ngettext("%(n)s published", "%(n)s published", published) % {
                "n": published
            }
        else:
            dataset_desc = gettext("None yet")
        return {
            "datasets": total,
            "datasets_desc": dataset_desc,
            "samples": samples.count(),
            "samples_desc": ngettext("%(n)s type", "%(n)s types", sample_types)
            % {"n": sample_types}
            if sample_types
            else gettext("None yet"),
            "measurements": measurements.count(),
            "measurements_desc": ngettext(
                "%(n)s type", "%(n)s types", measurement_types
            )
            % {"n": measurement_types}
            if measurement_types
            else gettext("None yet"),
        }

    def get_datasets_preview(self, datasets):
        """List the most recently updated datasets with their record counts.

        Args:
            datasets: The datasets the viewer may see.

        Returns:
            The first ``dataset_preview`` rows and how many more there are.
        """
        rows = (
            datasets.select_related("license")
            .annotate(
                n_samples=Count("samples", distinct=True),
                n_measurements=Count("measurements", distinct=True),
            )
            .order_by("-modified")
        )
        return {
            "rows": list(rows[: self.dataset_preview]),
            "more": max(rows.count() - self.dataset_preview, 0),
        }

    def get_licenses(self, datasets):
        """Summarise the licences the project's public datasets carry.

        Args:
            datasets: The datasets the viewer may see.

        Returns:
            The licences with how many datasets carry each, most common first, and how many public
            datasets carry none.
        """
        counter = Counter(
            datasets.filter(visibility=Visibility.PUBLIC).values_list(
                "license__name", flat=True
            )
        )
        unlicensed = counter.pop(None, 0)
        return {"items": counter.most_common(), "unlicensed": unlicensed}

    def get_citation_details(self):
        """Write the project's citation: Creators (Year). Title. Publisher. Identifier.

        Returns:
            The citation text, the link it ends with, whether that link is a DOI and how many
            creators it names.
        """
        project = self.base_object
        creators = [
            c.contributor
            for c in self.get_contributions()
            if "Creator" in self.get_role_names(c)
        ]
        start = {d.type: d.value for d in project.dates.all()}.get("Start")
        year = as_date(start).year if as_date(start) else project.added.year
        doi = next(
            (i.value for i in project.identifiers.all() if i.type == "DOI"), None
        )
        link = (
            f"https://doi.org/{doi}"
            if doi
            else self.request.build_absolute_uri(project.get_absolute_url())
        )
        return {
            "text": self.get_citation(
                authors=creators, year=year, title=project.name, link=link
            ),
            "link": link,
            "has_doi": bool(doi),
            "creators": len(creators),
        }

    def get_readiness(self, page):
        """List the metadata a harvester or a reuser looks for, and whether the project has it.

        Each item comes from DataCite's required and recommended properties or from what the FAIR
        principles ask of a record. Items with nowhere to fix them yet carry no link.

        Args:
            page: The page context gathered so far.

        Returns:
            The items, how many are done, the total and the percentage.
        """
        project = self.base_object
        urls = page["urls"]
        descriptions = {d["type"] for d in page["descriptions"]}
        team = page["team"]
        counts = page["counts"]
        items = [
            (
                gettext("An abstract describes the project"),
                "Abstract" in descriptions,
                urls["descriptions"],
            ),
            (
                gettext("At least one creator is credited"),
                page["citation"]["creators"] > 0,
                urls["contributors"],
            ),
            (
                gettext("Someone is named as the contact"),
                team["has_contact"],
                urls["contributors"],
            ),
            (
                gettext("A start date is recorded"),
                page["timeline"]["start"] is not None,
                urls["update"],
            ),
            (gettext("Keywords make it findable"), project.keywords.exists(), None),
            (gettext("Funding is acknowledged"), bool(project.funding), None),
            (
                gettext("It has a persistent identifier (DOI)"),
                page["citation"]["has_doi"],
                urls["update"],
            ),
            (
                gettext("At least one dataset is public"),
                Dataset.all_objects.filter(
                    project=project, visibility=Visibility.PUBLIC
                ).exists(),
                urls["datasets"],
            ),
            (
                gettext("Every public dataset has a licence"),
                counts["datasets"] > 0
                and page["licenses"]["unlicensed"] == 0
                and bool(page["licenses"]["items"]),
                urls["datasets"],
            ),
            (
                gettext("The project is public"),
                project.visibility == Visibility.PUBLIC,
                urls["update"],
            ),
        ]
        done = sum(1 for _label, ok, _url in items if ok)
        return {
            "items": [
                {"label": label, "done": ok, "url": url} for label, ok, url in items
            ],
            "done": done,
            "total": len(items),
            "percent": round(100 * done / len(items)),
        }

    def get_details(self, licenses):
        """List the rows of the Details card: organisation, status, licences and dates.

        Args:
            licenses: The licence summary from :meth:`get_licenses`.

        Returns:
            The rows, for :class:`c-card.details`.
        """
        project = self.base_object
        rows = []
        if project.owner:
            rows.append(
                {
                    "label": gettext("Organisation"),
                    "icon": "organization",
                    "record": project.owner,
                }
            )
        rows.append(
            {
                "label": gettext("Status"),
                "icon": "info",
                "badge": project.get_status_display(),
                "badge_variant": project.status_badge_variant,
            }
        )
        if licenses["items"]:
            text = ", ".join(f"{name} ({n})" for name, n in licenses["items"])
        else:
            text = gettext("No public datasets yet")
        row = {"label": gettext("Licences"), "icon": "license", "text": text}
        if licenses["unlicensed"]:
            row["note"] = ngettext(
                "%(n)s public dataset has no licence and can't be reused safely.",
                "%(n)s public datasets have no licence and can't be reused safely.",
                licenses["unlicensed"],
            ) % {"n": licenses["unlicensed"]}
        rows.append(row)
        rows.append(
            {"label": gettext("Added"), "icon": "calendar", "date": project.added}
        )
        rows.append(
            {
                "label": gettext("Last updated"),
                "icon": "time",
                "date": project.modified,
            }
        )
        return rows


@plugins.register(Project, order=100)
class DatasetList(PrivateRecordNotFoundMixin, Plugin, DatasetListView):
    """List the datasets that belong to the project."""

    page_title = _("Datasets")
    check = staticmethod(project_is_visible)

    def get_queryset(self, *args, **kwargs):
        """Limit to the project's datasets."""
        return self.base_object.datasets.all()

    def get_lookup_kwargs(self) -> dict:
        """Return no lookup kwargs, as the queryset is already scoped to the project."""
        return {}


@plugins.register(Project, label=_("Export"), order=200)
class ProjectExportView(PrivateRecordNotFoundMixin, Plugin, FairDMTemplateView):
    """Page for exporting the project's data."""

    page_title = _("Export Project Data")
    check = staticmethod(project_is_visible)
    page_icon = "export"

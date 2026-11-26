"""Prototype: the Contributors page of a project, dataset, sample or measurement.

People in the main column, organizations beside them. Each row has one actions control that
opens a sheet. Adding, editing and reordering happen in sheets, and every change answers with
the whole page region drawn again, so both columns and their counts always agree.

This is prototype code on a branch that is never merged. See PROTOTYPE.md.
"""

import json

from controlled_vocabularies.models import Record
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from mvp.ordering import InvalidOrder, save_order

from fairdm import plugins
from fairdm.contrib.plugins import reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

from ..models import Contribution, Contributor, Organization, Person
from ..services.crediting import Crediting
from .shared import ContributionPage

__all__ = ["Contributors"]

SHEET_ID = "contrib-sheet"

UNCITED = "prototype_uncited"
"""Faked: where a person left out of the record's citation is noted, in their ``config``.

A contribution has no field for it, so the prototype keeps a list of the records each person is
credited on but not cited in. The rebuild needs a field on the contribution.
"""


LEADER = "project-leader"
MEMBER = "project-member"


def role_by_slug(slug):
    """The contributor role with this slug, or None."""
    return Record.objects.filter(uri=f"https://w3id.org/fairdm/vocabularies/contributor-roles/{slug}").first()


def first_name_of(person, new_name=None):
    """The first of a person's given names, or their family name when they have none."""
    given = person.first_name if person else (new_name or {}).get("first_name", "")
    family = person.last_name if person else (new_name or {}).get("last_name", "")
    return (given.split() or [family or (person.name if person else "")])[0]


def record_key(credit):
    """The key that names a contribution's record in the faked citation list."""
    return f"{credit.content_type_id}:{credit.object_id}"


def is_cited(credit):
    """Whether the person a contribution credits appears in the record's citation."""
    return record_key(credit) not in (credit.contributor.config or {}).get(UNCITED, [])


def set_cited(credit, cited):
    """Put the person a contribution credits in the record's citation, or leave them out."""
    contributor = credit.contributor
    config = dict(contributor.config or {})
    left_out = set(config.get(UNCITED, []))
    (left_out.discard if cited else left_out.add)(record_key(credit))
    config[UNCITED] = sorted(left_out)
    if config != (contributor.config or {}):
        contributor.config = config
        contributor.save(update_fields=["config"])


class ContributorsBase(ContributionPage):
    """What every view of the prototype page shares."""

    region_template = "contributors/page/region.html"

    @property
    def list_url(self):
        """The address of the Contributors page."""
        return reverse(self.base_object, "contributors")

    def record_url(self, name, **kwargs):
        """Reverse one of this page's views for the record."""
        return reverse(self.base_object, name, **kwargs) if kwargs else reverse(self.base_object, name)

    @property
    def can_change(self):
        """Whether the viewer may change the record's contributors."""
        return self.access.can_manage(self.request.user)

    def require_change(self):
        """Refuse anyone who may not change the contributors."""
        if not self.can_change:
            raise PermissionDenied

    # ------------------------------------------------------------------ reading

    def people(self):
        """The people on the record, in their order, with what each row shows."""
        credits = (
            Contribution.objects.for_entity(self.base_object)
            .people()
            .select_related("contributor", "affiliation")
            .prefetch_related("roles")
        )
        rows = []
        for credit in credits:
            person = credit.contributor.get_real_instance() if credit.contributor else None
            if person is None:
                continue
            rows.append(
                {
                    "credit": credit,
                    "person": person,
                    "roles": list(credit.roles.all()),
                    "cited": is_cited(credit),
                    "edit_url": self.record_url("contributors-edit", pk=credit.pk),
                    "remove_url": self.record_url("contributors-remove", pk=credit.pk),
                }
            )
        return rows

    def organizations(self, people):
        """Every organization on the record: listed with a role, or the affiliation of someone listed.

        Args:
            people: The rows from :meth:`people`, whose affiliations count.

        Returns:
            One row per organization, listed ones in their order first, then organizations that
            only reach the record through a person's affiliation, by name.
        """
        credited_from = {}
        for row in people:
            if row["credit"].affiliation_id:
                credited_from.setdefault(row["credit"].affiliation_id, []).append(row["person"])
        rows = []
        seen = set()
        listed = (
            Contribution.objects.for_entity(self.base_object)
            .organizations()
            .select_related("contributor")
            .prefetch_related("roles")
        )
        for credit in listed:
            if credit.contributor is None:
                continue
            organization = credit.contributor.get_real_instance()
            seen.add(organization.pk)
            rows.append(
                {
                    "credit": credit,
                    "organization": organization,
                    "roles": list(credit.roles.all()),
                    "people": credited_from.get(organization.pk, []),
                    "edit_url": self.record_url("contributors-edit", pk=credit.pk),
                    "remove_url": self.record_url("contributors-remove", pk=credit.pk),
                }
            )
        missing = [pk for pk in credited_from if pk not in seen]
        for organization in Organization.objects.filter(pk__in=missing).order_by("name"):
            rows.append(
                {
                    "credit": None,
                    "organization": organization,
                    "roles": [],
                    "people": credited_from[organization.pk],
                    "edit_url": self.record_url("contributors-credit-organization", pk=organization.pk),
                }
            )
        return self.in_default_order(rows, people)

    def in_default_order(self, rows, people):
        """Order the organizations and give each the badges it shows.

        The affiliations of the people who lead the record come first, in the order those people
        are credited, and show Project Leader. An organization people are credited from, with no
        roles of its own, shows Project Member. One with roles of its own keeps them.

        Args:
            rows: The organization rows, listed ones first, then affiliations by name.
            people: The rows from :meth:`people`.

        Returns:
            The rows in their default order, each with ``badges``, the role labels it shows.
        """
        leader, member = role_by_slug(LEADER), role_by_slug(MEMBER)
        led_from = []
        for row in people:
            affiliation = row["credit"].affiliation_id
            if affiliation and affiliation not in led_from and any(r.slug == LEADER for r in row["roles"]):
                led_from.append(affiliation)
        for row in rows:
            badges = [str(role) for role in row["roles"]]
            row["leads"] = row["organization"].pk in led_from
            if row["leads"] and leader and str(leader) not in badges:
                badges.insert(0, str(leader))
            if not badges and row["people"] and member:
                badges.append(str(member))
            row["badges"] = badges
        rank = {pk: place for place, pk in enumerate(led_from)}
        return sorted(rows, key=lambda row: rank.get(row["organization"].pk, len(rank)))

    def region_context(self, toast=None):
        """Everything the page region draws."""
        people = self.people()
        return {
            "base_object": self.base_object,
            "kind": self.access.kind,
            "people_rows": people,
            "organization_rows": self.organizations(people),
            "can_change": self.can_change,
            "urls": {
                "add_person": self.record_url("contributors-add-person"),
                "add_organization": self.record_url("contributors-add-organization"),
                "reorder": self.record_url("contributors-reorder"),
            },
            "base_url": self.list_url,
            "toast": toast,
            "sheet_id": SHEET_ID,
        }

    def region_response(self, toast=None, close_sheet=True):
        """Answer with the page region drawn again, and close the open sheet."""
        html = render_to_string(self.region_template, self.region_context(toast), request=self.request)
        response = HttpResponse(html)
        if close_sheet:
            response["HX-Trigger"] = json.dumps({"contrib:done": True})
        return response

    def sheet_response(self, template, context, title, lead=""):
        """Answer with a sheet drawn into the page's sheet slot, and open it."""
        context = {
            **context,
            "sheet_id": SHEET_ID,
            "sheet_title": title,
            "sheet_lead": lead,
            "base_object": self.base_object,
            "kind": self.access.kind,
            "foot": self.foot(context),
        }
        html = render_to_string(template, context, request=self.request)
        response = HttpResponse(html)
        response["HX-Trigger-After-Settle"] = json.dumps({"mvp-sheet-open": {"id": SHEET_ID}})
        return response

    def step_response(self, template, context, chrome=True):
        """Answer with the next step of an open sheet: its body, and with ``chrome`` its foot.

        Args:
            template: The step's template.
            context: What it draws.
            chrome: Whether the answer also replaces the sheet's foot, out of band. A list of
                search results answers without it.
        """
        context = {**context, "sheet_id": SHEET_ID, "base_object": self.base_object, "kind": self.access.kind}
        html = render_to_string(template, context, request=self.request)
        if chrome:
            foot = {"foot": self.foot(context), "oob": True}
            html += render_to_string("contributors/page/sheets/foot.html", foot, request=self.request)
        return HttpResponse(html)

    @staticmethod
    def foot(context):
        """The sheet foot's main button, from the step's context: its words, icon and form."""
        return {
            "submit": context.get("submit_text", ""),
            "icon": context.get("submit_icon", ""),
            "form": context.get("submit_form", ""),
        }

    # ------------------------------------------------------------------ shared form parts

    def offered_roles(self):
        """The roles this kind of record offers."""
        return Crediting(self.base_object).offered_roles()

    def chosen_roles(self):
        """The roles ticked in the posted form, limited to the offered ones."""
        offered = {str(role.pk): role for role in self.offered_roles()}
        return [offered[pk] for pk in self.request.POST.getlist("roles") if pk in offered]

    def affiliation_choices(self, person):
        """The organizations to credit a person from: theirs first, then every other one.

        Args:
            person: The person, or None for someone not yet in the portal.

        Returns:
            ``(theirs, others)``: ``theirs`` is a list of ``(organization, note)`` for the
            organizations on the person's profile, current ones first, and ``others`` every
            other organization by name.
        """
        theirs = []
        if person is not None:
            affiliations = person.affiliations.select_related("organization").order_by(
                "-is_primary", "organization__name"
            )
            for affiliation in affiliations:
                if affiliation.organization_id in {org.pk for org, _note in theirs}:
                    continue
                note = _("Past") if affiliation.end_date else _("Current")
                theirs.append((affiliation.organization, note))
            theirs.sort(key=lambda pair: (pair[1] != _("Current"), pair[0].name))
        known = {org.pk for org, _note in theirs}
        others = Organization.objects.exclude(pk__in=known).order_by("name")
        return theirs, others

    def chosen_affiliation(self):
        """The organization picked in the posted form, or None."""
        pk = self.request.POST.get("affiliation")
        if not pk:
            return None
        return Organization.objects.filter(pk=pk).first()

    def credit_form_context(self, person, credit=None, new_name=None):
        """What the form for a person's affiliation and roles draws."""
        theirs, others = self.affiliation_choices(person)
        return {
            "person": person,
            "credit": credit,
            "new_name": new_name or {},
            "roles": self.offered_roles(),
            "held_roles": {role.pk for role in credit.roles.all()} if credit else set(),
            "theirs": theirs,
            "others": others,
            "current_affiliation": credit.affiliation_id if credit else (theirs[0][0].pk if theirs and theirs[0][1] == _("Current") else None),
        }


# ---------------------------------------------------------------------- people


class AddPerson(ContributorsBase):
    """The Add person sheet: find someone, then pick their affiliation and roles."""

    name = "add-person"
    url_path = "add-person"

    def get(self, request, *args, **kwargs):
        """Open the sheet at its search step, or answer a search."""
        self.require_change()
        query = request.GET.get("q", "").strip()
        listed = Contribution.objects.for_entity(self.base_object).values_list("contributor_id", flat=True)
        found = Person.objects.real().exclude(pk__in=listed).exclude(is_superuser=True)
        if query:
            found = found.filter(Q(name__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
        found = found.order_by("name")[:12]
        context = {"found": found, "query": query, "step_url": self.record_url("contributors-add-person-step")}
        if request.headers.get("HX-Target") == "contrib-person-results":
            return self.step_response("contributors/page/sheets/person_results.html", context, chrome=False)
        return self.sheet_response(
            "contributors/page/sheets/add_person.html",
            context,
            _("Add a person to this %(kind)s") % {"kind": self.access.kind},
        )


class AddPersonStep(ContributorsBase):
    """The second step of Add person: their affiliation on this record and their roles."""

    name = "add-person-step"
    url_path = "add-person/details"

    def get(self, request, *args, **kwargs):
        """Draw the details step for a chosen person, or for someone new."""
        self.require_change()
        person = None
        new_name = None
        if request.GET.get("person"):
            person = get_object_or_404(Person, uuid=request.GET["person"])
        else:
            new_name = {
                "first_name": request.GET.get("first_name", "").strip(),
                "last_name": request.GET.get("last_name", "").strip(),
                "orcid": request.GET.get("orcid", "").strip(),
            }
            if not new_name["last_name"]:
                return self.step_response(
                    "contributors/page/sheets/new_person.html",
                    {
                        "error": _("Give their family name.") if "last_name" in request.GET else "",
                        "new_name": new_name,
                        "step_url": self.record_url("contributors-add-person-step"),
                        "submit_text": _("Continue"),
                        "submit_form": "contrib-new-form",
                    },
                )
        context = self.credit_form_context(person, new_name=new_name)
        context["action"] = self.record_url("contributors-add-person-step")
        context["submit_text"] = _("Add %(name)s") % {"name": first_name_of(person, new_name)}
        context["submit_icon"] = "add"
        return self.step_response("contributors/page/sheets/credit_form.html", context)

    def post(self, request, *args, **kwargs):
        """Add the person with their affiliation and roles."""
        self.require_change()
        if request.POST.get("person"):
            person = get_object_or_404(Person, uuid=request.POST["person"])
        else:
            first = request.POST.get("first_name", "").strip()
            last = request.POST.get("last_name", "").strip()
            if not last:
                return HttpResponseBadRequest()
            person = Person.objects.create_unclaimed(first, last)
        crediting = Crediting(self.base_object)
        try:
            credit = crediting.add(person, organization=self.chosen_affiliation())
            crediting.update(credit, roles=self.chosen_roles())
        except ValidationError as error:
            return self.region_response(toast={"text": " ".join(error.messages), "tone": "error"})
        return self.region_response(toast={"text": _("%(name)s added.") % {"name": person.name}})


class EditCredit(ContributorsBase):
    """Edit one contributor: a person's affiliation on this record and roles, an organization's roles."""

    name = "edit"
    url_path = "<int:pk>/edit"

    def get(self, request, *args, **kwargs):
        """Open the edit sheet."""
        self.require_change()
        credit = self.get_contribution()
        contributor = credit.contributor.get_real_instance()
        if contributor.is_organization:
            context = {
                "organization": contributor,
                "credit": credit,
                "roles": self.offered_roles(),
                "held_roles": {role.pk for role in credit.roles.all()},
                "action": self.record_url("contributors-edit", pk=credit.pk),
                "submit_text": _("Save"),
            }
            return self.sheet_response("contributors/page/sheets/edit_organization.html", context, contributor.name)
        context = self.credit_form_context(contributor, credit=credit)
        context["action"] = self.record_url("contributors-edit", pk=credit.pk)
        context["submit_text"] = _("Save")
        return self.sheet_response("contributors/page/sheets/edit_person.html", context, contributor.name)

    def post(self, request, *args, **kwargs):
        """Save the edit."""
        self.require_change()
        credit = self.get_contribution()
        crediting = Crediting(self.base_object)
        contributor = credit.contributor.get_real_instance()
        try:
            if contributor.is_organization:
                crediting.update(credit, roles=self.chosen_roles())
            else:
                crediting.update(credit, roles=self.chosen_roles(), organization=self.chosen_affiliation())
        except ValidationError as error:
            return self.region_response(toast={"text": " ".join(error.messages), "tone": "error"})
        return self.region_response(toast={"text": _("%(name)s saved.") % {"name": contributor.name}})


class CreditOrganization(ContributorsBase):
    """Give an organization that is only someone's affiliation a role of its own on the record."""

    name = "credit-organization"
    url_path = "organization/<int:pk>/roles"

    def get(self, request, *args, **kwargs):
        """Open the roles sheet for an organization not yet listed."""
        self.require_change()
        organization = get_object_or_404(Organization, pk=kwargs["pk"])
        context = {
            "organization": organization,
            "credit": None,
            "roles": self.offered_roles(),
            "held_roles": set(),
            "action": self.record_url("contributors-credit-organization", pk=organization.pk),
            "submit_text": _("Save"),
        }
        return self.sheet_response("contributors/page/sheets/edit_organization.html", context, organization.name)

    def post(self, request, *args, **kwargs):
        """List the organization with the chosen roles."""
        self.require_change()
        organization = get_object_or_404(Organization, pk=kwargs["pk"])
        crediting = Crediting(self.base_object)
        try:
            crediting.list_organization(organization)
            credit = self.base_object.contributors.get(contributor=organization)
            crediting.update(credit, roles=self.chosen_roles())
        except ValidationError as error:
            return self.region_response(toast={"text": " ".join(error.messages), "tone": "error"})
        return self.region_response(toast={"text": _("%(name)s saved.") % {"name": organization.name}})


class RemoveCredit(ContributorsBase):
    """Remove a contributor, answering with an Undo."""

    name = "remove"
    url_path = "<int:pk>/remove"

    def post(self, request, *args, **kwargs):
        """Remove the contributor and offer to put them back."""
        self.require_change()
        credit = self.get_contribution()
        contributor = credit.contributor.get_real_instance()
        kept = {
            "contributor": contributor.pk,
            "roles": [role.pk for role in credit.roles.all()],
            "affiliation": credit.affiliation_id,
            "level": credit.level,
            "order": credit.order,
        }
        try:
            Crediting(self.base_object).remove(credit)
        except ValidationError as error:
            return self.region_response(toast={"text": " ".join(error.messages), "tone": "error"})
        return self.region_response(
            toast={
                "text": _("%(name)s removed.") % {"name": contributor.name},
                "undo_url": self.record_url("contributors-undo"),
                "undo": json.dumps(kept),
            }
        )


class UndoRemove(ContributorsBase):
    """Put a removed contributor back as they were."""

    name = "undo"
    url_path = "undo"

    def post(self, request, *args, **kwargs):
        """Recreate the removed contribution, in its old place."""
        self.require_change()
        try:
            kept = json.loads(request.POST["undo"])
        except (KeyError, ValueError):
            return HttpResponseBadRequest()
        contributor = get_object_or_404(Contributor, pk=kept["contributor"]).get_real_instance()
        if self.base_object.contributors.filter(contributor=contributor).exists():
            return self.region_response()
        crediting = Crediting(self.base_object)
        affiliation = Organization.objects.filter(pk=kept.get("affiliation")).first()
        credit = crediting.add(contributor, organization=affiliation)
        credit.roles.set(Record.objects.filter(pk__in=kept.get("roles", [])))
        credit.level = kept.get("level") if not contributor.is_organization else None
        credit.order = kept.get("order", credit.order)
        credit.save(update_fields=["level", "order"])
        return self.region_response(toast={"text": _("%(name)s is back.") % {"name": contributor.name}})


class Reorder(ContributorsBase):
    """The Reorder sheet: drag people into the order the record credits them in."""

    name = "reorder"
    url_path = "reorder"

    def get(self, request, *args, **kwargs):
        """Open the reorder sheet."""
        self.require_change()
        return self.sheet_response(
            "contributors/page/sheets/reorder.html",
            {"people_rows": self.people(), "action": self.record_url("contributors-reorder"), "submit_text": _("Save order")},
            _("Reorder people"),
        )

    def post(self, request, *args, **kwargs):
        """Save the order, and who appears in the citation."""
        self.require_change()
        people = Contribution.objects.for_entity(self.base_object).people()
        try:
            save_order(people, request.POST.getlist("order"), field="order")
        except InvalidOrder:
            return HttpResponseBadRequest()
        cited = set(request.POST.getlist("cited"))
        for credit in people.select_related("contributor"):
            set_cited(credit, str(credit.pk) in cited)
        return self.region_response(toast={"text": _("New order saved.")})


# ---------------------------------------------------------------------- organizations


class AddOrganization(ContributorsBase):
    """The Add organization sheet: find one, or name a new one, then pick its roles."""

    name = "add-organization"
    url_path = "add-organization"

    def get(self, request, *args, **kwargs):
        """Open the sheet at its search step, or answer a search, or draw the roles step."""
        self.require_change()
        if request.GET.get("organization") or request.GET.get("new_name"):
            organization = None
            if request.GET.get("organization"):
                organization = get_object_or_404(Organization, uuid=request.GET["organization"])
            context = {
                "organization": organization,
                "new_name": request.GET.get("new_name", "").strip(),
                "show_who": True,
                "credit": None,
                "roles": self.offered_roles(),
                "held_roles": set(),
                "action": self.record_url("contributors-add-organization"),
                "submit_text": _("Add to the %(kind)s") % {"kind": self.access.kind},
            }
            return self.step_response("contributors/page/sheets/organization_form.html", context)
        query = request.GET.get("q", "").strip()
        listed = Contribution.objects.for_entity(self.base_object).values_list("contributor_id", flat=True)
        found = Organization.objects.exclude(pk__in=listed)
        if query:
            found = found.filter(name__icontains=query)
        context = {"found": found.order_by("name")[:12], "query": query, "step_url": self.record_url("contributors-add-organization")}
        if request.headers.get("HX-Target") == "contrib-organization-results":
            return self.step_response("contributors/page/sheets/organization_results.html", context, chrome=False)
        return self.sheet_response(
            "contributors/page/sheets/add_organization.html",
            context,
            _("Add an organization to this %(kind)s") % {"kind": self.access.kind},
        )

    def post(self, request, *args, **kwargs):
        """List the organization with its roles."""
        self.require_change()
        if request.POST.get("organization"):
            organization = get_object_or_404(Organization, uuid=request.POST["organization"])
        else:
            name = request.POST.get("new_name", "").strip()
            if not name:
                return HttpResponseBadRequest()
            organization = Organization.objects.create(name=name)
        crediting = Crediting(self.base_object)
        try:
            crediting.list_organization(organization)
            credit = self.base_object.contributors.get(contributor=organization)
            crediting.update(credit, roles=self.chosen_roles())
        except ValidationError as error:
            return self.region_response(toast={"text": " ".join(error.messages), "tone": "error"})
        return self.region_response(toast={"text": _("%(name)s added.") % {"name": organization.name}})


@plugins.register(
    Project,
    Dataset,
    Sample,
    Measurement,
    label=gettext_lazy("Contributors"),
    icon="users",
    order=150,
)
class Contributors(ContributorsBase):
    """The Contributors page: people in the main column, organizations beside them."""

    url_path = "contributors"
    extra_views = [
        AddPerson,
        AddPersonStep,
        EditCredit,
        CreditOrganization,
        RemoveCredit,
        UndoRemove,
        Reorder,
        AddOrganization,
    ]
    template_name = "contributors/page/page.html"
    page_title = gettext_lazy("Contributors")

    class Media:
        css = {"all": ["contributors/page.css"]}
        js = ["contributors/page.js"]

    def get_context_data(self, **kwargs):
        """Add the region's context."""
        context = super().get_context_data(**kwargs)
        context.update(self.region_context())
        return context

"""Prototype: the Contributors page of a project, dataset, sample or measurement.

People in the main column, organizations beside them. Each row has one actions control that
opens a sheet. Adding, editing and reordering happen in sheets, and every change answers with
the whole page region drawn again, so both columns and their counts always agree.

This is prototype code on a branch that is never merged. See PROTOTYPE.md.
"""

import json
from urllib.parse import urlencode

from controlled_vocabularies.models import Record
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
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
from ..services.registries import JSON, Orcid, RegistryUnavailable, Ror, ask
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


# The sections of an ORCID record that name an organization the person belongs or belonged to, in
# the order they are offered when nothing else separates them.
ORCID_AFFILIATIONS = ("employment", "education", "qualification", "invited-position", "membership", "service")


def orcid_affiliations(orcid_id):
    """Every organization on a person's public ORCID record, current ones first, then the most recent.

    Read from all of the record's affiliation sections (employments, educations, qualifications,
    invited positions, memberships and services), ended ones included, each organization once.

    Args:
        orcid_id: The bare ORCID iD.

    Returns:
        One dictionary per organization: ``value`` (the form's value for it), ``name``, ``ror``
        (the ROR ID ORCID gives for it, or an empty string), ``current`` and ``note``. Empty when
        ORCID can't be reached.
    """

    def read(body):
        found = []
        for rank, section in enumerate(ORCID_AFFILIATIONS):
            for group in (body.get(f"{section}s") or {}).get("affiliation-group") or []:
                for summary in group["summaries"]:
                    entry = summary.get(f"{section}-summary") or {}
                    organization = entry.get("organization") or {}
                    if not organization.get("name"):
                        continue
                    place = organization.get("disambiguated-organization") or {}
                    ror = place.get("disambiguated-organization-identifier", "") if place.get("disambiguation-source") == "ROR" else ""
                    ended = entry.get("end-date") or {}
                    year = int(((ended.get("year") or {}).get("value")) or 0)
                    found.append({"name": organization["name"], "ror": ror, "current": not ended, "year": year, "rank": rank})
        return found

    try:
        found = ask(f"https://pub.orcid.org/v3.0/{orcid_id}/activities", read, headers=JSON) or []
    except RegistryUnavailable:
        return []
    seen, rows = set(), []
    for entry in sorted(found, key=lambda e: (not e["current"], -e["year"], e["rank"])):
        keys = {entry["name"].lower()} | ({entry["ror"]} if entry["ror"] else set())
        if keys & seen:
            continue
        seen |= keys
        rows.append({"name": entry["name"], "ror": entry["ror"], "current": entry["current"], "note": _("Current") if entry["current"] else _("Past")})
    for place, row in enumerate(rows):
        row["value"] = f"registry:{place}"
    return rows


def organization_for(entry):
    """The portal's organization for an affiliation on an ORCID record: found by ROR ID or name, or made.

    Raises:
        RegistryUnavailable: ROR could not be asked for an organization to make.
    """
    record = Ror().fetch(entry["ror"]) if entry["ror"] else None
    held = (Ror().known(record) if record else None) or Organization.objects.filter(name__iexact=entry["name"]).first()
    if held:
        return held
    return Ror().profile(record) if record else Organization.objects.create(name=entry["name"])


def initials_of(record, organization=False):
    """The initials an avatar shows for a registry record, by the rule the portal's own avatars use."""
    if organization:
        return Organization(name=record["name"]).get_initials()
    return f"{record.get('given', '')[:1]}{record.get('family', '')[:1]}".upper() or record["name"][:1].upper()


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
        are credited, then organizations that are Project Leader themselves, and all of them show
        Project Leader. An organization people are credited from, with no
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
            own_lead = any(role.slug == LEADER for role in row["roles"])
            row["leads"] = row["organization"].pk in led_from or own_lead
            if row["organization"].pk not in led_from and own_lead:
                led_from.append(row["organization"].pk)
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
            if context.get("head"):
                html += render_to_string("contributors/page/sheets/head.html", context, request=self.request)
        return HttpResponse(html)

    @staticmethod
    def head_for(contributor, new_name=None, organization=False):
        """The sheet's title on a step about one person or organization: their avatar and name.

        Args:
            contributor: The person or organization, or None for one not yet in the portal.
            new_name: For a person not yet in the portal, their ``first_name`` and ``last_name``;
                for an organization, its name.
            organization: Whether a contributor not yet in the portal is an organization.
        """
        if contributor is not None:
            return {"contributor": contributor, "title": contributor.name}
        if organization:
            return {"title": new_name, "initials": Organization(name=new_name).get_initials(), "organization": True}
        first, last = new_name.get("first_name", ""), new_name.get("last_name", "")
        return {"title": f"{first} {last}".strip(), "initials": f"{first[:1]}{last[:1]}".upper()}

    @staticmethod
    def foot(context):
        """The sheet foot's main button, from the step's context: its words, icon and form."""
        return {
            "submit": context.get("submit_text", ""),
            "icon": context.get("submit_icon", ""),
            "form": context.get("submit_form", ""),
            "back": context.get("back_url", ""),
            "next": context.get("next_url", ""),
            "next_text": context.get("next_text", ""),
            "arrow": context.get("submit_arrow", False),
        }

    # ------------------------------------------------------------------ shared form parts

    def offered_roles(self):
        """The roles this kind of record offers."""
        return Crediting(self.base_object).offered_roles()

    def chosen_roles(self, held=()):
        """The roles ticked in the posted form, limited to the offered ones.

        Project Member can't be taken away: it is kept for anyone being added, and for anyone
        who holds it.

        Args:
            held: The roles the contributor holds now, or None when they are being added.
        """
        offered = {str(role.pk): role for role in self.offered_roles()}
        chosen = [offered[pk] for pk in self.request.POST.getlist("roles") if pk in offered]
        for pk in self.locked_roles(held):
            if str(pk) in offered and offered[str(pk)] not in chosen:
                chosen.append(offered[str(pk)])
        return chosen

    def locked_roles(self, held):
        """The roles ticked and not removable: Project Member, for anyone added or holding it.

        Args:
            held: The pks of the roles the contributor holds now, or None when they are being
                added.
        """
        member = role_by_slug(MEMBER)
        if member is None or member.pk not in {role.pk for role in self.offered_roles()}:
            return set()
        return {member.pk} if held is None or member.pk in held else set()

    @staticmethod
    def held_by(credit):
        """The pks of the roles a contribution holds, or None when it counts as just added.

        An organization listed with no roles of its own is there as someone's affiliation and
        shows Project Member, so it is treated as just added.

        Args:
            credit: The contribution, or None when the contributor is being added.
        """
        if credit is None:
            return None
        held = {role.pk for role in credit.roles.all()}
        if not held and credit.contributor.get_real_instance().is_organization:
            return None
        return held

    def role_context(self, credit):
        """The roles to offer, the ones ticked, and the ones that can't be unticked.

        Args:
            credit: The contribution being edited, or None when the contributor is being added.
        """
        held = self.held_by(credit)
        locked = self.locked_roles(held)
        return {"roles": self.offered_roles(), "held_roles": (held or set()) | locked, "locked_roles": locked}

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

    def chosen_affiliation(self, orcid=""):
        """The organization picked in the posted form, or None.

        Args:
            orcid: The ORCID iD of the person being added, whose ORCID record's affiliations the
                form may offer. One of those is found in the portal by its ROR ID or its name, or
                made.

        Raises:
            RegistryUnavailable: ROR could not be asked for an organization to make.
        """
        value = self.request.POST.get("affiliation", "")
        if not value:
            return None
        if value.startswith("registry:") and orcid:
            chosen = next((a for a in orcid_affiliations(orcid) if a["value"] == value), None)
            return organization_for(chosen) if chosen else None
        return Organization.objects.filter(pk=value).first() if value.isdigit() else None

    def credit_form_context(self, person, credit=None, new_name=None):
        """What the form for a person's affiliation and roles draws."""
        theirs, others = self.affiliation_choices(person)
        return {
            "person": person,
            "credit": credit,
            "new_name": new_name or {},
            **self.role_context(credit),
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
        title = _("Add a person to this %(kind)s") % {"kind": self.access.kind}
        if request.headers.get("HX-Target") == "contrib-person-results":
            return self.step_response("contributors/page/sheets/person_results.html", context, chrome=False)
        if request.GET.get("back"):
            context["head"] = {"title": title}
            return self.step_response("contributors/page/sheets/person_search.html", context)
        return self.sheet_response("contributors/page/sheets/add_person.html", context, title)


class AddPersonStep(ContributorsBase):
    """The second step of Add person: their affiliation on this record and their roles."""

    name = "add-person-step"
    url_path = "add-person/details"

    def get(self, request, *args, **kwargs):
        """Draw the next step for a chosen person, or for someone new.

        Someone new is given by ORCID iD, or by name. An iD goes straight to their affiliation,
        offering the affiliations on their ORCID record. A name alone first shows the people ORCID
        finds by that name, to pick from or to skip.
        """
        self.require_change()
        person = None
        new_name = None
        orcid = None
        if request.GET.get("person"):
            person = get_object_or_404(Person, uuid=request.GET["person"])
        else:
            new_name = {
                "first_name": request.GET.get("first_name", "").strip(),
                "last_name": request.GET.get("last_name", "").strip(),
                "orcid": request.GET.get("orcid", "").strip(),
            }
            if new_name["orcid"] and not request.GET.get("form"):
                try:
                    orcid = Orcid().fetch(new_name["orcid"])
                except RegistryUnavailable:
                    orcid = None
                if orcid is None:
                    return self.new_person_step(new_name, _("ORCID has no public record under that iD."))
                person = Orcid().known(orcid)
                if person is None:
                    new_name.update(first_name=orcid["given"], last_name=orcid["family"], orcid=orcid["id"])
            elif not new_name["last_name"] or request.GET.get("form"):
                error = ""
                if "last_name" in request.GET and not new_name["last_name"] and not request.GET.get("form"):
                    error = _("Give their family name, or pick them from ORCID.")
                return self.new_person_step(new_name, error)
            elif not request.GET.get("skip"):
                return self.orcid_matches_step(new_name)
        context = self.credit_form_context(person, new_name=new_name)
        if new_name and new_name.get("orcid") and person is None:
            context["registry_affiliations"] = orcid_affiliations(new_name["orcid"])
            current = [a for a in context["registry_affiliations"] if a["current"]]
            if current:
                context["current_affiliation"] = current[0]["value"]
        context["action"] = self.record_url("contributors-add-person-step")
        context["head"] = self.head_for(person, new_name)
        if request.GET.get("person"):
            context["back_url"] = self.record_url("contributors-add-person") + "?back=1"
        else:
            context["back_url"] = self.step_url(new_name, form=1)
        context["submit_text"] = _("Add %(name)s") % {"name": first_name_of(person, new_name)}
        context["submit_icon"] = "add"
        return self.step_response("contributors/page/sheets/credit_form.html", context)

    def step_url(self, new_name, **extra):
        """The address of this step for someone new, carrying what is known of them."""
        query = {key: value for key, value in new_name.items() if value}
        return self.record_url("contributors-add-person-step") + "?" + urlencode({**query, **extra})

    def new_person_step(self, new_name, error=""):
        """The step that adds someone new: their ORCID iD, then their names."""
        return self.step_response(
            "contributors/page/sheets/new_person.html",
            {
                "error": error,
                "new_name": new_name,
                "step_url": self.record_url("contributors-add-person-step"),
                "orcid_search_url": self.record_url("contributors-registry", which="orcid"),
                "submit_text": _("Continue"),
                "submit_arrow": True,
                "submit_form": "contrib-new-form",
                "back_url": self.record_url("contributors-add-person") + "?back=1",
                "head": {"title": _("Add a person to this %(kind)s") % {"kind": self.access.kind}},
            },
        )

    def orcid_matches_step(self, new_name):
        """The step that shows who ORCID finds under the names given, to pick from or skip."""
        try:
            found = Orcid().search(f"{new_name['first_name']} {new_name['last_name']}".strip())
            unavailable = False
        except RegistryUnavailable:
            found, unavailable = {"results": [], "more": False}, True
        return self.step_response(
            "contributors/page/sheets/orcid_matches.html",
            {
                "found": found["results"],
                "unavailable": unavailable,
                "new_name": new_name,
                "pick_url": self.record_url("contributors-add-person-step"),
                "next_url": self.step_url(new_name, skip=1),
                "next_text": _("Add by name alone"),
                "back_url": self.step_url(new_name, form=1),
                "head": {"title": _("Do you mean?"), "lead": _("Powered by ORCID")},
            },
        )

    def post(self, request, *args, **kwargs):
        """Add the person with their affiliation and roles."""
        self.require_change()
        orcid = request.POST.get("orcid", "").strip()
        if request.POST.get("person"):
            person = get_object_or_404(Person, uuid=request.POST["person"])
        elif orcid:
            try:
                record = Orcid().fetch(orcid)
            except RegistryUnavailable:
                record = None
            if record is None:
                return self.region_response(toast={"text": _("ORCID could not be reached. Try again."), "tone": "error"})
            person = Orcid().profile(record)
        else:
            first = request.POST.get("first_name", "").strip()
            last = request.POST.get("last_name", "").strip()
            if not last:
                return HttpResponseBadRequest()
            person = Person.objects.create_unclaimed(first, last)
        crediting = Crediting(self.base_object)
        try:
            credit = crediting.add(person, organization=self.chosen_affiliation(orcid=orcid))
            crediting.update(credit, roles=self.chosen_roles(held=None))
        except (ValidationError, RegistryUnavailable) as error:
            text = " ".join(error.messages) if isinstance(error, ValidationError) else _("ROR could not be reached. Try again.")
            return self.region_response(toast={"text": text, "tone": "error"})
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
                **self.role_context(credit),
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
                crediting.update(credit, roles=self.chosen_roles(held=self.held_by(credit)))
            else:
                crediting.update(credit, roles=self.chosen_roles(held=self.held_by(credit)), organization=self.chosen_affiliation())
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
            **self.role_context(None),
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
            crediting.update(credit, roles=self.chosen_roles(held=None))
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


class RegistrySearch(ContributorsBase):
    """Search ORCID for people or ROR for organizations, for the live search in the add sheets."""

    name = "registry"
    url_path = "registry/<str:which>"

    def get(self, request, *args, **kwargs):
        """Answer with up to ten matches, each with the markup its option is drawn with."""
        self.require_change()
        registry = {"orcid": Orcid, "ror": Ror}.get(kwargs["which"])
        query = request.GET.get("q", "").strip()
        if registry is None or len(query) < 2:
            return JsonResponse({"results": []})
        try:
            found = registry().search(query)["results"]
        except RegistryUnavailable:
            return JsonResponse({"results": [], "unavailable": True})
        organization = kwargs["which"] == "ror"
        for record in found:
            record["html"] = render_to_string(
                "contributors/page/sheets/registry_option.html",
                {"record": record, "organization": organization, "initials": initials_of(record, organization)},
                request=request,
            )
        return JsonResponse({"results": found})


# ---------------------------------------------------------------------- organizations


class AddOrganization(ContributorsBase):
    """The Add organization sheet: find one, or name a new one, then pick its roles."""

    name = "add-organization"
    url_path = "add-organization"

    def get(self, request, *args, **kwargs):
        """Open the sheet at its search step, or answer a search, or draw the roles step."""
        self.require_change()
        new_name = request.GET.get("new_name", "").strip()
        ror = request.GET.get("ror", "").strip()
        if request.GET.get("form") or (request.GET.get("new_name") is not None and not new_name and not ror):
            return self.new_organization_step(new_name, ror)
        if ror:
            try:
                record = Ror().fetch(ror)
            except RegistryUnavailable:
                record = None
            if record is None:
                return self.new_organization_step(new_name, "", _("ROR has no record under that ID."))
            known = Ror().known(record)
            return self.roles_step(known, record["name"], "" if known else record["id"], back=self.step_url(ror=record["id"], form=1))
        if new_name and not request.GET.get("skip"):
            return self.ror_matches_step(new_name)
        if new_name:
            return self.roles_step(None, new_name, back=self.step_url(new_name=new_name, form=1))
        if request.GET.get("organization"):
            return self.roles_step(get_object_or_404(Organization, uuid=request.GET["organization"]))
        query = request.GET.get("q", "").strip()
        listed = Contribution.objects.for_entity(self.base_object).values_list("contributor_id", flat=True)
        found = Organization.objects.exclude(pk__in=listed)
        if query:
            found = found.filter(name__icontains=query)
        context = {"found": found.order_by("name")[:12], "query": query, "step_url": self.record_url("contributors-add-organization")}
        title = self.title()
        if request.headers.get("HX-Target") == "contrib-organization-results":
            return self.step_response("contributors/page/sheets/organization_results.html", context, chrome=False)
        if request.GET.get("back"):
            context["head"] = {"title": title}
            return self.step_response("contributors/page/sheets/organization_search.html", context)
        return self.sheet_response("contributors/page/sheets/add_organization.html", context, title)

    def title(self):
        """The sheet's own title."""
        return _("Add an organization to this %(kind)s") % {"kind": self.access.kind}

    def step_url(self, **query):
        """The address of a step of this sheet, carrying what is known of the organization."""
        query = {key: value for key, value in query.items() if value}
        return self.record_url("contributors-add-organization") + "?" + urlencode(query)

    def new_organization_step(self, new_name, ror="", error=""):
        """The step that adds an organization not in the portal: its ROR ID, then its name."""
        option = None
        if ror:
            try:
                option = Ror().fetch(ror)
            except RegistryUnavailable:
                option = None
        return self.step_response(
            "contributors/page/sheets/new_organization.html",
            {
                "error": error,
                "new_name": new_name,
                "ror_option": option,
                "step_url": self.record_url("contributors-add-organization"),
                "ror_search_url": self.record_url("contributors-registry", which="ror"),
                "submit_text": _("Continue"),
                "submit_arrow": True,
                "submit_form": "contrib-new-form",
                "back_url": self.record_url("contributors-add-organization") + "?back=1",
                "head": {"title": self.title()},
            },
        )

    def ror_matches_step(self, new_name):
        """The step that shows what ROR finds under the name given, to pick from or skip."""
        try:
            found = Ror().search(new_name)
            unavailable = False
        except RegistryUnavailable:
            found, unavailable = {"results": [], "more": False}, True
        return self.step_response(
            "contributors/page/sheets/ror_matches.html",
            {
                "found": [{**record, "initials": initials_of(record, True)} for record in found["results"]],
                "unavailable": unavailable,
                "new_name": new_name,
                "pick_url": self.record_url("contributors-add-organization"),
                "next_url": self.step_url(new_name=new_name, skip=1),
                "next_text": _("Add by name alone"),
                "back_url": self.step_url(new_name=new_name, form=1),
                "head": {"title": _("Do you mean?"), "lead": _("Powered by the Research Organization Registry (ROR)")},
            },
        )

    def roles_step(self, organization, new_name="", ror="", back=""):
        """The step that picks the organization's roles on this record.

        Args:
            organization: The organization, when it is in the portal.
            new_name: The name of one not in the portal yet.
            ror: Its ROR ID, when it was picked from ROR.
            back: Where Back goes; the search step when not given.
        """
        context = {
            "organization": organization,
            "new_name": new_name,
            "ror": ror,
            "show_who": True,
            "credit": None,
            **self.role_context(None),
            "action": self.record_url("contributors-add-organization"),
            "submit_text": _("Add to the %(kind)s") % {"kind": self.access.kind},
            "head": self.head_for(organization, new_name, organization=True),
            "back_url": back or self.record_url("contributors-add-organization") + "?back=1",
        }
        return self.step_response("contributors/page/sheets/organization_form.html", context)

    def post(self, request, *args, **kwargs):
        """List the organization with its roles."""
        self.require_change()
        if request.POST.get("organization"):
            organization = get_object_or_404(Organization, uuid=request.POST["organization"])
        elif request.POST.get("ror"):
            try:
                record = Ror().fetch(request.POST["ror"].strip())
            except RegistryUnavailable:
                record = None
            if record is None:
                return self.region_response(toast={"text": _("ROR could not be reached. Try again."), "tone": "error"})
            organization = Ror().known(record) or Ror().profile(record)
        else:
            name = request.POST.get("new_name", "").strip()
            if not name:
                return HttpResponseBadRequest()
            organization = Organization.objects.create(name=name)
        crediting = Crediting(self.base_object)
        try:
            crediting.list_organization(organization)
            credit = self.base_object.contributors.get(contributor=organization)
            crediting.update(credit, roles=self.chosen_roles(held=None))
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
        RegistrySearch,
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

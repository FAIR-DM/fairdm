"""What every view of a record's Contributors tab shares.

People are listed in the main column and organizations beside them. Each row has one
actions control that opens a sheet. Adding, editing and reordering happen in sheets, and
every change answers with the whole region drawn again, so both columns and their counts
always agree. The changes themselves are made by ``Crediting``.
"""

import json

from controlled_vocabularies.models import Record
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

from fairdm.contrib.plugins import reverse

from ..access import RecordAccess
from ..models import Contribution, Organization, Person
from ..services.crediting import Crediting
from ..services.registries import RegistryUnavailable, SearchLimitReached, count_search
from .shared import ContributionPage

SHEET_ID = "contrib-sheet"
"""The id of the one sheet the tab opens, which every step of an add or an edit is drawn
in.
"""

ROLES_DOCS_URL = "https://docs.fairdm.org/latest/reference/contributor-roles.html"
"""Where the page that says what each contributor role means is published."""

LEADER = "project-leader"
MEMBER = "project-member"
ROLE_URI = "https://w3id.org/fairdm/vocabularies/contributor-roles/{}"


def role_by_slug(slug):
    """Return the contributor role with this slug, or None.

    Args:
        slug: The role's slug, such as ``data-collector``.
    """
    return Record.objects.filter(uri=ROLE_URI.format(slug)).first()


def first_name_of(person, new_name=None):
    """Return the first of a person's given names, or their family name when they have
    none.

    Args:
        person: The person, or None for someone not yet in the portal.
        new_name: For someone not yet in the portal, their ``first_name`` and
            ``last_name``.
    """
    given = person.first_name if person else (new_name or {}).get("first_name", "")
    family = person.last_name if person else (new_name or {}).get("last_name", "")
    return (given.split() or [family or (person.name if person else "")])[0]


def initials_of(record, organization=False):
    """Return the initials an avatar shows for a registry record, by the portal's own
    rule.

    Args:
        record: A registry record with ``name`` and, for a person, ``given`` and
            ``family``.
        organization: Whether the record is an organization.
    """
    if organization:
        return Organization(name=record["name"]).get_initials()
    given, family = record.get("given", ""), record.get("family", "")
    return f"{given[:1]}{family[:1]}".upper() or record["name"][:1].upper()


class ContributorsBase(ContributionPage):
    """What every view of the tab shares: reading the lists, answering, and the roles
    field.
    """

    manager_only = True
    region_template = "cotton/contributor/tab/region.html"

    def record_url(self, name, **kwargs):
        """Return the address of one of the tab's views for the record."""
        return reverse(self.base_object, name, **kwargs)

    # ------------------------------------------------------------------ reading

    def people(self):
        """Return the people on the record in their order, with what each row shows."""
        people_credits = (
            Contribution.objects.for_entity(self.base_object)
            .people()
            .select_related("contributor", "affiliation")
            .prefetch_related("roles", "affiliation__identifiers")
        )
        people_credits = list(people_credits)
        persons = {
            person.pk: person
            for person in Person.objects.filter(
                pk__in=[credit.contributor_id for credit in people_credits]
            ).prefetch_related(
                "identifiers", "socialaccount_set", "affiliations__organization"
            )
        }
        for credit in people_credits:
            # Rows read the credit's contributor and record again and again.
            credit.content_object = self.base_object
            if credit.contributor_id in persons:
                credit.contributor = persons[credit.contributor_id]
        return [
            {
                "credit": credit,
                "person": credit.contributor,
                "roles": list(credit.roles.all()),
                "cited": credit.in_citation,
                "edit_url": self.record_url("contribution-list-edit", pk=credit.pk),
                "remove_url": self.record_url("contribution-list-remove", pk=credit.pk),
            }
            for credit in people_credits
            if credit.contributor
        ]

    def organizations(self, people):
        """Return every organization on the record in the order the tab shows them.

        An organization is on the tab when it is listed with roles or is the affiliation
        of someone listed.

        Args:
            people: The rows from ``people``, whose affiliations count.

        Returns:
            One row per organization: the affiliations of the people who lead the record
            first, then organizations that lead it themselves, then the organizations
            credited directly in their order, then those that are only an affiliation,
            by name.
        """
        credited_from = {}
        for row in people:
            if row["credit"].affiliation_id:
                credited_from.setdefault(row["credit"].affiliation_id, []).append(
                    row["person"]
                )
        listed = (
            Contribution.objects.for_entity(self.base_object)
            .organizations()
            .prefetch_related("roles")
        )
        listed = list(listed)
        known = {
            organization.pk: organization
            for organization in Organization.objects.filter(
                pk__in=[credit.contributor_id for credit in listed]
            ).prefetch_related("identifiers")
        }
        rows, seen = [], set()
        for credit in listed:
            organization = known.get(credit.contributor_id)
            if organization is None:
                continue
            seen.add(organization.pk)
            rows.append(
                {
                    "credit": credit,
                    "organization": organization,
                    "roles": list(credit.roles.all()),
                    "people": credited_from.get(organization.pk, []),
                    "edit_url": self.record_url("contribution-list-edit", pk=credit.pk),
                    "remove_url": self.record_url(
                        "contribution-list-remove", pk=credit.pk
                    ),
                }
            )
        only_affiliations = (
            Organization.objects.filter(
                pk__in=[pk for pk in credited_from if pk not in seen]
            )
            .prefetch_related("identifiers")
            .order_by("name")
        )
        for organization in only_affiliations:
            rows.append(
                {
                    "credit": None,
                    "organization": organization,
                    "roles": [],
                    "people": credited_from[organization.pk],
                    "edit_url": self.record_url(
                        "contribution-list-credit-organization", pk=organization.pk
                    ),
                }
            )
        return self.in_default_order(rows, people)

    def in_default_order(self, rows, people):
        """Order the organizations and give each the badges it shows.

        The affiliations of the people who lead the record come first, in the order
        those people are credited, then organizations that are Project Leader
        themselves, and all of them show Project Leader. An organization people are
        credited from, with no roles of its own, shows Project Member. One with roles of
        its own keeps them.

        Args:
            rows: The organization rows, listed ones first, then affiliations by name.
            people: The rows from ``people``.

        Returns:
            The rows in their default order, each with ``badges``, the role labels it
            shows.
        """
        leader, member = role_by_slug(LEADER), role_by_slug(MEMBER)
        led_from = []
        for row in people:
            affiliation = row["credit"].affiliation_id
            leads = any(role.pk == getattr(leader, "pk", None) for role in row["roles"])
            if affiliation and affiliation not in led_from and leads:
                led_from.append(affiliation)
        for row in rows:
            badges = [str(role) for role in row["roles"]]
            own_lead = any(
                role.pk == getattr(leader, "pk", None) for role in row["roles"]
            )
            pk = row["organization"].pk
            leads = pk in led_from or own_lead
            if own_lead and pk not in led_from:
                led_from.append(pk)
            if leads and leader and str(leader) not in badges:
                badges.insert(0, str(leader))
            if not badges and row["people"] and member:
                badges.append(str(member))
            row["badges"] = badges
        rank = {pk: place for place, pk in enumerate(led_from)}
        return sorted(rows, key=lambda row: rank.get(row["organization"].pk, len(rank)))

    def access_from_above(self, people):
        """Return who holds access from a record above without being credited here.

        Args:
            people: The rows from ``people``.

        Returns:
            One entry per person with their ``level`` label and the record it comes
            from, none for anyone who cannot see levels.
        """
        credited = {row["person"].pk for row in people}
        return [
            {
                "person": person,
                "label": level.label,
                "source_kind": RecordAccess(source).kind,
                "source_url": reverse(source, "contribution-list"),
            }
            for person, level, source in self.access.people_above()
            if person.pk not in credited
        ]

    @property
    def can_change(self):
        """Whether the viewer may change the record's contributors."""
        return self.can_see_levels

    def region_context(self, toast=None):
        """Return everything the region draws."""
        people = self.people()
        return {
            "base_object": self.base_object,
            "kind": self.access.kind,
            "people_rows": people,
            "organization_rows": self.organizations(people),
            "access_from_above": self.access_from_above(people)
            if self.can_change
            else [],
            "can_change": self.can_change,
            "urls": {
                "add_person": self.record_url("contribution-list-add-person"),
                "add_organization": self.record_url(
                    "contribution-list-add-organization"
                ),
                "reorder": self.record_url("contribution-list-reorder"),
            },
            "toast": toast,
            "sheet_id": SHEET_ID,
        }

    # ------------------------------------------------------------------ answering

    def region_response(self, toast=None, close_sheet=True):
        """Answer with the region drawn again, and close the open sheet.

        Args:
            toast: The notice to show, with its ``text``, optionally ``tone`` and an
                undo.
            close_sheet: Whether the answer tells the page to close the open sheet.
        """
        html = render_to_string(
            self.region_template, self.region_context(toast), request=self.request
        )
        response = HttpResponse(html)
        if close_sheet:
            response["HX-Trigger"] = json.dumps({"contrib:done": True})
        return response

    def refusal(self, error):
        """Answer a refused change with the region and the reason."""
        return self.region_response(
            toast={"text": " ".join(error.messages), "tone": "error"}
        )

    def sheet_response(self, template, context, title, lead=""):
        """Answer with a sheet for the sheet slot, and open it."""
        context = {
            **context,
            "sheet_id": SHEET_ID,
            "sheet_title": title,
            "sheet_lead": lead,
            "base_object": self.base_object,
            "kind": self.access.kind,
            "foot": self.foot(context),
        }
        response = HttpResponse(
            render_to_string(template, context, request=self.request)
        )
        response["HX-Trigger-After-Settle"] = json.dumps(
            {"mvp-sheet-open": {"id": SHEET_ID}}
        )
        return response

    def step_response(self, template, context, chrome=True):
        """Answer with the next step of the open sheet: its body, and with ``chrome``
        its foot.

        Args:
            template: The step's template.
            context: What it draws.
            chrome: Whether the answer also replaces the sheet's foot and head, out of
                band. A list of search results answers without it.
        """
        context = {
            **context,
            "sheet_id": SHEET_ID,
            "base_object": self.base_object,
            "kind": self.access.kind,
        }
        html = render_to_string(template, context, request=self.request)
        if chrome:
            html += render_to_string(
                "cotton/contributor/tab/foot.html",
                {"foot": self.foot(context), "oob": True},
                request=self.request,
            )
            if context.get("head"):
                html += render_to_string(
                    "contributors/tab/head.html", context, request=self.request
                )
        return HttpResponse(html)

    @staticmethod
    def head_for(contributor, new_name=None, organization=False):
        """Return the sheet's title on a step about one person or organization.

        Args:
            contributor: The person or organization, or None for one not yet in the
                portal.
            new_name: For a person not yet in the portal, their ``first_name`` and
                ``last_name``; for an organization, its name.
            organization: Whether a contributor not yet in the portal is an
                organization.
        """
        if contributor is not None:
            return {"contributor": contributor, "title": contributor.name}
        if organization:
            return {
                "title": new_name,
                "initials": Organization(name=new_name).get_initials(),
                "organization": True,
            }
        first, last = new_name.get("first_name", ""), new_name.get("last_name", "")
        return {
            "title": f"{first} {last}".strip(),
            "initials": f"{first[:1]}{last[:1]}".upper(),
        }

    @staticmethod
    def foot(context):
        """Return the sheet foot's buttons, from the step's context."""
        return {
            "submit": context.get("submit_text", ""),
            "icon": context.get("submit_icon", ""),
            "form": context.get("submit_form", ""),
            "back": context.get("back_url", ""),
            "next": context.get("next_url", ""),
            "next_text": context.get("next_text", ""),
            "next_include": context.get("next_include", ""),
            "arrow": context.get("submit_arrow", False),
        }

    def search_registry(self, call, *args, **kwargs):
        """Ask a registry for the signed-in person, counting it against their limit.

        Args:
            call: The registry method to call.

        Returns:
            ``(answer, problem)``: the answer, or None and ``"limited"`` when the person
            has searched too often, or ``"unavailable"`` when the registry could not be
            asked.
        """
        try:
            count_search(self.request.user)
            return call(*args, **kwargs), ""
        except SearchLimitReached:
            return None, "limited"
        except RegistryUnavailable:
            return None, "unavailable"

    def registry_refusal(self, registry, problem):
        """Answer a change that could not be made because a registry could
        not be asked.

        Args:
            registry: The registry's name, shown in the message.
            problem: ``limited`` when the user searched too fast, otherwise the
                registry could not be reached.
        """
        text = _("You are searching too fast. Wait a moment and try again.")
        if problem != "limited":
            text = _("%(registry)s could not be reached. Try again.") % {
                "registry": registry
            }
        return self.region_response(toast={"text": text, "tone": "error"})

    # ------------------------------------------------------------------ the roles field

    def offered_roles(self):
        """Return the roles this kind of record offers."""
        return Crediting(self.base_object).offered_roles()

    def locked_roles(self, held):
        """Return the pks of the roles ticked and not removable.

        Project Member is kept for anyone being added and for anyone who holds it.

        Args:
            held: The pks of the roles the contributor holds now, or None when they are
                being added.
        """
        member = role_by_slug(MEMBER)
        if member is None or member.pk not in {r.pk for r in self.offered_roles()}:
            return set()
        return {member.pk} if held is None or member.pk in held else set()

    def chosen_roles(self, held):
        """Return the roles ticked in the posted form, limited to the offered ones.

        Args:
            held: The pks of the roles the contributor holds now, or None when they are
                being added.
        """
        offered = {str(role.pk): role for role in self.offered_roles()}
        chosen = [
            offered[pk] for pk in self.request.POST.getlist("roles") if pk in offered
        ]
        for pk in self.locked_roles(held):
            if str(pk) in offered and offered[str(pk)] not in chosen:
                chosen.append(offered[str(pk)])
        return chosen

    @staticmethod
    def held_by(credit):
        """Return the pks of the roles a contribution holds, or None when it counts as
        new.

        An organization listed with no roles of its own is there as someone's
        affiliation and shows Project Member, so it is treated as just added.

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
        """Return the roles to offer, the ones ticked and the ones that can't be
        unticked.

        Args:
            credit: The contribution being edited, or None when the contributor is being
                added.
        """
        held = self.held_by(credit)
        locked = self.locked_roles(held)
        return {
            "roles": self.offered_roles(),
            "held_roles": (held or set()) | locked,
            "locked_roles": locked,
            "roles_docs_url": ROLES_DOCS_URL,
        }


def affiliation_choices(person):
    """Return the organizations to credit a person from: theirs first, then every other
    one.

    Args:
        person: The person, or None for someone not yet in the portal.

    Returns:
        ``(theirs, others)``: ``theirs`` is a list of ``(organization, current)`` for
        the organizations on the person's profile, current ones first, and ``others``
        every other organization by name.
    """
    theirs = []
    if person is not None:
        affiliations = person.affiliations.select_related("organization").order_by(
            "-is_primary", "organization__name"
        )
        known = set()
        for affiliation in affiliations:
            if affiliation.organization_id not in known:
                known.add(affiliation.organization_id)
                theirs.append((affiliation.organization, not affiliation.end_date))
        theirs.sort(key=lambda pair: (not pair[1], pair[0].name))
    others = Organization.objects.exclude(pk__in={org.pk for org, is_current in theirs})
    return theirs, others.order_by("name")

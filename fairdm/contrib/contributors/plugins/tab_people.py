"""Adding a person on a record's Contributors tab, in steps drawn in one sheet.

The steps are: find someone in the portal or by ORCID iD, then (for someone not in the portal)
who ORCID has under their name, the name checked, their affiliation on the record, and their
roles. Each step is a GET that answers with the next step, carrying what the earlier ones
learned in its address, and the last step posts.
"""

from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from fairdm.core.vocabularies import ORCID, ROR

from ..models import Contribution, ContributorIdentifier, Organization, Person
from ..services.crediting import Crediting
from ..services.registries import Orcid, RegistryUnavailable, Ror
from .tab_base import (
    ContributorsBase,
    affiliation_choices,
    first_name_of,
    initials_of,
)

PORTAL_RESULTS = 12
"""The most people or organizations a search of the portal lists."""


def split_name(typed):
    """Return given names and family name from a name typed whole: the last word is the family name."""
    words = typed.split()
    return {"first_name": " ".join(words[:-1]), "last_name": words[-1] if words else ""}


def portal_organization(entry):
    """Return the portal's organization for one picked from ORCID or ROR, making it if need be.

    It is found by its ROR ID, then by its name, and made only when neither matches.

    Args:
        entry: The organization's ``name`` and ``ror`` (an empty string when it has none).

    Raises:
        RegistryUnavailable: ROR could not be asked for an organization to make.
    """
    record = Ror().fetch(entry["ror"]) if entry["ror"] else None
    held = (Ror().known(record) if record else None) or Organization.objects.filter(
        name__iexact=entry["name"]
    ).first()
    if held:
        return held
    return (
        Ror().profile(record)
        if record
        else Organization.objects.create(name=entry["name"])
    )


class AddPerson(ContributorsBase):
    """The Add person sheet: find someone in the portal, or start someone new from the search."""

    name = "add-person"
    url_path = "add-person"

    def get(self, request, *args, **kwargs):
        """Open the sheet at its search step, answer a search, or return to the search."""
        query = request.GET.get("q", "").strip()
        listed = Contribution.objects.for_entity(self.base_object).values_list(
            "contributor_id", flat=True
        )
        found = Person.objects.real().exclude(pk__in=listed).exclude(is_superuser=True)
        identifier = Orcid().identifier_in(query)
        holders = ContributorIdentifier.objects.filter(
            type_id=ORCID, value=identifier
        ).values("related_id")
        if identifier:
            found = found.filter(pk__in=holders)
        elif query:
            found = found.filter(
                Q(name__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        found = list(found.order_by("name")[:PORTAL_RESULTS])
        context = {
            "found": found,
            "query": query,
            "step_url": self.record_url("contribution-list-add-person-step"),
        }
        if identifier and not found:
            context.update(self.unknown_identifier(identifier, holders))
        elif len(query) > 1 and not any(p.name.lower() == query.lower() for p in found):
            typed = split_name(query)
            context["new_row"] = {
                "name": query,
                "initials": f"{typed['first_name'][:1]}{typed['last_name'][:1]}".upper(),
                "url": AddPersonStep.step_url(self, typed, via="search"),
            }
        title = _("Add a person to this %(kind)s") % {"kind": self.access.kind}
        if request.headers.get("HX-Target") == "contrib-person-results":
            return self.step_response(
                "cotton/contributor/tab/person_results.html", context, chrome=False
            )
        if request.GET.get("back"):
            context["head"] = {"title": title}
            return self.step_response(
                "cotton/contributor/tab/person_search.html", context
            )
        return self.sheet_response(
            "contributors/tab/sheets/add_person.html", context, title
        )

    def unknown_identifier(self, identifier, holders):
        """Return what the results say about an ORCID iD nobody in the portal holds.

        Args:
            identifier: The bare ORCID iD typed.
            holders: A queryset of the ids of the people holding it in the portal.

        Returns:
            Context for the results: ``identifier``, and either ``listed_already`` (the person
            holding it is on the record already), a ``new_row`` for their public ORCID record,
            or ``problem`` when ORCID could not be asked.
        """
        context = {"identifier": identifier}
        on_record = Contribution.objects.for_entity(self.base_object)
        if on_record.filter(contributor_id__in=holders).exists():
            context["listed_already"] = True
            return context
        record, context["problem"] = self.search_registry(Orcid().fetch, identifier)
        if record:
            context["new_row"] = {
                "name": record["name"],
                "initials": initials_of(record),
                "detail": record["detail"],
                "orcid": record["id"],
                "url": AddPersonStep.step_url(
                    self, {}, orcid=record["id"], via="search"
                ),
            }
        return context


class AddPersonStep(ContributorsBase):
    """The steps of Add person after the search, and the post that adds the person."""

    name = "add-person-step"
    url_path = "add-person/details"

    AFFILIATION_KEYS = ("stage", "aq", "org", "ror", "org_name", "none", "from")
    """What the affiliation steps add to the address: which of them it is (``stage``), the name
    searched for (``aq``), and the organization picked: one in the portal (``org``), one from
    ROR or an ORCID record (``ror`` with its ``org_name``), one by name alone (``org_name``), or
    none (``none``)."""

    def step_url(self, new_name, **extra):
        """Return the address of this step for someone new, carrying what is known of them."""
        query = {key: value for key, value in new_name.items() if value}
        return (
            self.record_url("contribution-list-add-person-step")
            + "?"
            + urlencode({**query, **extra})
        )

    def search_url(self, **query):
        """Return the address that draws the person search again."""
        return (
            self.record_url("contribution-list-add-person")
            + "?"
            + urlencode({"back": 1, **query})
        )

    def get(self, request, *args, **kwargs):
        """Draw the next step for a chosen person, or for someone new.

        Someone new is given by ORCID iD, or by name. An iD goes straight to their affiliation,
        offering the affiliations on their ORCID record. A name first shows the people ORCID
        finds by that name ("Do you mean?"), which a name and an affiliation narrow (``find``
        and ``at``), to pick from or to skip. Skipping (``confirm``) asks for the given names and
        family name, guessed from the name, before the affiliation. A name or an iD typed in the
        search (``via=search``) comes straight here, and Back returns to the search.
        """
        via = request.GET.get("via", "")
        narrowed = {
            key: request.GET[key].strip()
            for key in ("find", "at")
            if request.GET.get(key, "").strip()
        }
        if request.GET.get("person"):
            person = get_object_or_404(Person, uuid=request.GET["person"])
            back = self.search_url()
            return self.affiliation_flow(person, None, back)
        typed = {
            "first_name": request.GET.get("first_name", "").strip(),
            "last_name": request.GET.get("last_name", "").strip(),
        }
        orcid_id = request.GET.get("orcid", "").strip()
        if orcid_id:
            return self.orcid_person(orcid_id, typed, via, narrowed)
        if request.GET.get("confirm"):
            return self.confirm_name_step(
                typed, narrowed, via, request.GET.get("given")
            )
        if request.GET.get("skip"):
            back = self.step_url(typed, via=via, confirm=1, given=1, **narrowed)
            return self.affiliation_flow(None, typed, back)
        return self.orcid_matches_step(
            typed, via, narrowed, only_list=bool(request.GET.get("list"))
        )

    def orcid_person(self, orcid_id, typed, via, narrowed):
        """Continue with someone picked from ORCID: the person the portal holds, or a new one."""
        record, problem = self.search_registry(Orcid().fetch, orcid_id)
        if record is None:
            return self.orcid_matches_step(
                typed, via, narrowed, problem=problem or "missing"
            )
        person = Orcid().known(record)
        new_name = None
        if person is None:
            new_name = {
                "first_name": record["given"],
                "last_name": record["family"],
                "orcid": record["id"],
            }
        if self.request.GET.get("matches"):
            back = self.step_url(typed, via=via, **narrowed)
        else:
            back = self.search_url(q=orcid_id)
        return self.affiliation_flow(person, new_name, back)

    # ------------------------------------------------------------------ affiliation

    def affiliation_flow(self, person, new_name, back_url):
        """Draw the steps that find the person's affiliation on this record, then their roles.

        The first step lists the organizations on their ORCID record or their profile, then the
        portal's, filtered by a search. A name that isn't in the portal is a New row, which
        leads to what ROR has under that name ("Do you mean?"), to pick from or to add by name
        alone. Picking any of them leads to the roles step, with the organization shown as their
        affiliation.
        """
        request = self.request
        carried = {
            key: value
            for key, value in request.GET.items()
            if key not in self.AFFILIATION_KEYS
        }
        here = (
            self.record_url("contribution-list-add-person-step")
            + "?"
            + urlencode(carried)
        )
        stage = request.GET.get("stage", "")
        query = request.GET.get("aq", "").strip()
        head = self.head_for(person, new_name)
        if stage == "roles":
            return self.person_roles_step(person, new_name, here, head)
        if stage == "ror":
            return self.ror_matches_step(here, query)
        context = self.affiliation_results(person, new_name, here, query)
        if stage == "results":
            return self.step_response(
                "cotton/contributor/tab/affiliation_results.html",
                context,
                chrome=False,
            )
        context.update(
            {
                "here": here,
                "next_url": here + "&" + urlencode({"stage": "roles", "none": 1}),
                "next_text": _("No affiliation"),
                "back_url": back_url,
                "head": head,
            }
        )
        return self.step_response(
            "contributors/tab/sheets/affiliation_search.html", context
        )

    def ror_matches_step(self, here, query):
        """Draw what ROR finds under the name typed, to pick from or to skip."""
        found, problem = self.search_registry(Ror().search, query)
        results = (found or {"results": []})["results"]
        return self.step_response(
            "contributors/tab/sheets/ror_matches.html",
            {
                "found": [
                    {**record, "initials": initials_of(record, True)}
                    for record in results
                ],
                "problem": problem,
                "pick_url": here
                + "&"
                + urlencode({"stage": "roles", "from": "ror", "aq": query}),
                "next_url": here
                + "&"
                + urlencode({"stage": "roles", "org_name": query, "aq": query}),
                "next_text": _("Add by name alone"),
                "back_url": here + "&" + urlencode({"aq": query}),
                "head": {
                    "title": _("Do you mean?"),
                    "lead": _("Powered by the Research Organization Registry (ROR)"),
                },
            },
        )

    def affiliation_results(self, person, new_name, here, query):
        """Return the organizations the affiliation step lists for a search, in their groups.

        Returns:
            The context of ``affiliation_results.html``: ``orcid`` (the organizations on the
            person's ORCID record), ``theirs`` (those on their profile), ``others`` (the
            portal's, up to twelve) and ``new_row``, each with the address of the roles step it
            leads to, and ``problem`` when ORCID could not be asked.
        """
        needle = query.lower()
        orcid, problem = [], ""
        if new_name and new_name.get("orcid") and person is None:
            entries, problem = self.search_registry(
                Orcid().affiliations, new_name["orcid"]
            )
            for entry in entries or []:
                if needle in entry["name"].lower():
                    picked = {
                        "stage": "roles",
                        "from": "orcid",
                        "org_name": entry["name"],
                        "aq": query,
                    }
                    if entry["ror"]:
                        picked["ror"] = entry["ror"]
                    orcid.append(
                        {
                            **entry,
                            "initials": Organization(name=entry["name"]).get_initials()[
                                :3
                            ],
                            "url": here + "&" + urlencode(picked),
                        }
                    )
        theirs, others = affiliation_choices(person)
        theirs = [
            (org, current) for org, current in theirs if needle in org.name.lower()
        ]
        named = {entry["name"].lower() for entry in orcid}
        held_rors = [entry["ror"] for entry in orcid if entry["ror"]]
        held_rors += [f"https://ror.org/{ror}" for ror in held_rors]
        if held_rors:
            others = others.exclude(
                identifiers__type_id=ROR, identifiers__value__in=held_rors
            )
        if query:
            others = others.filter(name__icontains=query)
        others = [
            org for org in others[: PORTAL_RESULTS * 4] if org.name.lower() not in named
        ]
        others = others[:PORTAL_RESULTS]
        shown = [e["name"] for e in orcid] + [pair[0].name for pair in theirs]
        shown += [org.name for org in others]
        context = {
            "query": query,
            "problem": problem,
            "orcid": orcid,
            "theirs": [
                (org, current, self.pick_url(here, org, query))
                for org, current in theirs
            ],
            "others": [(org, self.pick_url(here, org, query)) for org in others],
        }
        is_new = len(query) > 1 and not any(n.lower() == needle for n in shown)
        if is_new and not Organization.objects.filter(name__iexact=query).exists():
            context["new_row"] = {
                "name": query,
                "initials": Organization(name=query).get_initials()[:3],
                "organization": True,
                "url": here + "&" + urlencode({"stage": "ror", "aq": query}),
            }
        return context

    @staticmethod
    def pick_url(here, organization, query):
        """Return the address of the roles step for an organization of the portal."""
        return (
            here
            + "&"
            + urlencode({"stage": "roles", "org": organization.uuid, "aq": query})
        )

    def picked_affiliation(self, data):
        """Return the organization picked in the affiliation steps, without making it.

        Args:
            data: The step's query or the posted form, holding ``org``, ``ror`` and ``org_name``.

        Returns:
            ``(organization, entry)``: the portal's organization, or None, and for one not in
            the portal yet ``entry``, its ``name`` and ``ror``, that ``portal_organization``
            makes it from. Both None for no affiliation.
        """
        if data.get("org"):
            return Organization.objects.filter(uuid=data["org"]).first(), None
        ror, name = data.get("ror", "").strip(), data.get("org_name", "").strip()
        if ror:
            record = self.search_registry(Ror().fetch, ror)[0]
            if record:
                held = (
                    Ror().known(record)
                    or Organization.objects.filter(
                        name__iexact=name or record["name"]
                    ).first()
                )
                entry = {"name": name or record["name"], "ror": record["id"]}
                return held, None if held else entry
        if name:
            held = Organization.objects.filter(name__iexact=name).first()
            return held, None if held else {"name": name, "ror": ""}
        return None, None

    def person_roles_step(self, person, new_name, here, head):
        """Draw the step that picks the person's roles, the affiliation chosen under their name."""
        organization, entry = self.picked_affiliation(self.request.GET)
        query = self.request.GET.get("aq", "")
        if self.request.GET.get("from") == "ror":
            back = here + "&" + urlencode({"stage": "ror", "aq": query})
        else:
            back = here + "&" + urlencode({"aq": query}) if query else here
        lead = organization.name if organization else (entry or {}).get("name", "")
        context = {
            "person": person,
            "credit": None,
            "new_name": new_name or {},
            **self.role_context(None),
            "affiliation": organization,
            "new_affiliation": entry,
            "action": self.record_url("contribution-list-add-person-step"),
            "head": {**head, "lead": lead, "lead_new": bool(entry)},
            "back_url": back,
            "submit_text": _("Add %(name)s")
            % {"name": first_name_of(person, new_name)},
            "submit_icon": "add",
        }
        return self.step_response("cotton/contributor/tab/person_roles.html", context)

    # ------------------------------------------------------------------ names

    def orcid_matches_step(self, typed, via, narrowed, only_list=False, problem=""):
        """Draw who ORCID finds under a name, to pick from or skip.

        Args:
            typed: The names first given, which Back to the search returns with.
            via: ``"search"`` when the names were typed in the search, where Back then returns.
            narrowed: The name (``find``) and affiliation (``at``) the user narrowed the search
                to, the names first given when there are none.
            only_list: Whether to answer with the list of matches alone, as the narrowing
                fields ask for while the user types.
            problem: What went wrong asking ORCID for a person picked from the list.
        """
        name = f"{typed['first_name']} {typed['last_name']}".strip()
        find, at = narrowed.get("find", name), narrowed.get("at", "")
        found = None
        if find and not problem:
            found, problem = self.search_registry(Orcid().search, find, affiliation=at)
        context = {
            "found": (found or {"results": []})["results"],
            "problem": problem,
            "new_name": typed,
            "find": find,
            "at": at,
            "list_url": self.step_url(typed, via=via, list=1),
            "pick_url": self.step_url(
                typed,
                via=via,
                matches=1,
                **{k: v for k, v in (("find", find), ("at", at)) if v},
            ),
            "next_url": self.step_url(typed, confirm=1, via=via),
            "next_include": "#contrib-narrow",
            "next_text": _("Add by name alone"),
            "back_url": self.search_url(q=find),
            "head": {"title": _("Do you mean?"), "lead": _("Powered by ORCID")},
        }
        template = "contributors/tab/sheets/orcid_matches.html"
        if only_list:
            template = "cotton/contributor/tab/orcid_match_list.html"
        return self.step_response(template, context, chrome=not only_list)

    def confirm_name_step(self, typed, narrowed, via, given=False):
        """Draw the step that asks for someone's given names and family name.

        A name can't be split into the two reliably, so the step guesses (the last word is the
        family name) and the user corrects it. It follows Add by name alone, guessing from the
        name last searched. Back from the affiliation step returns to it with the names given.
        """
        name = f"{typed['first_name']} {typed['last_name']}".strip()
        names = typed if given else split_name(narrowed.get("find") or name)
        return self.step_response(
            "contributors/tab/sheets/confirm_name.html",
            {
                "names": names,
                "carried": {"via": via, "skip": 1, **narrowed},
                "step_url": self.record_url("contribution-list-add-person-step"),
                "submit_text": _("Continue"),
                "submit_arrow": True,
                "submit_form": "contrib-name-form",
                "back_url": self.step_url(typed, via=via, **narrowed),
                "head": {"title": _("Check their name")},
            },
        )

    # ------------------------------------------------------------------ adding

    def post(self, request, *args, **kwargs):
        """Add the person with their affiliation and roles."""
        orcid_id = request.POST.get("orcid", "").strip()
        if request.POST.get("person"):
            person = get_object_or_404(Person, uuid=request.POST["person"])
        elif orcid_id:
            record, problem = self.search_registry(Orcid().fetch, orcid_id)
            if record is None:
                return self.registry_refusal("ORCID", problem)
            person = Orcid().profile(record)
        else:
            last = request.POST.get("last_name", "").strip()
            if not last:
                return HttpResponseBadRequest()
            person = Person.objects.create_unclaimed(
                request.POST.get("first_name", "").strip(), last
            )
        crediting = Crediting(self.base_object)
        try:
            with transaction.atomic():
                organization, entry = self.picked_affiliation(request.POST)
                if entry:
                    organization = portal_organization(entry)
                credit = crediting.add(person, organization=organization)
                crediting.update(credit, roles=self.chosen_roles(held=None))
        except ValidationError as error:
            return self.refusal(error)
        except RegistryUnavailable:
            return self.registry_refusal("ROR", "unavailable")
        return self.region_response(
            toast={"text": _("%(name)s added.") % {"name": person.name}}
        )

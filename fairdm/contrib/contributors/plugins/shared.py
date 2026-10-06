"""The Contributors tab of a project, dataset, sample or measurement.

Prototype for ``specs/022-record-contributors-and-access``: the screens are the deliverable and
the code behind them is to be rebuilt. ``specs/022-record-contributors-and-access/sketch.md``
lists what is faked.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from guardian.utils import get_anonymous_user
from research_vocabs.models import Concept

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView

from ..access import RecordAccess
from ..choices import ContributionLevel
from ..models import Contribution, Contributor, Organization, Person
from ..services.crediting import UNCHANGED, Crediting


def level_choices(record, floor=None):
    """Return the three levels as the edit page draws them, marking those below ``floor``."""
    kind = RecordAccess(record).kind
    hints = {
        ContributionLevel.VIEW: _("Open this %(kind)s while it is private.")
        % {"kind": kind},
        ContributionLevel.EDIT: _("Also change this %(kind)s and the data in it.")
        % {"kind": kind},
        ContributionLevel.MANAGE: _(
            "Also change its contributors and their access, change its visibility and delete it."
        ),
    }
    return [
        {
            "value": level.value,
            "label": level.label,
            "hint": hints[level],
            "disabled": floor is not None and level < floor,
        }
        for level in ContributionLevel
    ]


class AffiliationChoice(forms.Form):
    """The choice of which organization a person is credited from on one record.

    The person's own affiliations are offered, the primary one selected to begin with. Any other
    organization can be named, and none can be chosen. The two fields keep the names the
    ``c-contribution.affiliation`` component draws.

    Args:
        person: The person, when they are already in the portal.
        credit: The person's contribution on the record, when it is being edited.
        suggested: An organization name to offer, such as an employer from ORCID.
    """

    affiliation = forms.CharField(required=False)
    affiliation_name = forms.CharField(
        required=False, max_length=Contributor._meta.get_field("name").max_length
    )

    def __init__(self, *args, person=None, credit=None, suggested="", **kwargs):
        super().__init__(*args, **kwargs)
        self.credit = credit
        self.suggested = suggested
        self.options = self.held_by(person)

    @staticmethod
    def held_by(person):
        """List a person's affiliations as options, the current primary first.

        Args:
            person: The person, or None.

        Returns:
            One ``{"value", "organization", "note"}`` dictionary per affiliation.
        """
        if person is None:
            return []
        held = sorted(
            person.affiliations.select_related("organization"),
            key=lambda a: (not a.is_primary, a.end_date is not None),
        )
        options = []
        for affiliation in held:
            if affiliation.is_primary:
                note = _("Their primary affiliation today")
            elif affiliation.end_date:
                note = _("Earlier, until %(when)s") % {"when": affiliation.end_date}
            else:
                note = _("Also current")
            options.append(
                {
                    "value": f"org:{affiliation.organization_id}",
                    "organization": affiliation.organization,
                    "note": note,
                }
            )
        return options

    def clean_affiliation(self):
        """Accept one of the person's affiliations, another organization, or none."""
        value = self.cleaned_data["affiliation"] or "none"
        if value not in {option["value"] for option in self.options} | {
            "other",
            "none",
        }:
            raise ValidationError(
                _("Choose one of the organizations offered."), code="invalid_choice"
            )
        return value

    def clean(self):
        """Refuse another organization chosen without a name."""
        cleaned = super().clean()
        if cleaned.get("affiliation") == "other" and not cleaned.get(
            "affiliation_name"
        ):
            self.add_error(
                "affiliation_name",
                ValidationError(
                    _("Enter the organization's name, or choose another answer."),
                    code="required",
                ),
            )
        return cleaned

    @property
    def problem(self):
        """The first message about what is wrong with the choice, or None."""
        for errors in self.errors.values():
            return errors[0]
        return None

    def organization(self):
        """Return the organization chosen, making it when it is named and not in the portal.

        Call it inside the transaction that saves the credit, so that an organization made for
        a save that is then refused is not kept.

        Returns:
            The organization, or None when none was chosen.
        """
        value = self.cleaned_data["affiliation"]
        if value.startswith("org:"):
            return Organization.objects.get(pk=value[4:])
        if value != "other":
            return None
        name = self.cleaned_data["affiliation_name"]
        match = Organization.objects.filter(name__iexact=name).first()
        return match or Organization.objects.create(name=name)

    def choice(self):
        """Shape the choice for the component that draws it.

        Returns:
            The options, which one is selected, the name typed for another organization, and
            every organization name for the suggestions. What a refused form held is kept.
        """
        values = {option["value"] for option in self.options}
        other_name = self.suggested
        if self.is_bound:
            selected = self.data.get("affiliation") or "none"
            other_name = self.data.get("affiliation_name", "")
        elif self.credit is not None:
            current = self.credit.affiliation
            selected = f"org:{current.pk}" if current else "none"
            if current and selected not in values:
                selected, other_name = "other", current.name
        elif self.suggested:
            selected = "other"
        elif self.options:
            selected = self.options[0]["value"]
        else:
            selected = "none"
        return {
            "options": self.options,
            "selected": selected,
            "other_name": other_name,
            "organizations": Organization.objects.order_by("name").values_list(
                "name", flat=True
            ),
        }


class ContributionPage(Plugin, FairDMTemplateView):
    """What every page of the tab shares: the record, its kind and who may manage it."""

    manager_only = False

    @cached_property
    def access(self):
        """What people may do on this record."""
        return RecordAccess(self.base_object)

    def dispatch(self, request, *args, **kwargs):
        """Refuse a page for changing contributors to anyone who may not manage the record."""
        if self.manager_only and not self.access.can_manage(request.user):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    @property
    def list_url(self):
        """The address of the record's Contributors tab."""
        return reverse(self.base_object, "contribution-list")

    def get_contribution(self):
        """Return the contribution named in the address, on this record only."""
        return get_object_or_404(
            self.base_object.contributors.select_related("contributor"),
            pk=self.kwargs["pk"],
        )

    def describe(self, contribution):
        """Work out everything the pages say about one contributor on this record."""
        contributor = contribution.contributor.get_real_instance()
        is_person = not contributor.is_organization
        own = above = source = effective = None
        if is_person:
            own = self.access.own_level(contributor)
            above, source = self.access.level_from_above(contributor)
            effective = max((level for level in (own, above) if level), default=None)
        return {
            "contribution": contribution,
            "contributor": contributor,
            "is_person": is_person,
            "own": own,
            "above": above,
            "source": source,
            "source_kind": RecordAccess(source).kind if source else "",
            "effective": effective,
            "manages": effective == ContributionLevel.MANAGE,
            "label": effective.label if effective else "",
            "from_above": bool(above and above == effective and above != own),
            "has_account": is_person and contributor.can_sign_in(),
            "affiliation": contribution.affiliation if is_person else None,
            "attached": [] if is_person else self.credited_from.get(contributor.pk, []),
            "removable": is_person or contributor.pk not in self.credited_from,
        }

    @cached_property
    def credited_from(self):
        """Map each organization on the record to the people credited here from it."""
        return Crediting(self.base_object).credited_from()

    def is_last_manager(self, contributor):
        """Say whether nobody else counts as able to manage the record."""
        return self.access.managers() == {contributor.pk}

    def get_context_data(self, **kwargs):
        """Add the record's kind, the tab's address and whether the viewer may manage."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        context.update(
            record=record,
            kind=RecordAccess(record).kind,
            list_url=self.list_url,
            can_manage=self.access.can_manage(self.request.user),
        )
        return context


#: Stand-ins for what an ORCID search would return. Nothing is fetched.
ORCID_RECORDS = [
    {
        "id": "0000-0002-1825-0097",
        "shown_id": "0000-0002-1825-0097",
        "name": "Josiah Carberry",
        "given": "Josiah",
        "family": "Carberry",
        "employer": "Brown University",
        "detail": "Brown University, Providence, United States",
    },
    {
        "id": "0000-0001-5109-3700",
        "shown_id": "0000-0001-5109-3700",
        "name": "Sofia Maria Garcia",
        "given": "Sofia Maria",
        "family": "Garcia",
        "employer": "Universidad de Granada",
        "detail": "Universidad de Granada, Spain",
    },
    {
        "id": "0000-0003-2874-1160",
        "shown_id": "0000-0003-2874-1160",
        "name": "Sofia Garcia Hernandez",
        "given": "Sofia",
        "family": "Garcia Hernandez",
        "employer": "GFZ Helmholtz Centre for Geosciences",
        "detail": "GFZ Helmholtz Centre for Geosciences, Potsdam, Germany",
    },
    {
        "id": "0000-0002-9079-593X",
        "shown_id": "0000-0002-9079-593X",
        "name": "Stephen Hawking",
        "given": "Stephen",
        "family": "Hawking",
        "employer": "",
        "detail": "No current employment listed",
    },
]

#: Stand-ins for what a search of the ROR registry would return. Nothing is fetched.
ROR_RECORDS = [
    {
        "id": "https://ror.org/04z8jg394",
        "shown_id": "ror.org/04z8jg394",
        "name": "GFZ Helmholtz Centre for Geosciences",
        "detail": "Facility · Potsdam, Germany",
    },
    {
        "id": "https://ror.org/03bnmw459",
        "shown_id": "ror.org/03bnmw459",
        "name": "University of Potsdam",
        "detail": "Education · Potsdam, Germany",
    },
    {
        "id": "https://ror.org/03e8s1d88",
        "shown_id": "ror.org/03e8s1d88",
        "name": "Potsdam Institute for Climate Impact Research",
        "detail": "Facility · Potsdam, Germany",
    },
    {
        "id": "https://ror.org/02nv7yv05",
        "shown_id": "ror.org/02nv7yv05",
        "name": "Forschungszentrum Jülich",
        "detail": "Facility · Jülich, Germany",
    },
]


class ContributionAdd(ContributionPage):
    """Add a contributor: one already in the portal, one looked up in a registry, or a new one.

    One page holds all three ways in as tabs that switch in the browser. ``via`` in the address
    or the form says which tab to open: ``portal``, ``registry`` or ``new``. The portal search
    reads ``q`` and the registry search reads ``rq``, so each tab keeps its own search.
    """

    manager_only = True
    is_person = True
    results_shown = 20
    registry_delay = 0.8
    registry_records = ()

    @property
    def via(self):
        """Which tab is open."""
        via = self.request.POST.get("via") or self.request.GET.get("via")
        return via if via in ("portal", "registry", "new") else "portal"

    def find_registry_record(self, identifier):
        """Return the registry stand-in with this identifier, or None."""
        return next((r for r in self.registry_records if r["id"] == identifier), None)

    def search_registry(self, term):
        """Pretend to search the registry by name or identifier, taking a moment over it."""
        import time

        time.sleep(self.registry_delay)
        needle = term.lower()
        return [
            r
            for r in self.registry_records
            if needle in r["name"].lower() or needle in r["id"].lower()
        ]

    def search_portal(self, term):
        """Return the people or organizations in the portal whose name matches."""
        model = Person if self.is_person else Organization
        matches = model.objects.filter(name__icontains=term).order_by("name")
        if self.is_person:
            matches = matches.exclude(pk=get_anonymous_user().pk)
        return list(matches[: self.results_shown])

    def get_context_data(self, **kwargs):
        """Add which tab is open, each tab's search and matches, and any chosen record."""
        context = super().get_context_data(**kwargs)
        via = self.via
        listed = set(
            self.base_object.contributors.values_list("contributor_id", flat=True)
        )
        term = self.request.GET.get("q", "").strip()
        registry_term = self.request.GET.get("rq", "").strip()
        refused = kwargs.get("affiliation")
        adding = {
            "is_person": self.is_person,
            "on_portal": via == "portal",
            "on_registry": via == "registry",
            "on_new": via == "new",
            "term": term,
            "registry_term": registry_term,
            "results": [],
            "registry_results": [],
            "picked": None,
            "chosen": None,
            "errors": kwargs.get("errors", {}),
            "values": kwargs.get("values", {}),
            "same_name": kwargs.get("same_name", []),
            "new_affiliation": AffiliationChoice(
                refused if via == "new" else None
            ).choice()
            if self.is_person
            else None,
        }
        picked = self.request.GET.get("person") or (
            self.request.POST.get("contributor") if via == "portal" else None
        )
        if self.is_person and picked and picked.isdigit():
            person = Person.objects.filter(pk=picked).first()
            if person is not None and person.pk not in listed:
                adding["picked"] = {
                    "person": person,
                    "affiliation": AffiliationChoice(
                        refused if via == "portal" else None, person=person
                    ).choice(),
                }
        if term and not adding["picked"]:
            adding["results"] = [
                {"contributor": c, "listed": c.pk in listed}
                for c in self.search_portal(term)
            ]
        chosen = self.request.GET.get("chosen") or self.request.POST.get("registry_id")
        if chosen:
            found = self.find_registry_record(chosen)
            if found is not None:
                adding["chosen"] = {
                    "record": found,
                    "affiliation": AffiliationChoice(
                        refused if via == "registry" else None,
                        suggested=found.get("employer", ""),
                    ).choice()
                    if self.is_person
                    else None,
                }
        elif registry_term:
            adding["registry_results"] = self.search_registry(registry_term)
        context["adding"] = adding
        return context

    def add(self, contributor, choice=None):
        """Add the contributor last, at the view level, and go on to their edit page."""
        record = self.base_object
        organization = None
        try:
            with transaction.atomic():
                organization = choice.organization() if choice is not None else None
                listed = (
                    organization is None
                    or record.contributors.filter(contributor=organization).exists()
                )
                contribution = Crediting(record).add(
                    contributor, organization=organization
                )
        except ValidationError as refused:
            messages.error(self.request, refused.messages[0])
            return redirect(self.request.get_full_path())
        if contributor.is_organization:
            said = _("%(name)s was added. Say what they did here.") % {
                "name": contributor
            }
        else:
            said = _(
                "%(name)s was added. Say what they did, and what they may do here."
            ) % {"name": contributor}
            if not listed:
                said += " " + _("%(organization)s was added to the organizations.") % {
                    "organization": organization
                }
        messages.success(self.request, said)
        return redirect(f"{self.list_url}{contribution.pk}/edit/")

    def create(self, name, given="", family=""):
        """Make a new profile with nothing but a name."""
        if not self.is_person:
            return Organization.objects.get_or_create(name=name)[0]
        person = Person(first_name=given, last_name=family, name=name, email=None)
        person.set_unusable_password()
        person.save()
        return person

    def refuse(self, **kwargs):
        """Draw the page again with what was entered and what is wrong with it."""
        return self.render_to_response(self.get_context_data(**kwargs), status=422)

    def post(self, request, *args, **kwargs):
        """Add someone from the portal, from a registry record, or from the form."""
        portal = None
        if pk := request.POST.get("contributor"):
            portal = get_object_or_404(Contributor, pk=pk).get_real_instance()

        choice = None
        if self.is_person:
            person = portal if isinstance(portal, Person) else None
            choice = AffiliationChoice(request.POST, person=person)
            if not choice.is_valid():
                return self.refuse(
                    affiliation=request.POST, errors={"affiliation": choice.problem}
                )

        if portal is not None:
            return self.add(portal, choice)

        if registry_id := request.POST.get("registry_id"):
            found = self.find_registry_record(registry_id)
            if found is None:
                raise PermissionDenied
            model = Person if self.is_person else Organization
            existing = model.objects.filter(name=found["name"]).first()
            return self.add(
                existing
                or self.create(
                    found["name"], found.get("given", ""), found.get("family", "")
                ),
                choice,
            )

        values = {key: request.POST.get(key, "").strip() for key in request.POST}
        errors = {}
        if self.is_person:
            if not values.get("given"):
                errors["given"] = _("Enter their given name.")
            if not values.get("family"):
                errors["family"] = _("Enter their family name.")
            name = f"{values.get('given', '')} {values.get('family', '')}".strip()
        else:
            if not values.get("name"):
                errors["name"] = _("Enter the organization's name.")
            name = values.get("name", "")
        if errors:
            return self.refuse(errors=errors, values=values)

        model = Person if self.is_person else Organization
        same_name = list(model.objects.filter(name__iexact=name)[:5])
        if same_name and not request.POST.get("confirmed"):
            return self.refuse(values=values, same_name=same_name)
        return self.add(
            self.create(name, values.get("given", ""), values.get("family", "")),
            choice,
        )


class ContributionAddPerson(ContributionAdd):
    """Add a person: from the portal, from ORCID, or entered by hand, with their affiliation."""

    url_path = "add-person"
    template_name = "contributors/plugins/contribution_add_person.html"
    page_title = gettext_lazy("Add a person")
    registry_records = ORCID_RECORDS


class ContributionAddOrganization(ContributionAdd):
    """Add an organization: from the portal, from ROR, or entered by hand."""

    url_path = "add-organization"
    template_name = "contributors/plugins/contribution_add_organization.html"
    page_title = gettext_lazy("Add an organization")
    is_person = False
    registry_records = ROR_RECORDS


class ContributionEdit(ContributionPage):
    """Set a contributor's contribution roles and, for a person, their level."""

    url_path = "<int:pk>/edit"
    manager_only = True
    template_name = "contributors/plugins/contribution_edit.html"
    page_title = gettext_lazy("Edit a contributor")

    def get_context_data(self, **kwargs):
        """Add the contributor, the roles on offer and the levels that may be chosen."""
        context = super().get_context_data(**kwargs)
        entry = self.describe(self.get_contribution())
        choice = kwargs.get("choice")
        if choice is None and entry["is_person"]:
            choice = AffiliationChoice(
                person=entry["contributor"], credit=entry["contribution"]
            )
        held = set(entry["contribution"].roles.values_list("pk", flat=True))
        chosen_roles = kwargs.get("chosen_roles", held)
        context.update(
            entry=entry,
            roles=[
                {"concept": concept, "checked": concept.pk in chosen_roles}
                for concept in Crediting(self.base_object).offered_roles()
            ],
            levels=level_choices(self.base_object, floor=entry["above"]),
            chosen_level=kwargs.get("chosen_level", entry["effective"]),
            errors=kwargs.get("errors", {}),
            affiliation=choice.choice() if choice else None,
        )
        return context

    def post(self, request, *args, **kwargs):
        """Save the roles and the level together, or neither."""
        entry = self.describe(self.get_contribution())
        contribution, contributor = entry["contribution"], entry["contributor"]

        chosen_roles = {int(pk) for pk in request.POST.getlist("roles") if pk.isdigit()}
        level = request.POST.get("level")
        level = ContributionLevel(int(level)) if level in ("1", "2", "3") else None
        errors = {}

        choice = None
        if entry["is_person"]:
            choice = AffiliationChoice(
                request.POST, person=contributor, credit=contribution
            )
            if not choice.is_valid():
                errors["affiliation"] = choice.problem
            if level is None:
                errors["level"] = _("Choose what this person may do.")
            elif entry["above"] and level < entry["above"]:
                errors["level"] = _(
                    "They hold “%(level)s” from the %(kind)s above, and it cannot be lowered here."
                ) % {
                    "level": entry["above"].label,
                    "kind": entry["source_kind"],
                }
            elif (
                entry["own"] == ContributionLevel.MANAGE
                and level != ContributionLevel.MANAGE
                and self.is_last_manager(contributor)
            ):
                errors["level"] = _(
                    "%(name)s is the only person who can manage this %(kind)s. "
                    "Give someone else “Can manage” first."
                ) % {"name": contributor, "kind": self.access.kind}

        crediting = Crediting(self.base_object)
        listed = set(
            self.base_object.contributors.values_list("contributor_id", flat=True)
        )
        organization = UNCHANGED
        with transaction.atomic():
            if choice is not None and choice.is_valid():
                organization = choice.organization()
            try:
                crediting.update(
                    contribution,
                    roles=Concept.objects.filter(pk__in=chosen_roles),
                    organization=organization,
                )
            except ValidationError as refused:
                errors["roles"] = refused.message
            if errors:
                transaction.set_rollback(True)
            elif entry["is_person"]:
                contribution.level = level
                contribution.save(update_fields=["level"])
        if errors:
            context = self.get_context_data(
                errors=errors,
                chosen_roles=chosen_roles,
                chosen_level=level,
                choice=choice,
            )
            return self.render_to_response(context, status=422)

        said = _("%(name)s was saved.") % {"name": contributor}
        if organization not in (UNCHANGED, None) and organization.pk not in listed:
            said += " " + _("%(organization)s was added to the organizations.") % {
                "organization": organization
            }
        messages.success(request, said)
        return redirect(self.list_url)


class ContributionRemove(ContributionPage):
    """Confirm, then remove a contributor and whatever they held through being listed."""

    url_path = "<int:pk>/remove"
    manager_only = True
    template_name = "contributors/plugins/contribution_remove.html"
    page_title = gettext_lazy("Remove a contributor")

    def get_context_data(self, **kwargs):
        """Add the contributor and whether removing them would leave nobody to manage."""
        context = super().get_context_data(**kwargs)
        entry = self.describe(self.get_contribution())
        context.update(
            entry=entry,
            refused=entry["own"] == ContributionLevel.MANAGE
            and self.is_last_manager(entry["contributor"]),
        )
        return context

    def must_stay(self, entry):
        """Say whether removing the contributor would leave nobody to manage the record."""
        return entry["own"] == ContributionLevel.MANAGE and self.is_last_manager(
            entry["contributor"]
        )

    def post(self, request, *args, **kwargs):
        """Remove the contributor unless the service refuses or they are the last manager."""
        record = self.base_object
        entry = self.describe(self.get_contribution())
        contributor = entry["contributor"]
        if self.must_stay(entry):
            return self.render_to_response(self.get_context_data(), status=422)
        try:
            Crediting(record).remove(entry["contribution"])
        except ValidationError:
            return self.render_to_response(self.get_context_data(), status=422)
        messages.success(
            request,
            _("%(name)s was removed from this %(kind)s.")
            % {"name": contributor, "kind": RecordAccess(record).kind},
        )
        return redirect(self.list_url)


class ContributionMove(ContributionPage):
    """Move a contributor one place up or down among the people, or among the organizations."""

    url_path = "<int:pk>/move"
    manager_only = True
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        """Swap the contributor with the neighbour of their own kind."""
        everyone = list(
            self.base_object.contributors.select_related("contributor").order_by(
                "order", "pk"
            )
        )
        for place, contribution in enumerate(everyone):
            contribution.order = place
        moving = next(c for c in everyone if c.pk == self.kwargs["pk"])
        is_organization = moving.contributor.get_real_instance().is_organization
        peers = [
            c
            for c in everyone
            if c.contributor is not None
            and c.contributor.get_real_instance().is_organization == is_organization
        ]
        index = peers.index(moving)
        target = index - 1 if request.POST.get("direction") == "up" else index + 1
        if 0 <= target < len(peers):
            other = peers[target]
            moving.order, other.order = other.order, moving.order
        Contribution.objects.bulk_update(everyone, ["order"])
        return redirect(f"{self.list_url}#contributor-{self.kwargs['pk']}")


@plugins.register(
    Project,
    Dataset,
    Sample,
    Measurement,
    label=gettext_lazy("Contributors"),
    icon="users",
    order=150,
)
class ContributionList(ContributionPage):
    """List a record's people and organizations, each in their own order, with the controls."""

    url_path = "contributors"
    template_name = "contributors/plugins/contribution_list.html"
    page_title = gettext_lazy("Contributors")
    extra_views = [
        ContributionAddPerson,
        ContributionAddOrganization,
        ContributionEdit,
        ContributionRemove,
        ContributionMove,
    ]

    def get_page_subtitle(self):
        """Name the record the contributors belong to."""
        return str(self.base_object)

    def get_context_data(self, **kwargs):
        """Add the people, the organizations and, for a manager, access held from above."""
        context = super().get_context_data(**kwargs)
        record = self.base_object
        term = self.request.GET.get("q", "").strip()
        contributions = [
            c
            for c in record.contributors.select_related("contributor")
            .prefetch_related("roles")
            .order_by("order", "pk")
            if c.contributor is not None
        ]
        entries = [self.describe(contribution) for contribution in contributions]
        groups = {}
        for is_person in (True, False):
            group = [entry for entry in entries if entry["is_person"] == is_person]
            for place, entry in enumerate(group, start=1):
                entry.update(place=place, first=place == 1, last=place == len(group))
            groups[is_person] = {
                "total": len(group),
                "movable": not term and len(group) > 1,
                "rows": [
                    entry
                    for entry in group
                    if not term or term.lower() in entry["contributor"].name.lower()
                ],
            }

        access_from_above = []
        if context["can_manage"]:
            listed = {c.contributor_id for c in contributions}
            access_from_above = [
                {
                    "person": person,
                    "label": level.label,
                    "source": source,
                    "source_kind": RecordAccess(source).kind,
                    "source_url": reverse(source, "contribution-list"),
                }
                for person, level, source in self.access.people_above()
                if person.pk not in listed
            ]
        parents = self.access.above
        context.update(
            people=groups[True],
            organizations=groups[False],
            total=len(entries),
            term=term,
            access_from_above=access_from_above,
            parent=parents[0] if parents else None,
            parent_url=reverse(parents[0], "contribution-list") if parents else "",
            parent_kind=capfirst(RecordAccess(parents[0]).kind) if parents else "",
        )
        return context

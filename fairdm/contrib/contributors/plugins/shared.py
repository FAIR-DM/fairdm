"""The Contributors tab of a project, dataset, sample or measurement, and the pages it leads to.

Every page opens only when the record's overview would, and a page that changes anything asks
whether the viewer can manage the record on every request. The changes themselves are made by
``Crediting``.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django_countries import countries
from guardian.utils import get_anonymous_user
from research_vocabs.models import Concept

from fairdm import plugins
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.contrib.plugins.access import can_open
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView

from ..access import RecordAccess
from ..choices import ContributionLevel
from ..models import Contribution, Contributor, Organization, Person
from ..services.crediting import UNCHANGED, Crediting
from ..services.registries import Orcid, RegistryUnavailable, Ror


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
        elif self.options:
            selected = self.options[0]["value"]
        elif self.suggested:
            selected = "other"
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


class NewPersonForm(forms.Form):
    """A person typed in by hand: two names, and an email address that is kept and never shown.

    The email address is refused when the portal already holds it, without saying whose it is.
    A person whose name a profile already has is offered those profiles first: ``same_name``
    holds them, and the form is not valid until ``confirmed`` is sent.
    """

    given = forms.CharField(
        max_length=Person._meta.get_field("first_name").max_length,
        error_messages={"required": gettext_lazy("Enter their given name.")},
    )
    family = forms.CharField(
        max_length=Person._meta.get_field("last_name").max_length,
        error_messages={"required": gettext_lazy("Enter their family name.")},
    )
    email = forms.EmailField(required=False)
    confirmed = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.same_name = []

    def clean_email(self):
        """Refuse an address the portal holds, in any case, and say nothing of who holds it."""
        email = self.cleaned_data["email"]
        if email and Person.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _("This email address cannot be used."), code="email_in_use"
            )
        return email

    def clean(self):
        """Offer the profiles that share the name, unless the field errors come first."""
        cleaned = super().clean()
        if not self.errors:
            same = Q(name__iexact=self.name()) | Q(
                first_name__iexact=cleaned["given"], last_name__iexact=cleaned["family"]
            )
            self.same_name = list(Person.objects.real().filter(same)[:5])
            if self.same_name and not cleaned["confirmed"]:
                raise ValidationError(
                    _("Someone with this name is already in the portal."),
                    code="same_name",
                )
        return cleaned

    def name(self):
        """Return the full name the two names make."""
        return f"{self.cleaned_data['given']} {self.cleaned_data['family']}"

    def save(self):
        """Make the person, with no account.

        Returns:
            The saved person: active, not claimed, with an unusable password.
        """
        person = Person(
            first_name=self.cleaned_data["given"],
            last_name=self.cleaned_data["family"],
            name=self.name(),
            email=self.cleaned_data["email"] or None,
        )
        person.set_unusable_password()
        person.save()
        return person


class NewOrganizationForm(forms.Form):
    """An organization typed in by hand: a name, and optionally a city, a country and a website.

    An organization is never made when one of that name is in the portal: ``same_name`` holds the
    existing one and the form is not valid. The country is a name or a code from the country
    field's own list.
    """

    name = forms.CharField(
        max_length=Contributor._meta.get_field("name").max_length,
        error_messages={"required": gettext_lazy("Enter the organization's name.")},
    )
    city = forms.CharField(
        required=False, max_length=Organization._meta.get_field("city").max_length
    )
    country = forms.CharField(required=False)
    website = forms.URLField(required=False, assume_scheme="https")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.same_name = []

    def clean_country(self):
        """Resolve a country name or code to the code the field stores."""
        value = self.cleaned_data["country"]
        if not value:
            return ""
        code = value.upper() if value.upper() in countries else countries.by_name(value)
        if not code or not isinstance(code, str):
            raise ValidationError(
                _("Choose a country from the list, by name or by code."),
                code="invalid_country",
            )
        return code

    def clean(self):
        """Offer the organization that already has the name, and make no second."""
        cleaned = super().clean()
        if not self.errors:
            self.same_name = list(
                Organization.objects.filter(name__iexact=cleaned["name"])[:5]
            )
            if self.same_name:
                raise ValidationError(
                    _("An organization with this name is already in the portal."),
                    code="same_name",
                )
        return cleaned

    def save(self):
        """Make the organization.

        Returns:
            The saved organization.
        """
        website = self.cleaned_data["website"]
        return Organization.objects.create(
            name=self.cleaned_data["name"],
            city=self.cleaned_data["city"] or None,
            country=self.cleaned_data["country"] or None,
            links=[website] if website else [],
        )


class ContributionPage(Plugin, FairDMTemplateView):
    """What every page of the tab shares: the record, its kind and who may manage it."""

    manager_only = False

    @cached_property
    def access(self):
        """What people may do on this record."""
        return RecordAccess(self.base_object)

    @property
    def overview(self):
        """The overview plugin of the record's kind, whose check decides who may open the record."""
        from fairdm.core.dataset.plugins import Overview as DatasetOverview
        from fairdm.core.measurement.plugins import Overview as MeasurementOverview
        from fairdm.core.project.plugins import Overview as ProjectOverview
        from fairdm.core.sample.plugins import Overview as SampleOverview

        return {
            Project: ProjectOverview,
            Dataset: DatasetOverview,
            Sample: SampleOverview,
            Measurement: MeasurementOverview,
        }[self.access.model]

    def dispatch(self, request, *args, **kwargs):
        """Answer as the overview does when the record is closed to the viewer, then refuse a page for changing contributors to anyone who may not manage the record."""
        if not can_open(self.overview, request, self.base_object):
            raise Http404(
                _("No %(kind)s matches the given query.") % {"kind": self.access.kind}
            )
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
        if is_person and self.can_see_levels:
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
    def can_see_levels(self):
        """Whether the viewer may be told what people may do: only someone who can manage."""
        return self.access.can_manage(self.request.user)

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


class ContributionAdd(ContributionPage):
    """Add a contributor: one already in the portal, one looked up in a registry, or a new one.

    One page holds all three ways in as tabs that switch in the browser. ``via`` in the address
    or the form says which tab to open: ``portal``, ``registry`` or ``new``. The portal search
    reads ``q`` and the registry search reads ``rq``, so each tab keeps its own search. A
    registry that cannot be reached leaves the other two ways working.

    Attributes:
        is_person: Whether the page adds a person rather than an organization.
        registry_class: ``Orcid`` or ``Ror``.
        form_class: The form behind the by-hand way.
        results_shown: The most matches the portal search lists.
    """

    manager_only = True
    is_person = True
    registry_class = Orcid
    form_class = NewPersonForm
    results_shown = 20

    @property
    def via(self):
        """Which tab is open."""
        via = self.request.POST.get("via") or self.request.GET.get("via")
        return via if via in ("portal", "registry", "new") else "portal"

    @cached_property
    def registry(self):
        """The registry behind the page's second tab."""
        return self.registry_class()

    def search_portal(self, term):
        """Find the people or organizations in the portal whose name matches.

        Args:
            term: Part of a name.

        Returns:
            The matches up to ``results_shown``, and whether there are more.
        """
        model = Person if self.is_person else Organization
        matches = model.objects.filter(name__icontains=term).order_by("name")
        if self.is_person:
            matches = matches.exclude(pk=get_anonymous_user().pk)
        found = list(matches[: self.results_shown + 1])
        return found[: self.results_shown], len(found) > self.results_shown

    def choice_for(self, way, choice, **fresh):
        """Shape the organization choice a tab draws.

        Args:
            way: The tab, ``portal`` or ``new``.
            choice: The bound ``AffiliationChoice`` of a refused request, or None.
            **fresh: Arguments for a new ``AffiliationChoice`` when the request was not refused
                on this tab.

        Returns:
            What ``c-contribution.affiliation`` draws.
        """
        if choice is None or self.via != way:
            choice = AffiliationChoice(**fresh)
        return choice.choice()

    def chosen_record(self, record, choice):
        """Describe the registry record the manager has chosen, with the organization choice.

        Args:
            record: The record fetched from the registry.
            choice: The bound ``AffiliationChoice`` of a refused request, or None.

        Returns:
            What the chosen step of the registry tab draws.
        """
        if not self.is_person:
            return {"record": record, "affiliation": None}
        if choice is None:
            choice = AffiliationChoice(
                person=self.registry.known(record), suggested=record["employer"]
            )
        return {"record": record, "affiliation": choice.choice()}

    def search_registry(self, adding, record, choice):
        """Fill in the registry tab: the chosen record, or the matches of the search.

        A registry that cannot be reached leaves the tab with nothing and says so.

        Args:
            adding: What the page draws, which this adds to.
            record: A record already fetched for a refused request, or None.
            choice: The bound ``AffiliationChoice`` of a refused request, or None.
        """
        chosen = self.request.GET.get("chosen") or self.request.POST.get("registry_id")
        try:
            if chosen and record is None:
                record = self.registry.fetch(chosen)
            if record is not None:
                adding["chosen"] = self.chosen_record(record, choice)
            elif adding["registry_term"]:
                found = self.registry.search(adding["registry_term"])
                adding["registry_results"] = found["results"]
                adding["registry_more"] = found["more"]
        except RegistryUnavailable:
            adding["registry_unavailable"] = True

    def get_context_data(self, **kwargs):
        """Add which tab is open, each tab's search and matches, and any chosen record.

        Args:
            **kwargs: What a refused request hands back: ``form``, ``choice``, ``record``,
                ``errors``, ``values`` and ``registry_unavailable``.
        """
        context = super().get_context_data(**kwargs)
        via = self.via
        form, choice = kwargs.get("form"), kwargs.get("choice")
        listed = set(
            self.base_object.contributors.values_list("contributor_id", flat=True)
        )
        term = self.request.GET.get("q", "").strip()
        adding = {
            "is_person": self.is_person,
            "on_portal": via == "portal",
            "on_registry": via == "registry",
            "on_new": via == "new",
            "term": term,
            "registry_term": self.request.GET.get("rq", "").strip(),
            "results": [],
            "results_more": False,
            "registry_results": [],
            "registry_more": False,
            "registry_unavailable": kwargs.get("registry_unavailable", False),
            "picked": None,
            "chosen": None,
            "errors": kwargs.get("errors", {}),
            "values": kwargs.get("values", {}),
            "form": form,
            "same_name": form.same_name if form is not None else [],
            "new_affiliation": self.choice_for("new", choice)
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
                    "affiliation": self.choice_for("portal", choice, person=person),
                }
        if term and not adding["picked"]:
            matches, adding["results_more"] = self.search_portal(term)
            adding["results"] = [
                {"contributor": c, "listed": c.pk in listed} for c in matches
            ]
        if via == "registry" and not adding["registry_unavailable"]:
            self.search_registry(adding, kwargs.get("record"), choice)
        context["adding"] = adding
        return context

    def add(self, make, choice=None):
        """Add the contributor last, at the view level, and go on to their edit page.

        The contributor is made, the organization made and the credit written in one
        transaction, so a refusal leaves nothing behind.

        Args:
            make: A function that returns the contributor, making them if they are new.
            choice: The valid ``AffiliationChoice`` of a person, or None.
        """
        record = self.base_object
        organization = None
        try:
            with transaction.atomic():
                contributor = make()
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

    def refuse(self, **kwargs):
        """Draw the page again with what was entered and what is wrong with it."""
        return self.render_to_response(self.get_context_data(**kwargs), status=422)

    def add_from_portal(self):
        """Add a contributor who is already in the portal."""
        pk = self.request.POST.get("contributor", "")
        contributor = get_object_or_404(
            Contributor, pk=pk if pk.isdigit() else 0
        ).get_real_instance()
        choice = None
        if self.is_person:
            person = contributor if isinstance(contributor, Person) else None
            choice = AffiliationChoice(self.request.POST, person=person)
            if not choice.is_valid():
                return self.refuse(
                    choice=choice, errors={"affiliation": choice.problem}
                )
        return self.add(lambda: contributor, choice)

    def add_from_registry(self):
        """Add the record the manager chose, fetched again by its identifier.

        Nothing the form carries but the identifier is read. A registry that cannot be reached
        answers 200 with the tab saying so, and nothing is made.
        """
        try:
            record = self.registry.fetch(self.request.POST.get("registry_id", ""))
        except RegistryUnavailable:
            return self.render_to_response(
                self.get_context_data(registry_unavailable=True)
            )
        if record is None:
            messages.error(
                self.request, _("That record could not be found, so nothing was added.")
            )
            return redirect(self.request.get_full_path())
        choice = None
        if self.is_person:
            choice = AffiliationChoice(
                self.request.POST, person=self.registry.known(record)
            )
            if not choice.is_valid():
                return self.refuse(
                    choice=choice,
                    record=record,
                    errors={"affiliation": choice.problem},
                )
        return self.add(lambda: self.registry.profile(record), choice)

    def add_by_hand(self):
        """Make a contributor from the form, or draw the page again with what is wrong."""
        form = self.form_class(self.request.POST)
        choice = AffiliationChoice(self.request.POST) if self.is_person else None
        valid = form.is_valid()
        if choice is not None:
            valid = choice.is_valid() and valid
        if not valid:
            errors = {
                field: messages_[0]
                for field, messages_ in form.errors.items()
                if field != "__all__"
            }
            if choice is not None and choice.problem:
                errors["affiliation"] = choice.problem
            values = {
                key: self.request.POST.get(key, "").strip() for key in form.fields
            }
            return self.refuse(form=form, choice=choice, errors=errors, values=values)
        return self.add(form.save, choice)

    def post(self, request, *args, **kwargs):
        """Add someone from the portal, from a registry record, or from the form."""
        return {
            "registry": self.add_from_registry,
            "new": self.add_by_hand,
        }.get(self.via, self.add_from_portal)()


class ContributionAddPerson(ContributionAdd):
    """Add a person: from the portal, from ORCID, or entered by hand, with their affiliation."""

    url_path = "add-person"
    template_name = "contributors/plugins/contribution_add_person.html"
    page_title = gettext_lazy("Add a person")


class ContributionAddOrganization(ContributionAdd):
    """Add an organization: from the portal, from ROR, or entered by hand."""

    url_path = "add-organization"
    template_name = "contributors/plugins/contribution_add_organization.html"
    page_title = gettext_lazy("Add an organization")
    is_person = False
    registry_class = Ror
    form_class = NewOrganizationForm


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
            elif (
                entry["own"] == ContributionLevel.MANAGE
                and level != ContributionLevel.MANAGE
                and not (entry["above"] and level < entry["above"])
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
                    level=level,
                    organization=organization,
                )
            except ValidationError as refused:
                for refusal in refused.error_list:
                    field = "level" if refusal.code == "below_inherited" else "roles"
                    errors[field] = refusal.message % (refusal.params or {})
            if errors:
                transaction.set_rollback(True)
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

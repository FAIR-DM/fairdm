"""The views of a record's Contributors tab that change one credit or the order."""

from django.core import signing
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from mvp.ordering import InvalidOrder, save_order

from ..access import RecordAccess
from ..choices import ContributionLevel
from ..models import Contribution, Contributor, Organization
from ..services.crediting import UNCHANGED, Crediting
from .shared import level_choices
from .tab_base import ContributorsBase, affiliation_choices

UNDO_SALT = "contributors-undo"
UNDO_SECONDS = 300
"""How long after a removal it can be undone."""


class EditCredit(ContributorsBase):
    """Edit one contributor: a person's affiliation, access level and roles, or an
    organization's roles.
    """

    name = "edit"
    url_path = "<int:pk>/edit"

    def get(self, request, *args, **kwargs):
        """Open the edit sheet."""
        credit = self.get_contribution()
        contributor = credit.contributor.get_real_instance()
        context = {
            "credit": credit,
            **self.role_context(credit),
            "action": self.record_url("contribution-list-edit", pk=credit.pk),
            "submit_text": _("Save"),
        }
        if contributor.is_organization:
            context["organization"] = contributor
            template = "contributors/tab/sheets/edit_organization.html"
        else:
            context.update(self.person_fields(contributor, credit))
            template = "contributors/tab/sheets/edit_person.html"
        return self.sheet_response(template, context, contributor.name)

    def person_fields(self, person, credit):
        """Return what the form for a person's affiliation and level draws."""
        theirs, others = affiliation_choices(person)
        held, source = self.access.level_from_above(person)
        return {
            "person": person,
            "theirs": theirs,
            "others": others,
            "current_affiliation": credit.affiliation_id,
            "levels": level_choices(self.base_object, floor=held),
            "current_level": credit.level,
            "level_source_kind": RecordAccess(source).kind if source else "",
        }

    def post(self, request, *args, **kwargs):
        """Save the edit."""
        credit = self.get_contribution()
        contributor = credit.contributor.get_real_instance()
        arguments = {"roles": self.chosen_roles(self.held_by(credit))}
        if not contributor.is_organization:
            arguments["organization"] = self.chosen_affiliation()
            arguments["level"] = self.chosen_level()
        try:
            Crediting(self.base_object).update(credit, **arguments)
        except ValidationError as error:
            return self.refusal(error)
        return self.region_response(
            toast={"text": _("%(name)s saved.") % {"name": contributor.name}}
        )

    def chosen_affiliation(self):
        """Return the organization picked in the posted form, None
        for no affiliation.
        """
        value = self.request.POST.get("affiliation", "")
        return (
            Organization.objects.filter(pk=value).first() if value.isdigit() else None
        )

    def chosen_level(self):
        """Return the level picked in the posted form, None to leave it as it is."""
        value = self.request.POST.get("level", "")
        return (
            ContributionLevel(int(value))
            if value in {str(level.value) for level in ContributionLevel}
            else None
        )


class CreditOrganization(ContributorsBase):
    """Give an organization that is only someone's affiliation roles of its own on the
    record.
    """

    name = "credit-organization"
    url_path = "organization/<int:pk>/roles"

    def get(self, request, *args, **kwargs):
        """Open the roles sheet for an organization not yet listed."""
        organization = get_object_or_404(Organization, pk=kwargs["pk"])
        context = {
            "organization": organization,
            "credit": None,
            **self.role_context(None),
            "action": self.record_url(
                "contribution-list-credit-organization", pk=organization.pk
            ),
            "submit_text": _("Save"),
        }
        return self.sheet_response(
            "contributors/tab/sheets/edit_organization.html", context, organization.name
        )

    def post(self, request, *args, **kwargs):
        """List the organization with the chosen roles."""
        organization = get_object_or_404(Organization, pk=kwargs["pk"])
        crediting = Crediting(self.base_object)
        try:
            crediting.list_organization(organization)
            credit = self.base_object.contributors.get(contributor=organization)
            crediting.update(credit, roles=self.chosen_roles(held=None))
        except ValidationError as error:
            return self.refusal(error)
        return self.region_response(
            toast={"text": _("%(name)s saved.") % {"name": organization.name}}
        )


class RemoveCredit(ContributorsBase):
    """Remove a contributor, answering with an Undo."""

    name = "remove"
    url_path = "<int:pk>/remove"

    def post(self, request, *args, **kwargs):
        """Remove the contributor and offer to put them back."""
        credit = self.get_contribution()
        contributor = credit.contributor.get_real_instance()
        kept = signing.dumps(
            {
                "contributor": contributor.pk,
                "roles": [role.pk for role in credit.roles.all()],
                "affiliation": credit.affiliation_id,
                "level": credit.level,
                "order": credit.order,
            },
            salt=UNDO_SALT,
        )
        try:
            Crediting(self.base_object).remove(credit)
        except ValidationError as error:
            return self.refusal(error)
        return self.region_response(
            toast={
                "text": _("%(name)s removed.") % {"name": contributor.name},
                "undo_url": self.record_url("contribution-list-undo"),
                "undo": kept,
            }
        )


class UndoRemove(ContributorsBase):
    """Put a removed contributor back as they were."""

    name = "undo"
    url_path = "undo"

    def post(self, request, *args, **kwargs):
        """Recreate the removed contribution in its old place, with its
        roles and level.
        """
        try:
            kept = signing.loads(
                request.POST.get("undo", ""), salt=UNDO_SALT, max_age=UNDO_SECONDS
            )
        except signing.BadSignature:
            return HttpResponseBadRequest()
        contributor = get_object_or_404(Contributor, pk=kept["contributor"])
        contributor = contributor.get_real_instance()
        if self.base_object.contributors.filter(contributor=contributor).exists():
            return self.region_response()
        crediting = Crediting(self.base_object)
        offered = {role.pk: role for role in crediting.offered_roles()}
        try:
            credit = crediting.add(
                contributor,
                organization=Organization.objects.filter(
                    pk=kept["affiliation"]
                ).first(),
            )
            crediting.update(
                credit,
                roles=[offered[pk] for pk in kept["roles"] if pk in offered],
                level=None if contributor.is_organization else kept["level"],
                organization=UNCHANGED,
            )
        except ValidationError as error:
            return self.refusal(error)
        credit.order = kept["order"]
        credit.save(update_fields=["order"])
        return self.region_response(
            toast={"text": _("%(name)s is back.") % {"name": contributor.name}}
        )


class Reorder(ContributorsBase):
    """The Reorder sheet: drag people into the order the record credits them in."""

    name = "reorder"
    url_path = "reorder"

    def get(self, request, *args, **kwargs):
        """Open the reorder sheet."""
        return self.sheet_response(
            "contributors/tab/sheets/reorder.html",
            {
                "people_rows": self.people(),
                "action": self.record_url("contribution-list-reorder"),
                "submit_text": _("Save order"),
            },
            _("Reorder people"),
        )

    def post(self, request, *args, **kwargs):
        """Save the order the people were given in."""
        people = Contribution.objects.for_entity(self.base_object).people()
        try:
            save_order(people, request.POST.getlist("order"), field="order")
        except InvalidOrder:
            return HttpResponseBadRequest()
        return self.region_response(toast={"text": _("New order saved.")})

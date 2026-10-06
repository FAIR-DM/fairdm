"""The one place the contributors of a project, dataset, sample or measurement are changed."""

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _
from research_vocabs.models import Concept

from ..choices import ContributionLevel
from ..models import Contribution, Person

UNCHANGED = object()
"""Passed as the organization of ``Crediting.update`` to leave it as it is."""


class Crediting:
    """Add, change and remove the contributors of one record.

    Each refusal is a ``ValidationError`` with a code, so a page can attach it to a field and a
    test can assert on it.

    Args:
        record: A project, dataset, sample or measurement, of any registered type.
    """

    def __init__(self, record):
        self.record = record

    def offered_roles(self):
        """Return the contribution roles the record's type offers.

        Returns:
            The concepts of the roles vocabulary that its group names for this type, in the
            vocabulary's order.
        """
        names = list(self.record.CONTRIBUTOR_ROLES.values)
        concepts = Concept.objects.filter(
            vocabulary__name="fairdm-roles", name__in=names
        )
        return sorted(concepts, key=lambda concept: names.index(concept.name))

    def add(self, contributor, *, organization=None):
        """List a contributor on the record, last of its kind. A person starts at the view level.

        Args:
            contributor: The person or organization to list.
            organization: The organization a person is credited from on this record, listed on
                the record too if it is not already. None credits them from none. Ignored for
                an organization.

        Returns:
            The new contribution.

        Raises:
            ValidationError: With code ``duplicate`` when the contributor is already listed,
                or ``superuser`` when they are a superuser, who cannot be credited.
        """
        contributor = contributor.get_real_instance()
        if self.record.contributors.filter(contributor=contributor).exists():
            raise ValidationError(
                _("%(name)s is already a contributor on this record.")
                % {"name": contributor},
                code="duplicate",
            )
        is_person = isinstance(contributor, Person)
        if is_person and contributor.is_superuser:
            raise ValidationError(
                _("%(name)s is a superuser, and a superuser cannot be a contributor.")
                % {"name": contributor},
                code="superuser",
            )
        with transaction.atomic():
            if is_person and organization is not None:
                self.list_organization(organization)
            return Contribution.objects.create(
                contributor=contributor,
                content_type=ContentType.objects.get_for_model(self.record),
                object_id=self.record.pk,
                level=ContributionLevel.VIEW if is_person else None,
                affiliation=organization if is_person else None,
            )

    def list_organization(self, organization):
        """List an organization on the record, unless it already is.

        Args:
            organization: The organization to list.
        """
        if not self.record.contributors.filter(contributor=organization).exists():
            self.add(organization)

    def update(self, contribution, *, roles, organization=UNCHANGED):
        """Replace the roles a contributor holds on the record, and for a person the organization.

        Their level is left as it is.

        Args:
            contribution: The contribution to change.
            roles: Concepts of the roles vocabulary, none or more.
            organization: The organization a person is credited from, listed on the record too
                if it is not already. None credits them from none, and ``UNCHANGED`` leaves
                it as it is. Ignored for an organization.

        Raises:
            ValidationError: With code ``role_not_offered`` when a role is not in the group the
                record's type offers.
        """
        offered = {concept.pk for concept in self.offered_roles()}
        if any(role.pk not in offered for role in roles):
            raise ValidationError(
                _("Choose from the roles offered for this kind of record."),
                code="role_not_offered",
            )
        with transaction.atomic():
            contribution.roles.set(roles)
            is_person = not contribution.contributor.get_real_instance().is_organization
            if organization is not UNCHANGED and is_person:
                if organization is not None:
                    self.list_organization(organization)
                contribution.affiliation = organization
                contribution.save(update_fields=["affiliation"])

    def remove(self, contribution):
        """Remove a contributor from the record, and with them the level they held on it.

        Args:
            contribution: The contribution to remove.

        Raises:
            ValidationError: With code ``credited_from`` when it is an organization that
                people on the record are credited from. Its ``params["people"]`` lists them.
        """
        people = self.credited_from().get(contribution.contributor_id, [])
        if people:
            raise ValidationError(
                _("%(name)s cannot be removed while %(names)s are credited from it."),
                code="credited_from",
                params={
                    "name": str(contribution.contributor),
                    "names": ", ".join(person.name for person in people),
                    "people": people,
                },
            )
        contribution.delete()

    def make_creator(self, user, *, roles=()):
        """List the person who created the record at the manage level.

        A superuser cannot be credited, so for one this does nothing and the create still
        succeeds.

        Args:
            user: The person who created the record.
            roles: Names of roles in the roles vocabulary to give them. They are not checked
                against the record type's group.

        Returns:
            The creator's contribution, or None for a superuser.
        """
        if user.is_superuser:
            return None
        with transaction.atomic():
            contribution = self.record.contributors.filter(contributor=user).first()
            if contribution is None:
                contribution = self.add(user)
            contribution.level = ContributionLevel.MANAGE
            contribution.save(update_fields=["level"])
            contribution.roles.add(
                *Concept.objects.filter(
                    vocabulary__name="fairdm-roles", name__in=list(roles)
                )
            )
        return contribution

    def credited_from(self):
        """Say who on the record is credited from each organization.

        Returns:
            A dictionary from an organization's id to the people credited from it on this
            record, in their order.
        """
        found = {}
        credited = (
            self.record.contributors.exclude(affiliation=None)
            .select_related("contributor")
            .order_by("order", "pk")
        )
        for credit in credited:
            if credit.contributor is not None:
                found.setdefault(credit.affiliation_id, []).append(credit.contributor)
        return found

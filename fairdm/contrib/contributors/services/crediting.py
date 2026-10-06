"""The one place the contributors of a project, dataset, sample or measurement are changed."""

from contextlib import contextmanager

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _
from research_vocabs.models import Concept

from ..access import RecordAccess
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

    @contextmanager
    def locked(self):
        """Hold the record's row for the length of a change, in one transaction.

        Two changes to one record wait for each other, so each reads the contributors the other
        left. A private record is found too. A database that cannot lock rows runs the change
        in the transaction alone.

        Yields:
            Nothing. Read the record's contributors only inside the block.
        """
        model = type(self.record)
        manager = getattr(model, "all_objects", model._default_manager)
        with transaction.atomic():
            list(
                manager.select_for_update()
                .filter(pk=self.record.pk)
                .values_list("pk", flat=True)
            )
            yield

    def would_leave_no_manager(self, contribution, level=None):
        """Say whether removing a contribution, or lowering its level, leaves nobody to manage.

        Only going from at least one person who counts as able to manage the record to none is
        a refusal. A record that has no manager already may lose or raise anyone.

        Args:
            contribution: The contribution on this record to remove or lower.
            level: The level it would be given. None asks about removing it.

        Returns:
            True when the contribution is the only thing that makes the record manageable.
        """
        if level == ContributionLevel.MANAGE:
            return False
        stored = (
            Contribution.objects.filter(pk=contribution.pk)
            .values_list("level", flat=True)
            .first()
        )
        if stored != ContributionLevel.MANAGE:
            return False
        access = RecordAccess(self.record)
        person = contribution.contributor_id
        if access.managers() != {person}:
            return False
        return not any(
            held == ContributionLevel.MANAGE and record is not access.record
            for record, held in access.levels_held(person)
        )

    def last_manager_refusal(self, contribution):
        """Build the refusal for a change that would leave the record with nobody to manage.

        Args:
            contribution: The contribution of the person who must stay.

        Returns:
            A ``ValidationError`` with code ``last_manager``.
        """
        return ValidationError(
            _(
                "%(name)s is the only person who can manage this %(kind)s. "
                "Give someone else \u201cCan manage\u201d first."
            ),
            code="last_manager",
            params={
                "name": str(contribution.contributor),
                "kind": RecordAccess(self.record).kind,
            },
        )

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
            ValidationError: With code ``superuser`` when they are a superuser, who cannot be
                credited, or ``duplicate`` when the contributor is already listed.
        """
        contributor = contributor.get_real_instance()
        is_person = isinstance(contributor, Person)
        if is_person and contributor.is_superuser:
            raise ValidationError(
                _("%(name)s is a superuser, and a superuser cannot be a contributor.")
                % {"name": contributor},
                code="superuser",
            )
        with self.locked():
            if self.record.contributors.filter(contributor=contributor).exists():
                raise ValidationError(
                    _("%(name)s is already a contributor on this record.")
                    % {"name": contributor},
                    code="duplicate",
                )
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

    def update(self, contribution, *, roles, level=None, organization=UNCHANGED):
        """Replace the roles a contributor holds on the record, and for a person the level and organization.

        Args:
            contribution: The contribution to change.
            roles: Concepts of the roles vocabulary, none or more.
            level: The level to give a person, a ``ContributionLevel``. None leaves it as it
                is. Ignored for an organization.
            organization: The organization a person is credited from, listed on the record too
                if it is not already. None credits them from none, and ``UNCHANGED`` leaves
                it as it is. Ignored for an organization.

        Raises:
            ValidationError: With code ``role_not_offered`` when a role is not in the group the
                record's type offers, and ``below_inherited`` when the level is below what the
                person holds from a record above, and ``last_manager`` when it would leave the
                record with nobody who counts as able to manage it. When several apply the error
                holds them all, in its ``error_list``. Nothing is saved.
        """
        is_person = not contribution.contributor.get_real_instance().is_organization
        with self.locked():
            refusals = []
            offered = {concept.pk for concept in self.offered_roles()}
            if any(role.pk not in offered for role in roles):
                refusals.append(
                    ValidationError(
                        _("Choose from the roles offered for this kind of record."),
                        code="role_not_offered",
                    )
                )
            if level is not None and is_person:
                held, source = RecordAccess(self.record).level_from_above(
                    contribution.contributor.get_real_instance()
                )
                if held is not None and level < held:
                    refusals.append(
                        ValidationError(
                            _(
                                "They hold \u201c%(level)s\u201d from the %(kind)s above, and it cannot be lowered here."
                            ),
                            code="below_inherited",
                            params={
                                "level": held.label,
                                "kind": RecordAccess(source).kind,
                                "source": source,
                            },
                        )
                    )
                if self.would_leave_no_manager(contribution, level):
                    refusals.append(self.last_manager_refusal(contribution))
            if refusals:
                raise refusals[0] if len(refusals) == 1 else ValidationError(refusals)
            contribution.roles.set(roles)
            changed = []
            if level is not None and is_person:
                contribution.level = level
                changed.append("level")
            if organization is not UNCHANGED and is_person:
                if organization is not None:
                    self.list_organization(organization)
                contribution.affiliation = organization
                changed.append("affiliation")
            if changed:
                contribution.save(update_fields=changed)

    def remove(self, contribution):
        """Remove a contributor from the record, and with them the level they held on it.

        Args:
            contribution: The contribution to remove.

        Raises:
            ValidationError: With code ``credited_from`` when it is an organization that
                people on the record are credited from, its ``params["people"]`` listing them,
                and ``last_manager`` when it is the only person who counts as able to manage
                the record. Nothing is removed.
        """
        with self.locked():
            people = self.credited_from().get(contribution.contributor_id, [])
            if people:
                raise ValidationError(
                    _(
                        "%(name)s cannot be removed while %(names)s are credited from it."
                    ),
                    code="credited_from",
                    params={
                        "name": str(contribution.contributor),
                        "names": ", ".join(person.name for person in people),
                        "people": people,
                    },
                )
            if self.would_leave_no_manager(contribution):
                raise self.last_manager_refusal(contribution)
            contribution.delete()

    def move(self, contribution, direction):
        """Move a contributor one place earlier or later among the contributors of its kind.

        People are placed among people and organizations among organizations, so the other list
        is left alone. The first moving earlier and the last moving later change nothing. Where
        old data gives two contributors the same place, their places are told apart by their
        creation order first.

        Args:
            contribution: The contribution to move, on this record.
            direction: ``"up"`` for earlier or ``"down"`` for later.

        Raises:
            ValidationError: With code ``direction`` when it is neither, and ``not_listed``
                when the contribution is not on this record. Nothing is moved.
        """
        if direction not in ("up", "down"):
            raise ValidationError(
                _("Choose to move earlier or later."), code="direction"
            )
        with self.locked():
            contributions = Contribution.objects.for_entity(self.record)
            is_organization = (
                contribution.contributor.get_real_instance().is_organization
            )
            peers = list(
                contributions.organizations()
                if is_organization
                else contributions.people()
            )
            index = next(
                (
                    place
                    for place, peer in enumerate(peers)
                    if peer.pk == contribution.pk
                ),
                None,
            )
            if index is None:
                raise ValidationError(
                    _("This contributor is not listed on this record."),
                    code="not_listed",
                )
            target = index - 1 if direction == "up" else index + 1
            if not 0 <= target < len(peers):
                return
            places = [peer.order for peer in peers]
            if len(set(places)) < len(places):
                places = [places[0] + place for place in range(len(peers))]
            places[index], places[target] = places[target], places[index]
            for peer, place in zip(peers, places, strict=True):
                peer.order = place
            Contribution.objects.bulk_update(peers, ["order"])
            contribution.order = places[index]

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
        with self.locked():
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

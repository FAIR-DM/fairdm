"""Managers and querysets for people, affiliations and contributions."""

from django.contrib.auth.models import BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ordered_model.models import OrderedModelManager, OrderedModelQuerySet

from fairdm.db.models import PrefetchPolymorphicManager, PrefetchPolymorphicQuerySet


class PersonQuerySet(PrefetchPolymorphicQuerySet):
    """Person queryset with a filter for each claim and account state."""

    def real(self):
        """Exclude superusers and the django-guardian anonymous user.

        Returns:
            Persons that are not superusers and do not have the email ``AnonymousUser``.
        """
        return self.exclude(is_superuser=True).exclude(email="AnonymousUser")

    def active(self):
        """Filter to active persons.

        Returns:
            Persons with ``is_active`` true.
        """
        return self.filter(is_active=True)

    def inactive(self):
        """Filter to deactivated accounts, whatever their claim status or email.

        Returns:
            Persons with ``is_active`` false.
        """
        return self.filter(is_active=False)

    def claimed(self):
        """Filter to active persons who have claimed their accounts.

        A deactivated account is never claimed here, even though its flag is still true.

        Returns:
            Persons with ``is_active`` and ``is_claimed`` true.
        """
        return self.filter(is_active=True, is_claimed=True)

    def unclaimed(self):
        """Filter to persons who have not claimed their accounts.

        This covers both ghost profiles and invited profiles.

        Returns:
            Persons with ``is_claimed`` false.
        """
        return self.filter(is_claimed=False)

    def ghost(self):
        """Filter to ghost profiles, the attribution-only records made by ``create_unclaimed``.

        Returns:
            Active, unclaimed persons with no email.
        """
        return self.filter(is_active=True, is_claimed=False, email__isnull=True)

    def invited(self):
        """Filter to invited profiles, which have an email but have not been claimed.

        Returns:
            Active, unclaimed persons with an email.
        """
        return self.filter(is_active=True, is_claimed=False, email__isnull=False)


class UserManager(
    BaseUserManager, PrefetchPolymorphicManager.from_queryset(PersonQuerySet)
):
    """Manager for the Person model, which has no username field.

    The state filters come from ``PersonQuerySet``.
    """

    use_in_migrations = False

    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password.

        Args:
            email: The user's email, which is required.
            password: The password. None sets an unusable password.
            **extra_fields: Other model fields.

        Returns:
            The saved user.

        Raises:
            ValueError: The email is empty.
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a non-staff person with the given email and password.

        Args:
            email: The person's email.
            password: The password. None sets an unusable password.
            **extra_fields: Other model fields.

        Returns:
            The saved person.
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a staff superuser with the given email and password.

        Args:
            email: The user's email.
            password: The password. None sets an unusable password.
            **extra_fields: Other model fields.

        Returns:
            The saved superuser.

        Raises:
            ValueError: ``is_staff`` or ``is_superuser`` is passed as false.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def create_unclaimed(self, first_name: str, last_name: str, **extra_fields):
        """Create a ghost profile: an active, unclaimed person with no email and an unusable password.

        Args:
            first_name: Given name.
            last_name: Family name.
            **extra_fields: Any other Contributor or Person fields.

        Returns:
            The saved person.
        """
        extra_fields["email"] = None
        extra_fields["is_claimed"] = False
        extra_fields["is_active"] = True
        extra_fields["first_name"] = first_name
        extra_fields["last_name"] = last_name
        extra_fields.setdefault("name", f"{first_name} {last_name}".strip())

        user = self.model(**extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class AffiliationQuerySet(models.QuerySet):
    """Affiliation queryset with filters for primary, current, past and owner affiliations."""

    def primary(self):
        """Return the affiliation marked primary.

        Returns:
            The primary affiliation, or None when none is set.
        """
        return self.filter(is_primary=True).first()

    def current(self):
        """Filter to current affiliations, which have no end date.

        Returns:
            Affiliations with ``end_date`` null.
        """
        return self.filter(end_date__isnull=True)

    def past(self):
        """Filter to past affiliations, which have an end date.

        Returns:
            Affiliations with ``end_date`` set.
        """
        return self.filter(end_date__isnull=False)

    def owners(self):
        """Filter to current owner affiliations.

        Ownership is defined here once: a current affiliation (see :meth:`current`) of
        type OWNER. An ended OWNER affiliation confers no ownership.

        Returns:
            Current affiliations with type OWNER.
        """
        from fairdm.contrib.contributors.models import Affiliation

        return self.current().filter(type=Affiliation.MembershipType.OWNER)


class AffiliationManager(models.Manager.from_queryset(AffiliationQuerySet)):
    """Manager for the Affiliation model, exposing the ``AffiliationQuerySet`` filters.

    ``primary()`` returns one affiliation or None, so it cannot be chained further.
    """


class ContributionQuerySet(OrderedModelQuerySet):
    """Contribution queryset with filters by role, entity and contributor."""

    def by_role(self, role_name: str):
        """Filter contributions to those holding a role.

        Args:
            role_name: Name of a concept in the roles vocabulary.

        Returns:
            Contributions with that role.
        """
        return self.filter(roles__name=role_name)

    def for_entity(self, obj):
        """Filter contributions to those credited on one object.

        Args:
            obj: A model instance, such as a project or dataset, that contributions point at.

        Returns:
            Contributions for that object.
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def by_contributor(self, contributor):
        """Filter contributions to those by one contributor across all objects.

        Args:
            contributor: The contributor.

        Returns:
            Contributions by that contributor.
        """
        return self.filter(contributor=contributor)


class ContributionManager(OrderedModelManager.from_queryset(ContributionQuerySet)):
    """Manager for the Contribution model, with the ordered-model methods and the ``ContributionQuerySet`` filters."""

from django.contrib.auth.models import BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ordered_model.models import OrderedModelManager, OrderedModelQuerySet

from fairdm.db.models import PrefetchPolymorphicManager


class UserManager(BaseUserManager, PrefetchPolymorphicManager):
    """Define a model manager for User model with no username field.

    This manager is unified with PersonQuerySet to provide both user creation
    methods and state-based filtering. See research.md D8 for manager unification
    rationale.
    """

    use_in_migrations = False

    def get_queryset(self):
        """Return PersonQuerySet for unified manager functionality."""
        return PersonQuerySet(self.model, using=self._db)

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def create_unclaimed(self, first_name: str, last_name: str, **extra_fields):
        """Create an unclaimed (Ghost state) Person record.

        Creates a provenance-only attribution record with:
        - email=None (no email address)
        - is_claimed=False (not owned by a user)
        - is_active=True (allows future claiming via invitation)
        - set_unusable_password() (cannot log in until claimed)

        This implements the Ghost state in the 4-state machine. See research.md D3.

        Args:
            first_name: Given name (required).
            last_name: Family name (required).
            **extra_fields: Any other Contributor/Person fields.

        Returns:
            Person instance (saved, Ghost state).
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

    # Proxy methods for PersonQuerySet
    def real(self):
        """Proxy to queryset real() method."""
        return self.get_queryset().real()

    def active(self):
        """Proxy to queryset active() method."""
        return self.get_queryset().active()

    def claimed(self):
        """Proxy to queryset claimed() method."""
        return self.get_queryset().claimed()

    def unclaimed(self):
        """Proxy to queryset unclaimed() method."""
        return self.get_queryset().unclaimed()

    def ghost(self):
        """Proxy to queryset ghost() method."""
        return self.get_queryset().ghost()

    def invited(self):
        """Proxy to queryset invited() method."""
        return self.get_queryset().invited()


class PersonQuerySet(models.QuerySet):
    """QuerySet for Person model with state-based filtering methods.

    Provides methods for querying persons based on their claim status and account state.
    See research.md D3 for the complete 4-state machine (Ghost→Invited→Claimed→Banned).
    """

    def real(self):
        """Exclude superusers and django-guardian anonymous user.

        Safe for portal-facing queries where superusers should not appear
        in contributor lists or search results.

        Returns:
            QuerySet: Person objects excluding is_superuser=True and email="AnonymousUser"
        """
        return self.exclude(is_superuser=True).exclude(email="AnonymousUser")

    def active(self):
        """Filter to active persons only.

        Returns:
            QuerySet: Person objects with is_active=True
        """
        return self.filter(is_active=True)

    def claimed(self):
        """Filter to persons who have claimed their accounts.

        Claimed persons have is_claimed=True and can log in. This includes
        both active and banned accounts.

        Returns:
            QuerySet: Person objects with is_claimed=True
        """
        return self.filter(is_claimed=True)

    def unclaimed(self):
        """Filter to persons who have not claimed their accounts.

        Unclaimed persons include both Ghost (no email) and Invited (email present
        but not yet claimed) states.

        Returns:
            QuerySet: Person objects with is_claimed=False
        """
        return self.filter(is_claimed=False)

    def ghost(self):
        """Filter to ghost profiles (provenance-only attribution records).

        Ghost profiles have no email and are created via create_unclaimed() for
        attribution purposes. They cannot receive invitations.

        Returns:
            QuerySet: Person objects with is_claimed=False and email=NULL
        """
        return self.filter(is_claimed=False, email__isnull=True)

    def invited(self):
        """Filter to invited profiles (email present but not claimed).

        Invited profiles have an email address but the person has not yet
        completed registration/claiming.

        Returns:
            QuerySet: Person objects with is_claimed=False and email NOT NULL
        """
        return self.filter(is_claimed=False, email__isnull=False)


class PersonalContributorsQuerySet(models.QuerySet):
    """Deprecated: Use PersonQuerySet instead.

    This queryset is maintained for backward compatibility during the migration
    to unified manager architecture. Will be removed in a future version.
    """

    def all(self):
        """A queryset of all contributors, excluding superusers the django-guardian anonymous user."""
        return self.exclude(is_superuser=True).exclude(email="AnonymousUser")

    def active(self):
        """A queryset of all active contributors."""
        return self.all().filter(is_active=True)

    def claimed(self):
        """Persons with email IS NOT NULL and is_active=True (have claimed their account)."""
        return self.all().filter(email__isnull=False, is_active=True)

    def unclaimed(self):
        """Persons with email IS NULL (provenance-only records)."""
        return self.all().filter(email__isnull=True)


class PersonalContributorsManager(models.Manager):
    """Deprecated: Use Person.objects (UserManager) instead.

    This manager is maintained for backward compatibility during the migration
    to unified manager architecture. Will be removed in a future version.

    Recommended usage:
        - Person.objects.real() instead of Person.contributors.all()
        - Person.objects.claimed() instead of Person.contributors.claimed()
        - Person.objects.unclaimed() instead of Person.contributors.unclaimed()
    """

    def get_queryset(self):
        """Return a queryset of all contributors."""
        return PersonalContributorsQuerySet(self.model, using=self._db).all()

    def all(self):
        """Return all contributors."""
        return self.get_queryset().all()

    def active(self):
        """Return all active contributors."""
        return self.get_queryset().active()

    def claimed(self):
        """Return all claimed contributors (with email and active)."""
        return self.get_queryset().claimed()

    def unclaimed(self):
        """Return all unclaimed contributors (no email)."""
        return self.get_queryset().unclaimed()


class AffiliationQuerySet(models.QuerySet):
    """QuerySet for Affiliation model with time-based filtering methods.

    Provides methods for querying affiliations based on their temporal state
    (primary, current, or past) as documented in data-model.md.
    """

    def primary(self):
        """Get the primary affiliation.

        Returns the affiliation marked with is_primary=True, or None if no
        primary affiliation is set.

        Returns:
            Affiliation or None: The primary affiliation instance

        Usage:
            primary = person.affiliations.primary()
        """
        return self.filter(is_primary=True).first()

    def current(self):
        """Get all current (active) affiliations.

        Current affiliations have end_date=NULL, meaning they are still active.

        Returns:
            QuerySet: Affiliation objects with no end date

        Usage:
            current_orgs = person.affiliations.current()
        """
        return self.filter(end_date__isnull=True)

    def past(self):
        """Get all past (historical) affiliations.

        Past affiliations have end_date IS NOT NULL, meaning the affiliation
        has ended.

        Returns:
            QuerySet: Affiliation objects with an end date set

        Usage:
            past_orgs = person.affiliations.past()
        """
        return self.filter(end_date__isnull=False)


class AffiliationManager(models.Manager):
    """Manager for Affiliation model using PersonQuerySet methods."""

    def get_queryset(self):
        """Return AffiliationQuerySet."""
        return AffiliationQuerySet(self.model, using=self._db)

    def primary(self):
        """Proxy to queryset primary() method."""
        return self.get_queryset().primary()

    def current(self):
        """Proxy to queryset current() method."""
        return self.get_queryset().current()

    def past(self):
        """Proxy to queryset past() method."""
        return self.get_queryset().past()


class ContributionQuerySet(OrderedModelQuerySet):
    """QuerySet for Contribution model with filtering methods."""

    def by_role(self, role_name: str):
        """Filter contributions to those containing the specified role.

        Args:
            role_name: Name matching a Concept in FairDMRoles vocabulary.
        """
        return self.filter(roles__name=role_name)

    def for_entity(self, obj):
        """All contributions for a specific entity (Project/Dataset/etc.).

        Args:
            obj: Any model instance with a GenericRelation to Contribution.
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.filter(content_type=content_type, object_id=obj.pk)

    def by_contributor(self, contributor):
        """All contributions by a specific contributor across all entities."""
        return self.filter(contributor=contributor)


class ContributionManager(OrderedModelManager):
    """Manager for Contribution model."""

    def get_queryset(self):
        return ContributionQuerySet(self.model, using=self._db)

    def by_role(self, role_name: str):
        return self.get_queryset().by_role(role_name)

    def for_entity(self, obj):
        return self.get_queryset().for_entity(obj)

    def by_contributor(self, contributor):
        return self.get_queryset().by_contributor(contributor)

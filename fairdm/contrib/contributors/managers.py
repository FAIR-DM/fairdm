from django.contrib.auth.models import BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ordered_model.models import OrderedModelManager, OrderedModelQuerySet

from fairdm.db.models import PrefetchPolymorphicManager, PrefetchPolymorphicQuerySet


class PersonQuerySet(PrefetchPolymorphicQuerySet):
    """QuerySet for Person model with state-based filtering methods.

    Provides methods for querying persons based on their claim status and account state.
    See decisions.md D8 for the account-state derivation.
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

    def inactive(self):
        """Filter to deactivated accounts - the highest-precedence state (D8).

        Deactivation is decided first: a deactivated person is inactive
        regardless of claim status or email address, mirroring
        `Person.account_state`.

        Returns:
            QuerySet: Person objects with is_active=False
        """
        return self.filter(is_active=False)

    def claimed(self):
        """Filter to persons who have claimed their accounts.

        Claimed persons are active and have is_claimed=True. Deactivation is
        decided first (D8), so a deactivated account is never claimed here
        even though the stored flag is still True.

        Returns:
            QuerySet: Person objects with is_active=True and is_claimed=True
        """
        return self.filter(is_active=True, is_claimed=True)

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

        Ghost profiles are active, have no email and are created via
        create_unclaimed() for attribution purposes. They cannot receive
        invitations. Deactivation is decided first (D8): a deactivated
        person with no email is inactive, not ghost.

        Returns:
            QuerySet: Person objects with is_active=True, is_claimed=False
            and email=NULL
        """
        return self.filter(is_active=True, is_claimed=False, email__isnull=True)

    def invited(self):
        """Filter to invited profiles (email present but not claimed).

        Invited profiles are active and have an email address but the person
        has not yet completed registration/claiming. Deactivation is decided
        first (D8): a deactivated person with an email is inactive, not
        invited.

        Returns:
            QuerySet: Person objects with is_active=True, is_claimed=False
            and email NOT NULL
        """
        return self.filter(is_active=True, is_claimed=False, email__isnull=False)


class UserManager(
    BaseUserManager, PrefetchPolymorphicManager.from_queryset(PersonQuerySet)
):
    """Manager for the Person model with no username field.

    `real()`, `active()`, `claimed()`, `unclaimed()`, `ghost()`, `invited()`
    and `inactive()` are defined once on `PersonQuerySet` above and reach this
    manager through `PrefetchPolymorphicManager.from_queryset()` (FR-040,
    D14), matching the pattern `fairdm.core.dataset.models.DatasetManager`
    uses - no manager-side reimplementation is kept here.
    """

    use_in_migrations = False

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password.

        A `None` password (the default `create_user`/`create_superuser` pass
        through) sets an unusable one - `AbstractBaseUser.set_password(None)`
        already does this, so no separate branch is needed here (FR-009, FR-010).
        """
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a Person with the given email and password.

        Sets an unusable password when none is supplied (FR-010).
        """
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
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

        This implements the Ghost state in the 4-state machine. See decisions.md D8.

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

    def owners(self):
        """Get all current owner affiliations.

        Ownership is defined once, here, as a current affiliation
        (``end_date`` is NULL - see :meth:`current`) whose type is OWNER. A
        person whose OWNER affiliation has ended - the field's help_text
        documents ending an affiliation as ending the rights it conferred -
        is not an owner, even though the row's type still reads OWNER.
        Every caller that decides who may manage an organization
        (``OrganizationPermissionBackend.has_perm``, ``Organization.owner()``,
        ``Organization.transfer_ownership()``) derives from this method
        rather than re-deriving the rule.

        Returns:
            QuerySet: current Affiliation objects with type=OWNER

        Usage:
            org.affiliations.owners()
        """
        from fairdm.contrib.contributors.models import Affiliation

        return self.current().filter(type=Affiliation.MembershipType.OWNER)


class AffiliationManager(models.Manager.from_queryset(AffiliationQuerySet)):
    """Manager for the Affiliation model.

    `primary()`, `current()` and `past()` are defined once on
    `AffiliationQuerySet` above and reach this manager through
    `Manager.from_queryset()` (FR-040, D14). `primary()` returns a single
    `Affiliation` or `None` rather than a queryset - `from_queryset` copies a
    method's forwarding call regardless of its return type, so this does not
    prevent composition; it only means `.primary()` cannot be chained with a
    further queryset method, which no caller in this codebase does.
    """


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


class ContributionManager(OrderedModelManager.from_queryset(ContributionQuerySet)):
    """Manager for the Contribution model.

    `by_role()`, `for_entity()` and `by_contributor()` are defined once on
    `ContributionQuerySet` above and reach this manager through
    `OrderedModelManager.from_queryset()` (FR-040, D14) - `OrderedModelManager`
    is itself `models.Manager.from_queryset(OrderedModelQuerySet)`, so this
    keeps the ordered-model queryset methods (`get_max_order()`, `above()`,
    etc.) alongside the contribution-specific ones.
    """

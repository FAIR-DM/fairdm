from django.contrib.auth.models import BaseUserManager
from django.contrib.contenttypes.models import ContentType
from django.db import models
from ordered_model.models import OrderedModelManager, OrderedModelQuerySet

from fairdm.db.models import PrefetchPolymorphicManager


class UserManager(BaseUserManager, PrefetchPolymorphicManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = False

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
        """Create an unclaimed (provenance-only) Person record.

        Sets email=None, is_active=False, set_unusable_password().

        Args:
            first_name: Given name (required).
            last_name: Family name (required).
            **extra_fields: Any other Contributor/Person fields.

        Returns:
            Person instance (saved, is_active=False, email=None).
        """
        extra_fields["email"] = None
        extra_fields["is_active"] = False
        extra_fields["first_name"] = first_name
        extra_fields["last_name"] = last_name
        extra_fields.setdefault("name", f"{first_name} {last_name}".strip())

        user = self.model(**extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user


class PersonalContributorsQuerySet(models.QuerySet):
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
    """A manager for the PersonalContributor model."""

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

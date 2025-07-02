from django.contrib.auth.models import BaseUserManager
from django.db import models

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


class PersonalContributorsQuerySet(models.QuerySet):
    def all(self):
        """A queryset of all contributors, excluding superusers the django-guardian anonymous user."""
        return self.exclude(is_superuser=True).exclude(email="AnonymousUser")

    def active(self):
        """A queryset of all active contributors."""
        return self.all().filter(is_active=True)


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


class ContributionManager(models.QuerySet):
    def by_role(self, role):
        """Returns all contributions with the given role"""
        return self.filter(roles__contains=role)

    # def get_contact_persons(self):
    #     return self.filter(roles__contains=ContributionRoles.CONTACT_PERSON)

    # def lead_contributors(self):
    #     """Returns all project leads"""
    #     return self.filter(roles__contains=ContributionRoles.PROJECT_LEADER)

    # def funding_contributors(self):
    #     """Returns all project leads"""
    #     return self.filter(roles__contains=ContributionRoles.SPONSOR)

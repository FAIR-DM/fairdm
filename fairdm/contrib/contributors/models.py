import json
import random

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from easy_icons import icon
from easy_thumbnails.fields import ThumbnailerImageField
from jsonfield_toolkit.models import ArrayField
from model_utils import FieldTracker
from ordered_model.models import OrderedModel
from research_vocabs.fields import ConceptManyToManyField
from research_vocabs.models import AbstractConcept
from shortuuid.django_fields import ShortUUIDField

from fairdm.core.abstract import AbstractIdentifier
from fairdm.core.vocabularies import FairDMIdentifiers, FairDMRoles
from fairdm.db import models

# from polymorphic.models import PolymorphicModel
from fairdm.db.models import PolymorphicModel
from fairdm.utils.models import PolymorphicMixin
from fairdm.utils.utils import default_image_path

from .managers import UserManager


def contributor_permissions_default():
    return {"edit": False}


class Contributor(PolymorphicMixin, PolymorphicModel):
    """A Contributor is a person or organisation that makes a contribution to a project, dataset, sample or measurement
    within the database. This model stores publicly available information about the contributor that can be used
    for proper attribution and formal publication of datasets. The fields are designed to align with the DataCite
    Contributor schema."""

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="c",
        verbose_name="UUID",
    )

    image = ThumbnailerImageField(
        verbose_name=_("profile image"),
        blank=True,
        null=True,
        upload_to=default_image_path,
    )

    name = models.CharField(
        max_length=512,
        verbose_name=_("preferred name"),
        # help_text=_("This name is displayed publicly within the website."),
    )

    alternative_names = ArrayField(
        base_field=models.CharField(max_length=255),
        verbose_name=_("alternative names"),
        help_text=_("Any other names by which the contributor is known."),
        null=True,
        blank=True,
        default=list,
    )

    profile = models.TextField(_("profile"), null=True, blank=True)

    links = ArrayField(
        base_field=models.URLField(),
        verbose_name=_("links"),
        help_text=_("A list of online resources related to this contributor."),
        null=True,
        blank=True,
        default=list,
    )

    lang = ArrayField(
        base_field=models.CharField(max_length=5),
        verbose_name=_("language"),
        help_text=_("Language of the contributor."),
        blank=True,
        null=True,
        default=list,
    )

    last_synced = models.DateField(
        verbose_name=_("last synced"),
        help_text=_("The last time the contributor was synced with the external provider (e.g. ORCID, ROR)."),
        editable=False,
        null=True,
        blank=True,
        default=None,
    )

    synced_data = models.JSONField(
        verbose_name=_("synced data"),
        help_text=_("A JSON representation of the contributor's data from the external provider."),
        editable=False,
        null=True,
        blank=True,
        default=dict,
    )

    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date added"),
        help_text=_("The date and time this record was added to the database."),
    )
    modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified"),
        help_text=_("The date and time this record was last modified."),
    )

    tracker = FieldTracker()

    class Meta:  # type: ignore
        ordering = ["name"]
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")

    def save(self, *args, **kwargs):
        if self.tracker.has_changed("synced_data"):
            self.last_synced = timezone.now().date()
        super().save(*args, **kwargs)

    @staticmethod
    def base_class():
        # this is required for many of the class methods in PolymorphicMixin
        return Contributor

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("contributor:overview", kwargs={"uuid": self.uuid})

    def get_update_url(self):
        return reverse("contributor-update", kwargs={"uuid": self.uuid})

    def get_identifier_icon(self):
        return icon(self.DEFAULT_IDENTIFIER)

    def get_default_identifier(self):
        return self.identifiers.filter(type=self.DEFAULT_IDENTIFIER).first()

    def profile_image(self):
        if self.image:
            return self.image.url
        return static("img/brand/icon.svg")

    @classproperty
    def type_of(cls):
        # this is required for many of the class methods in PolymorphicMixin
        return Contributor

    def type(self):
        return self.polymorphic_ctype.model
        # if hasattr(self, "person", None):
        #     return "person"
        # return "organization"

    @property
    def projects(self):
        Project = apps.get_model("project.Project")
        return Project.objects.filter(contributors__contributor=self)

    @property
    def datasets(self):
        Dataset = apps.get_model("dataset.Dataset")
        return Dataset.objects.filter(contributors__contributor=self)

    @property
    def samples(self):
        Sample = apps.get_model("sample.Sample")
        return Sample.objects.filter(contributors__contributor=self)

    @property
    def measurements(self):
        Measurement = apps.get_model("measurement.Measurement")
        return Measurement.objects.filter(contributors__contributor=self)

    def add_to(self, obj, roles=[]):
        """Adds the contributor to a project, dataset, sample or measurement."""
        c = Contribution.objects.get_or_create(
            contributor=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
        )
        try:
            c = Contribution.objects.get(contributor=self, object_id=obj.id)
        except Contribution.DoesNotExist:
            c = Contribution.objects.create(contributor=self, content_object=obj, roles=roles)
        else:
            c.add_roles(roles)
            c.save()

        return c
        # return Contribution.objects.create(contributor=self, content_object=obj, roles=roles)


class Person(AbstractUser, Contributor):
    DEFAULT_IDENTIFIER = "ORCID"

    objects = UserManager()  # type: ignore[var-annotated]

    # null is allowed for the email field, as a Person object/User account can be created by someone else. E.g. when
    # adding a new contributor to a database entry.
    # The email field is not stored in this case, as we don't have permission from the email owner.
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    username = Contributor.__str__

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.email == "":
            self.email = None

    def get_provider(self, provider: str):
        qs = self.socialaccount_set.filter(provider=provider)  # type: ignore[attr-defined]
        return qs.get() if qs else None

    def primary_affiliation(self):
        """
        Returns the default (primary) affiliation for the contributor.

        This method queries the contributor's organization memberships, selecting the related organization,
        and returns the first OrganizationMember object where `is_primary` is True. If no primary affiliation
        exists, returns None.

        Returns:
            OrganizationMember or None: The primary organization membership of the contributor, or None if not set.
        """
        return self.organization_memberships.select_related("organization").filter(is_primary=True).first()

    def current_affiliations(self):
        """
        Returns a queryset of OrganizationMember objects representing the contributor's current affiliations.
        The queryset is optimized with select_related to include related Organization data.
        """
        return self.organization_memberships.select_related("organization").filter(is_current=True)

    def location(self):
        """Returns the location of the contributor. TODO: make this a foreign key to a location model."""
        return random.choice(["Potsdam", "Adelaide", "Dresden"])
        return self.organization.location

    def get_absolute_url(self):
        return reverse("contributor:overview", kwargs={"uuid": self.uuid})

    @property
    def given(self):
        """Alias for self.first_name."""
        return self.first_name

    @property
    def family(self):
        """Alias for self.last_name."""
        return self.last_name

    @property
    def orcid_is_authenticated(self):
        return self.get_provider("orcid") is not None

    def icon(self):
        if self.orcid_is_authenticated:
            return "orcid"
        return "orcid_unauthenticated"

    @classmethod
    def from_orcid(self, data, person=None):
        """Create a person from ORCID data."""
        from .utils import contributor_from_orcid_data

        person = contributor_from_orcid_data(data, person)

        return person

    def as_geojson(self):
        """Returns the organization as a GeoJSON object."""
        aff = self.primary_affiliation()
        if aff:
            org = aff.organization
            return json.dumps(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [org.lon, org.lat],
                    },
                    "properties": {
                        "name": self.name,
                        "description": self.profile,
                        "icon": self.icon(),
                        "url": self.get_absolute_url(),
                    },
                },
                default=float,
            )


class OrganizationMember(models.Model):
    """A membership model that links a person to an organization."""

    class MembershipType(models.IntegerChoices):
        PENDING = 0, _("Pending")
        MEMBER = 1, _("Member")
        ADMIN = 2, _("Admin")
        OWNER = 3, _("Owner")

    person = models.ForeignKey(
        to="contributors.Person",
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        verbose_name=_("person"),
        help_text=_("The person that is a member of the organization."),
    )

    organization = models.ForeignKey(
        to="contributors.Organization",
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("organization"),
        help_text=_("The organization that the person is a member of."),
    )

    type = models.IntegerField(
        _("type"),
        choices=MembershipType,
        default=MembershipType.MEMBER,
        help_text=_("The type of membership that the person has with the organization"),
    )

    is_primary = models.BooleanField(
        _("primary organization"),
        default=False,
        help_text=_("Denotes whether this is the primary affiliation of the contributor."),
    )

    is_current = models.BooleanField(
        _("is current"),
        default=True,
        help_text=_("Denotes whether this is a current affiliation of the contributor."),
    )

    class Meta:
        verbose_name = _("affiliation")
        verbose_name_plural = _("affiliations")

    def __str__(self):
        return f"{self.person} - {self.organization}"


class Organization(Contributor):
    """An organization is a contributor that represents a group of people, such as a university, research institute,
    company or government agency. Organizations can have multiple members and can be affiliated with other organizations.
    Organizations can also have sub-organizations, such as departments or research groups."""

    DEFAULT_IDENTIFIER = "ROR"

    members = models.ManyToManyField(
        to="contributors.Person",
        through="contributors.OrganizationMember",
        verbose_name=_("members"),
        related_name="affiliations",
        help_text=_("A list of personal contributors that are members of the organization."),
    )

    parent = models.ForeignKey(
        to="self",
        on_delete=models.CASCADE,
        related_name="sub_organizations",
        verbose_name=_("parent organization"),
        help_text=_("The organization that this organization is a part of."),
        blank=True,
        null=True,
    )

    lat = models.DecimalField(
        max_digits=7,
        decimal_places=5,
        verbose_name=_("latitude"),
        help_text=_("The latitude of the organization."),
        null=True,
        blank=True,
    )

    lon = models.DecimalField(
        max_digits=8,
        decimal_places=5,
        verbose_name=_("longitude"),
        help_text=_("The longitude of the organization."),
        null=True,
        blank=True,
    )

    city = models.CharField(
        max_length=255,
        verbose_name=_("city"),
        help_text=_("The city where the organization is based."),
        null=True,
        blank=True,
    )

    country = models.CharField(
        max_length=255,
        verbose_name=_("country"),
        help_text=_("The country where the organization is based."),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # from .utils import contributor_from_ror_data
        # contributor_from_ror_data(self.synced_data, self)
        super().save(*args, **kwargs)

    @classmethod
    def from_ror(self, data):
        """Create an organization from a ROR ID."""
        from .utils import contributor_from_ror_data

        contributor_from_ror_data(data)

    def icon(self):
        return "ror"

    def get_memberships(self):
        """
        Returns a queryset of all memberships related to this instance, with related 'person' objects fetched efficiently using select_related.

        Returns:
            QuerySet: A queryset of Membership objects associated with this instance, with related Person objects prefetched.
        """
        return self.memberships.select_related("person").all()

    def owner(self):
        """Returns the owners of the organization."""
        if memberships := self.get_memberships().filter(type=OrganizationMember.MembershipType.OWNER).first():
            return memberships.person
        return None

    def as_geojson(self):
        """Returns the organization as a GeoJSON object."""
        return json.dumps(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [self.lon, self.lat],
                },
                "properties": {
                    "name": self.name,
                    "description": self.profile,
                    "icon": self.icon(),
                    "url": self.get_absolute_url(),
                },
            },
            default=float,
        )


class Contribution(OrderedModel):
    """A contributor is a person or organisation that has contributed to the project or
    dataset. This model is based on the Datacite schema for contributors."""

    ROLES_VOCAB = FairDMRoles()
    # objects = ContributionManager().as_manager()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=23)
    content_object = GenericForeignKey("content_type", "object_id")
    contributor = models.ForeignKey(
        "contributors.Contributor",
        verbose_name=_("contributor"),
        help_text=_("The person or organisation that contributed to the project or dataset."),
        related_name="contributions",
        null=True,
        on_delete=models.SET_NULL,
    )

    # roles = models.JSONField(
    #     verbose_name=_("roles"),
    #     help_text=_("Assigned roles for this contributor."),
    #     default=list,
    #     null=True,
    #     blank=True,
    # )

    roles = ConceptManyToManyField(
        vocabulary=FairDMRoles,
        verbose_name=_("roles"),
        help_text=_("The roles assigned to the contributor for this contribution."),
    )

    # we can't rely on the contributor field to store necessary information, as the profile may have changed or been deleted, therefore we need to store the contributor's name and other details at the time of publication
    store = models.JSONField(
        _("contributor"),
        help_text=_("A JSON representation of the contributor profile at the time of publication"),
        default=dict,
    )

    # holds the permissions for each contributor, e.g. whether they can edit the object
    permissions = models.JSONField(
        _("permissions"),
        help_text=_("A JSON representation of the contributor's permissions at the time of publication"),
        default=contributor_permissions_default,
    )

    class Meta:
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")
        unique_together = ("content_type", "object_id", "contributor")
        ordering = ["object_id", "order"]

    def save(self, *args, **kwargs):
        if self.contributor.type_of == Person:
            if self.contributor.is_superuser and settings.DEBUG is False:
                # disallow superusers from being contributors
                raise ValueError(
                    _(
                        "Superusers cannot be contributors. Please remove the superuser status or use a different account."
                    )
                )

        # if not self.pk:
        #     # If this is a new contribution, we need to store the contributor's profile data
        #     if self.contributor:
        #         self.store = {
        #             "name": self.contributor.name,
        #             "given": self.contributor.given or None,
        #             "family": self.contributor.family or None,
        #         }
        #         # Store ORCID if available
        #         orcid = self.contributor.get_default_identifier()
        #         if orcid:
        #             self.store["ORCID"] = orcid.identifier
        return super().save(*args, **kwargs)

    def __str__(self):
        return force_str(self.contributor)

    def __repr__(self):
        return f"<{self.contributor}: {self.roles}>"

    def add_roles(self, roles: list):
        """Adds a role to the contributor."""

        self.roles += roles
        self.roles = sorted(set(self.roles))
        self.save()

    def verbose_roles(self):
        """Returns a human-readable list of roles for the contributor."""
        roles_dict = dict(self.ROLES_VOCAB.choices)
        return [roles_dict.get(role) for role in self.roles]

    def get_absolute_url(self):
        """Returns the absolute url of the contributor's profile."""
        return self.contributor.get_absolute_url()

    def get_update_url(self):
        related_name = self.object._meta.model_name
        letter = related_name[0]
        return reverse("contribution-update", kwargs={"uuid": self.object.uuid, "model": letter})

    def profile_to_data(self):
        """Converts the profile to a JSON object."""

        data = {
            "name": self.profile.name,
            "given": self.profile.given,
            "family": self.profile.family,
        }

        ORCID = self.profile.identifiers.filter(scheme="ORCID").first()
        if ORCID:
            data["ORCID"] = ORCID.identifier

        affiliation = self.profile.primary_affiliation()
        if affiliation:
            data["affiliation"] = affiliation

        return data

    def from_contributor(self, contributor):
        """Creates a new contribution from a contributor object."""
        return self.objects.create(contributor=contributor)

    def icon(self):
        return "ror"


class ContributorRole(AbstractConcept):
    vocabulary_name = None
    vocabulary = None
    _vocabulary = FairDMRoles()

    class Meta:
        verbose_name = _("role")
        verbose_name_plural = _("roles")


class ContributorIdentifier(AbstractIdentifier):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Contributor", on_delete=models.CASCADE)


def forwards():
    EmailAddress = apps.get_model("account.EmailAddress")
    User = apps.get_model(settings.AUTH_USER_MODEL)
    user_email_field = getattr(settings, "ACCOUNT_USER_MODEL_EMAIL_FIELD", "email")

    def get_users_with_multiple_primary_email():
        user_uuids = []
        for email_address_dict in (
            EmailAddress.objects.filter(primary=True).values("user").annotate(Count("user")).filter(user__count__gt=1)
        ):
            user_uuids.append(email_address_dict["user"])
        return User.objects.filter(uuid__in=user_uuids)

    def unset_extra_primary_emails(user):
        qs = EmailAddress.objects.filter(user=user, primary=True)
        primary_email_addresses = list(qs)
        if not primary_email_addresses:
            return
        primary_email_address = primary_email_addresses[0]
        if user_email_field:
            for address in primary_email_addresses:
                if address.email.lower() == getattr(user, user_email_field, "").lower():
                    primary_email_address = address
                    break
        qs.exclude(uuid=primary_email_address.uuid).update(primary=False)

    for user in get_users_with_multiple_primary_email().iterator():
        unset_extra_primary_emails(user)

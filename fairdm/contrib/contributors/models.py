import json
from functools import cached_property

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
from django_countries.fields import CountryField
from django_lifecycle import AFTER_CREATE, AFTER_DELETE, BEFORE_CREATE, hook
from django_lifecycle.mixins import LifecycleModelMixin
from easy_icons import icon
from easy_thumbnails.fields import ThumbnailerImageField
from jsonfield_toolkit.models import ArrayField
from model_utils import FieldTracker
from ordered_model.models import OrderedModel
from research_vocabs.fields import ConceptManyToManyField
from shortuuid.django_fields import ShortUUIDField

from fairdm.core.abstract import AbstractIdentifier
from fairdm.core.vocabularies import FairDMIdentifiers, FairDMRoles
from fairdm.db import models

# from polymorphic.models import PolymorphicModel
from fairdm.db.models import PolymorphicModel
from fairdm.utils.models import PolymorphicMixin
from fairdm.utils.permissions import remove_all_model_perms
from fairdm.utils.utils import default_image_path

from .managers import PersonalContributorsManager, UserManager
from .validators import validate_iso_639_1_language_code


def contributor_permissions_default():
    return {"edit": False}


class Contributor(PolymorphicMixin, PolymorphicModel):
    """
    Base model for contributors to research data.

    A Contributor represents a person or organization that makes contributions to
    projects, datasets, samples, or measurements within the database. This model stores
    publicly available information for proper attribution and formal publication, aligned
    with DataCite Contributor schema.

    This is a polymorphic model with two concrete implementations:
    - Person: Individual contributors
    - Organization: Institutional contributors

    Attributes:
        uuid (ShortUUIDField): Unique identifier for the contributor
        name (CharField): Full name of the contributor
        profile (TextField): Biographical information or description
        avatar (ThumbnailerImageField): Profile picture
        links (ArrayField): URLs to external profiles/websites
        keywords (ConceptManyToManyField): Research topics and interests
        synced_data (JSONField): Raw data from external identifier sync
        last_synced (DateTimeField): Last synchronization timestamp
        weight (FloatField): Sorting weight based on contributions and profile completeness
        owner (ForeignKey): User who manages this contributor profile
        permissions (JSONField): Access control permissions
        created (DateTimeField): Record creation timestamp
        modified (DateTimeField): Record modification timestamp

    Lifecycle Hooks:
        - update_weight: Recalculates weight when synced_data changes

    Abstract Methods (implemented by subclasses):
        - icon: Returns the icon identifier
        - default_identifier: Returns the primary external identifier
        - calculate_profile_completion: Returns completion percentage (0-1)

    See Also:
        - Person: Individual contributor implementation
        - Organization: Institutional contributor implementation
        - Contribution: Links contributors to research objects
    """

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
        help_text=_("A profile image for the contributor. This is displayed in the contributor's profile."),
        resize_source={
            "size": (1200, 1200),
            "format": "WEBP",
        },
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
        base_field=models.CharField(max_length=5, validators=[validate_iso_639_1_language_code]),
        verbose_name=_("language"),
        help_text=_("ISO 639-1 language codes (e.g., 'en', 'es', 'fr')."),
        blank=True,
        null=True,
        default=list,
        error_messages={
            "item_invalid": _("Item %(nth)s in the array is invalid."),
        },
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

    weight = models.FloatField(
        _("weight"),
        help_text=_(
            "A weighting factor to determine sort order of contributors in public lists based on their contributions, completion of profile and linking of external identifiers."
        ),
        default=1.0,
        editable=False,
    )

    location = models.ForeignKey(
        "fairdm_location.Point",
        verbose_name=_("location"),
        help_text=_("The geographic location of the contributor."),
        on_delete=models.SET_NULL,
        related_name="contributors",
        null=True,
        blank=True,
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

    class Meta:  # type: ignore
        ordering = ["name"]
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")

    def save(self, *args, **kwargs):
        """
        Save the contributor instance.

        Automatically updates the last_synced field when synced_data changes,
        tracking when the contributor was last synchronized with external
        providers (ORCID, ROR).
        """
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

    @property
    def default_identifier(self):
        """Returns the default identifier for this contributor."""
        return self.identifiers.filter(type=self.DEFAULT_IDENTIFIER).first()

    def profile_image(self):
        if self.image:
            return self.image.url
        return static("img/brand/icon.svg")

    def get_initials(self):
        """Return initials from the first letter of the first two words in the name."""
        if not self.name:
            return
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        if len(words) == 1 and words[0]:
            return words[0][0].upper()
        return "?"

    @classproperty
    def type_of(cls):
        # this is required for many of the class methods in PolymorphicMixin
        return Contributor

    def type(self):
        return self.polymorphic_ctype.model

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

    def calculate_profile_completion(self):
        """
        Calculate the profile completion percentage.

        Checks for presence of key fields: profile text, image, and links.

        Returns:
            float: Profile completion percentage (0.0 to 1.0)
        """
        fields_to_check = ["profile", "image", "links"]
        filled_fields = sum(1 for field in fields_to_check if getattr(self, field))
        return filled_fields / len(fields_to_check)

    def calculate_weight(self):
        """
        Calculate contributor weight for ranking in lists.

        Weight is calculated based on:
        - Number of contributions (50%)
        - Profile completion (30%)
        - Presence of external identifiers (20%)

        Returns:
            float: Weight value between 0.0 and 1.0
        """
        # Contribution count component (0-1 scale, max at 10 contributions)
        contribution_count = min(self.contributions.count() / 10.0, 1.0)

        # Profile completion component (0-1 scale)
        profile_completion = self.calculate_profile_completion()

        # Identifier presence component (0-1 scale)
        has_identifiers = 1.0 if self.identifiers.exists() else 0.0

        # Weighted sum
        weight = (contribution_count * 0.5) + (profile_completion * 0.3) + (has_identifiers * 0.2)

        return round(weight, 2)

    def to_datacite(self):
        """
        Export contributor metadata in DataCite JSON format.

        Returns DataCite-compatible creator/contributor object following
        the DataCite Metadata Schema 4.4.

        Returns:
            dict: DataCite-formatted contributor metadata
        """
        from .utils.transforms import contributor_to_datacite

        return contributor_to_datacite(self)

    def to_schema_org(self):
        """
        Export contributor metadata in Schema.org JSON-LD format.

        Returns Schema.org-compatible Person or Organization object.

        Returns:
            dict: Schema.org JSON-LD formatted contributor metadata
        """
        from .utils.transforms import contributor_to_schema_org

        return contributor_to_schema_org(self)

    def get_recent_contributions(self, limit: int = 5):
        """
        Get the most recent contributions by this contributor.

        Args:
            limit: Maximum number of contributions to return (default: 5)

        Returns:
            QuerySet: Recent Contribution objects ordered by creation date
        """
        return self.contributions.select_related("content_type").order_by("-id")[:limit]

    def get_contributions_by_type(self, model_name: str):
        """
        Get all contributions to a specific type of object (project, dataset, sample, measurement).

        Args:
            model_name: Name of the model (e.g., 'project', 'dataset', 'sample', 'measurement')

        Returns:
            QuerySet: Contribution objects filtered by content type

        Example:
            >>> person.get_contributions_by_type("project")
            <QuerySet [<Contribution: John Doe: ['ContactPerson']>]>
        """
        content_type = ContentType.objects.get(
            app_label=(model_name.split(".")[0] if "." in model_name else model_name.lower()),
            model=model_name.split(".")[-1].lower(),
        )
        return self.contributions.filter(content_type=content_type).select_related("content_type")

    def has_contribution_to(self, obj) -> bool:
        """
        Check if this contributor has contributed to a specific object.

        Args:
            obj: A Project, Dataset, Sample, or Measurement instance

        Returns:
            bool: True if contributor has contributed to the object, False otherwise

        Example:
            >>> person.has_contribution_to(my_project)
            True
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.contributions.filter(content_type=content_type, object_id=obj.pk).exists()

    def get_co_contributors(self, limit: int | None = None):
        """
        Get other contributors who have contributed to the same objects as this contributor.

        Returns contributors ordered by frequency of co-contribution (most frequent first).

        Args:
            limit: Maximum number of co-contributors to return (default: all)

        Returns:
            QuerySet: Contributor objects ordered by co-contribution count

        Example:
            >>> person.get_co_contributors(limit=5)
            <QuerySet [<Person: Jane Smith>, <Person: Bob Wilson>, ...]>
        """
        # Get all content objects this contributor has contributed to
        my_contributions = self.contributions.values_list("content_type_id", "object_id")

        # Find other contributors to those same objects
        from django.db.models import Count

        co_contributors = (
            Contributor.objects.filter(contributions__content_type_id__in=[ct for ct, _ in my_contributions])
            .filter(contributions__object_id__in=[oid for _, oid in my_contributions])
            .exclude(pk=self.pk)  # Exclude self
            .annotate(collaboration_count=Count("contributions"))
            .order_by("-collaboration_count")
        )

        if limit:
            return co_contributors[:limit]
        return co_contributors

    def add_to(self, obj, roles=None):
        """Adds the contributor to a project, dataset, sample or measurement."""
        if roles is None:
            roles = []
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
    contributors = PersonalContributorsManager()  # type: ignore[var-annotated]

    # null is allowed for the email field, as a Person object/User account can be created by someone else. E.g. when
    # adding a new contributor to a database entry.
    # The email field is not stored in this case, as we don't have permission from the email owner.
    email = models.EmailField(_("email address"), unique=True, null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    username = Contributor.__str__
    tracker = FieldTracker()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def clean(self):
        """Validate Person fields including email, URLs, and ORCID format."""
        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator, validate_email

        super().clean()

        # Clean empty email to None
        if self.email == "":
            self.email = None

        # Validate email if provided
        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError({"email": _("Enter a valid email address.")}) from None

        # Validate URLs in links array
        if self.links:
            url_validator = URLValidator()
            for url in self.links:
                try:
                    url_validator(url)
                except ValidationError:
                    raise ValidationError({"links": _(f"Invalid URL: {url}")}) from None

        # Validate ORCID format if present
        if orcid := self.identifiers.filter(type="ORCID").first():
            orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
            import re

            if not re.match(orcid_pattern, orcid.value):
                raise ValidationError(
                    {"identifiers": _(f"Invalid ORCID format: {orcid.value}. Expected format: 0000-0000-0000-0000")}
                )

    def orcid(self):
        return self.identifiers.filter(type="ORCID").first()

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
        Get all current affiliations for this person.

        Returns a queryset of OrganizationMember objects representing the contributor's
        current affiliations, optimized with select_related to include Organization data.

        Returns:
            QuerySet: Current OrganizationMember objects
        """
        return self.organization_memberships.select_related("organization").filter(is_current=True)

    @property
    def given(self):
        """Alias for self.first_name."""
        return self.first_name

    @property
    def family(self):
        """Alias for self.last_name."""
        return self.last_name

    def get_full_name_display(self, name_format: str = "given_family") -> str:
        """
        Get formatted full name with various display options.

        Args:
            name_format: Display format - one of:
                - "given_family": "John Doe" (default)
                - "family_given": "Doe, John"
                - "family_initial": "Doe, J."
                - "initials_family": "J. Doe"

        Returns:
            str: Formatted full name, falls back to self.name if components missing
        """
        if not self.first_name and not self.last_name:
            return self.name

        first = self.first_name or ""
        last = self.last_name or ""

        if name_format == "family_given":
            parts = [p for p in [last, first] if p]
            return ", ".join(parts) if len(parts) > 1 else parts[0] if parts else self.name
        elif name_format == "family_initial":
            initial = f"{first[0]}." if first else ""
            parts = [p for p in [last, initial] if p]
            return ", ".join(parts) if len(parts) > 1 else parts[0] if parts else self.name
        elif name_format == "initials_family":
            initial = f"{first[0]}." if first else ""
            parts = [p for p in [initial, last] if p]
            return " ".join(parts) if parts else self.name
        else:  # given_family (default)
            parts = [p for p in [first, last] if p]
            return " ".join(parts) if parts else self.name

    @property
    def orcid_is_authenticated(self):
        return self.get_provider("orcid") is not None

    def icon(self):
        if self.orcid_is_authenticated:
            return "orcid"
        return "orcid_unauthenticated"

    @classmethod
    def from_orcid(cls, orcid_id):
        """Create a person from ORCID data."""
        from .utils.transforms import ORCIDTransform

        return ORCIDTransform.update_or_create(orcid_id)

    def as_geojson(self):
        """Returns the organization as a GeoJSON object."""
        aff = self.primary_affiliation()
        if aff and aff.organization.location:
            org = aff.organization
            return json.dumps(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [org.location.longitude, org.location.latitude],
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
        return None

    @cached_property
    def is_data_admin(self):
        """Check if the contributor is a data administrator."""
        return self.is_superuser or self.groups.filter(name="Data Administrators").exists()

    def get_location_display(self):
        """Get a human-readable location string."""
        aff = self.primary_affiliation()
        if aff and aff.organization:
            org = aff.organization
            parts = []
            if org.city:
                parts.append(org.city)
            if org.country:
                parts.append(org.country.name)
            return ", ".join(parts)
        return None


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
        unique_together = ("person", "organization")

    def save(self, *args, **kwargs):
        """Ensure only one primary affiliation per person."""
        if self.is_primary:
            # Unset other primary affiliations for this person
            OrganizationMember.objects.filter(person=self.person, is_primary=True).exclude(pk=self.pk).update(
                is_primary=False
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.person} - {self.organization}"


class Organization(Contributor):
    """An organization is a contributor that represents a group of people, such as a university, research institute,
    company or government agency. Organizations can have multiple members and can be affiliated with other organizations.
    Organizations can also have sub-organizations, such as departments or research groups.
    """

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

    city = models.CharField(
        max_length=255,
        verbose_name=_("city"),
        help_text=_("The city where the organization is based."),
        null=True,
        blank=True,
    )

    country = CountryField(
        blank_label=_("(Select a country)"),
        verbose_name=_("country"),
        help_text=_("The country where the organization is based."),
        null=True,
        blank=True,
    )

    @property
    def lat(self):
        """Backwards-compatible property for latitude."""
        return self.location.latitude if self.location else None

    @property
    def lon(self):
        """Backwards-compatible property for longitude."""
        return self.location.longitude if self.location else None

    tracker = FieldTracker()

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")

    def __str__(self):
        return self.name

    def clean(self):
        """Validate Organization fields including URLs and ROR format."""
        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator

        super().clean()

        # Validate URLs in links array
        if self.links:
            url_validator = URLValidator()
            for url in self.links:
                try:
                    url_validator(url)
                except ValidationError:
                    raise ValidationError({"links": _(f"Invalid URL: {url}")}) from None

        # Validate ROR format if present (only if saved - identifiers don't exist before save)
        if self.pk and (ror := self.identifiers.filter(type="ROR").first()):
            # ROR IDs are alphanumeric strings starting with 0
            ror_pattern = r"^0[a-z0-9]{6}[0-9]{2}$"
            import re

            if not re.match(ror_pattern, ror.value):
                raise ValidationError(
                    {"identifiers": _(f"Invalid ROR format: {ror.value}. Expected format: 0xxxxxx00")}
                ) from None

    @hook(AFTER_CREATE)
    def update_identifier(self):
        """
        Extract and create ROR identifier after organization creation.

        This lifecycle hook automatically creates a ContributorIdentifier
        record when an organization is created with ROR data in synced_data.
        This ensures proper external identifier linking for organizations
        imported from ROR.
        """
        if self.synced_data:
            ror = self.synced_data.get("id")
            self.identifiers.add(type="ROR", value=ror)

    @classmethod
    def from_ror(self, ror, commit=True):
        """Create an organization from a ROR ID."""
        from .utils.transforms import RORTransform

        return RORTransform.update_or_create(ror, commit)

    def icon(self):
        return "organization"

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
        if not self.location:
            return None
        return json.dumps(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [self.location.longitude, self.location.latitude],
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

    def get_location_display(self):
        """Get a human-readable location string."""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country.name)
        return ", ".join(parts) if parts else None


class Contribution(LifecycleModelMixin, OrderedModel):
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

    roles = ConceptManyToManyField(
        vocabulary=FairDMRoles,
        verbose_name=_("roles"),
        help_text=_("The roles assigned to the contributor for this contribution."),
    )

    affiliation = models.ForeignKey(
        "contributors.Organization",
        verbose_name=_("affiliation"),
        help_text=_("The organization that the contributor is affiliated with for this contribution."),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,  # Prevent deletion of the Organization if there are contributions associated with it
    )

    class Meta:
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")
        unique_together = ("content_type", "object_id", "contributor")
        ordering = ["object_id", "order"]

    @classmethod
    def add_to(cls, contributor, obj, roles=None, affiliation=None):
        """Add a contributor to an object with specified roles and affiliation."""
        contribution, _created = cls.objects.get_or_create(
            contributor=contributor,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            defaults={"affiliation": affiliation} if affiliation else {},
        )
        if roles:
            from research_vocabs.models import Concept

            roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles", name__in=roles)
            contribution.roles.set(roles_qs)
        return contribution

    def save(self, *args, **kwargs):
        if self.contributor.type_of == Person and self.contributor.is_superuser and settings.DEBUG is False:
            # disallow superusers from being contributors
            raise ValueError(
                _("Superusers cannot be contributors. Please remove the superuser status or use a different account.")
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        return force_str(self.contributor)

    def __repr__(self):
        return f"<{self.contributor}: {self.roles}>"

    @hook(BEFORE_CREATE)
    def set_default_affiliation(self):
        """
        Automatically set affiliation for person contributors.

        If a contribution is being created by a Person and no affiliation
        is specified, this hook will use the person's primary organizational
        affiliation as the default. This ensures proper attribution and
        organizational linking for contributions.

        Only runs before contribution creation and only for Person contributors.
        """
        if not self.affiliation and self.is_person():  # noqa: SIM102
            # Set the users primary_affiliation as default
            if org := self.contributor.organization_memberships.filter(is_primary=True).first():
                self.affiliation = org.organization

    @hook(AFTER_DELETE)
    def remove_user_perms(self):
        """
        Clean up permissions when a contribution is deleted.

        This lifecycle hook automatically removes all object-level permissions
        that were granted to a person contributor on the contributed object.
        This ensures proper permission cleanup and prevents orphaned permissions
        when contributions are removed.

        Only applies to Person contributors (not organizations).
        """
        if self.is_person():
            remove_all_model_perms(self.contributor, self.content_object)

    def is_person(self):
        """Check if the contributor is a person."""
        return isinstance(self.contributor, Person)

    def get_absolute_url(self):
        """Returns the absolute url of the contributor's profile."""
        return self.contributor.get_absolute_url()

    def get_update_url(self):
        related_name = self.object._meta.model_name
        letter = related_name[0]
        return reverse("contribution-update", kwargs={"uuid": self.object.uuid, "model": letter})


class ContributorIdentifier(AbstractIdentifier, LifecycleModelMixin):
    VOCABULARY = FairDMIdentifiers()
    related = models.ForeignKey("Contributor", on_delete=models.CASCADE)

    @hook(AFTER_CREATE)
    def fetch_ror_data(self):
        """
        Fetch organization data from ROR API when a ROR identifier is added.

        This lifecycle hook automatically fetches metadata from the ROR API
        when a new ROR identifier is created for an Organization. The fetched
        data is stored in the organization's synced_data field.
        """
        if self.type == "ROR" and isinstance(self.related, Organization):
            from .utils.transforms import RORTransform

            try:
                ror_data = RORTransform.fetch_from_api(self.value)
                # Store the fetched data
                self.related.synced_data = ror_data
                self.related.save(update_fields=["synced_data"])
            except Exception as e:
                # Log the error but don't prevent the identifier from being saved
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to fetch ROR data for {self.value}: {e}")


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

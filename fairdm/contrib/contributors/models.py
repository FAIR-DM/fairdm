import json
import logging
from functools import cached_property

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django.db.models.functions import Lower
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from django_lifecycle import AFTER_CREATE, BEFORE_CREATE, hook
from django_lifecycle.mixins import LifecycleModelMixin
from easy_icons import icon
from easy_thumbnails.fields import ThumbnailerImageField
from model_utils import FieldTracker
from ordered_model.models import OrderedModel
from research_vocabs.fields import ConceptManyToManyField
from shortuuid.django_fields import ShortUUIDField

from fairdm.core.abstract import AbstractIdentifier
from fairdm.core.vocabularies import FairDMIdentifiers, FairDMRoles
from fairdm.db import models
from fairdm.db.fields import PartialDateField

# from polymorphic.models import PolymorphicModel
from fairdm.db.models import PolymorphicModel
from fairdm.utils.models import PolymorphicMixin
from fairdm.utils.utils import default_image_path

from .choices import AccountState, OrganizationType
from .managers import AffiliationManager, ContributionManager, UserManager
from .validators import validate_iso_639_1_language_codes

logger = logging.getLogger(__name__)


def contributor_permissions_default() -> dict:
    """Default permissions for contributions. Referenced by migration 0001."""
    return {}


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
        uuid (ShortUUIDField): Public identifier for the contributor
        image (ThumbnailerImageField): Profile image
        name (CharField): Preferred name of the contributor
        alternative_names (JSONField): Other names by which the contributor is known
        profile (TextField): Free-text description
        links (JSONField): URLs to related online resources
        lang (JSONField): ISO 639-1 language preferences
        location (ForeignKey): Geographic location
        last_synced (DateField): Last synchronization timestamp
        synced_data (JSONField): Raw data from external identifier sync
        config (JSONField): General-purpose configuration data; this specification does
            not define its contents
        added (DateTimeField): Record creation timestamp
        modified (DateTimeField): Record modification timestamp

    Abstract Methods (implemented by subclasses):
        - icon: Returns the icon identifier
        - default_identifier: Returns the primary external identifier

    See Also:
        - Person: Individual contributor implementation
        - Organization: Institutional contributor implementation
        - Contribution: Links contributors to research objects
    """

    uuid = ShortUUIDField(
        editable=False,
        unique=True,
        prefix="c",
        verbose_name=_("UUID"),
        help_text=_("The contributor's public identifier."),
    )

    image = ThumbnailerImageField(
        verbose_name=_("profile image"),
        blank=True,
        null=True,
        upload_to=default_image_path,
        help_text=_(
            "A profile image for the contributor. This is displayed in the contributor's profile."
        ),
        resize_source={
            "size": (1200, 1200),
            "format": "WEBP",
        },
    )

    name = models.CharField(
        max_length=512,
        verbose_name=_("preferred name"),
        help_text=_("The name by which the contributor is publicly known."),
    )

    alternative_names = models.JSONField(
        verbose_name=_("alternative names"),
        help_text=_("Any other names by which the contributor is known."),
        null=True,
        blank=True,
        default=list,
    )

    profile = models.TextField(
        verbose_name=_("profile"),
        help_text=_("A free-text description of the contributor."),
        null=True,
        blank=True,
    )

    links = models.JSONField(
        verbose_name=_("links"),
        help_text=_("A list of online resources related to this contributor."),
        null=True,
        blank=True,
        default=list,
    )

    lang = models.JSONField(
        verbose_name=_("language"),
        help_text=_("ISO 639-1 language codes (e.g., 'en', 'es', 'fr')."),
        blank=True,
        null=True,
        default=list,
        validators=[validate_iso_639_1_language_codes],
    )

    last_synced = models.DateField(
        verbose_name=_("last synced"),
        help_text=_(
            "The last time the contributor was synced with the external provider (e.g. ORCID, ROR)."
        ),
        editable=False,
        null=True,
        blank=True,
        default=None,
    )

    synced_data = models.JSONField(
        verbose_name=_("synced data"),
        help_text=_(
            "A JSON representation of the contributor's data from the external provider."
        ),
        editable=False,
        null=True,
        blank=True,
        default=dict,
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

    config = models.JSONField(
        verbose_name=_("configuration"),
        help_text=_(
            "General-purpose configuration data for this contributor. This specification "
            "does not define its contents."
        ),
        default=dict,
        blank=True,
    )

    added = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date added"),
        help_text=_("The date and time this record was added to the database."),
    )
    modified = models.DateTimeField(
        auto_now=True,
        db_index=True,
        verbose_name=_("Last modified"),
        help_text=_("The date and time this record was last modified."),
    )

    tracker = FieldTracker()

    class Meta:  # type: ignore[no-redef]
        ordering = ["name"]
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")
        default_related_name = "contributors"

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

    def credited_object_ids(self, base_model):
        """Object ids of this contributor's credits whose content type is ``base_model``
        or one of its polymorphic subclasses.

        Django's multi-table inheritance gives every polymorphic subclass row the same
        primary key as its base row, so these ids double as ``base_model`` primary keys
        directly. That's what lets ``samples`` and ``measurements`` below find a credit
        recorded against a concrete specimen or measurement type - ``Sample`` and
        ``Measurement`` can never be instantiated directly, so every real credit is
        stored under a subclass's own content type, which a ``GenericRelation`` reverse
        query from the polymorphic base alone cannot match (FR-034).
        """
        content_type_ids = self.contributions.values_list(
            "content_type_id", flat=True
        ).distinct()
        matching_type_ids = [
            content_type_id
            for content_type_id in content_type_ids
            if issubclass(
                ContentType.objects.get_for_id(content_type_id).model_class() or object,
                base_model,
            )
        ]
        return self.contributions.filter(
            content_type_id__in=matching_type_ids
        ).values_list("object_id", flat=True)

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
        """Every specimen this contributor is credited on, resolved through the concrete
        type each contribution actually names (FR-034; see ``credited_object_ids``)."""
        Sample = apps.get_model("sample.Sample")
        return Sample.objects.filter(pk__in=self.credited_object_ids(Sample))

    @property
    def measurements(self):
        """Every measurement this contributor is credited on - see ``samples`` above."""
        Measurement = apps.get_model("measurement.Measurement")
        return Measurement.objects.filter(pk__in=self.credited_object_ids(Measurement))

    def get_credit_counts(self):
        """Report this contributor's credit count for each kind of research output
        (FR-034).

        Resolved in a bounded number of queries: one to group and count credits by
        content type, plus one more per distinct content type encountered - at most
        four, one for each of project, dataset, sample and measurement.

        Returns:
            dict: Mapping of each credited model's plural verbose name to its count.
        """
        counts_by_type = self.contributions.values("content_type").annotate(
            total=Count("id")
        )
        result = {}
        for entry in counts_by_type:
            model_class = ContentType.objects.get_for_id(
                entry["content_type"]
            ).model_class()
            if model_class is not None:
                result[model_class._meta.verbose_name_plural] = entry["total"]
        return result

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
            app_label=(
                model_name.split(".")[0] if "." in model_name else model_name.lower()
            ),
            model=model_name.split(".")[-1].lower(),
        )
        return self.contributions.filter(content_type=content_type).select_related(
            "content_type"
        )

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
        return self.contributions.filter(
            content_type=content_type, object_id=obj.pk
        ).exists()

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
        # The (content_type, object_id) pairs this contributor is actually credited on.
        my_contributions = list(
            self.contributions.values_list("content_type_id", "object_id")
        )
        if not my_contributions:
            return Contributor.objects.none()

        from django.db.models import Count, Q

        # Matches a contribution sharing one of *my* exact (content_type, object_id)
        # pairs - not merely any of my content types together with any of my object
        # ids, which two separate filter() calls would allow to pair up across
        # different objects entirely.
        shared_credit = Q()
        for content_type_id, object_id in my_contributions:
            shared_credit |= Q(
                contributions__content_type_id=content_type_id,
                contributions__object_id=object_id,
            )

        co_contributors = (
            Contributor.objects.exclude(pk=self.pk)
            .annotate(
                collaboration_count=Count(
                    "contributions", filter=shared_credit, distinct=True
                )
            )
            .filter(collaboration_count__gt=0)
            .order_by("-collaboration_count")
        )

        if limit:
            return co_contributors[:limit]
        return co_contributors

    def add_to(self, obj, roles=None):
        """Adds the contributor to a project, dataset, sample or measurement."""
        if roles is None:
            roles = []
        contribution, _ = Contribution.objects.get_or_create(
            contributor=self,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
        )
        if roles:
            from research_vocabs.models import Concept

            roles_qs = Concept.objects.filter(
                vocabulary__name="fairdm-roles", name__in=roles
            )
            # accumulate, don't replace (FR-031, design review SPEC-001): a second
            # credit under a new role must add to the roles already recorded, not
            # discard them.
            contribution.roles.add(*roles_qs)
        return contribution


class Person(AbstractUser, Contributor):
    DEFAULT_IDENTIFIER = "ORCID"

    objects = UserManager()  # type: ignore[var-annotated]

    # null is allowed for the email field, as a Person object/User account can be created by someone else. E.g. when
    # adding a new contributor to a database entry.
    email = models.EmailField(
        _("email address"),
        help_text=_(
            "The person's email address. Null for an unclaimed profile created for "
            "attribution alone."
        ),
        null=True,
        blank=True,
        # Django's auth checks require the field named by USERNAME_FIELD to be
        # unique (auth.W004), and they read this flag rather than Meta.constraints.
        # The case-insensitive constraint in Meta is the stronger rule and the one
        # that actually stops two people sharing an address; this keeps Django's own
        # contract satisfied rather than silencing the check that states it.
        unique=True,
    )

    is_claimed = models.BooleanField(
        _("is claimed"),
        default=False,
        db_index=True,
        help_text=_(
            "True if this person has claimed their account. False for ghost/invited profiles. "
            "Indexed because the account-state filters and the administrative claim-status "
            "filter both read it (decisions.md D8, Article IX)."
        ),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="unique_person_email_ci",
                condition=models.Q(email__isnull=False),
                violation_error_message=_(
                    "A person with this email address already exists."
                ),
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Save Person, auto-populating name from first/last if blank."""
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    @property
    def account_state(self) -> AccountState:
        """The person's account state, derived rather than stored (decisions.md D8).

        Computed from `is_active`, `is_claimed` and `email` in a fixed
        precedence, so it can never disagree with the fields it reads:
        inactive if the account is deactivated, otherwise claimed, otherwise
        invited if an email address is present, otherwise ghost.
        `PersonQuerySet`'s four state filters mirror this exact ordering.

        Returns:
            AccountState: exactly one of INACTIVE, CLAIMED, INVITED or GHOST.
        """
        if not self.is_active:
            return AccountState.INACTIVE
        if self.is_claimed:
            return AccountState.CLAIMED
        if self.email:
            return AccountState.INVITED
        return AccountState.GHOST

    def clean(self):
        """Validate Person fields including email, URLs, and ORCID format."""
        import re

        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator, validate_email

        super().clean()

        # Clean empty email to None
        if self.email == "":
            self.email = None

        # Prevent claimed users from nulling their email. Reads the stored claim
        # value (is_claimed) rather than has_usable_password()/is_active - those
        # describe something else and reading them here was a fourth site
        # deciding claim status from the wrong thing (design review RECON-001,
        # decisions.md D8, D21).
        if self.pk and self.is_claimed and self.email is None:
            raise ValidationError(
                {"email": _("Claimed users cannot remove their email address.")}
            )

        # Validate and normalize email if provided
        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError(
                    {"email": _("Enter a valid email address.")}
                ) from None
            # Fully lowercase the email (Django only lowercases domain)
            self.email = self.email.lower()

        # Validate URLs in links array
        if self.links:
            url_validator = URLValidator()
            for url in self.links:
                try:
                    url_validator(url)
                except ValidationError:
                    raise ValidationError(
                        {"links": _("Invalid URL: %(url)s") % {"url": url}}
                    ) from None

        # Validate ORCID format if present
        if self.pk and (orcid := self.identifiers.filter(type="ORCID").first()):
            orcid_pattern = r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$"
            if not re.match(orcid_pattern, orcid.value):
                raise ValidationError(
                    {
                        "identifiers": _(
                            "Invalid ORCID format: %(value)s. Expected format: "
                            "0000-0000-0000-0000"
                        )
                        % {"value": orcid.value}
                    }
                )

    def orcid(self):
        return self.identifiers.filter(type="ORCID").first()

    def get_provider(self, provider: str):
        qs = self.socialaccount_set.filter(provider=provider)  # type: ignore[attr-defined]
        return qs.get() if qs else None

    def primary_affiliation(self):
        """Returns the primary affiliation for the contributor.

        Returns:
            Affiliation or None: The primary organizational affiliation, or None if not set.
        """
        return (
            self.affiliations.select_related("organization")
            .filter(is_primary=True)
            .first()
        )

    def current_affiliations(self):
        """Get all current affiliations for this person.

        Returns affiliations that have no end_date (active) and are verified (type >= MEMBER).

        Returns:
            QuerySet: Current Affiliation objects.
        """
        return self.affiliations.select_related("organization").filter(
            end_date__isnull=True, type__gte=1
        )

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
            return (
                ", ".join(parts) if len(parts) > 1 else parts[0] if parts else self.name
            )
        elif name_format == "family_initial":
            initial = f"{first[0]}." if first else ""
            parts = [p for p in [last, initial] if p]
            return (
                ", ".join(parts) if len(parts) > 1 else parts[0] if parts else self.name
            )
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
        """Create a person from ORCID data.

        Creates the Person instance synchronously using ORCIDTransform,
        then schedules async task for full ORCID data sync.

        Args:
            orcid_id: ORCID identifier (e.g., '0000-0002-1825-0097')

        Returns:
            Person: Created or updated Person instance
        """
        from django.db import transaction

        from .tasks import sync_contributor_identifier
        from .utils.transforms import ORCIDTransform

        # Create/update person synchronously
        person = ORCIDTransform.update_or_create(orcid_id)

        # Schedule async sync task after commit
        if person and person.pk:
            orcid_identifier = person.identifiers.filter(type="ORCID").first()
            if orcid_identifier:
                transaction.on_commit(
                    lambda: sync_contributor_identifier.delay(orcid_identifier.pk)
                )

        return person

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
        return (
            self.is_superuser or self.groups.filter(name="Data Administrators").exists()
        )

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


class Affiliation(models.Model):
    """An affiliation linking a person to an organization with time bounds and verification state.

    The type field implements a security state machine:
        PENDING (0): User-declared, awaiting verification
        MEMBER (1): Verified by existing member
        ADMIN (2): Can manage organization and approve pending members
        OWNER (3): Full management rights, maps to manage_organization permission

    Setting ``end_date`` ends any rights the affiliation's type would
    otherwise confer - an OWNER affiliation with an end_date no longer
    grants ``manage_organization``, for example - because rights derived
    from an affiliation are read off its *current* state, not its type
    alone (see ``AffiliationQuerySet.owners()``).

    Attributes:
        person: The affiliated person.
        organization: The organization.
        type: Security/verification state (0-3).
        is_primary: Whether this is the person's primary affiliation for citation.
        start_date: When the affiliation began (PartialDateField for variable precision).
        end_date: When it ended; NULL means active. Ends any rights the
            affiliation's type conferred.
    """

    objects = AffiliationManager()  # type: ignore[var-annotated]
    tracker = FieldTracker()

    class MembershipType(models.IntegerChoices):
        PENDING = 0, _("Pending")
        MEMBER = 1, _("Member")
        ADMIN = 2, _("Admin")
        OWNER = 3, _("Owner")

    person = models.ForeignKey(
        to="contributors.Person",
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("person"),
        help_text=_("The person that is a member of the organization."),
    )

    organization = models.ForeignKey(
        to="contributors.Organization",
        on_delete=models.CASCADE,
        related_name="affiliations",
        verbose_name=_("organization"),
        help_text=_("The organization that the person is a member of."),
    )

    type = models.IntegerField(
        _("type"),
        choices=MembershipType,
        default=MembershipType.MEMBER,
        db_index=True,
        help_text=_(
            "The verification state / role of the person within the organization."
        ),
    )

    is_primary = models.BooleanField(
        _("primary organization"),
        default=False,
        help_text=_(
            "Denotes whether this is the primary affiliation of the contributor."
        ),
    )

    start_date = PartialDateField(
        verbose_name=_("start date"),
        help_text=_(
            "When the affiliation began. Supports year, year-month, or full date precision."
        ),
        null=True,
        blank=True,
    )

    end_date = PartialDateField(
        verbose_name=_("end date"),
        help_text=_(
            "When the affiliation ended. Leave blank for active affiliations. "
            "Setting an end date ends any rights the affiliation's type would "
            "otherwise confer, such as manage_organization for an owner."
        ),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("affiliation")
        verbose_name_plural = _("affiliations")
        default_related_name = "affiliations"
        constraints = [
            models.UniqueConstraint(
                fields=["person", "organization"],
                name="unique_affiliation_person_organization",
            ),
            models.UniqueConstraint(
                fields=["person"],
                condition=models.Q(is_primary=True),
                name="unique_primary_affiliation_per_person",
            ),
        ]

    def clean(self):
        """Refuse a second membership of the same organisation with a readable
        message, rather than leaving the person to discover it as a database
        error (FR-021)."""
        from django.core.exceptions import ValidationError

        super().clean()
        if self.person_id and self.organization_id:
            duplicates = Affiliation.objects.filter(
                person=self.person, organization=self.organization
            )
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                raise ValidationError(
                    {
                        "organization": _(
                            "%(person)s is already a member of %(organization)s."
                        )
                        % {"person": self.person, "organization": self.organization}
                    }
                )

    def save(self, *args, **kwargs):
        """Ensure only one primary affiliation per person.

        The demotion of any other primary affiliation and this save happen
        inside one transaction (FR-024): if the save fails, the demotion is
        rolled back too, rather than leaving the person with none marked
        primary.
        """
        if self.is_primary:
            from django.db import transaction

            with transaction.atomic():
                Affiliation.objects.filter(person=self.person, is_primary=True).exclude(
                    pk=self.pk
                ).update(is_primary=False)
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.person} - {self.organization}"


# Backward-compatible alias
OrganizationMember = Affiliation


class Organization(Contributor):
    """An organization is a contributor that represents a group of people, such as a university, research institute,
    company or government agency. Organizations can have multiple members and can be affiliated with other organizations.
    Organizations can also have sub-organizations, such as departments or research groups.
    """

    DEFAULT_IDENTIFIER = "ROR"

    type = models.CharField(
        max_length=32,
        choices=OrganizationType.choices,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("organization type"),
        help_text=_(
            "The kind of institution this organization is, drawn from ROR's set of "
            "organization types."
        ),
    )

    members = models.ManyToManyField(
        to="contributors.Person",
        through="contributors.Affiliation",
        verbose_name=_("members"),
        related_name="+",
        help_text=_(
            "A list of personal contributors that are members of the organization."
        ),
    )

    parent = models.ForeignKey(
        to="self",
        on_delete=models.SET_NULL,
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
        db_index=True,
    )

    country = CountryField(
        blank_label=_("(Select a country)"),
        verbose_name=_("country"),
        help_text=_("The country where the organization is based."),
        null=True,
        blank=True,
        db_index=True,
    )

    @property
    def lat(self):
        """Backwards-compatible property for latitude."""
        return self.location.latitude if self.location else None

    @property
    def lon(self):
        """Backwards-compatible property for longitude."""
        return self.location.longitude if self.location else None

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")
        default_related_name = "organizations"

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
                    raise ValidationError(
                        {"links": _("Invalid URL: %(url)s") % {"url": url}}
                    ) from None

        # Validate ROR format if present (only if saved - identifiers don't exist before save)
        if self.pk and (ror := self.identifiers.filter(type="ROR").first()):
            # ROR IDs are alphanumeric strings starting with 0
            ror_pattern = r"^0[a-z0-9]{6}[0-9]{2}$"
            import re

            if not re.match(ror_pattern, ror.value):
                raise ValidationError(
                    {
                        "identifiers": _(
                            "Invalid ROR format: %(value)s. Expected format: 0xxxxxx00"
                        )
                        % {"value": ror.value}
                    }
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
            if ror:
                self.identifiers.get_or_create(type="ROR", defaults={"value": ror})

    @classmethod
    def from_ror(cls, ror, commit=True):
        """Create an organization from a ROR ID.

        Creates the Organization instance synchronously using RORTransform,
        then schedules async task for full ROR data sync if commit=True.

        Args:
            ror: ROR identifier (e.g., 'https://ror.org/04aj4c181')
            commit: Whether to save the instance (default: True)

        Returns:
            Organization: Created or updated Organization instance
        """
        from django.db import transaction

        from .tasks import sync_contributor_identifier
        from .utils.transforms import RORTransform

        # Create/update organization synchronously
        org = RORTransform.update_or_create(ror, commit)

        # Schedule async sync task after commit (only if committing)
        if commit and org and org.pk:
            ror_identifier = org.identifiers.filter(type="ROR").first()
            if ror_identifier:
                transaction.on_commit(
                    lambda: sync_contributor_identifier.delay(ror_identifier.pk)
                )

        return org

    def icon(self):
        return "organization"

    def get_memberships(self):
        """
        Returns a queryset of all memberships related to this instance, with related 'person' objects fetched efficiently using select_related.

        Returns:
            QuerySet: A queryset of Membership objects associated with this instance, with related Person objects prefetched.
        """
        return self.affiliations.select_related("person").all()

    def owner(self):
        """Returns the organization's current owner, or None if it has none.

        Derived through ``AffiliationQuerySet.owners()`` - a current
        (``end_date`` is NULL) affiliation of type OWNER - so an OWNER
        affiliation whose end_date has been set no longer counts, even
        though its type still reads OWNER (Defect A).
        """
        if membership := self.get_memberships().owners().first():
            return membership.person
        return None

    def transfer_ownership(self, new_owner):
        """Transfer ownership of this organization to an existing member.

        Demotes each *current* incumbent owner to administrator and promotes
        ``new_owner`` to owner in one atomic operation (FR-029). Management
        rights are derived from the affiliation's type at check time (D13)
        rather than stored, so this method changes only the affiliation
        records: no permission is granted, revoked or written anywhere.
        Only current OWNER affiliations (``AffiliationQuerySet.owners()``)
        are demoted - an affiliation that already carries an end date is
        history and is left exactly as it is (Defect A).

        ``new_owner`` must hold a current (no end_date) affiliation of type
        MEMBER or higher, and must be an active, claimed person. A pending,
        self-declared affiliate; an affiliation that has already ended; an
        unclaimed profile nobody controls; or a deactivated account would
        each hand control of the organization to someone who cannot be the
        intended new owner (Defect C), so each is refused with its own
        message.

        Args:
            new_owner: The Person to become the organization's owner. Must
                already hold a current, verified affiliation with this
                organization, and be an active, claimed account.

        Raises:
            ValidationError: If ``new_owner`` is not a member of this
                organization, holds only a pending or already-ended
                affiliation, or is an unclaimed or deactivated account.
        """
        from django.core.exceptions import ValidationError
        from django.db import transaction

        new_owner_affiliation = self.affiliations.filter(person=new_owner).first()
        if new_owner_affiliation is None:
            raise ValidationError(
                _("%(person)s is not a member of %(organization)s.")
                % {"person": new_owner, "organization": self}
            )
        if new_owner_affiliation.end_date is not None:
            raise ValidationError(
                _("%(person)s's affiliation with %(organization)s has ended.")
                % {"person": new_owner, "organization": self}
            )
        if new_owner_affiliation.type < Affiliation.MembershipType.MEMBER:
            raise ValidationError(
                _(
                    "%(person)s's affiliation with %(organization)s is still "
                    "pending verification."
                )
                % {"person": new_owner, "organization": self}
            )
        if not new_owner.is_claimed:
            raise ValidationError(
                _("%(person)s has not claimed their account.") % {"person": new_owner}
            )
        if not new_owner.is_active:
            raise ValidationError(
                _("%(person)s's account is deactivated.") % {"person": new_owner}
            )

        with transaction.atomic():
            self.affiliations.owners().update(type=Affiliation.MembershipType.ADMIN)
            new_owner_affiliation.type = Affiliation.MembershipType.OWNER
            new_owner_affiliation.save()

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


# Shared by Contribution.Meta's UniqueConstraint and Contribution.clean(), so a form
# validating before save and a raw insert refuse a duplicate credit with the same wording.
CONTRIBUTION_UNIQUE_PAIRING_MESSAGE = _(
    "This contributor is already credited on this object."
)


class Contribution(LifecycleModelMixin, OrderedModel):
    """A contributor is a person or organisation that has contributed to the project or
    dataset. This model is based on the Datacite schema for contributors."""

    ROLES_VOCAB = FairDMRoles()
    objects = ContributionManager()
    content_type = models.ForeignKey(
        ContentType,
        verbose_name=_("content type"),
        help_text=_("The type of object this contribution is attributed to."),
        on_delete=models.CASCADE,
    )
    object_id = models.CharField(
        verbose_name=_("object id"),
        help_text=_("The id of the object this contribution is attributed to."),
        max_length=23,
    )
    content_object = GenericForeignKey("content_type", "object_id")
    contributor = models.ForeignKey(
        "contributors.Contributor",
        verbose_name=_("contributor"),
        help_text=_(
            "The person or organisation that contributed to the project or dataset."
        ),
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
        help_text=_(
            "The organization that the contributor is affiliated with for this contribution."
        ),
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.PROTECT,  # Prevent deletion of the Organization if there are contributions associated with it
    )

    class Meta:
        verbose_name = _("contributor")
        verbose_name_plural = _("contributors")
        constraints = [
            models.UniqueConstraint(
                fields=["content_type", "object_id", "contributor"],
                name="unique_contribution_per_contributor_object",
                violation_error_message=CONTRIBUTION_UNIQUE_PAIRING_MESSAGE,
            ),
        ]
        indexes = [
            models.Index(
                fields=["content_type", "object_id"],
                name="contribution_object_idx",
            ),
        ]
        ordering = ["object_id", "order"]

    def clean(self):
        """Refuse a second credit for the same contributor/object pairing, with the same
        message the named UniqueConstraint carries (FR-031, Article IX), and refuse a role
        drawn from any vocabulary other than the framework's roles vocabulary (FR-032,
        design review SPEC-001)."""
        from django.core.exceptions import ValidationError

        super().clean()

        # clean() also runs on partially-bound instances — a generic inline formset
        # validates its forms before the parent object supplies the content type — so
        # the pairing can only be checked once all three of its parts are present.
        if self.content_type_id and self.object_id and self.contributor_id:
            duplicate = (
                Contribution.objects.exclude(pk=self.pk)
                .filter(
                    content_type_id=self.content_type_id,
                    object_id=self.object_id,
                    contributor_id=self.contributor_id,
                )
                .exists()
            )
            if duplicate:
                raise ValidationError(CONTRIBUTION_UNIQUE_PAIRING_MESSAGE)

        if self.pk and self.roles.exclude(vocabulary__name="fairdm-roles").exists():
            raise ValidationError(
                _(
                    "A contribution's roles must be drawn from the framework's roles "
                    "vocabulary."
                )
            )

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

            roles_qs = Concept.objects.filter(
                vocabulary__name="fairdm-roles", name__in=roles
            )
            # accumulate, don't replace (FR-031, design review SPEC-001): a second
            # credit under a new role must add to the roles already recorded, not
            # discard them.
            contribution.roles.add(*roles_qs)
        return contribution

    def save(self, *args, **kwargs):
        if (
            self.contributor.type_of == Person
            and self.contributor.is_superuser
            and settings.DEBUG is False
        ):
            # disallow superusers from being contributors
            raise ValueError(
                _(
                    "Superusers cannot be contributors. Please remove the superuser status or use a different account."
                )
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
            if org := self.contributor.affiliations.filter(is_primary=True).first():
                self.affiliation = org.organization

    def is_person(self):
        """Check if the contributor is a person."""
        return isinstance(self.contributor, Person)

    def get_absolute_url(self):
        """Returns the absolute url of the contributor's profile."""
        return self.contributor.get_absolute_url()

    def get_update_url(self):
        related_name = self.content_object._meta.model_name
        letter = related_name[0]
        return reverse(
            "contribution-update",
            kwargs={"uuid": self.content_object.uuid, "model": letter},
        )


class ContributorIdentifier(AbstractIdentifier, LifecycleModelMixin):
    """External identifiers for a Contributor (``Person`` or ``Organization``).

    Drawn from the contributor identifier collection
    (``FairDMIdentifiers.from_collection("Contributor")``), the union of the
    person and organisation collections rather than the unscoped vocabulary -
    a person cannot hold a specimen identifier such as IGSN (005 F1/F2).
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Contributor")
    related = models.ForeignKey(
        "Contributor",
        verbose_name=_("contributor"),
        help_text=_("The contributor this identifier belongs to."),
        on_delete=models.CASCADE,
    )

    def clean(self):
        """A contributor must not carry two identifiers of the same type (FR-038).

        The database constraint (``contributoridentifier_unique_type``) already
        refuses this; this adds a message naming the type so a form or admin caller
        sees why, ahead of the constraint's own generic message.
        """
        from django.core.exceptions import ValidationError

        super().clean()
        if self.related_id and self.type:
            duplicates = ContributorIdentifier.objects.filter(
                related_id=self.related_id, type=self.type
            )
            if self.pk:
                duplicates = duplicates.exclude(pk=self.pk)
            if duplicates.exists():
                raise ValidationError(
                    {
                        "type": _(
                            "This contributor already has an identifier of type "
                            "'%(type)s'."
                        )
                        % {"type": self.type}
                    }
                )

    @hook(AFTER_CREATE)
    def dispatch_sync_task(self):
        """Dispatch async Celery task to sync data from external API.

        Uses transaction.on_commit() to ensure the identifier is visible
        in the database before the task runs.
        """
        from django.db import transaction

        def _dispatch():
            try:
                from .tasks import sync_contributor_identifier

                sync_contributor_identifier.delay(self.pk)
            except Exception as e:
                logger.warning(
                    f"Failed to dispatch sync task for identifier {self.pk}: {e}"
                )

        transaction.on_commit(_dispatch)


class ClaimMethod(models.TextChoices):
    ORCID = "orcid", _("ORCID Social Login")
    EMAIL = "email", _("Email Verification")
    TOKEN = "token", _("Claim Token Link")
    ADMIN_MERGE = "admin_merge", _("Admin-Initiated Merge")
    ADMIN_MANUAL = "admin_manual", _("Admin Manual Activation")


class ClaimingAuditLogManager(models.Manager):
    def for_person(self, pk):
        return self.filter(
            models.Q(source_person_id=pk) | models.Q(target_person_id=pk)
        )

    def failures(self):
        return self.filter(success=False)

    def by_method(self, method: str):
        return self.filter(method=method)

    def recent(self, days: int = 30):
        from datetime import timedelta

        from django.utils import timezone as tz

        cutoff = tz.now() - timedelta(days=days)
        return self.filter(timestamp__gte=cutoff)


class ClaimingAuditLog(models.Model):
    """Immutable audit trail for all profile claiming events.

    Records are never modified or deleted — only created. The save() override
    enforces immutability at the application layer.
    """

    objects = ClaimingAuditLogManager()

    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("timestamp"))

    method = models.CharField(
        max_length=20,
        choices=ClaimMethod.choices,
        verbose_name=_("method"),
    )

    source_person = models.ForeignKey(
        "contributors.Person",
        on_delete=models.SET_NULL,
        null=True,
        related_name="claim_log_as_source",
        verbose_name=_("source person"),
        help_text=_("The unclaimed Person being claimed."),
    )

    target_person = models.ForeignKey(
        "contributors.Person",
        on_delete=models.SET_NULL,
        null=True,
        related_name="claim_log_as_target",
        verbose_name=_("target person"),
        help_text=_("The resulting claimed Person."),
    )

    initiated_by = models.ForeignKey(
        "contributors.Person",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claim_log_initiated",
        verbose_name=_("initiated by"),
        help_text=_("Admin who initiated the claim, if admin-driven."),
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP address"),
    )

    success = models.BooleanField(verbose_name=_("success"))

    failure_reason = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("failure reason"),
    )

    details = models.JSONField(default=dict, verbose_name=_("details"))

    class Meta:
        verbose_name = _("claiming audit log")
        verbose_name_plural = _("claiming audit logs")
        ordering = ["-timestamp"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValueError(
                "ClaimingAuditLog records are immutable and cannot be updated."
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.method} | {self.source_person} → {self.target_person} | {'✓' if self.success else '✗'}"


def forwards():
    EmailAddress = apps.get_model("account.EmailAddress")
    User = apps.get_model(settings.AUTH_USER_MODEL)
    user_email_field = getattr(settings, "ACCOUNT_USER_MODEL_EMAIL_FIELD", "email")

    def get_users_with_multiple_primary_email():
        user_uuids = []
        for email_address_dict in (
            EmailAddress.objects.filter(primary=True)
            .values("user")
            .annotate(Count("user"))
            .filter(user__count__gt=1)
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

"""Models for people, organisations, their identifiers and their credits on research objects."""

import json
import logging

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
from fairdm.db.models import PolymorphicModel
from fairdm.utils.models import PolymorphicMixin
from fairdm.utils.utils import default_image_path

from .choices import AccountState, OrganizationType
from .managers import AffiliationManager, ContributionManager, UserManager
from .validators import validate_iso_639_1_language_codes

logger = logging.getLogger(__name__)


def contributor_permissions_default() -> dict:
    """Return the empty default permissions dict, which migration 0001 references.

    Returns:
        An empty dict.
    """
    return {}


class Contributor(PolymorphicMixin, PolymorphicModel):
    """A person or organisation credited on projects, datasets, samples or measurements.

    Holds the public information needed for attribution and publication, aligned with the
    DataCite contributor schema. The model is polymorphic, with :class:`Person` and
    :class:`Organization` as its concrete types, and :class:`Contribution` links a
    contributor to a research object.

    Attributes:
        uuid: Public identifier.
        image: Profile image.
        name: Preferred name.
        alternative_names: Other names by which the contributor is known.
        profile: Free-text description.
        links: URLs of related online resources.
        lang: ISO 639-1 language codes.
        last_synced: When the contributor was last synced with an external provider.
        synced_data: Raw data from the external provider.
        location: Geographic location.
        config: General-purpose configuration data.
        added: When the record was created.
        modified: When the record was last modified.
        tracker: Tracks field changes, used to stamp ``last_synced``.
        is_organization: Whether the concrete type is :class:`Organization`.
    """

    is_organization = False

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
        """Stamp ``last_synced`` when ``synced_data`` has changed, then save."""
        if self.tracker.has_changed("synced_data"):
            self.last_synced = timezone.now().date()
        super().save(*args, **kwargs)

    @staticmethod
    def base_class():
        """Return ``Contributor``, which ``PolymorphicMixin`` needs as the base class."""
        return Contributor

    def __str__(self):
        """Return the contributor's name."""
        return self.name

    def get_absolute_url(self):
        """Return the URL of the contributor's overview page."""
        return reverse("contributor:overview", kwargs={"uuid": self.uuid})

    def get_update_url(self):
        """Return the URL of the contributor's edit page."""
        return reverse("contributor-update", kwargs={"uuid": self.uuid})

    def get_identifier_icon(self):
        """Return the icon for the contributor's default identifier scheme.

        Returns:
            The rendered icon.
        """
        return icon(self.DEFAULT_IDENTIFIER)

    def get_default_identifier(self):
        """Return the contributor's identifier of the default scheme.

        Reads ``identifiers.all()``, so a listing that prefetches ``identifiers`` costs no
        query per contributor.

        Returns:
            The identifier, or None when there is none.
        """
        return next(
            (i for i in self.identifiers.all() if i.type == self.DEFAULT_IDENTIFIER),
            None,
        )

    @property
    def default_identifier(self):
        """The contributor's identifier of the default scheme, or None."""
        return self.get_default_identifier()

    @property
    def primary_organization(self):
        """The organisation the contributor is shown with: None here, a person overrides it."""
        return None

    def profile_image(self):
        """Return the URL of the profile image, or of the brand icon when there is none.

        Returns:
            The image URL.
        """
        if self.image:
            return self.image.url
        return static("img/brand/icon.svg")

    def get_initials(self):
        """Return initials from the first letter of the first two words in the name.

        Returns:
            Up to two capital letters, or an empty string when there is no name.
        """
        if not self.name:
            return ""
        words = self.name.split()
        if len(words) >= 2:
            return (words[0][0] + words[1][0]).upper()
        if len(words) == 1 and words[0]:
            return words[0][0].upper()
        return "?"

    @classproperty
    def type_of(cls):
        """``Contributor``, which ``PolymorphicMixin`` needs as the base type."""
        return Contributor

    def type(self):
        """Return the name of the concrete model, such as ``person``.

        Returns:
            The model name of the polymorphic content type.
        """
        return self.polymorphic_ctype.model

    def credited_object_ids(self, base_model):
        """Return the object ids of this contributor's credits on ``base_model`` or a subclass.

        Subclass rows share their base row's primary key, so the ids are also ``base_model``
        primary keys. Credits on samples and measurements are stored under the concrete
        subclass's content type, which a reverse ``GenericRelation`` from the base cannot match.

        Args:
            base_model: The polymorphic base model, such as ``Sample``.

        Returns:
            The credited objects' ids.
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
        """The projects this contributor is credited on."""
        Project = apps.get_model("project.Project")
        return Project.objects.filter(contributors__contributor=self)

    @property
    def datasets(self):
        """The datasets this contributor is credited on."""
        Dataset = apps.get_model("dataset.Dataset")
        return Dataset.objects.filter(contributors__contributor=self)

    @property
    def samples(self):
        """The samples this contributor is credited on, whatever their concrete type."""
        Sample = apps.get_model("sample.Sample")
        return Sample.objects.filter(pk__in=self.credited_object_ids(Sample))

    @property
    def measurements(self):
        """The measurements this contributor is credited on, whatever their concrete type."""
        Measurement = apps.get_model("measurement.Measurement")
        return Measurement.objects.filter(pk__in=self.credited_object_ids(Measurement))

    def get_credit_counts(self):
        """Count this contributor's credits for each kind of research output.

        Returns:
            A map of each credited model's plural verbose name to its count.
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
        """Export the contributor as a DataCite 4.4 creator or contributor object.

        Returns:
            The DataCite metadata.
        """
        from .utils.transforms import contributor_to_datacite

        return contributor_to_datacite(self)

    def to_schema_org(self):
        """Export the contributor as a Schema.org ``Person`` or ``Organization``.

        Returns:
            The JSON-LD metadata.
        """
        from .utils.transforms import contributor_to_schema_org

        return contributor_to_schema_org(self)

    def get_recent_contributions(self, limit: int = 5):
        """Return the contributor's most recent contributions.

        Args:
            limit: Maximum number of contributions to return.

        Returns:
            Contributions, newest first.
        """
        return self.contributions.select_related("content_type").order_by("-id")[:limit]

    def get_contributions_by_type(self, model_name: str):
        """Return the contributor's contributions to one type of object.

        Args:
            model_name: The model name, such as ``project``, ``dataset``, ``sample`` or ``measurement``.

        Returns:
            Contributions to that type.

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
        """Check whether this contributor is credited on an object.

        Args:
            obj: A Project, Dataset, Sample or Measurement instance.

        Returns:
            True when the contributor is credited on the object.

        Example:
            >>> person.has_contribution_to(my_project)
            True
        """
        content_type = ContentType.objects.get_for_model(obj)
        return self.contributions.filter(
            content_type=content_type, object_id=obj.pk
        ).exists()

    def get_co_contributors(self, limit: int | None = None):
        """Return other contributors credited on the same objects, most frequent first.

        Args:
            limit: Maximum number of co-contributors to return. Defaults to all.

        Returns:
            Contributors annotated with ``collaboration_count``.

        Example:
            >>> person.get_co_contributors(limit=5)
            <QuerySet [<Person: Jane Smith>, <Person: Bob Wilson>, ...]>
        """
        my_contributions = list(
            self.contributions.values_list("content_type_id", "object_id")
        )
        if not my_contributions:
            return Contributor.objects.none()

        from django.db.models import Count, Q

        # Match exact (content_type, object_id) pairs; separate filters could pair across objects.
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
        """Credit the contributor on an object, adding roles to any already recorded.

        Args:
            obj: A project, dataset, sample or measurement.
            roles: Names of roles in the roles vocabulary.

        Returns:
            The contribution, created if it did not exist.
        """
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
            contribution.roles.add(*roles_qs)
        return contribution


class Person(AbstractUser, Contributor):
    """An individual contributor who can also sign in as a user.

    A person may be a ghost (no email), invited (email, unclaimed), claimed, or inactive.
    See :attr:`account_state`.

    Attributes:
        DEFAULT_IDENTIFIER: The identifier scheme shown by default.
        objects: The person manager.
        email: Login address, null for an unclaimed profile created for attribution alone.
        is_claimed: Whether the person has claimed the account.
        USERNAME_FIELD: The field used to sign in, which is the email.
        REQUIRED_FIELDS: Fields required by ``createsuperuser``, which is none.
        username: Removed, as people sign in by email.
    """

    DEFAULT_IDENTIFIER = "ORCID"

    objects = UserManager()  # type: ignore[var-annotated]

    email = models.EmailField(
        _("email address"),
        help_text=_(
            "The person's email address. Null for an unclaimed profile created for "
            "attribution alone."
        ),
        null=True,
        blank=True,
        # auth.W004 reads this flag, not Meta.constraints. The case-insensitive constraint is the real rule.
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
        """Return the person's name."""
        return self.name

    def save(self, *args, **kwargs):
        """Fill a blank name from the first and last names, then save."""
        if not self.name:
            self.name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    @property
    def account_state(self) -> AccountState:
        """The person's account state, derived from ``is_active``, ``is_claimed`` and ``email``.

        The precedence is inactive, then claimed, then invited when there is an email, then ghost.
        The ``PersonQuerySet`` state filters mirror this order.

        Returns:
            Exactly one of INACTIVE, CLAIMED, INVITED or GHOST.
        """
        if not self.is_active:
            return AccountState.INACTIVE
        if self.is_claimed:
            return AccountState.CLAIMED
        if self.email:
            return AccountState.INVITED
        return AccountState.GHOST

    def clean(self):
        """Normalise the email and validate it, the links and the ORCID iD."""
        import re

        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator, validate_email

        super().clean()

        if self.email == "":
            self.email = None

        if self.pk and self.is_claimed and self.email is None:
            raise ValidationError(
                {"email": _("Claimed users cannot remove their email address.")}
            )

        if self.email:
            try:
                validate_email(self.email)
            except ValidationError:
                raise ValidationError(
                    {"email": _("Enter a valid email address.")}
                ) from None
            # Django's normalisation lowercases only the domain.
            self.email = self.email.lower()

        if self.links:
            url_validator = URLValidator()
            for url in self.links:
                try:
                    url_validator(url)
                except ValidationError:
                    raise ValidationError(
                        {"links": _("Invalid URL: %(url)s") % {"url": url}}
                    ) from None

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
        """Return the person's ORCID identifier.

        Returns:
            The identifier, or None when there is none.
        """
        return self.identifiers.filter(type="ORCID").first()

    def get_provider(self, provider: str):
        """Return the person's social account for a provider.

        Args:
            provider: The allauth provider id, such as ``orcid``.

        Returns:
            The social account, or None when there is none.
        """
        qs = self.socialaccount_set.filter(provider=provider)  # type: ignore[attr-defined]
        return qs.get() if qs else None

    def primary_affiliation(self):
        """Return the person's primary affiliation.

        Reads ``affiliations.all()``, so a listing that prefetches
        ``affiliations__organization`` costs no query per person.

        Returns:
            The primary affiliation, or None when none is set.
        """
        return next((a for a in self.affiliations.all() if a.is_primary), None)

    @property
    def primary_organization(self):
        """The organisation of the person's primary affiliation, or None."""
        affiliation = self.primary_affiliation()
        return affiliation.organization if affiliation else None

    @property
    def portal_roles(self):
        """The labels of the portal roles the person holds, in declaration order.

        An inactive person holds none, as on the portal's team page. Reads
        ``groups.all()``, so a listing that prefetches ``groups`` costs no query per person.
        """
        from fairdm.portal_roles import PortalRoles

        if not self.is_active:
            return []
        held = {group.name for group in self.groups.all()}
        return [role.label for role in PortalRoles.ROLES if role.name in held]

    def get_initials(self):
        """Return the initials of the given and family names, else of the preferred name.

        Returns:
            Up to two capital letters, or an empty string when there is no name.
        """
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if first or last:
            return (first[:1] + last[:1]).upper()
        return super().get_initials()

    def current_affiliations(self):
        """Return the person's verified affiliations that have not ended.

        Returns:
            Affiliations with no end date and a type of member or above.
        """
        return self.affiliations.select_related("organization").filter(
            end_date__isnull=True, type__gte=1
        )

    @property
    def given(self):
        """The person's first name."""
        return self.first_name

    @property
    def family(self):
        """The person's last name."""
        return self.last_name

    def get_full_name_display(self, name_format: str = "given_family") -> str:
        """Format the person's name.

        Args:
            name_format: One of ``given_family`` ("John Doe"), ``family_given`` ("Doe, John"),
                ``family_initial`` ("Doe, J.") or ``initials_family`` ("J. Doe").
                Any other value is treated as ``given_family``.

        Returns:
            The formatted name, or ``name`` when the first and last names are both empty.
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
        else:
            parts = [p for p in [first, last] if p]
            return " ".join(parts) if parts else self.name

    @property
    def orcid_is_authenticated(self):
        """Whether the person has signed in with ORCID.

        Reads ``socialaccount_set.all()``, so a listing that prefetches it costs no query per
        person.
        """
        return any(a.provider == "orcid" for a in self.socialaccount_set.all())  # type: ignore[attr-defined]

    def icon(self):
        """Return the icon name, showing whether the ORCID iD is authenticated.

        Returns:
            ``orcid`` or ``orcid_unauthenticated``.
        """
        if self.orcid_is_authenticated:
            return "orcid"
        return "orcid_unauthenticated"

    @classmethod
    def from_orcid(cls, orcid_id):
        """Create or update a person from ORCID data and schedule a full sync after commit.

        Args:
            orcid_id: The ORCID iD, such as ``0000-0002-1825-0097``.

        Returns:
            The created or updated person.
        """
        from django.db import transaction

        from .tasks import sync_contributor_identifier
        from .utils.transforms import ORCIDTransform

        person = ORCIDTransform.update_or_create(orcid_id)

        if person and person.pk:
            orcid_identifier = person.identifiers.filter(type="ORCID").first()
            if orcid_identifier:
                transaction.on_commit(
                    lambda: sync_contributor_identifier.delay(orcid_identifier.pk)
                )

        return person

    def as_geojson(self):
        """Return the primary affiliation's organisation location as a GeoJSON feature.

        Returns:
            The feature as a JSON string, or None when there is no located affiliation.
        """
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

    def get_location_display(self):
        """Return the primary affiliation's organisation city and country.

        Returns:
            The location text, or None when there is no primary affiliation.
        """
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
    """A person's membership of an organisation, with time bounds and a verification state.

    The type runs from pending (declared, unverified) through member and admin to owner,
    which maps to ``manage_organization``. Setting ``end_date`` ends the rights the type
    confers, as ``AffiliationQuerySet.owners()`` reads only current affiliations.

    Attributes:
        objects: The affiliation manager.
        tracker: Tracks field changes.
        person: The affiliated person.
        organization: The organisation.
        type: The verification state and role, from 0 to 3.
        is_primary: Whether this is the person's primary affiliation for citation.
        start_date: When the affiliation began, with variable precision.
        end_date: When it ended. Null means it is still active.
    """

    objects = AffiliationManager()  # type: ignore[var-annotated]
    tracker = FieldTracker()

    class MembershipType(models.IntegerChoices):
        """Verification state and role within an organisation."""

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
        """Refuse a second membership of the same organisation with a readable message."""
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
        """Demote the person's other primary affiliation in the same transaction, then save."""
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
        """Return the person and organisation."""
        return f"{self.person} - {self.organization}"


OrganizationMember = Affiliation


class Organization(Contributor):
    """A contributor that represents a group of people, such as a university, institute, company or agency.

    An organisation can have members and sub-organisations, such as departments or research groups.

    Attributes:
        DEFAULT_IDENTIFIER: The identifier scheme shown by default.
        type: The kind of institution, from ROR's organisation types.
        members: The people affiliated with the organisation.
        parent: The organisation this one is part of.
        city: The city where the organisation is based.
        country: The country where the organisation is based.
    """

    DEFAULT_IDENTIFIER = "ROR"
    is_organization = True

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
        """The location's latitude, or None without a location."""
        return self.location.latitude if self.location else None

    @property
    def lon(self):
        """The location's longitude, or None without a location."""
        return self.location.longitude if self.location else None

    class Meta:
        verbose_name = _("organization")
        verbose_name_plural = _("organizations")
        default_related_name = "organizations"

    def __str__(self):
        """Return the organisation's name."""
        return self.name

    def clean(self):
        """Validate the links and the ROR identifier."""
        from django.core.exceptions import ValidationError
        from django.core.validators import URLValidator

        super().clean()

        if self.links:
            url_validator = URLValidator()
            for url in self.links:
                try:
                    url_validator(url)
                except ValidationError:
                    raise ValidationError(
                        {"links": _("Invalid URL: %(url)s") % {"url": url}}
                    ) from None

        # Identifiers exist only after the first save.
        if self.pk and (ror := self.identifiers.filter(type="ROR").first()):
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
        """Create the ROR identifier from ``synced_data`` after the organisation is created."""
        if self.synced_data:
            ror = self.synced_data.get("id")
            if ror:
                self.identifiers.get_or_create(type="ROR", defaults={"value": ror})

    @classmethod
    def from_ror(cls, ror, commit=True):
        """Create or update an organisation from a ROR record and, when committing, schedule a full sync after commit.

        Args:
            ror: The ROR identifier, such as ``https://ror.org/04aj4c181``.
            commit: Whether to save the instance.

        Returns:
            The created or updated organisation.
        """
        from django.db import transaction

        from .tasks import sync_contributor_identifier
        from .utils.transforms import RORTransform

        org = RORTransform.update_or_create(ror, commit)

        if commit and org and org.pk:
            ror_identifier = org.identifiers.filter(type="ROR").first()
            if ror_identifier:
                transaction.on_commit(
                    lambda: sync_contributor_identifier.delay(ror_identifier.pk)
                )

        return org

    def icon(self):
        """Return the icon name.

        Returns:
            ``organization``.
        """
        return "organization"

    def get_memberships(self):
        """Return the organisation's affiliations with their people loaded.

        Returns:
            Affiliations with ``person`` selected.
        """
        return self.affiliations.select_related("person").all()

    def owner(self):
        """Return the organisation's current owner, derived through ``AffiliationQuerySet.owners()``.

        Returns:
            The owner, or None when there is none.
        """
        if membership := self.get_memberships().owners().first():
            return membership.person
        return None

    def transfer_ownership(self, new_owner):
        """Make an existing member the owner, demoting each current owner to admin, atomically.

        Only affiliation records change, as management rights are derived from them.
        Ended affiliations are left as they are.

        Args:
            new_owner: The person to become owner. Must be an active, claimed account with a
                current affiliation of member type or above.

        Raises:
            ValidationError: The person is not a member, holds a pending or ended affiliation,
                or is an unclaimed or deactivated account.
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
        """Return the organisation's location as a GeoJSON feature.

        Returns:
            The feature as a JSON string, or None when there is no location.
        """
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
        """Return the organisation's city and country.

        Returns:
            The location text, or None when both are empty.
        """
        parts = []
        if self.city:
            parts.append(self.city)
        if self.country:
            parts.append(self.country.name)
        return ", ".join(parts) if parts else None

    @property
    def summary(self):
        """The organisation's type and place, joined by a middle dot, or an empty string."""
        parts = [self.get_type_display() if self.type else "", self.get_location_display() or ""]
        return " · ".join(str(p) for p in parts if p)

    def get_initials(self):
        """Return the organisation's acronym when its name starts with one, else its initials.

        "GFZ Helmholtz Centre" gives "GFZ" and "University of Potsdam" gives "UP".

        Returns:
            The acronym or up to two capital letters, or an empty string when there is no name.
        """
        words = (self.name or "").split()
        if not words:
            return ""
        if words[0].isupper() and len(words[0]) <= 5:
            return words[0]
        capitals = "".join(w[:1] for w in words if w[:1].isupper())[:2]
        return capitals or words[0][:1].upper()


CONTRIBUTION_UNIQUE_PAIRING_MESSAGE = _(
    "This contributor is already credited on this object."
)

CONTRIBUTION_ROLES_VOCABULARY_MESSAGE = _(
    "A contribution's roles must be drawn from the framework's roles vocabulary."
)


class Contribution(LifecycleModelMixin, OrderedModel):
    """A contributor's credit on a project, dataset, sample or measurement, based on the DataCite contributor schema.

    Attributes:
        ROLES_VOCAB: The roles vocabulary.
        objects: The contribution manager.
        content_type: The type of the credited object.
        object_id: The id of the credited object.
        content_object: The credited object.
        contributor: The person or organisation credited.
        roles: The roles held on this credit.
        affiliation: The organisation the contributor is affiliated with for this credit.
    """

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
        on_delete=models.PROTECT,
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
        """Refuse a duplicate credit and any stored role outside the roles vocabulary."""
        from django.core.exceptions import ValidationError

        super().clean()

        # Inline formsets validate before the parent supplies the content type, so wait for all three parts.
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

        # Many-to-many data is not validated on save; `refuse_off_vocabulary_role` is the real enforcement.
        if self.pk and self.roles.exclude(vocabulary__name="fairdm-roles").exists():
            raise ValidationError(CONTRIBUTION_ROLES_VOCABULARY_MESSAGE)

    @classmethod
    def add_to(cls, contributor, obj, roles=None, affiliation=None):
        """Credit a contributor on an object, adding roles to any already recorded.

        Args:
            contributor: The person or organisation to credit.
            obj: The project, dataset, sample or measurement.
            roles: Names of roles in the roles vocabulary.
            affiliation: The organisation to set on a newly created credit.

        Returns:
            The contribution, created if it did not exist.
        """
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
            contribution.roles.add(*roles_qs)
        return contribution

    def save(self, *args, **kwargs):
        """Refuse to credit a superuser outside debug mode, then save."""
        if (
            self.contributor.type_of == Person
            and self.contributor.is_superuser
            and settings.DEBUG is False
        ):
            raise ValueError(
                _(
                    "Superusers cannot be contributors. Please remove the superuser status or use a different account."
                )
            )

        return super().save(*args, **kwargs)

    def __str__(self):
        """Return the credited contributor."""
        return force_str(self.contributor)

    def __repr__(self):
        """Return the contributor and roles."""
        return f"<{self.contributor}: {self.roles}>"

    @hook(BEFORE_CREATE)
    def set_default_affiliation(self):
        """Default a new person's credit to their primary affiliation."""
        if not self.affiliation and self.is_person():  # noqa: SIM102
            if org := self.contributor.affiliations.filter(is_primary=True).first():
                self.affiliation = org.organization

    def is_person(self):
        """Check whether the contributor is a person.

        Returns:
            True when the contributor is a ``Person``.
        """
        return isinstance(self.contributor, Person)

    def get_absolute_url(self):
        """Return the URL of the contributor's profile."""
        return self.contributor.get_absolute_url()

    def get_update_url(self):
        """Return the URL of the edit page for the credited object's contributors."""
        related_name = self.content_object._meta.model_name
        letter = related_name[0]
        return reverse(
            "contribution-update",
            kwargs={"uuid": self.content_object.uuid, "model": letter},
        )


class ContributorIdentifier(AbstractIdentifier, LifecycleModelMixin):
    """An external identifier of a contributor, such as an ORCID iD or a ROR id.

    Types are drawn from the contributor identifier collection, so a person cannot hold a
    specimen identifier such as an IGSN.

    Attributes:
        VOCABULARY: The identifier types a contributor may hold.
        related: The contributor the identifier belongs to.
    """

    VOCABULARY = FairDMIdentifiers.from_collection("Contributor")
    related = models.ForeignKey(
        "Contributor",
        verbose_name=_("contributor"),
        help_text=_("The contributor this identifier belongs to."),
        on_delete=models.CASCADE,
    )

    def clean(self):
        """Refuse a second identifier of the same type, with a message naming the type."""
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
        """Queue a sync with the external provider once the transaction commits."""
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
    """The ways a profile can be claimed."""

    ORCID = "orcid", _("ORCID Social Login")
    EMAIL = "email", _("Email Verification")
    TOKEN = "token", _("Claim Token Link")
    ADMIN_MERGE = "admin_merge", _("Admin-Initiated Merge")
    ADMIN_MANUAL = "admin_manual", _("Admin Manual Activation")


class ClaimingAuditLogManager(models.Manager):
    """Manager with filters for the claiming audit log."""

    def for_person(self, pk):
        """Filter to events where the person was the source or the target.

        Args:
            pk: The person's primary key.

        Returns:
            Matching log entries.
        """
        return self.filter(
            models.Q(source_person_id=pk) | models.Q(target_person_id=pk)
        )

    def failures(self):
        """Filter to failed claim attempts.

        Returns:
            Log entries where ``success`` is false.
        """
        return self.filter(success=False)

    def by_method(self, method: str):
        """Filter to one claiming method.

        Args:
            method: A :class:`ClaimMethod` value.

        Returns:
            Matching log entries.
        """
        return self.filter(method=method)

    def recent(self, days: int = 30):
        """Filter to events within the last few days.

        Args:
            days: How many days back to include.

        Returns:
            Matching log entries.
        """
        from datetime import timedelta

        from django.utils import timezone as tz

        cutoff = tz.now() - timedelta(days=days)
        return self.filter(timestamp__gte=cutoff)


class ClaimingAuditLog(models.Model):
    """Immutable audit trail of profile claiming events, created once and never updated.

    Attributes:
        objects: The audit log manager.
        timestamp: When the event happened.
        method: How the profile was claimed.
        source_person: The unclaimed person being claimed.
        target_person: The resulting claimed person.
        initiated_by: The admin who started the claim, when admin-driven.
        ip_address: The requester's IP address.
        success: Whether the claim succeeded.
        failure_reason: Why the claim failed.
        details: Extra structured details.
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
        """Refuse to update an existing entry, then save."""
        if self.pk:
            raise ValueError(
                "ClaimingAuditLog records are immutable and cannot be updated."
            )
        super().save(*args, **kwargs)

    def __str__(self):
        """Return the method, both people and the outcome."""
        return f"{self.method} | {self.source_person} → {self.target_person} | {'✓' if self.success else '✗'}"


def forwards():
    """Keep one primary email address for each user with several, preferring the one matching the user's email."""
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

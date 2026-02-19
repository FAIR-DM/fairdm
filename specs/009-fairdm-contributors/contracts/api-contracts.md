# API Contracts: FairDM Contributors System

**Date**: 2026-02-18
**Feature**: 009-fairdm-contributors

This document defines the internal Python API contracts (public methods, manager interfaces, and module-level APIs) that developers interact with. FairDM contributors does not expose REST endpoints in this feature — REST API is handled by the optional API app. These contracts define the **programmatic surface area** that must remain stable.

---

## 1. Model Manager Contracts

### 1.1 UserManager (Person.objects)

```python
class UserManager(BaseUserManager):
    """Email-based user manager. No username field."""

    def create_user(
        self, email: str, password: str | None = None, **extra_fields
    ) -> Person:
        """Create a claimed Person with email and password.

        Args:
            email: Valid email address (required, will be lowercased).
            password: Raw password string. If None, set_unusable_password().
            **extra_fields: first_name, last_name, etc.

        Returns:
            Person instance (saved, is_active=True).

        Raises:
            ValueError: If email is empty.
        """

    def create_superuser(
        self, email: str, password: str, **extra_fields
    ) -> Person:
        """Create a superuser. Sets is_staff=True, is_superuser=True."""

    def create_unclaimed(
        self, first_name: str, last_name: str, **extra_fields
    ) -> Person:
        """Create an unclaimed (provenance-only) Person record.

        Sets email=None, is_active=False, set_unusable_password().

        Args:
            first_name: Given name (required).
            last_name: Family name (required).
            **extra_fields: Any other Contributor/Person fields.

        Returns:
            Person instance (saved, is_active=False, email=None).
        """
```

### 1.2 PersonQuerySet (Person.objects)

```python
class PersonQuerySet(QuerySet):
    """Extended queryset for filtering Person records by account state."""

    def real(self) -> QuerySet[Person]:
        """Exclude ghost/provenance-only records (unclaimed with no email).
        
        **Recommended for portal queries** to show only actual people, not data placeholders.
        
        Returns:
            Persons where NOT (is_claimed=False AND email IS NULL).
        """

    def claimed(self) -> QuerySet[Person]:
        """Persons with email IS NOT NULL and is_active=True.
        
        Returns:
            Active user accounts (can log in).
        """

    def unclaimed(self) -> QuerySet[Person]:
        """Persons with email IS NULL (provenance-only records).
        
        Returns:
            Person records created for data attribution before user registration.
        """
    
    def ghost(self) -> QuerySet[Person]:
        """Unclaimed persons with no email (provenance placeholders).
        
        Returns:
            Persons where is_claimed=False AND email IS NULL.
        """
    
    def invited(self) -> QuerySet[Person]:
        """Unclaimed persons with email set (pending claim).
        
        Returns:
            Persons where is_claimed=False AND email IS NOT NULL.
        """
```

### 1.3 ContributionManager

```python
class ContributionManager(Manager):
    """Manager for querying contributions across entities."""

    def by_role(self, role_name: str) -> QuerySet[Contribution]:
        """Filter contributions to those containing the specified role.

        Args:
            role_name: Name matching a Concept in FairDMRoles vocabulary.
        """

    def for_entity(self, obj: Model) -> QuerySet[Contribution]:
        """All contributions for a specific entity (Project/Dataset/etc.).

        Args:
            obj: Any model instance with a GenericRelation to Contribution.
        """

    def by_contributor(self, contributor: Contributor) -> QuerySet[Contribution]:
        """All contributions by a specific contributor across all entities."""
```

---

## 2. Model Instance Contracts

### 2.1 Contributor (Base)

```python
class Contributor:

    @property
    def is_claimed(self) -> bool:
        """Whether this contributor is a claimed, active account.
        Always False for Organization. Check on Person subclass."""

    def get_visible_fields(self, viewer: Person | None = None) -> dict[str, Any]:
        """Return field values respecting privacy_settings.

        Args:
            viewer: The person viewing. None = anonymous/public.
                    If viewer is self or staff, all fields returned.

        Returns:
            Dict of field_name → value for visible fields only.
        """

    def to_datacite(self) -> dict:
        """Export contributor as DataCite Creator/Contributor dict."""

    def to_schema_org(self) -> dict:
        """Export contributor as Schema.org Person/Organization JSON-LD dict."""

    def calculate_weight(self) -> float:
        """Compute relevance score: 50% contributions + 30% profile + 20% identifiers.
        Returns 0.0-1.0."""

    def add_to(
        self, obj: Model, roles: list[str] | None = None
    ) -> Contribution:
        """Add this contributor to a research output.

        Args:
            obj: Project, Dataset, Sample, or Measurement instance.
            roles: List of role names from FairDMRoles vocabulary.

        Returns:
            The created or updated Contribution instance.
        """

    def get_co_contributors(self, limit: int | None = None) -> QuerySet[Contributor]:
        """Other contributors on the same objects, ranked by co-occurrence frequency."""

    def get_recent_contributions(self, limit: int = 5) -> QuerySet[Contribution]:
        """Most recent contributions by this contributor."""

    def get_contributions_by_type(self, model_name: str) -> QuerySet[Contribution]:
        """Contributions filtered by target content type model name."""

    def has_contribution_to(self, obj: Model) -> bool:
        """Check if this contributor has any contribution to the given object."""
```

### 2.2 Person

```python
class Person(AbstractUser, Contributor):

    # NOTE: is_claimed is now a BooleanField, not a property (research.md D3)
    is_claimed: bool  # BooleanField, default=False, enables Ghost/Invited/Claimed/Banned state machine

    def orcid(self) -> ContributorIdentifier | None:
        """Return the ORCID identifier, or None."""

    # NOTE: Affiliation queries moved to AffiliationQuerySet (research.md D3)
    # Usage: person.affiliations.primary() returns Affiliation | None
    # Usage: person.affiliations.current() returns QuerySet[Affiliation]
    # See AffiliationQuerySet contract below for available methods

    @classmethod
    def from_orcid(cls, orcid_id: str) -> Person:
        """Factory: create or update Person from ORCID public API data.

        Args:
            orcid_id: Valid ORCID identifier (e.g., "0000-0001-2345-6789").

        Returns:
            Person instance (saved).
        """

    @property
    def given(self) -> str:
        """Alias for first_name."""

    @property
    def family(self) -> str:
        """Alias for last_name."""

    def get_full_name_display(self, name_format: str) -> str:
        """Format name in specified style.

        Args:
            name_format: One of "given_family", "family_given",
                         "family_initial", "initials_family".
        """
```

### 2.3 Organization

```python
class AffiliationQuerySet(models.QuerySet[Affiliation]):
    """QuerySet methods for querying Person affiliations."""

    def primary(self) -> Affiliation | None:
        """Return the primary affiliation (is_primary=True), or None if no primary set."""

    def current(self) -> QuerySet[Affiliation]:
        """Return active affiliations (end_date IS NULL)."""

    def past(self) -> QuerySet[Affiliation]:
        """Return past affiliations (end_date IS NOT NULL)."""


class Organization(Contributor):

    @classmethod
    def from_ror(cls, ror: str, commit: bool = True) -> Organization:
        """Factory: create or update Organization from ROR API data.

        Args:
            ror: ROR identifier (e.g., "https://ror.org/03yrm5c26" or "03yrm5c26").
            commit: Whether to save to database.

        Returns:
            Organization instance.
        """

    def owner(self) -> Affiliation | None:
        """Return the Affiliation record with type=3 (OWNER), or None."""

    def get_memberships(self) -> QuerySet[Affiliation]:
        """All verified affiliations (type >= 1) with select_related('person')."""

    def transfer_ownership(self, new_owner: Person) -> None:
        """Transfer manage_organization permission to new_owner.

        Sets current owner's type to ADMIN (2), new owner's type to OWNER (3).
        Wraps state changes + permission sync in transaction.atomic().
        Logs transfer via django-activity-stream.

        Args:
            new_owner: Must be an existing verified member (type >= 1).

        Raises:
            ValueError: If new_owner is not a verified member.
            PermissionError: If caller doesn't have manage_organization.
        """
```

### 2.4 Affiliation

```python
class Affiliation:

    # Affiliation types (security/verification states)
    PENDING = 0  # Awaiting verification
    MEMBER = 1   # Verified member
    ADMIN = 2    # Can manage org, approve members
    OWNER = 3    # Full management rights

    @property
    def is_active(self) -> bool:
        """True if end_date is None (ongoing affiliation)."""

    @property
    def is_verified(self) -> bool:
        """True if type >= MEMBER (not pending)."""

    def verify(self) -> None:
        """Promote from PENDING to MEMBER (requires admin/owner caller)."""

    def promote_to_admin(self) -> None:
        """Promote from MEMBER to ADMIN (requires owner caller)."""

    def end(self, end_date: PartialDate | None = None) -> None:
        """Mark affiliation as ended.

        Args:
            end_date: PartialDate affiliation ended. Defaults to today.
        """
```

### 2.5 Contribution

```python
class Contribution:

    @classmethod
    def add_to(
        cls,
        contributor: Contributor,
        obj: Model,
        roles: list[str] | None = None,
        affiliation: Organization | None = None,
    ) -> Contribution:
        """Create or update a contribution linking contributor to obj.

        Args:
            contributor: Person or Organization.
            obj: Project, Dataset, Sample, or Measurement.
            roles: Role names from FairDMRoles vocabulary.
            affiliation: Organization affiliation at time of contribution.

        Returns:
            Contribution instance (saved).
        """
```

---

## 3. Transform Registry Contract

```python
# Module: fairdm.contrib.contributors.utils.transforms

class TransformRegistry:
    """Singleton registry for contributor metadata transforms."""

    def register(
        self, format_name: str, transform_class: type[BaseTransform] | None = None
    ) -> Callable | None:
        """Register a transform class for a format.

        Can be used as decorator:
            @transforms.register("my-format")
            class MyTransform(BaseTransform): ...

        Or direct call:
            transforms.register("my-format", MyTransform)

        Args:
            format_name: Unique format key (e.g., "datacite", "schema.org").
            transform_class: BaseTransform subclass.

        Raises:
            ValueError: If format_name already registered.
        """

    def get(self, format_name: str) -> BaseTransform:
        """Get a transform instance by format name.

        Raises:
            KeyError: If format_name not registered.
        """

    def list(self) -> list[str]:
        """List all registered format names."""

    def export_all(self, contributor: Contributor) -> dict[str, dict]:
        """Export contributor in all registered formats.

        Returns:
            Dict of format_name → export dict.
        """


class BaseTransform:
    """Base class for bidirectional contributor metadata transforms."""

    format_name: str              # e.g., "datacite"
    format_version: str | None    # e.g., "4.4"
    content_type: str             # e.g., "application/json"
    supports_persons: bool        # True
    supports_organizations: bool  # True

    def export(self, contributor: Contributor) -> dict:
        """Convert internal Contributor to external format dict.

        Args:
            contributor: Person or Organization instance.

        Returns:
            Dict in the target metadata format.
        """

    def import_data(
        self,
        data: dict,
        instance: Contributor | None = None,
        save: bool = True,
    ) -> ImportResult:
        """Convert external format dict to internal Contributor.

        Args:
            data: Dict in the source metadata format.
            instance: Existing Contributor to update. If None, creates new.
            save: Whether to save to database.

        Returns:
            ImportResult with instance, created flag, unmapped fields, warnings.
        """

    def validate(self, data: dict) -> ValidationResult:
        """Validate inbound data against this format's schema.

        Returns:
            ValidationResult with valid flag, errors, warnings.
        """

    def supported_fields(self) -> list[str]:
        """Which internal model fields this transform reads/writes."""

    @staticmethod
    def dictget(data: dict, path: str, default: Any = None) -> Any:
        """Safely navigate nested dict by dot-separated path."""


@dataclass
class ImportResult:
    instance: Contributor
    created: bool
    unmapped_fields: dict[str, Any]
    warnings: list[str]


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]
```

---

## 4. Celery Task Contracts

```python
# Module: fairdm.contrib.contributors.tasks

@shared_task(
    autoretry_for=(RequestException,),
    retry_backoff=True,
    max_retries=3,
    rate_limit="10/m",
)
def sync_contributor_identifier(identifier_pk: int) -> None:
    """Fetch external data for a ContributorIdentifier.

    Determines API (ORCID/ROR) from identifier type.
    Updates Contributor.synced_data and last_synced.

    Dispatched from ContributorIdentifier.AFTER_CREATE hook
    via transaction.on_commit().
    """

@shared_task
def refresh_all_contributors() -> dict[str, int]:
    """Periodic task: refresh stale contributors.

    Queries contributors where last_synced < 7 days ago.
    Processes in batches of 50 with 1s inter-batch delay.

    Returns:
        {"synced": N, "skipped": N, "failed": N}

    Schedule: Weekly (e.g., Sunday 03:00 UTC via Celery Beat).
    """

@shared_task
def detect_duplicate_contributors() -> dict[str, int]:
    """Periodic task: identify potential duplicate contributor profiles.

    Uses name similarity and identifier matching.

    Returns:
        {"groups_found": N, "total_duplicates": N}

    Schedule: Monthly via Celery Beat.
    """
```

---

## 5. Template Tag Contracts

```python
# Module: fairdm.contrib.contributors.templatetags.contributor_tags

@register.filter
def by_role(contributions: QuerySet, role_names: str) -> QuerySet:
    """Filter contributions to those with specified roles.

    Usage: {{ contributions|by_role:"Creator,DataCollector" }}

    Args:
        contributions: Contribution queryset.
        role_names: Comma-separated role names from FairDMRoles.

    Returns:
        Filtered queryset.
    """

@register.filter
def has_role(contribution: Contribution, role_names: str) -> bool:
    """Check if a contribution has any of the specified roles.

    Usage: {% if contribution|has_role:"Creator" %}...{% endif %}

    Args:
        contribution: Single Contribution instance.
        role_names: Comma-separated role names.

    Returns:
        True if any role matches.
    """
```

---

## 6. Utility Contracts

```python
# Module: fairdm.contrib.contributors.utils.helpers

def get_contributor_avatar(
    contributor: Contributor, size: int = 64
) -> str:
    """Return avatar URL for a contributor.

    Falls back to static icon if no image set.

    Args:
        contributor: Person or Organization instance.
        size: Thumbnail dimension in pixels.

    Returns:
        URL string.
    """

def current_user_has_role(
    request: HttpRequest,
    obj: Model,
    roles: str | list[str],
) -> bool:
    """Check if the request's authenticated user has a specified role on obj.

    Args:
        request: Django HttpRequest (must have .user).
        obj: Entity with contributions (Project, Dataset, etc.).
        roles: Role name(s) to check.

    Returns:
        True if user has any of the specified roles on obj.
    """

def update_or_create_contribution(
    contributor: Contributor,
    obj: Model,
    roles: list[str] | None = None,
    affiliation: Organization | None = None,
) -> tuple[Contribution, bool]:
    """Create or update a contribution.

    Returns:
        (Contribution instance, created: bool)
    """
```

# Data Model: Core Projects MVP

**Phase**: 1 (Design & Contracts)
**Date**: January 14, 2026
**Purpose**: Define entity structure, relationships, and validation rules

## Entity Definitions

### Project

**Purpose**: Top-level organizational container representing a research initiative, grant, or collaboration.

**Fields**:

- `id` (AutoField): Primary key
- `uuid` (ShortUUIDField): Human-readable unique identifier with prefix "p" (e.g., "p_AB12CD34")
- `name` (CharField, max 255): Project name (required, indexed)
- `image` (ImageField): Optional project image/logo
- `visibility` (IntegerField): Access level (Private=0, Organization=1, Public=2) - default Private
- `status` (IntegerField): Project lifecycle phase (Concept=0, Planning=1, Active=2, OnHold=3, Complete=4, Cancelled=5) - default Concept
- `funding` (JSONField): Structured funding data following DataCite schema (nullable)
- `owner` (ForeignKey to Organization): Owning organization (nullable, PROTECT)
- `added` (DateTimeField): Creation timestamp (auto_now_add)
- `modified` (DateTimeField): Last modification timestamp (auto_now)
- `keywords` (ManyToManyField): Controlled vocabulary keywords
- `tags` (ManyToManyField): Free-form tags

**Relationships**:

- One-to-Many with ProjectDescription (related_name="descriptions")
- One-to-Many with ProjectDate (related_name="dates")
- One-to-Many with ProjectIdentifier (related_name="identifiers")
- Generic Relation to Contribution (contributors)
- Many-to-One with Organization (owner)
- Many-to-Many with Keyword (keywords)
- Many-to-Many with Tag (tags)
- One-to-Many with Dataset (datasets) - existing relationship

**Validation Rules**:

- `name`: Required, max 255 characters, cannot be only whitespace
- `visibility`: Must be one of defined choices
- `status`: Must be one of defined choices
- `funding`: If provided, must conform to DataCite FundingReference schema
- `owner`: Must exist and be active

**Permissions** (via django-guardian):

- `view_project`: Can view project details
- `change_project_metadata`: Can edit descriptions, dates, identifiers, keywords
- `change_project_settings`: Can edit name, status, visibility, owner
- `delete_project`: Can delete project (blocked if has datasets)

**QuerySet Methods**:

- `get_visible()`: Returns only public projects
- `with_contributors()`: Prefetches contributors for display
- `with_metadata()`: Prefetches all related metadata (descriptions, dates, identifiers, contributors)
- `with_list_data()`: Optimized for list views (owner, keywords only)

---

### ProjectDescription

**Purpose**: Typed text descriptions providing context about the project (Abstract, Methods, Significance, etc.).

**Fields**:

- `id` (AutoField): Primary key
- `related` (ForeignKey to Project): Parent project (CASCADE)
- `type` (Concept from controlled vocabulary): Description type (Abstract, Methods, Significance, Background, etc.)
- `text` (TextField): Description content (required)
- `order` (PositiveIntegerField): Display order (default=0)
- `added` (DateTimeField): Creation timestamp
- `modified` (DateTimeField): Modification timestamp

**Relationships**:

- Many-to-One with Project (related_name="descriptions")

**Validation Rules**:

- `related` + `type`: Must be unique together (database constraint)
- `text`: Required, cannot be only whitespace
- `type`: Must be from ProjectDescription vocabulary

**Constraints**:

- unique_together = [("related", "type")]
- ordering = ["order", "added"]

**Custom Validation**:

```python
def clean(self):
    if self.related_id and self.type:
        existing = ProjectDescription.objects.filter(
            related=self.related, type=self.type
        ).exclude(pk=self.pk).exists()
        if existing:
            raise ValidationError({
                "type": _("A description of this type already exists for this project.")
            })
```

---

### ProjectDate

**Purpose**: Typed date records marking project milestones and phases (start, end, data collection periods).

**Fields**:

- `id` (AutoField): Primary key
- `related` (ForeignKey to Project): Parent project (CASCADE)
- `type` (Concept from controlled vocabulary): Date type (ProjectStart, ProjectEnd, DataCollectionStart, DataCollectionEnd, etc.)
- `date` (DateField): Date value (required)
- `end_date` (DateField): Optional end date for ranges (nullable)
- `order` (PositiveIntegerField): Display order (default=0)
- `added` (DateTimeField): Creation timestamp
- `modified` (DateTimeField): Modification timestamp

**Relationships**:

- Many-to-One with Project (related_name="dates")

**Validation Rules**:

- `related` + `type`: May have multiple dates of same type (e.g., multiple data collection periods)
- `date`: Required
- `end_date`: If provided, must be >= `date` (enforced at form/model level)
- `type`: Must be from ProjectDate vocabulary

**Constraints**:

- ordering = ["order", "date"]

**Custom Validation**:

```python
def clean(self):
    super().clean()
    if self.date and self.end_date and self.end_date < self.date:
        raise ValidationError({
            "end_date": _("End date cannot be before start date.")
        })
```

---

### ProjectIdentifier

**Purpose**: External identifiers for project discovery and citation (DOI, grant numbers, proposal IDs).

**Fields**:

- `id` (AutoField): Primary key
- `related` (ForeignKey to Project): Parent project (CASCADE)
- `type` (Concept from controlled vocabulary): Identifier type (DOI, GrantNumber, ProposalID, URL, etc.)
- `identifier` (CharField, max 255): Identifier value (required)
- `url` (URLField): Optional URL for the identifier (nullable)
- `order` (PositiveIntegerField): Display order (default=0)
- `added` (DateTimeField): Creation timestamp
- `modified` (DateTimeField): Modification timestamp

**Relationships**:

- Many-to-One with Project (related_name="identifiers")

**Validation Rules**:

- `related` + `type` + `identifier`: Should be unique (soft enforcement - warn but allow)
- `identifier`: Required, max 255 characters
- `url`: If provided, must be valid URL format
- `type`: Must be from ProjectIdentifier vocabulary

**Constraints**:

- ordering = ["order", "added"]

**Display Logic**:

- DOI identifiers: Display as clickable link with <https://doi.org/> prefix
- URL identifiers: Display as clickable link
- Other types: Display as text

---

## Controlled Vocabularies

### Project Status (ProjectStatus Choice)

| Value | Label | Description |
|-------|-------|-------------|
| 0 | Concept | Initial planning phase, not yet approved |
| 1 | Planning | Approved and in detailed planning |
| 2 | Active | Currently executing/collecting data |
| 3 | On Hold | Temporarily paused |
| 4 | Complete | Finished and in archival phase |
| 5 | Cancelled | Discontinued before completion |

### Project Visibility (Visibility Choice)

| Value | Label | Description |
|-------|-------|-------------|
| 0 | Private | Only team members can view |
| 1 | Organization | Anyone in owning organization can view |
| 2 | Public | Anyone can view (including anonymous) |

### Description Types (from FairDMDescriptions.Project)

- Abstract
- Methods
- Significance
- Background
- Objectives
- Expected Outcomes
- Technical Approach
- Related Work

### Date Types (from FairDMDates.Project)

- Project Start
- Project End
- Data Collection Start
- Data Collection End
- Milestone
- Publication Date
- Award Date

### Identifier Types (from FairDMIdentifiers)

- DOI
- Grant Number
- Proposal ID
- URL
- Handle
- ARK
- PURL
- Other

---

## Relationships Diagram

```
┌─────────────────────────┐
│      Organization       │
│                         │
└────────────┬────────────┘
             │ owner (FK, nullable)
             │
             ▼
┌─────────────────────────┐
│        Project          │◄───────┐
│  - uuid                 │        │
│  - name                 │        │ related (FK, CASCADE)
│  - visibility           │        │
│  - status               │        ├─── ProjectDescription
│  - funding (JSON)       │        │      - type (unique with related)
└────────┬────────────────┘        │      - text
         │                         │
         ├─────────────────────────┤
         │                         │
         │ related (FK, CASCADE)   ├─── ProjectDate
         │                         │      - type
         │                         │      - date, end_date
         │                         │
         │                         ├─── ProjectIdentifier
         │                         │      - type
         │                         │      - identifier, url
         │                         │
         ├─────────────────────────┘
         │
         │ contributors (GenericRelation)
         ├─── Contribution
         │      - contributor (Person/Organization)
         │      - role (from vocabulary)
         │
         │ keywords (M2M)
         ├─── Keyword (controlled vocabulary)
         │
         │ tags (M2M)
         ├─── Tag (free-form)
         │
         │ datasets (reverse FK)
         └─── Dataset (one-to-many)
```

---

## State Transitions

### Project Status Workflow

```
Concept → Planning → Active → Complete
            ↓         ↓         ↑
            └→ On Hold ────────┘
                      ↓
                  Cancelled
```

**Valid Transitions**:

- Concept → Planning, Cancelled
- Planning → Active, On Hold, Cancelled
- Active → On Hold, Complete
- On Hold → Active, Cancelled
- Complete → [terminal state]
- Cancelled → [terminal state]

**Business Rules**:

- Cannot delete project if status is Active or Complete
- Can only set visibility to Public if status is Active or Complete
- Must have at least one description (Abstract) before setting status to Active (recommendation, not enforced)

---

## Funding Schema (DataCite)

**JSON Structure**:

```json
{
  "funding": [
    {
      "funderName": "string (required)",
      "funderIdentifier": "string (optional, ROR/Crossref Funder ID/etc.)",
      "funderIdentifierType": "ROR|Crossref Funder ID|GRID|ISNI|Other",
      "awardNumber": "string (optional)",
      "awardURI": "string (optional, URL format)",
      "awardTitle": "string (optional)"
    }
  ]
}
```

**Example**:

```json
{
  "funding": [
    {
      "funderName": "National Science Foundation",
      "funderIdentifier": "https://ror.org/021nxhr62",
      "funderIdentifierType": "ROR",
      "awardNumber": "1234567",
      "awardURI": "https://www.nsf.gov/awardsearch/showAward?AWD_ID=1234567",
      "awardTitle": "Understanding Arctic Climate Change Dynamics"
    }
  ]
}
```

---

## Migration Strategy

**Existing Migrations**: 5 migrations already exist in `fairdm/core/project/migrations/`

**New Migrations Required**:

1. Update Project.funding field help_text to reference DataCite schema
2. Add custom permissions to Project model (change_project_metadata, change_project_settings)
3. Add unique_together constraint to ProjectDescription (related, type)
4. Add date validation to ProjectDate model (clean method)
5. Update verbose_name and help_text for i18n compliance across all models

**Backward Compatibility**:

- No breaking changes to existing fields
- New permissions are additive
- Existing funding data (if any) should be manually migrated to DataCite format
- unique_together on ProjectDescription may fail if existing data has duplicates (run cleanup script first)

---

## Summary

- 4 core entities: Project, ProjectDescription, ProjectDate, ProjectIdentifier
- 3 controlled vocabularies: Status, Visibility, Descriptor Types (descriptions/dates/identifiers)
- DataCite-compliant funding schema (JSONField)
- Object-level permissions via django-guardian
- Optimized QuerySets for list/detail views
- Comprehensive validation at database and model levels
- All user-facing strings wrapped for i18n

Ready for contract generation (API schemas, form contracts).

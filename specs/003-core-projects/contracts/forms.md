# Form Contracts: Core Projects MVP

**Phase**: 1 (Design & Contracts)
**Date**: January 14, 2026
**Purpose**: Define form inputs, validation rules, and error handling

## ProjectCreateForm

**Purpose**: Streamlined project creation (GitHub-style minimal fields)

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| name | CharField | Yes | Max 255 chars, not blank | "Enter a descriptive name for your project" |
| status | ChoiceField | Yes | Must be valid status choice | "Select the current phase of your project" |
| visibility | ChoiceField | Yes | Must be valid visibility choice | "Who should be able to view this project?" |
| owner | ModelChoiceField(Organization) | No | Must be active organization | "Select the organization that owns this project" |

**Widget Customization**:

- name: TextInput with placeholder "e.g., Arctic Climate Study 2024-2026"
- status: Select with default "Concept"
- visibility: Select with default "Private"
- owner: Select2 with autocomplete (if user belongs to multiple orgs)

**Validation Rules**:

1. Name cannot be only whitespace
2. Name uniqueness is NOT enforced (allow duplicates with warning)
3. Owner defaults to user's primary organization if available
4. Status defaults to "Concept"
5. Visibility defaults to "Private"

**Success Behavior**:

- On save: Create Project instance
- Redirect to: project_detail view with success message "Project created successfully. Add metadata to make it discoverable."
- Assign permissions: Creator gets all permissions, owner organization gets view permission

**Error Messages**:

| Condition | Error Message |
|-----------|---------------|
| Name blank | "Project name is required." |
| Name > 255 chars | "Project name cannot exceed 255 characters." |
| Invalid status | "Please select a valid project status." |
| Invalid visibility | "Please select a valid visibility level." |
| Owner not found | "Selected organization does not exist." |

---

## ProjectEditForm

**Purpose**: Comprehensive project metadata editing

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| name | CharField | Yes | Max 255 chars | "Project name (visible to all viewers)" |
| image | ImageField | No | Valid image format | "Upload a project logo or representative image" |
| status | ChoiceField | Yes | Valid status | "Current project phase" |
| visibility | ChoiceField | Yes | Valid visibility | "Who can view this project" |
| owner | ModelChoiceField(Organization) | No | Active organization | "Owning organization (controls permissions)" |
| keywords | ModelMultipleChoiceField(Keyword) | No | From vocabulary | "Add keywords to improve discoverability" |
| tags | CharField | No | Comma-separated | "Add free-form tags (comma-separated)" |

**Widget Customization**:

- name: TextInput (standard)
- image: ClearableFileInput with preview
- status: Select
- visibility: Select with description for each choice
- owner: Select2 with autocomplete
- keywords: ConceptMultiSelect (autocomplete from vocabulary)
- tags: TextInput with tag-input widget

**Validation Rules**:

1. All rules from ProjectCreateForm
2. Image must be valid format (JPEG, PNG, WebP), max 5MB
3. Cannot change owner if project has datasets (soft validation - warn but allow for admins)
4. Cannot set visibility to Public if status is Concept (enforce)

**Success Behavior**:

- On save: Update Project instance
- Redirect to: Same page (project_edit) with success message "Project updated successfully."
- No permission changes (permissions set at creation)

**Error Messages**:

| Condition | Error Message |
|-----------|---------------|
| Image too large | "Image must be smaller than 5MB." |
| Invalid image format | "Please upload a valid image (JPEG, PNG, or WebP)." |
| Public + Concept status | "Projects in Concept phase cannot be made public. Change status first." |
| Owner change with datasets | "Warning: Changing owner affects permissions for all datasets. Proceed with caution." |

---

## ProjectDescriptionForm

**Purpose**: Add/edit project descriptions inline

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| type | ChoiceField | Yes | From vocabulary | "Select the type of description" |
| text | TextField | Yes | Not blank | "Enter the description text" |
| order | IntegerField | No | >= 0 | "Display order (lower numbers first)" |

**Widget Customization**:

- type: Select with available types only (exclude already-used types)
- text: Textarea (rows=5)
- order: NumberInput with default 0

**Validation Rules**:

1. Type + Project must be unique (enforced in clean())
2. Text cannot be only whitespace
3. Order defaults to 0

**Inline Formset Configuration**:

```python
ProjectDescriptionFormSet = inlineformset_factory(
    Project,
    ProjectDescription,
    form=ProjectDescriptionForm,
    extra=1,
    can_delete=True,
    max_num=10,
)
```

**Error Messages**:

| Condition | Error Message |
|-----------|---------------|
| Duplicate type | "A description of this type already exists for this project." |
| Text blank | "Description text is required." |
| Invalid type | "Please select a valid description type." |

---

## ProjectDateForm

**Purpose**: Add/edit project dates inline

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| type | ChoiceField | Yes | From vocabulary | "Select the type of date" |
| date | DateField | Yes | Valid date | "Enter the date" |
| end_date | DateField | No | >= date | "Optional end date for date ranges" |
| order | IntegerField | No | >= 0 | "Display order" |

**Widget Customization**:

- type: Select
- date: DateInput with HTML5 date picker
- end_date: DateInput with HTML5 date picker
- order: NumberInput with default 0

**Validation Rules**:

1. Date is required
2. End_date, if provided, must be >= date (enforced in clean())
3. Multiple dates of same type are allowed

**Inline Formset Configuration**:

```python
ProjectDateFormSet = inlineformset_factory(
    Project,
    ProjectDate,
    form=ProjectDateForm,
    extra=1,
    can_delete=True,
    max_num=20,
)
```

**Error Messages**:

| Condition | Error Message |
|-----------|---------------|
| Date blank | "Date is required." |
| End before start | "End date cannot be before start date." |
| Invalid date format | "Please enter a valid date (YYYY-MM-DD)." |

---

## ProjectIdentifierForm

**Purpose**: Add/edit project identifiers inline

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| type | ChoiceField | Yes | From vocabulary | "Select the type of identifier" |
| identifier | CharField | Yes | Max 255 chars | "Enter the identifier value" |
| url | URLField | No | Valid URL | "Optional URL for this identifier" |
| order | IntegerField | No | >= 0 | "Display order" |

**Widget Customization**:

- type: Select
- identifier: TextInput
- url: URLInput
- order: NumberInput with default 0

**Validation Rules**:

1. Identifier is required, max 255 characters
2. URL, if provided, must be valid URL format
3. Soft validation: Warn if same type+identifier already exists (allow duplicates)

**Inline Formset Configuration**:

```python
ProjectIdentifierFormSet = inlineformset_factory(
    Project,
    ProjectIdentifier,
    form=ProjectIdentifierForm,
    extra=1,
    can_delete=True,
    max_num=10,
)
```

**Error Messages**:

| Condition | Error Message |
|-----------|---------------|
| Identifier blank | "Identifier value is required." |
| Identifier > 255 | "Identifier cannot exceed 255 characters." |
| Invalid URL | "Please enter a valid URL." |
| Duplicate warning | "Warning: A similar identifier already exists for this project." |

---

## ProjectFilterForm

**Purpose**: Filter project list view

**Fields**:

| Field | Type | Required | Validation | Help Text |
|-------|------|----------|------------|-----------|
| search | CharField | No | Max 255 chars | "Search project names and descriptions" |
| status | ChoiceField | No | Valid status | "Filter by project status" |
| visibility | ChoiceField | No | Valid visibility | "Filter by visibility level" |
| owner | ModelChoiceField(Organization) | No | Valid organization | "Filter by owning organization" |
| keywords | ModelMultipleChoiceField(Keyword) | No | From vocabulary | "Filter by keywords (AND logic)" |
| tags | CharField | No | Comma-separated | "Filter by tags" |
| contributor | ModelChoiceField(Person/Org) | No | Valid contributor | "Filter by team member" |

**Widget Customization**:

- search: SearchInput with placeholder "Search projects..."
- status: Select with empty option "Any"
- visibility: Select with empty option "Any"
- owner: Select2 with autocomplete, empty option "Any"
- keywords: ConceptMultiSelect
- tags: TextInput
- contributor: Select2 with autocomplete, empty option "Any"

**Filtering Logic**:

- search: Case-insensitive substring match on name, descriptions.text, keywords.label
- status: Exact match
- visibility: Exact match
- owner: Exact match on owner FK
- keywords: AND logic (all selected keywords must be present)
- tags: Exact match on tag name
- contributor: Match on contributors.contributor

**No Validation Required**: All filters are optional, invalid values are ignored

---

## Form Layout (django-crispy-forms)

### ProjectCreateForm Layout

```python
layout = Layout(
    Fieldset(
        _('Create New Project'),
        'name',
        'status',
        'visibility',
        'owner',
    ),
    ButtonHolder(
        Submit('submit', _('Create Project'), css_class='btn btn-primary'),
        HTML('<a href="{% url "project:project_list" %}" class="btn btn-secondary">Cancel</a>'),
    )
)
```

### ProjectEditForm Layout

```python
layout = Layout(
    Fieldset(
        _('Basic Information'),
        'image',
        'name',
        'status',
        'visibility',
        'owner',
    ),
    Fieldset(
        _('Discoverability'),
        'keywords',
        'tags',
    ),
    ButtonHolder(
        Submit('submit', _('Save Changes'), css_class='btn btn-primary'),
        HTML('<a href="{% url "project:project_detail" project.uuid %}" class="btn btn-secondary">Cancel</a>'),
    )
)
```

---

## Client-Side Validation (HTML5)

- Required fields: Add `required` attribute
- Max length: Add `maxlength` attribute
- Date fields: Use `type="date"` for browser date picker
- URL fields: Use `type="url"` for URL validation
- Number fields: Use `type="number"` with `min="0"` for order fields

**JavaScript Enhancements** (Progressive):

- Date range validation: Client-side check that end_date >= date
- Description type filtering: Hide already-used types in dropdown
- Character counter: Show remaining characters for name field
- Tag autocomplete: Suggest existing tags as user types

---

## Summary

- 7 form contracts defined: Create, Edit, Description, Date, Identifier, Filter, plus inline formsets
- All validation rules specified with error messages
- Widget customization for better UX
- i18n ready (all strings wrapped)
- Client-side enhancements documented
- Crispy forms layouts specified

Ready for view contracts and quickstart guide.

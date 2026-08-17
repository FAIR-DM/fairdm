# Feature Specification: Model registry and generated components

**Feature Branch**: `002-fairdm-registry`

**Created**: 2026-01-07 · **Rewritten**: 2026-08-17

**Status**: Draft

**Goals**: G2 — registering a model is enough to get a working portal surface, with configuration
needed only where a default is wrong.

**Roadmap**: R2 — Model registry and generated components.

**Input**: A portal defines its own sample and measurement types. The framework ships the views,
URLs, API, admin and import/export that serve them, and cannot know those model classes exist. The
registry is how a portal declares what it has and how each type should appear, and it is the only
place that declaration is made.

## Clarifications

### Session 2026-08-17

- Q: Should component classes be cached once generated, or regenerated on each request? → A: No
  caching. Generating the components a page needs costs 0.18–1.1 ms depending on field count, and
  Django's own `ModelFormMixin.get_form_class()` regenerates uncached on every request. Caching
  bought nothing measurable and cost the override hook, because a cached attribute is read without
  consulting the method a portal may have overridden.
- Q: Is the public accessor for each component a method or a property? → A: A method,
  `get_<component>_class()`. This is the pattern Django uses throughout its view and mixin layer,
  so it is already familiar, and it is overridable. No property alias is provided: two ways to
  reach one thing is what allowed consumers to drift onto the path that ignores overrides.
- Q: What happens when a configuration declares both a field list and a custom class for the same
  component? → A: `ImproperlyConfigured` at registration, following Django's rule for `fields`
  and `form_class` on `ModelFormMixin`. Silently preferring one and ignoring the other leaves a
  portal developer with a field list that has no effect and nothing to explain why.
- Q: Where does configuration validation live, registration or the Django check framework? → A:
  Registration only. Django runs system checks from management commands, so a check never fires on
  a production WSGI or ASGI boot, which makes it a weaker guarantee than it appears. Registration
  happens at import, so it fails on every start.
- Q: Should validation also check that a field's type suits the component it is listed for, for
  example refusing a field that cannot be filtered? → A: No. Whether a field is usable by a given
  component depends on the backend, the declared lookups and third-party field types, so any rule
  the registry encodes will refuse fields that would have worked. The component libraries already
  raise on their own terms and are correct more often. Validation covers existence and path
  resolution only.
- Q: What happens when code reaches for the configuration of a model that was never registered? →
  A: Raise, naming the model. Returning `None` turns a missing registration into an
  `AttributeError` at a call site far from the cause.
- Q: Should the configuration class remain a dataclass? → A: No. A registration class declares
  class attributes, which is how `Meta` and `ModelAdmin` are written and what portal developers
  expect. A dataclass shadows those attributes with instance defaults and then needs bespoke code
  to copy them back.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register a model and get every component (Priority: P1)

A researcher has defined a `RockSample` model and wants the portal to present it. They write a
configuration class naming the model and the fields that matter, and the framework supplies the
form, table, filter set, serializer, import and export resource, and admin entry.

**Why this priority**: This is the whole promise of the registry. If a field list is not enough to
get working components, nothing else in the feature matters.

**Independent Test**: Register a model with a field list, then ask the configuration for each of the
six component classes and confirm each is the expected type and covers the declared fields.

**Acceptance Scenarios**:

1. **Given** a `RockSample` model and a configuration declaring `fields = ["name", "location"]`,
   **When** the configuration class is decorated with `@register`, **Then** registration completes
   and the model appears in the registry.
2. **Given** that registration, **When** `get_table_class()` is called, **Then** it returns a
   `django_tables2.Table` subclass with columns for `name` and `location`.
3. **Given** that registration, **When** `get_form_class()` is called, **Then** it returns a
   `ModelForm` subclass whose fields are `name` and `location`.
4. **Given** that registration, **When** `get_filterset_class()`, `get_serializer_class()`,
   `get_resource_class()` and `get_admin_class()` are called, **Then** each returns a subclass of
   its respective base built from the same field list.
5. **Given** a configuration that declares no `fields` at all, **When** any component is requested,
   **Then** it is built from the model's own editable fields, with the framework's internal
   plumbing left out.
6. **Given** a configuration declaring `table_fields` alongside `fields`, **When** the table and the
   form are requested, **Then** the table uses `table_fields` and the form uses `fields`.

---

### User Story 2 - Replace one component without touching the others (Priority: P1)

A portal needs a table with a computed column that cannot be described by a field list. The
developer writes that one `Table` class, attaches it to the configuration, and every other component
carries on being generated.

**Why this priority**: Progressive enhancement is the reason the registry is worth using. Needing
one custom component must not cost a developer the other five.

**Independent Test**: Register a model with a custom table class and a field list for the rest, then
confirm the table is the supplied class and the remaining five are still generated.

**Acceptance Scenarios**:

1. **Given** a configuration declaring `table_class = RockSampleTable`, **When**
   `get_table_class()` is called, **Then** it returns `RockSampleTable` unchanged.
2. **Given** that same configuration, **When** `get_form_class()` is called, **Then** a generated
   form is returned, unaffected by the custom table.
3. **Given** a configuration declaring `admin_class` as the dotted path
   `"myapp.admin.RockSampleAdmin"`, **When** `get_admin_class()` is called, **Then** the class is
   imported and returned.
4. **Given** a configuration whose `table_class` does not subclass `django_tables2.Table`, **When**
   the model is registered, **Then** registration fails with a message naming the model, the
   attribute and the expected base class.

---

### User Story 3 - Configuration mistakes stop the process at registration (Priority: P1)

A developer mistypes a field name, or leaves a stale field in a list after renaming a model field.
The portal refuses to start and says exactly what is wrong, rather than serving a broken page later.

**Why this priority**: The framework's reliability rests on this. A misconfiguration that survives
startup surfaces as a failed request, in a different file, possibly only for one user role.

**Independent Test**: Attempt registrations with each class of mistake and confirm each raises at
registration with a message identifying the model, the attribute and the offending value.

**Acceptance Scenarios**:

1. **Given** a configuration declaring `fields = ["nam"]` on a model with a `name` field, **When**
   the model is registered, **Then** registration fails, and the message names the model, the
   attribute, the unknown field and `name` as a suggestion.
2. **Given** a configuration declaring `filterset_fields = ["dataset__nonexistent"]`, **When** the
   model is registered, **Then** registration fails, because every segment of a related path is
   resolved and not only the first.
3. **Given** a configuration declaring both `form_fields` and `form_class`, **When** the model is
   registered, **Then** registration fails with `ImproperlyConfigured`, because the field list
   could never take effect.
4. **Given** a model that is not a concrete subclass of `Sample` or `Measurement`, **When** it is
   registered, **Then** registration fails naming the two permitted base classes.
5. **Given** a model that is already registered, **When** it is registered a second time, **Then**
   registration fails with a message carrying the module and qualified name of the first
   registration.
6. **Given** a model that was never registered, **When** its configuration is requested, **Then**
   the call raises with a message naming the model, rather than returning nothing.

---

### User Story 4 - Build a component in code when a field list cannot say it (Priority: P2)

A portal needs a filter set chosen at startup according to which optional dependency is installed.
The developer overrides `get_filterset_class()` on the configuration class and returns whatever they
like. Every part of the framework that needs a filter set for that model gets theirs.

**Why this priority**: Below the first three because a field list or a custom class covers almost
every case. It earns its place because it is the escape hatch that stops a portal from being blocked
on a framework change, and because a consistent override point costs nothing to provide.

**Independent Test**: Subclass a configuration, override one accessor, register it, and confirm every
framework path that needs that component receives the overridden class.

**Acceptance Scenarios**:

1. **Given** a configuration overriding `get_form_class()` to return a hand-written class, **When**
   the framework asks that configuration for a form class, **Then** the overridden class is
   returned.
2. **Given** that same configuration, **When** any other component is requested, **Then** it is
   generated as normal.
3. **Given** an overridden accessor, **When** the same accessor is called twice, **Then** the
   override runs both times, because no result is cached anywhere.
4. **Given** an overridden accessor, **When** any part of the framework needs that component,
   **Then** it reaches it through the accessor, so no consumer can receive the generated class in
   place of the override.

---

### User Story 5 - Find out what a portal has registered (Priority: P2)

A developer building a search page across every sample type asks the registry which types exist and
gets each one's configuration, without naming any model in their own code.

**Why this priority**: The framework's own API, browse pages and admin all depend on this, and so
does any addon. It sits below the first three because it is a smaller surface with less to get
wrong.

**Independent Test**: Register several sample and measurement types, then confirm each introspection
call returns exactly the expected models and configurations.

**Acceptance Scenarios**:

1. **Given** three registered sample types and two measurement types, **When** `registry.samples`
   is read, **Then** it returns the three sample models and no measurement models.
2. **Given** the same, **When** `registry.measurements` is read, **Then** it returns the two
   measurement models.
3. **Given** the same, **When** `registry.models` is read, **Then** it returns all five.
4. **Given** a registered model, **When** `registry.get_for_model()` is called with either the model
   class or the string `"app_label.model_name"`, **Then** the same configuration is returned for
   both.
5. **Given** a model that is not registered, **When** `registry.is_registered()` is called for it,
   **Then** it returns `False` without raising.

---

### Edge Cases

- **A configuration names no model.** Registration fails, naming the configuration class, because
  the decorator has nothing to register against.
- **A field list contains tuples used to group fields for layout.** The grouping is preserved for
  consumers that want it and flattened before a component is generated, so a grouped list and a
  plain one produce the same fields.
- **A field list names a related path such as `dataset__title`.** Every segment is resolved at
  registration. The component libraries decide whether they can use it.
- **A model has a many-to-many field with an explicit through model.** It is left out of the default
  field list, because Django's admin rejects it and a generated admin would fail to load.
- **A custom admin class does not subclass the polymorphic child admin base.** Registration fails,
  because Django's admin for a polymorphic child registered against the wrong base misbehaves in
  ways that are hard to trace back.
- **Admin site registration fails for a registered model.** The error propagates. A model whose
  admin silently failed to register looks identical to one nobody asked for.
- **Two configurations are declared for the same model in different modules.** The second fails, and
  the message carries where the first one was declared, because import order decides which arrives
  first and that is not obvious from either file.

## Requirements *(mandatory)*

### Functional Requirements

Registration and lookup (US1, US3, US5)

- **FR-001**: A `@register` decorator MUST register a configuration class, which MUST declare the
  model it configures.
- **FR-002**: Registration MUST reject any model that is not a concrete subclass of `Sample` or
  `Measurement`.
- **FR-003**: Registering a model twice MUST raise `DuplicateRegistrationError`, carrying the model
  and the module and qualified name of the first registration.
- **FR-004**: The registry MUST provide `get_for_model()`, accepting a model class or the string
  `"app_label.model_name"` and returning that model's configuration.
- **FR-005**: The registry MUST provide `samples`, `measurements` and `models` listing registered
  models, `get_all_configs()` listing their configurations, and `is_registered()` answering without
  raising.
- **FR-006**: Requesting the configuration of an unregistered model MUST raise, naming the model.
  No accessor may return `None` in its place.
- **FR-007**: Registering a model MUST register its admin class with the Django admin site, and any
  failure to do so MUST propagate.

Component generation (US1)

- **FR-008**: A configuration MUST expose exactly six accessors, each returning a class:
  `get_form_class()`, `get_table_class()`, `get_filterset_class()`, `get_serializer_class()`,
  `get_resource_class()` and `get_admin_class()`.
- **FR-009**: When no custom class is declared for a component, its accessor MUST return a class
  generated from that component's resolved field list.
- **FR-010**: Field resolution MUST take the component-specific list if declared, otherwise the
  shared `fields` list, otherwise the default field list.
- **FR-011**: The default field list MUST include the model's own editable fields and exclude `id`,
  polymorphic type columns, multi-table inheritance pointers, fields with `auto_now` or
  `auto_now_add`, fields with `editable=False`, reverse relations, and many-to-many fields with an
  explicit through model.
- **FR-012**: A field list MAY contain tuples grouping field names for layout, and MUST be flattened
  before a component is generated.
- **FR-013**: A field list MAY name related fields using Django's double-underscore paths.
- **FR-014**: No component class may be cached. Each call to an accessor MUST return the result of
  generating or resolving it again.
- **FR-015**: Generating any component MUST NOT require database access.

Customisation (US2, US4)

- **FR-016**: A configuration MAY declare a custom class for any component, as either a class or a
  dotted import path, and its accessor MUST return that class unchanged.
- **FR-017**: A declared custom class MUST be validated at registration as a subclass of the base
  its component requires.
- **FR-018**: A custom admin class for a `Sample` or `Measurement` subclass MUST subclass the
  framework's polymorphic child admin base for that hierarchy.
- **FR-019**: Every accessor MUST be overridable on a configuration subclass.
- **FR-020**: Every consumer inside the framework MUST obtain a component class by calling its
  accessor. No attribute or property may expose a component class in a way that bypasses an
  override.

Validation (US3)

- **FR-021**: All configuration validation MUST happen while the model is being registered, and MUST
  raise rather than collect.
- **FR-022**: Every name in every field list MUST be validated for existence, and every segment of a
  related path MUST be resolved.
- **FR-023**: Declaring both a component's field list and its custom class MUST raise
  `ImproperlyConfigured`, naming both attributes.
- **FR-024**: A validation error MUST name the model, the attribute, the offending value, and a
  suggestion where a close match exists.
- **FR-025**: The registry MUST NOT contribute Django system checks. Validation exists in one place.

Metadata (US1, US5)

- **FR-026**: A configuration MAY carry structured metadata about the model: description, authority,
  keywords, repository URL, citation and maintainer.
- **FR-027**: A configuration MUST supply a display name and description, defaulting to the model's
  own verbose name where none is declared.

### Non-Functional Requirements

- **NFR-001**: Validating every registered model's configuration MUST take under 5 ms in total for
  100 registered models, so that startup cost stays invisible during development.
- **NFR-002**: Requesting all six components for one model MUST take under 5 ms, so that a view
  that builds components per request is never the reason a page is slow.

### Key Entities

- **Registry**: The single object holding every registration for a running portal. Maps a model to
  its configuration and answers which models are registered.
- **ModelConfiguration**: A class a portal writes, declaring the model, the fields each component
  should use, and any custom component classes. It is where a portal states how its model appears,
  and the class a portal subclasses to override an accessor.
- **Component**: One of the six classes the framework needs per model. Either generated from a field
  list or supplied by the portal.
- **Field list**: The names a component is built from. Declared once as `fields` for every
  component, or per component where they differ, or left out entirely for the framework to decide.
- **Model metadata**: Description, authority, keywords, repository URL, citation and maintainer for a
  registered model, so a model can describe and credit itself.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A model registered with nothing but a model reference and a field list yields all six
  component classes, each covering exactly the declared fields.
- **SC-002**: A model registered with no field list at all yields all six component classes, and
  none of them exposes an internal column such as `id` or a polymorphic type pointer.
- **SC-003**: Replacing one component with a custom class leaves the other five generated and
  unchanged.
- **SC-004**: Overriding any accessor on a configuration subclass changes what every part of the
  framework receives for that component, with no consumer able to reach the generated class instead.
- **SC-005**: Every class of configuration mistake in User Story 3 is refused while the model is
  being registered, and each message names the model, the attribute and the offending value.
- **SC-006**: A portal developer can list every registered sample and measurement type, and reach
  each one's configuration, without naming a model class.
- **SC-007**: Validation for 100 registered models completes in under 5 ms, and requesting all six
  components for one model completes in under 5 ms.
- **SC-008**: Field resolution, field validation and field flattening each exist once in the
  codebase.
- **SC-009**: The demo portal registers at least three sample types and two measurement types,
  covering a bare field list, per-component field lists, a custom component class, and an overridden
  accessor.

## Assumptions

- Django REST Framework, django-tables2, django-filter, django-import-export and django-crispy-forms
  are hard dependencies of the framework. No component generation path needs to handle one of them
  being absent.
- Registration happens while Django populates the app registry, so a configuration can rely on model
  classes being importable and must not rely on the database being reachable.
- `Sample` and `Measurement` remain polymorphic base classes that portals subclass, and the base
  classes themselves are never registered.
- Only concrete model classes are registered. Abstract models have no components.

## Out of scope

- Views, URL patterns and templates. The registry supplies component classes and nothing else
  assembles them into pages.
- The plugin registry, which attaches behaviour to detail views and is a separate mechanism with a
  separate specification.
- Rewiring existing framework consumers that currently reach around the registry. Those are recorded
  against their own features and handled separately, so this specification is not blocked on them.
- Caching or memoising component classes. Should profiling ever justify it, it is a change with its
  own measurement behind it.

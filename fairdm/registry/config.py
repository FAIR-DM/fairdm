"""Model configuration: how a portal declares the way its model appears.

A portal writes a ``ModelConfiguration`` subclass, names the model and the fields
that matter, and the framework supplies six component classes from it. There are
three tiers of customisation, in increasing order of effort:

1. declare a field list, shared or per component;
2. declare a custom class for one component;
3. override that component's ``get_<component>_class()`` method.

Every caller inside the framework reaches a component through its accessor, so an
override at tier 3 is what the whole framework receives. Nothing is cached: an
accessor builds or resolves its class on every call, which is what Django's own
``ModelFormMixin.get_form_class()`` does.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple, cast

from django.core.exceptions import ImproperlyConfigured
from django.db.models.constants import LOOKUP_SEP
from django.forms import ModelForm
from django.utils.functional import Promise
from django.utils.module_loading import import_string
from django_filters import FilterSet
from django_tables2 import Table
from import_export.resources import ModelResource

from fairdm.registry.exceptions import ConfigurationError, FieldValidationError

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.db import models
    from rest_framework.serializers import ModelSerializer


@dataclass(frozen=True, kw_only=True)
class Authority:
    """The authority that created or maintains a data model.

    Attributes:
        name: The full name of the authority (required)
        short_name: An abbreviated name for the authority
        website: The authority's website URL
    """

    name: str | Promise
    """The name of the authority that created this metadata. This is required.

    Accepts a lazy translation as well as a plain string, so an app config can
    declare its authority with ``gettext_lazy`` before the translations load.
    """

    short_name: str = ""
    """The short name of the authority that created this metadata."""

    website: str = ""
    """The website of the authority that created this metadata."""


@dataclass(frozen=True, kw_only=True)
class Citation:
    """A citation for a data model.

    Attributes:
        text: The full citation text
        doi: The DOI for the citation
    """

    text: str = ""
    """The citation for the data model."""

    doi: str = ""
    """The DOI for the citation."""


@dataclass
class ModelMetadata:
    """Structured metadata describing a registered model.

    Holds FAIR-compliant metadata about a Sample or Measurement model, so that a
    registered model can describe and credit itself.
    """

    description: str = ""
    authority: Authority | None = None
    keywords: list[str] = field(default_factory=list)
    repository_url: str = ""
    citation: Citation | None = None
    maintainer: str = ""
    maintainer_email: str = ""


class Component(NamedTuple):
    """One row of the component table.

    Attributes:
        fields_attr: the configuration attribute holding this component's own field list
        class_attr: the configuration attribute holding a supplied class
        base: the class a supplied class must subclass
        factory: the name of the generator in ``fairdm.registry.factories``
    """

    fields_attr: str
    class_attr: str
    base: type | None
    factory: str


COMPONENTS: dict[str, Component] = {
    "form": Component("form_fields", "form_class", ModelForm, "FormFactory"),
    "table": Component("table_fields", "table_class", Table, "TableFactory"),
    "filterset": Component(
        "filterset_fields", "filterset_class", FilterSet, "FilterFactory"
    ),
    "serializer": Component(
        "serializer_fields", "serializer_class", None, "SerializerFactory"
    ),
    "resource": Component(
        "resource_fields", "resource_class", ModelResource, "ResourceFactory"
    ),
    "admin": Component("admin_list_display", "admin_class", None, "AdminFactory"),
}
"""Every component the registry produces, and where its configuration lives.

``base`` is ``None`` for the two components whose base class cannot be imported at
module scope: the serializer's base comes from Django REST Framework and the
admin's from ``django.contrib.admin``, both of which import app code.
"""


def flatten_fields(fields: Sequence[Any] | None) -> list[str]:
    """Flatten a field list that groups names in tuples for layout.

    A grouped list and a plain one produce the same fields, so grouping is free
    for a portal to use and invisible to every generator.
    """
    if not fields:
        return []

    flat: list[str] = []
    for item in fields:
        if isinstance(item, (tuple, list)):
            flat.extend(item)
        else:
            flat.append(item)
    return flat


def _component_base(name: str) -> type | None:
    """Resolve a component's base class, importing app code only when asked."""
    declared = COMPONENTS[name].base
    if declared is not None:
        return declared
    if name == "serializer":
        from rest_framework.serializers import BaseSerializer

        return BaseSerializer
    if name == "admin":
        from django.contrib.admin import ModelAdmin as DjangoModelAdmin

        return DjangoModelAdmin
    return None


class ModelConfiguration:
    """How one model appears across every framework surface.

    Written as a subclass declaring class attributes, the way ``Meta`` and
    ``ModelAdmin`` are written::

        @fairdm.register
        class RockSampleConfig(ModelConfiguration):
            model = RockSample
            fields = ["name", "location", "date_collected"]

    Declare a component's own field list where it differs from the rest::

            table_fields = ["name", "location", "contributor"]

    Supply a class to replace one component outright::

            table_class = RockSampleTable

    Or override its accessor when a field list cannot say what you need::

            def get_table_class(self):
                return build_table(self.model)

    Declaring both a component's field list and its class is refused at
    registration, following Django's rule for ``fields`` and ``form_class``.
    """

    model: "type[models.Model]" = None  # type: ignore[assignment]
    """The Django model this configures. A concrete Sample or Measurement subclass.

    Declared non-optional because every method may rely on it: the default of None
    exists only so that a subclass can supply it, and ``_validate_model`` refuses a
    configuration that reaches the end of construction without one.
    """

    metadata: ModelMetadata | None = None
    """Structured metadata about the model."""

    fields: list[Any] = []
    """Field list inherited by every component that declares none of its own.

    Names may use Django's double-underscore paths, and may be grouped in tuples
    for layout. An empty list means the framework decides.
    """

    exclude: list[str] = []
    """Names to leave out of every component."""

    search_fields: list[str] | None = None
    """Field paths `SearchMixin` searches with `?q=` (FR-024).

    `None` (the default) resolves to `["name"]` via `get_search_fields()`. Every
    entry must resolve to a text field - `CharField` or `TextField` - the same test
    `FilterFactory._get_search_fields` already applies, so a numeric, boolean or
    date field is refused at import rather than raising on a visitor's first search
    (FR-026, decisions.md D12).
    """

    form_fields: list[Any] | None = None
    table_fields: list[Any] | None = None
    filterset_fields: list[Any] | None = None
    serializer_fields: list[Any] | None = None
    resource_fields: list[Any] | None = None
    admin_list_display: list[Any] | None = None

    form_class: type[ModelForm] | str | None = None
    table_class: type[Table] | str | None = None
    filterset_class: type[FilterSet] | str | None = None
    serializer_class: "type[ModelSerializer] | str | None" = None
    resource_class: type[ModelResource] | str | None = None
    admin_class: "type[ModelAdmin] | str | None" = None

    display_name: str = ""
    """Human-readable name, defaulting to the model's verbose name."""

    description: str = ""
    """Description of this model type."""

    #: Attributes a caller may set per instance.
    _OVERRIDABLE = (
        "metadata",
        "fields",
        "exclude",
        "search_fields",
        *(c.fields_attr for c in COMPONENTS.values()),
        *(c.class_attr for c in COMPONENTS.values()),
        "display_name",
        "description",
    )

    def __init__(self, model: "type[models.Model] | None" = None, **overrides: Any):
        """Build a configuration, validating it before it can be registered.

        ``model`` may be passed positionally, as ``registry.register`` does, or by
        keyword alongside any other configuration attribute.
        """
        if model is not None:
            self.model = model

        for name, value in overrides.items():
            if name not in self._OVERRIDABLE:
                raise TypeError(
                    f"{type(self).__name__}() got an unexpected keyword argument "
                    f"{name!r}"
                )
            setattr(self, name, value)

        # Give each instance its own copy of the mutable declarative defaults, so
        # that a caller appending to one configuration's list cannot reach another.
        for name in ("fields", "exclude"):
            if name not in overrides:
                setattr(self, name, list(getattr(self, name)))

        self._validate_model()

        if not self.display_name:
            self.display_name = str(self.model._meta.verbose_name).title()
        if self.metadata is None:
            self.metadata = ModelMetadata()

        self._validate_component_conflicts()
        self._validate_fields()
        self._validate_search_fields()
        self._validate_custom_classes()
        self._validate_admin_inheritance()

    # Validation, all of it at construction time so that a misconfigured portal
    # stops at import rather than serving a broken page.

    def _validate_model(self) -> None:
        """A configuration needs a model. Whether that model may be *registered* is
        the registry's decision, made in FairDMRegistry.register per FR-002."""
        if self.model is None:
            raise ConfigurationError("ModelConfiguration.model is required")

    def _validate_component_conflicts(self) -> None:
        """Refuse a component configured two ways at once.

        Django refuses the same pair on ``ModelFormMixin``. Silently preferring one
        leaves a portal holding a field list that has no effect.
        """
        for name, spec in COMPONENTS.items():
            if (
                getattr(self, spec.fields_attr) is not None
                and getattr(self, spec.class_attr) is not None
            ):
                raise ImproperlyConfigured(
                    f"{type(self).__name__} for {self.model.__name__} declares both "
                    f"{spec.fields_attr} and {spec.class_attr}. Specifying both a "
                    f"field list and a class for the {name} component is not "
                    f"permitted, because the field list would have no effect. "
                    f"Remove one of them."
                )

    def _field_lists(self) -> list[tuple[str, list[Any]]]:
        """Every declared field list, by the attribute that declared it."""
        lists: list[tuple[str, list[Any]]] = [("fields", self.fields)]
        lists += [
            (spec.fields_attr, getattr(self, spec.fields_attr))
            for spec in COMPONENTS.values()
        ]
        return [(name, value) for name, value in lists if value]

    def _validate_fields(self) -> None:
        """Every name in every field list must resolve, path segments included."""
        for attr, field_list in self._field_lists():
            for name in flatten_fields(field_list):
                self._validate_field_path(name, attr)

    def _validate_field_path(self, path: str, attr: str) -> None:
        """Refuse a path that does not resolve, naming why."""
        from fairdm.utils.inspection import FieldInspector

        inspector = FieldInspector(self.model)
        resolves, reason = inspector.resolve_path(path)
        if resolves:
            return

        raise FieldValidationError(
            field_name=path,
            model=self.model,
            attribute=attr,
            reason=reason,
            suggestion=(
                ", ".join(inspector.close_matches(path.split(LOOKUP_SEP)[0]))
                if reason is None
                else None
            ),
        )

    def _validate_search_fields(self) -> None:
        """Every `search_fields` entry must resolve, and resolve to a text field.

        Two passes (data-model.md, decisions.md D12): `_validate_field_path` decides
        whether the path exists at all, the same test `fields` uses, then a positive
        type check on the resolved final field - a `DecimalField`, `BooleanField` or
        `DateField` resolves cleanly and would otherwise only raise on the first
        search a visitor types. `icontains` is registered on `Field` itself, so
        asking whether the field *has* the lookup would reject nothing.
        """
        from django.db import models as django_models

        for path in self.search_fields or []:
            self._validate_field_path(path, "search_fields")

            model: Any = self.model
            field = None
            for segment in path.split(LOOKUP_SEP):
                field = model._meta.get_field(segment)
                model = field.related_model

            if not isinstance(
                field, (django_models.CharField, django_models.TextField)
            ):
                raise FieldValidationError(
                    field_name=path,
                    model=self.model,
                    attribute="search_fields",
                    reason=(
                        f"{field.__class__.__name__} is not a text field - "
                        "search_fields must resolve to a CharField or TextField"
                    ),
                )

    def _validate_custom_classes(self) -> None:
        """A supplied class must subclass the base its component requires."""
        for name, spec in COMPONENTS.items():
            declared = getattr(self, spec.class_attr)
            if declared is None:
                continue

            # Resolve a dotted path before the check, so a string cannot skip it.
            supplied = self._get_class(declared)
            base = _component_base(name)
            if base is not None and not issubclass(supplied, base):
                raise ConfigurationError(
                    f"{spec.class_attr} for {self.model.__name__} must be a subclass "
                    f"of {base.__module__}.{base.__qualname__}. Got "
                    f"{supplied.__name__} instead.",
                    model=self.model,
                )

    def _validate_admin_inheritance(self) -> None:
        """A supplied admin must use the child admin base for its hierarchy.

        django-polymorphic's parent and child admins are not interchangeable, and a
        child registered against the parent base misbehaves in ways that are hard to
        trace back to the registration.
        """
        if self.admin_class is None:
            return

        admin_cls = self._get_class(self.admin_class)

        try:
            from fairdm.core.measurement.admin import MeasurementChildAdmin
            from fairdm.core.models import Measurement, Sample
            from fairdm.core.sample.admin import SampleChildAdmin
        except ImportError:  # pragma: no cover - core app always present in practice
            return

        if issubclass(self.model, Sample) and not issubclass(
            admin_cls, SampleChildAdmin
        ):
            raise ConfigurationError(
                f"Admin class for Sample subclass {self.model.__name__} must inherit "
                f"from SampleChildAdmin. Got {admin_cls.__name__} instead. "
                f"Change your admin class to: "
                f"class {admin_cls.__name__}(SampleChildAdmin): ..."
            )

        if issubclass(self.model, Measurement) and not issubclass(
            admin_cls, MeasurementChildAdmin
        ):
            raise ConfigurationError(
                f"Admin class for Measurement subclass {self.model.__name__} must "
                f"inherit from MeasurementChildAdmin (the child admin base class). Got "
                f"{admin_cls.__name__} instead. Change your admin class to: "
                f"class {admin_cls.__name__}(MeasurementChildAdmin): ..."
            )

    # Field resolution and component production.

    @classmethod
    def get_default_fields(cls, model: "type[models.Model]") -> list[str]:
        """The framework's own choice of fields for a model, per FR-011.

        Delegates to ``FieldInspector``, which is the single implementation. Two
        copies of this rule used to be live in the same request path and disagreed
        on three points, so the API and the admin could show different default
        fields for one model.
        """
        from fairdm.utils.inspection import FieldInspector

        return FieldInspector(model).get_default_fields()

    def resolve_fields(self, component: str) -> list[str]:
        """The field list one component is built from.

        A component's own list wins, then the shared list, then the framework's
        defaults. Grouping tuples are flattened, and anything in ``exclude`` is
        dropped.
        """
        spec = COMPONENTS[component]
        declared = getattr(self, spec.fields_attr)
        chosen = (
            declared
            if declared is not None
            else (self.fields or self.get_default_fields(self.model))
        )
        excluded = set(self.exclude)
        return [name for name in flatten_fields(chosen) if name not in excluded]

    def get_search_fields(self) -> list[str]:
        """The fields `SearchMixin` searches on `?q=`, defaulting to `["name"]`
        when this configuration declares none (FR-024, data-model.md)."""
        return self.search_fields or ["name"]

    def _component_class(self, component: str) -> type:
        """Resolve or build one component's class. Never cached."""
        spec = COMPONENTS[component]
        declared = getattr(self, spec.class_attr)
        if declared is not None:
            return self._get_class(declared)

        from fairdm.registry import factories

        factory = getattr(factories, spec.factory)
        generated = factory(
            model=self.model, fields=self.resolve_fields(component)
        ).generate()
        return cast(type, generated)

    def get_form_class(self) -> type[ModelForm]:
        """The ModelForm for this model. Override to build your own."""
        return self._component_class("form")

    def get_table_class(self) -> type[Table]:
        """The django-tables2 Table for this model. Override to build your own."""
        return self._component_class("table")

    def get_filterset_class(self) -> type[FilterSet]:
        """The django-filter FilterSet for this model. Override to build your own."""
        return self._component_class("filterset")

    def get_serializer_class(self) -> "type[ModelSerializer]":
        """The REST serializer for this model. Override to build your own."""
        return cast("type[ModelSerializer]", self._component_class("serializer"))

    def get_resource_class(self) -> type[ModelResource]:
        """The import and export resource. Override to build your own."""
        return cast(type[ModelResource], self._component_class("resource"))

    def get_admin_class(self) -> "type[ModelAdmin]":
        """The Django admin class for this model. Override to build your own."""
        return cast("type[ModelAdmin]", self._component_class("admin"))

    # Naming.

    def _get_class(self, class_or_path: str | type) -> type:
        """Import a class from a dotted path, or return the class unchanged."""
        if isinstance(class_or_path, str):
            return cast(type, import_string(class_or_path))
        return cast(type, class_or_path)

    def get_display_name(self) -> str:
        """The human-readable name for this model."""
        return self.display_name or str(self.model._meta.verbose_name).title()

    def get_description(self) -> str:
        """The description for this model."""
        if self.metadata and self.metadata.description:
            return self.metadata.description
        return self.description or f"Configuration for {self.model.__name__}"

    def get_slug(self) -> str:
        """The URL-safe name for this model, used in routes and view names."""
        return self.model._meta.model_name or ""

    def get_verbose_name(self) -> str:
        """The model's singular verbose name."""
        return str(self.model._meta.verbose_name)

    def get_verbose_name_plural(self) -> str:
        """The model's plural verbose name."""
        return str(self.model._meta.verbose_name_plural)

    def __repr__(self) -> str:
        model = self.model._meta.label if self.model else None
        return f"<{type(self).__name__}: {model}>"


class SampleConfig(ModelConfiguration):
    """Configuration for a Sample subclass. Named for clarity at the call site."""


class MeasurementConfig(ModelConfiguration):
    """Configuration for a Measurement subclass. Named for clarity at the call site."""


__all__ = [
    "COMPONENTS",
    "Authority",
    "Citation",
    "Component",
    "MeasurementConfig",
    "ModelConfiguration",
    "ModelMetadata",
    "SampleConfig",
    "flatten_fields",
]

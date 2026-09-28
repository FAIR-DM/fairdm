"""Factories that generate Django components from a ModelConfiguration.

Each factory builds one component (form, table, filter set, admin, serializer or
resource), choosing widgets, columns and filters from the model's field types.
"""

from typing import Any, cast

from django.contrib import admin
from django.db import models
from django.forms import ModelForm, modelform_factory
from django_filters import FilterSet
from django_filters.filterset import filterset_factory
from django_tables2 import Table
from django_tables2.tables import table_factory

from fairdm.utils.inspection import FieldInspector


class ComponentFactory:
    """Base factory for generating Django components from configuration.

    This abstract base class provides common functionality for all component factories.
    Subclasses implement specific generation logic for Forms, Tables, Filters, etc.

    Args:
        model: The Django model class to generate components for.
        fields: Field names to use. ``None`` uses the model's safe fields.
    """

    def __init__(self, model: type[models.Model], fields: list[str] | None = None):
        self.model = model
        self.fields = fields
        self.inspector = FieldInspector(model)

    def get_fields(self) -> list[str]:
        """Return the fields to use.

        Explicitly provided fields win, then the model's safe fields as found by
        ``inspector.get_safe_fields()``.

        Returns:
            The field names to use.
        """
        if self.fields is not None:
            return self.fields

        return cast(list[str], self.inspector.get_safe_fields())

    def generate(self) -> Any:
        """Generate the component. Subclasses must implement it.

        Returns:
            The generated component class.

        Raises:
            NotImplementedError: Always, on the base class.
        """
        raise NotImplementedError("Subclasses must implement generate()")


class FormFactory(ComponentFactory):
    """Factory for generating ModelForm classes with smart widgets.

    Dates, large text, email and URL fields get a matching widget, and the form
    carries a crispy-forms helper with a submit button.
    """

    def generate(self) -> type[ModelForm]:
        """Generate a ModelForm class with smart widgets.

        Returns:
            A ModelForm subclass with smart widgets and a crispy-forms helper.
        """
        from crispy_forms.helper import FormHelper
        from crispy_forms.layout import Submit

        fields = self.get_fields()

        widgets = self._get_smart_widgets()

        # Built on the sample or measurement form mixin so a type with no form of
        # its own keeps the mixin's widgets, dataset scoping and guidance text.
        form_class = modelform_factory(
            self.model,
            form=self.get_base_form_class(),
            fields=fields,
            widgets=widgets,
        )

        original_init = form_class.__init__

        def __init__(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_method = "post"
            self.helper.add_input(Submit("submit", "Save"))

        form_class.__init__ = __init__  # type: ignore[method-assign]

        return form_class

    def _get_smart_widgets(self) -> dict[str, Any]:
        """Choose a widget for each field by its type.

        Returns:
            A dict mapping field names to widget instances.
        """
        from django import forms

        widgets: dict[str, forms.Widget] = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.DateField) and not isinstance(
                    field, models.DateTimeField
                ):
                    widgets[field_name] = forms.DateInput(attrs={"type": "date"})

                elif isinstance(field, models.DateTimeField):
                    widgets[field_name] = forms.DateTimeInput(
                        attrs={"type": "datetime-local"}
                    )

                elif isinstance(field, models.TextField) or (
                    isinstance(field, models.CharField)
                    and getattr(field, "max_length", 0) > 200
                ):
                    widgets[field_name] = forms.Textarea(attrs={"rows": 4})

                elif isinstance(field, models.EmailField):
                    widgets[field_name] = forms.EmailInput()

                elif isinstance(field, models.URLField):
                    widgets[field_name] = forms.URLInput()

            except Exception:  # noqa: S110
                pass

        return widgets

    def get_base_form_class(self) -> type[ModelForm]:
        """Return the base ModelForm to build the form on.

        Mirrors `TableFactory.get_base_table_class()`: a sample or measurement type
        supplying no form of its own still gets `SampleFormMixin`'s or
        `MeasurementFormMixin`'s widget configuration, dataset scoping and guidance
        text rather than a bare `ModelForm`.

        Returns:
            A form class carrying the mixin for the model's hierarchy, or
            ``ModelForm`` for any other model.
        """
        from fairdm.core.measurement.forms import MeasurementFormMixin
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.forms import SampleFormMixin
        from fairdm.core.sample.models import Sample

        if issubclass(self.model, Sample):
            return cast(
                type[ModelForm],
                type("SampleFormBase", (SampleFormMixin, ModelForm), {}),
            )

        if issubclass(self.model, Measurement):
            return cast(
                type[ModelForm],
                type("MeasurementFormBase", (MeasurementFormMixin, ModelForm), {}),
            )

        return ModelForm


class TableFactory(ComponentFactory):
    """Factory for generating Table classes with smart column types.

    Dates, emails, URLs and booleans get a matching column. Large text fields are
    left out of the table.
    """

    def generate(self) -> type[Table]:
        """Generate a django-tables2 Table class with smart columns.

        Returns:
            A Table subclass with smart columns.
        """
        fields = self.get_fields()

        filtered_fields = self._filter_table_fields(fields)

        extra_columns = self._get_smart_columns(filtered_fields)

        base_table = self.get_base_table_class()
        if extra_columns:
            table_attrs = extra_columns.copy()
            base_table = type("SmartTable", (base_table,), table_attrs)

        table_class = table_factory(
            self.model,
            table=base_table,
            fields=filtered_fields,
        )

        # No template or CSS classes: the project's DJANGO_TABLES2_TEMPLATE setting
        # decides how a generated table is styled.
        return cast(type[Table], table_class)

    def _filter_table_fields(self, fields: list[str]) -> list[str]:
        """Filter out fields that shouldn't appear in tables (large text, etc).

        Args:
            fields: List of field names

        Returns:
            The field names suitable for a table, or all of them if none are.
        """
        filtered = []
        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.TextField):
                    continue
                if (
                    isinstance(field, models.CharField)
                    and getattr(field, "max_length", 0) > 200
                ):
                    continue

                filtered.append(field_name)

            except Exception:
                filtered.append(field_name)

        return filtered or fields

    def _get_smart_columns(self, fields: list[str]) -> dict[str, Any]:
        """Choose a column type for each field by its type.

        Args:
            fields: List of field names

        Returns:
            Dictionary mapping field names to column instances
        """
        import django_tables2 as tables

        columns = {}

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.DateField) and not isinstance(
                    field, models.DateTimeField
                ):
                    columns[field_name] = tables.DateColumn(format="Y-m-d")

                elif isinstance(field, models.DateTimeField):
                    columns[field_name] = tables.DateTimeColumn(format="Y-m-d H:i")

                elif isinstance(field, models.EmailField):
                    columns[field_name] = tables.EmailColumn()

                elif isinstance(field, models.URLField):
                    columns[field_name] = tables.URLColumn()

                elif isinstance(field, models.BooleanField):
                    columns[field_name] = tables.BooleanColumn()

            except Exception:  # noqa: S110
                pass

        return columns

    def get_base_table_class(self) -> type[Table]:
        """Return the base table class for the model.

        Returns:
            The sample or measurement table for those hierarchies, otherwise
            ``Table``.
        """
        from fairdm.contrib.collections.tables import MeasurementTable, SampleTable
        from fairdm.core.models import Measurement, Sample

        if issubclass(self.model, Sample):
            return cast(type[Table], SampleTable)
        elif issubclass(self.model, Measurement):
            return cast(type[Table], MeasurementTable)

        return cast(type[Table], Table)


def published_related_queryset(related_model: type[models.Model]) -> Any:
    """Return the published records of a model, or ``None`` when publication is moot.

    The dataset branch goes through `Dataset.all_objects`, never
    `Dataset.objects`: the default manager excludes PRIVATE datasets, and a
    published-but-private dataset is the ordinary state, so
    `Dataset.objects.published()` would leave a filter offering nothing while
    the table shows that dataset's rows. Publication is the only test a listing
    applies.

    `None` rather than an unscoped queryset, so a caller can tell "every
    published one" from "not this model's question" - a content-type filter
    already scoped to the registered types must not be widened back out.

    Args:
        related_model: The model whose records a filter offers.

    Returns:
        A queryset of the published records for a Dataset, Sample or Measurement
        model, otherwise ``None``.
    """
    from fairdm.core.dataset.models import Dataset
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

    if issubclass(related_model, Dataset):
        return Dataset.all_objects.published()
    if issubclass(related_model, (Sample, Measurement)):
        return related_model._default_manager.published()
    return None


class PublishedChoicesMixin:
    """Narrow every related-record filter to published records, last.

    Scoping filters as the factory builds them is not enough, in two ways that
    both leaked.

    A generated filter set inherits `SampleFilterMixin` or
    `MeasurementFilterMixin`, and both assign their own hand-declared `dataset`
    (and, for measurements, `sample`) choice lists in `__init__` - from
    `Dataset.all_objects` and `Sample.objects` respectively, neither of which
    applies publication. Those assignments happen at instantiation, after any
    class-level override, so a class-level fix does not survive them.

    And a registration may supply its own `filterset_class`, or override
    `get_filterset_class()` outright, in which case the factory never runs at
    all. That is a documented tier of the configuration API, not an edge case.

    So this is applied by the listing view to whatever filter set it is handed,
    and it is placed first in the bases, so its `__init__` runs the rest of the
    chain and then re-scopes what that chain assigned. It reads each filter's
    own queryset rather than the model field, so a many-to-many or reverse
    relation django-filter generated for itself is covered by the same pass,
    and a relation publication says nothing about is left alone.

    It applies to the listings and to nothing else. Every other page that
    builds a filter on those two core mixins keeps their behaviour.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for filter_ in self.filters.values():
            queryset = getattr(filter_, "queryset", None)
            if queryset is None or not hasattr(queryset, "model"):
                continue
            scoped = published_related_queryset(queryset.model)
            if scoped is not None:
                filter_.queryset = scoped

    @classmethod
    def applied_to(cls, filterset_class: type) -> type:
        """Put this mixin in front of a filter set, unless it is already there.

        Idempotent, because a listing resolves its filter set on every request and a
        fresh subclass per request would leak classes.

        Args:
            filterset_class: The filter set to scope.

        Returns:
            ``filterset_class`` itself if it already has the mixin, otherwise a
            subclass with the mixin first.
        """
        if issubclass(filterset_class, cls):
            return filterset_class
        return type(
            f"Published{filterset_class.__name__}",
            (cls, filterset_class),
            {},
        )


class FilterFactory(ComponentFactory):
    """Factory for generating FilterSet classes with smart filter types.

    Dates get range filters, choice fields a choice filter, foreign keys a model
    choice filter, numbers a range filter and text a case-insensitive contains filter.
    """

    def generate(self) -> type[FilterSet]:
        """Generate a django-filter FilterSet class with smart filters.

        Fields django-filter cannot resolve are dropped one at a time until it
        accepts the rest.

        Returns:
            A FilterSet subclass with smart filters.

        Raises:
            AssertionError: django-filter rejected the fields for a reason other
                than an unresolved field name.
        """
        import re

        fields = self.get_fields()

        # django-filter rejects names that are not model fields.
        model_field_names = {f.name for f in self.model._meta.get_fields()}
        fields = [f for f in fields if f in model_field_names]

        filter_overrides = self._get_smart_filters(fields)

        # Built on the sample or measurement filter mixin so a type with no filter
        # set of its own keeps the mixin's declared filters.
        base_filterset = self.get_base_filterset_class()

        try:
            meta_attrs = {
                "model": self.model,
                "fields": fields,
            }
            Meta = type("Meta", (), meta_attrs)

            filterset_attrs = {"Meta": Meta}
            filterset_attrs.update(filter_overrides)

            filterset_class = type(
                f"{self.model.__name__}FilterSet",
                (base_filterset,),
                filterset_attrs,
            )

            return cast(type[FilterSet], filterset_class)

        except Exception:
            # The base class is passed here too, or a model landing in this branch
            # would lose the mixin.
            fields = [f for f in fields if f in model_field_names]

            max_attempts = len(fields)
            attempt = 0

            while attempt < max_attempts:
                try:
                    filterset_class = filterset_factory(
                        self.model,
                        filterset=base_filterset,
                        fields=fields,
                    )
                    return cast(type[FilterSet], filterset_class)
                except AssertionError as e:
                    error_msg = str(e)
                    if "resolved field" in error_msg:
                        match = re.search(r"resolved field '(\w+)'", error_msg)
                        if match:
                            problematic_field = match.group(1)
                            fields = [f for f in fields if f != problematic_field]
                            attempt += 1
                            if not fields:
                                break
                            continue
                    raise

            return cast(
                type[FilterSet],
                filterset_factory(self.model, filterset=base_filterset, fields=[]),
            )

    def _get_smart_filters(self, fields: list[str]) -> dict[str, Any]:
        """Choose a filter type for each field by its type.

        Args:
            fields: List of field names

        Returns:
            Dictionary mapping field names to filter instances
        """
        import django_filters as filters

        filter_overrides = {}

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.DateField) and not isinstance(
                    field, models.DateTimeField
                ):
                    filter_overrides[field_name] = filters.DateFromToRangeFilter()

                elif isinstance(field, models.DateTimeField):
                    filter_overrides[field_name] = filters.DateTimeFromToRangeFilter()

                elif isinstance(field, models.BooleanField):
                    filter_overrides[field_name] = filters.BooleanFilter()

                elif hasattr(field, "choices") and field.choices:
                    filter_overrides[field_name] = filters.ChoiceFilter(
                        choices=field.choices
                    )

                elif isinstance(field, models.ForeignKey):
                    filter_overrides[field_name] = filters.ModelChoiceFilter(
                        queryset=self._published_related_queryset(field.related_model)
                    )

                elif isinstance(
                    field, (models.IntegerField, models.FloatField, models.DecimalField)
                ):
                    filter_overrides[field_name] = filters.RangeFilter()

                elif isinstance(field, (models.CharField, models.TextField)):
                    filter_overrides[field_name] = filters.CharFilter(
                        lookup_expr="icontains"
                    )

            except Exception:  # noqa: S110
                pass

        return filter_overrides

    def _published_related_queryset(self, related_model: type[models.Model]) -> Any:
        """Return a related-record filter's choices, scoped to published records.

        Falls back to the model's own default manager for a relation
        publication says nothing about, such as a content type.

        Args:
            related_model: The model on the other end of the relation.

        Returns:
            A queryset of the records to offer.
        """
        scoped = published_related_queryset(related_model)
        if scoped is None:
            return related_model._default_manager.all()
        return scoped

    def get_base_filterset_class(self) -> type[FilterSet]:
        """Return the base FilterSet to build the filter set on.

        Mirrors `TableFactory.get_base_table_class()`: a sample or measurement
        type's generated filter set carries `SampleFilterMixin`'s or
        `MeasurementFilterMixin`'s declared filters rather than a bare
        `FilterSet`. Both mixins are already `FilterSet` subclasses, so, unlike the
        form factory, no wrapping is needed here.

        Returns:
            The mixin for the model's hierarchy, or ``FilterSet`` for any other
            model.
        """
        from fairdm.core.measurement.filters import MeasurementFilterMixin
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.filters import SampleFilterMixin
        from fairdm.core.sample.models import Sample

        if issubclass(self.model, Sample):
            return cast(type[FilterSet], SampleFilterMixin)

        if issubclass(self.model, Measurement):
            return cast(type[FilterSet], MeasurementFilterMixin)

        return cast(type[FilterSet], FilterSet)


class AdminFactory(ComponentFactory):
    """Factory for generating Django Admin ModelAdmin classes.

    Generates ``list_display``, ``search_fields`` and ``list_filter``, groups fields
    into fieldsets, marks timestamps and ids read-only and adds a date hierarchy
    where the model has a date field.
    """

    def generate(self) -> type[admin.ModelAdmin]:
        """Generate a Django ModelAdmin class.

        Returns:
            ModelAdmin subclass configured for the model
        """
        fields = self.get_fields()
        inspector = FieldInspector(self.model)

        admin_base = self._get_admin_base_class()

        attrs = {
            "model": self.model,
            "list_display": self._get_list_display(fields, inspector),
            "search_fields": self._get_search_fields(fields, inspector),
            "list_filter": self._get_list_filter(fields, inspector),
        }

        if admin_base is not admin.ModelAdmin:
            base_readonly = getattr(admin_base, "readonly_fields", [])
            auto_readonly = self._get_readonly_fields(inspector)
            merged_readonly = list(dict.fromkeys(list(base_readonly) + auto_readonly))
            attrs["readonly_fields"] = merged_readonly
        else:
            attrs["readonly_fields"] = self._get_readonly_fields(inspector)

        date_hierarchy = self._get_date_hierarchy(inspector)
        if date_hierarchy:
            attrs["date_hierarchy"] = date_hierarchy

        if admin_base is not admin.ModelAdmin:
            attrs["base_model"] = self.model
            attrs["show_in_index"] = True
            # The base class already sets fields and fieldsets,
            # and Django rejects both.
        else:
            if len(fields) > 6:
                attrs["fieldsets"] = self._get_fieldsets(fields, inspector)
            else:
                attrs["fields"] = fields

        app_label = self._get_admin_app_label()
        if app_label:
            meta_attrs = {"app_label": app_label}
            attrs["Meta"] = type("Meta", (), meta_attrs)

        admin_class_name = f"{self.model.__name__}Admin"
        admin_class = type(admin_class_name, (admin_base,), attrs)

        return admin_class

    def _get_list_display(
        self, fields: list[str], inspector: FieldInspector
    ) -> list[str]:
        """Get list_display fields for admin changelist.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of field names for list_display (max 5)
        """
        display_fields = []

        if "id" in fields:
            display_fields.append("id")

        for name_field in ["name", "title", "label"]:
            if name_field in fields and name_field not in display_fields:
                display_fields.append(name_field)
                break

        for field_name in fields:
            if len(display_fields) >= 5:
                break
            if field_name in display_fields:
                continue

            field = inspector.get_field(field_name)
            if isinstance(field, models.TextField):
                continue
            if (
                isinstance(field, models.CharField)
                and field.max_length
                and field.max_length > 200
            ):
                continue

            display_fields.append(field_name)

        return display_fields if display_fields else ["__str__"]

    def _get_search_fields(
        self, fields: list[str], inspector: FieldInspector
    ) -> list[str]:
        """Get search_fields for admin search.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of searchable field names
        """
        search_fields = []

        for field_name in fields:
            field = inspector.get_field(field_name)

            if isinstance(field, (models.CharField, models.TextField)):
                search_fields.append(field_name)

            if isinstance(field, models.EmailField):
                search_fields.append(field_name)

        return search_fields

    def _get_list_filter(
        self, fields: list[str], inspector: FieldInspector
    ) -> list[str]:
        """Get list_filter fields for admin sidebar.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            List of filterable field names
        """
        filter_fields = []

        for field_name in fields:
            field = inspector.get_field(field_name)
            if field is None:
                continue

            if isinstance(field, models.BooleanField):
                filter_fields.append(field_name)

            if hasattr(field, "choices") and field.choices:
                filter_fields.append(field_name)

            if isinstance(field, models.ForeignKey):
                filter_fields.append(field_name)

        return filter_fields

    def _get_readonly_fields(self, inspector: FieldInspector) -> list[str]:
        """Get readonly fields for admin forms.

        Args:
            inspector: FieldInspector instance

        Returns:
            List of readonly field names
        """
        readonly = []

        for field_name in ["id", "created", "modified", "created_at", "updated_at"]:
            if inspector.has_field(field_name):
                readonly.append(field_name)

        return readonly

    def _get_date_hierarchy(self, inspector: FieldInspector) -> str | None:
        """Get date field for date_hierarchy.

        Args:
            inspector: FieldInspector instance

        Returns:
            Field name or None
        """
        for field_name in ["created", "modified", "date", "created_at", "updated_at"]:
            if inspector.has_field(field_name):
                field = inspector.get_field(field_name)
                if isinstance(field, (models.DateField, models.DateTimeField)):
                    return field_name

        return None

    def _get_fieldsets(
        self, fields: list[str], inspector: FieldInspector
    ) -> tuple[tuple[str | None, dict], ...]:
        """Get fieldsets for admin form grouping.

        Args:
            fields: Available field names
            inspector: FieldInspector instance

        Returns:
            Tuple of fieldset tuples (django-polymorphic expects tuples, not lists)
        """
        fieldsets: list[tuple[str | None, dict[str, Any]]] = []

        basic_fields = []
        for field_name in ["name", "title", "label", "description"]:
            if field_name in fields:
                basic_fields.append(field_name)

        if basic_fields:
            fieldsets.append((None, {"fields": basic_fields}))

        data_fields = []
        metadata_fields = ["id", "created", "modified", "created_at", "updated_at"]

        for field_name in fields:
            if field_name not in basic_fields and field_name not in metadata_fields:
                data_fields.append(field_name)

        if data_fields:
            fieldsets.append(("Data", {"fields": data_fields}))

        meta_fields = []
        for field_name in metadata_fields:
            if field_name in fields:
                meta_fields.append(field_name)

        if meta_fields:
            fieldsets.append(
                ("Metadata", {"fields": meta_fields, "classes": ["collapse"]})
            )

        # django-polymorphic concatenates fieldsets, so they must be tuples.
        return tuple(fieldsets) if fieldsets else ((None, {"fields": fields}),)

    def _get_admin_app_label(self) -> str | None:
        """Determine the app_label for admin grouping based on model inheritance.

        Returns:
            App label string for Sample/Measurement subtypes, None otherwise
        """
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            if issubclass(self.model, Sample):
                return "sample"
            elif issubclass(self.model, Measurement):
                return "measurement"
        except (ImportError, TypeError):
            pass
        return None

    def _get_admin_base_class(self) -> type[admin.ModelAdmin]:
        """Determine the correct admin base class for polymorphic models.

        For Sample subclasses, returns SampleChildAdmin.
        For Measurement subclasses, returns MeasurementChildAdmin.
        Otherwise returns standard ModelAdmin.

        Returns:
            Admin base class appropriate for the model
        """
        try:
            from fairdm.core.measurement.models import Measurement
            from fairdm.core.sample.models import Sample

            if issubclass(self.model, Sample) and self.model is not Sample:
                from fairdm.core.sample.admin import SampleChildAdmin

                return SampleChildAdmin

            if issubclass(self.model, Measurement) and self.model is not Measurement:
                from fairdm.core.measurement.admin import MeasurementChildAdmin

                return MeasurementChildAdmin

        except (ImportError, TypeError):
            pass

        return admin.ModelAdmin


class SerializerFactory(ComponentFactory):
    """Factory for generating DRF ModelSerializer classes.

    Foreign keys are represented by their string form.
    """

    def generate(self) -> type:
        """Generate a DRF ModelSerializer class.

        Returns:
            A ModelSerializer subclass that shows foreign keys as strings.
        """
        from rest_framework import serializers

        fields = self.get_fields()

        nested_serializers = self._get_nested_serializers()

        meta_attrs = {
            "model": self.model,
            "fields": list(fields),
        }
        Meta = type("Meta", (), meta_attrs)

        serializer_attrs = {"Meta": Meta}
        serializer_attrs.update(nested_serializers)

        serializer_class_name = f"{self.model.__name__}Serializer"
        serializer_class = type(
            serializer_class_name,
            (serializers.ModelSerializer,),
            serializer_attrs,
        )

        return serializer_class

    def _get_nested_serializers(self) -> dict[str, Any]:
        """Build a string-related field for each ForeignKey.

        Returns:
            Dictionary mapping field names to nested serializer fields
        """
        from rest_framework import serializers

        nested: dict[str, serializers.Field] = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.ForeignKey):
                    nested[field_name] = serializers.StringRelatedField()

            except Exception:  # noqa: S110
                pass

        return nested


class ResourceFactory(ComponentFactory):
    """Factory for generating import/export Resource classes.

    Foreign keys are matched on the related model's natural key where it has one,
    otherwise on its primary key.
    """

    def generate(self) -> type:
        """Generate an import/export Resource class.

        Returns:
            A ModelResource subclass with foreign key widgets.
        """
        from import_export import resources

        fields = self.get_fields()

        meta_attrs = {
            "model": self.model,
            "fields": list(fields),
            "export_order": list(fields),
        }
        Meta = type("Meta", (), meta_attrs)

        resource_attrs = {"Meta": Meta}

        fk_widgets = self._get_fk_widgets()
        resource_attrs.update(fk_widgets)

        resource_class_name = f"{self.model.__name__}Resource"
        resource_class = type(
            resource_class_name,
            (resources.ModelResource,),
            resource_attrs,
        )

        return resource_class

    def _get_fk_widgets(self) -> dict[str, Any]:
        """Generate ForeignKey widgets with natural key support.

        Returns:
            Dictionary mapping field names to widget instances
        """
        from import_export import widgets

        fk_widgets = {}
        fields = self.get_fields()

        for field_name in fields:
            try:
                field = self.model._meta.get_field(field_name)

                if isinstance(field, models.ForeignKey):
                    if hasattr(field.related_model, "natural_key"):
                        fk_widgets[field_name] = widgets.ForeignKeyWidget(
                            field.related_model, "natural_key"
                        )
                    else:
                        fk_widgets[field_name] = widgets.ForeignKeyWidget(
                            field.related_model, "pk"
                        )

            except Exception:  # noqa: S110
                pass

        return fk_widgets


__all__ = [
    "AdminFactory",
    "ComponentFactory",
    "FilterFactory",
    "FormFactory",
    "ResourceFactory",
    "SerializerFactory",
    "TableFactory",
]

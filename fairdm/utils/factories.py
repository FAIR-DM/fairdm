from django.forms import modelform_factory
from django_filters.filterset import filterset_factory
from django_tables2 import table_factory
from import_export.resources import ModelDeclarativeMetaclass, ModelResource

__all__ = [
    "filterset_factory",
    "modelform_factory",
    "modelresource_factory",
    "serializer_factory",
    "table_factory",
]


def modelresource_factory(model, resource_class=ModelResource, **kwargs):
    """
    Factory for creating ``ModelResource`` class for given Django model.
    """
    meta = type("Meta", (object,), {"model": model, **kwargs})
    metaclass = ModelDeclarativeMetaclass
    return metaclass(
        f"{model.__name__}Resource",
        (resource_class,),
        {
            "Meta": meta,
        },
    )


def serializer_factory(model, base_serializer, **kwargs):
    meta = type("Meta", (base_serializer.Meta,), {"model": model, **kwargs})
    return type(f"{model.__name__}Serializer", (base_serializer,), {"Meta": meta})


class AutoGenerationFactories:
    """
    Factory class for auto-generating forms, serializers, filters, and tables
    based on configuration classes for Sample and Measurement subclasses.
    """

    def generate_form(self, model_class, config):
        """
        Auto-generate a ModelForm based on configuration.

        Args:
            model_class: The Django model class
            config: Configuration instance with list_fields/detail_fields

        Returns:
            ModelForm subclass
        """
        from django.forms import ModelForm

        # Determine fields to include
        fields = getattr(config, "detail_fields", None) or getattr(config, "list_fields", None)
        if fields is None:
            # Use all fields except those in private_fields
            private_fields = getattr(config, "private_fields", [])
            fields = [
                f.name for f in model_class._meta.fields if f.name not in private_fields and not f.name.startswith("_")
            ]

        # Create form using modelform_factory
        form_class = modelform_factory(
            model_class, form=ModelForm, fields=fields, **getattr(config, "form_options", {})
        )

        return form_class

    def generate_filterset(self, model_class, config):
        """
        Auto-generate a FilterSet based on configuration.

        Args:
            model_class: The Django model class
            config: Configuration instance with filter_fields

        Returns:
            FilterSet subclass
        """
        # Determine fields to filter on
        filter_fields = getattr(config, "filter_fields", [])
        if not filter_fields:
            # Default filter fields - common filterable fields
            default_fields = ["created", "modified", "name"]
            filter_fields = [f.name for f in model_class._meta.fields if f.name in default_fields]

        # Create filterset using filterset_factory
        filterset_class = filterset_factory(
            model_class, fields=filter_fields, **getattr(config, "filterset_options", {})
        )

        return filterset_class

    def generate_table(self, model_class, config):
        """
        Auto-generate a django-tables2 Table based on configuration.

        Args:
            model_class: The Django model class
            config: Configuration instance with list_fields

        Returns:
            Table subclass
        """
        import django_tables2 as tables

        # Determine fields to display
        list_fields = getattr(config, "list_fields", [])
        if not list_fields:
            # Default table fields
            default_fields = ["name", "created", "modified"]
            list_fields = [f.name for f in model_class._meta.fields if f.name in default_fields]

        # Always add an actions column
        fields = list_fields + ["actions"]

        # Create table using table_factory
        table_class = table_factory(model_class, fields=fields, **getattr(config, "table_options", {}))

        # Add actions column for detail link
        if "actions" in fields:
            table_class.actions = tables.TemplateColumn(
                template_name="fairdm/tables/actions_column.html", verbose_name="Actions", orderable=False
            )

        return table_class

    def generate_resource(self, model_class, config):
        """
        Auto-generate an import/export ModelResource based on configuration.

        Args:
            model_class: The Django model class
            config: Configuration instance

        Returns:
            ModelResource subclass
        """
        # Use existing modelresource_factory
        resource_options = getattr(config, "resource_options", {})
        return modelresource_factory(model_class, **resource_options)

    def generate_serializer(self, model_class, config):
        """
        Auto-generate a DRF ModelSerializer based on configuration.

        Args:
            model_class: The Django model class
            config: Configuration instance

        Returns:
            ModelSerializer subclass (if DRF is available)
        """
        try:
            from rest_framework import serializers

            # Determine fields to serialize
            fields = getattr(config, "list_fields", None)
            if fields is None:
                fields = "__all__"

            # Create Meta class
            meta_attrs = {"model": model_class, "fields": fields, **getattr(config, "serializer_options", {})}
            meta_class = type("Meta", (), meta_attrs)

            # Create serializer class
            serializer_class = type(
                f"{model_class.__name__}Serializer", (serializers.ModelSerializer,), {"Meta": meta_class}
            )

            return serializer_class

        except ImportError:
            # DRF not available
            return None

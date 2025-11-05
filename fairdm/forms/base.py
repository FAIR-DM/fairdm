from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Div, Layout
from django import forms
from django.contrib.admin.utils import flatten, flatten_fieldsets
from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ModelFormMetaclass
from partial_date import fields as partial_date_fields

from fairdm.utils import fields_to_crispy_layout, fieldsets_to_crispy_layout

from .fields import PartialDateField


class BaseMetaClass:
    """
    Base metaclass for FairDM forms and model forms that adds custom behavior.
    """

    def __new__(cls, name, bases, attrs):
        # Let Django do its normal processing first

        meta = attrs.get("Meta", None)

        meta_fields = getattr(meta, "fields", [])

        # Initialize the config dict with inherited values
        custom_conf = {
            "formfield_overrides": {},
            "field_overrides": {},
            "explicit_fields": None,
            "fieldsets": None,
            "form_attrs": {},
            "helper_attrs": {},
            "help_text": None,
        }

        # Merge inherited _custom_conf from base classes (in MRO order)
        for base in reversed(bases):
            base_conf = getattr(base, "_custom_conf", {})
            for key, value in base_conf.items():
                if isinstance(value, dict):
                    custom_conf[key].update(value)
                elif value is not None:
                    custom_conf[key] = value

        # Now apply any values defined in the current class's Meta
        if meta := attrs.get("Meta", None):
            for key in custom_conf:
                val = cls._get_conf_and_remove(meta, key)
                if isinstance(custom_conf[key], dict) and isinstance(val, dict):
                    custom_conf[key].update(val)
                elif val:
                    custom_conf[key] = val

            custom_conf["fields"] = meta_fields  # preserve fields in case they are nested

            if custom_conf["fieldsets"]:
                meta.fields = flatten_fieldsets(custom_conf["fieldsets"])
            else:
                # if meta.fields is declared as a nested list, flatten it
                meta.fields = flatten(meta_fields)

        new_class = super().__new__(cls, name, bases, attrs)

        # ✅ Attach to the form class
        new_class._custom_conf = custom_conf

        return new_class

    def _get_conf_and_remove(meta, attr):
        """
        Helper method to get a configuration value and remove it from the attributes.
        """
        if hasattr(meta, attr):
            value = getattr(meta, attr)
            delattr(meta, attr)
            return value


class FairDMModelFormMetaclass(BaseMetaClass, ModelFormMetaclass):
    """
    Metaclass for BaseModelForm that allows for custom field declarations.
    This can be extended to add common fields or behaviors to all model forms.
    """

    pass


class FairDMFormMetaclass(BaseMetaClass, DeclarativeFieldsMetaclass):
    """
    Metaclass for BaseForm that allows for custom field declarations.
    This can be extended to add common fields or behaviors to all forms.
    """

    pass


class FairDMFormMixin:
    """
    Mixin class that can be
    """

    _custom_conf = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._custom_conf.get("explicit_fields") is True:
            allowed = set(self.Meta.fields or [])
            for name in list(self.fields.keys()):
                if name not in allowed:
                    self.fields.pop(name)

        if formfield_overrides := self._custom_conf["formfield_overrides"]:
            for name in self.fields:
                if name in self.declared_fields:
                    continue  # respect manual declarations

                model_field = self._meta.model._meta.get_field(name)

                for model_field_type, form_class in formfield_overrides.items():
                    if isinstance(model_field, model_field_type):
                        # Get default kwargs from formfield() and inject form_class
                        self.fields[name] = model_field.formfield(form_class=form_class)
                        break

        # Apply field overrides if specified
        for name, kwargs in self._custom_conf.get("field_overrides").items():
            for key, value in kwargs.items():
                setattr(self.fields[name], key, value)

        self.helper = self._helper()

    def _helper(self):
        """
        Returns the FormHelper instance for this form.
        This can be used to customize the form's layout and attributes.
        """
        helper = FormHelper()
        for key, value in self._custom_conf.get("helper_attrs", {}).items():
            setattr(helper, key, value)

        if form_attrs := self._custom_conf.get("form_attrs"):
            helper.attrs = form_attrs
        if not helper.form_id:
            helper.form_id = self.get_form_id()
        helper.layout = self.get_layout()
        help_text = self.get_help_text()
        if help_text is not None:
            helper.layout.insert(0, help_text)

        return helper

    def get_layout(self):
        """
        Returns the layout for the form.
        This can be overridden in subclasses to provide custom layouts.
        """
        if fieldsets := self._custom_conf.get("fieldsets"):
            return fieldsets_to_crispy_layout(fieldsets)
        elif fields := self._custom_conf.get("fields"):
            return fields_to_crispy_layout(fields)

        if hasattr(self, "_meta") and hasattr(self._meta, "fields"):  # noqa: SIM102
            # If _meta.fields is defined, use it
            if isinstance(self._meta.fields, list | tuple):
                return fields_to_crispy_layout(self._meta.fields)

        return Layout()

    def get_help_text(self):
        """
        Returns the help text for a specific field.
        This can be overridden in subclasses to provide custom help texts.
        """
        if help_text := self._custom_conf.get("help_text"):
            # Ensure help text is HTML-safe
            # return HTML(help_text)
            return Div(HTML(help_text), css_class="mb-3")
        return None

    def get_form_id(self):
        """
        Returns the form ID.
        This can be overridden in subclasses to provide custom form IDs.
        """
        return f"{self.__class__.__name__.lower()}"


class Form(FairDMFormMixin, forms.Form, metaclass=FairDMFormMetaclass):
    """
    Base form class that can be extended for custom forms.
    This class can be used to define common behavior or attributes for all forms.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any common initialization logic here

    class Meta:
        formfield_overrides = {
            partial_date_fields.PartialDateField: PartialDateField,
        }
        explicit_fields = True
        form_attrs = {
            "x-data": {},
        }


class ModelForm(FairDMFormMixin, forms.ModelForm, metaclass=FairDMModelFormMetaclass):
    """
    Base model form class that can be extended for custom model forms.
    This class can be used to define common behavior or attributes for all model forms.
    """

    class Meta:
        formfield_overrides = {
            partial_date_fields.PartialDateField: PartialDateField,
        }
        explicit_fields = True
        form_attrs = {
            "x-data": {},
        }

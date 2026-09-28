"""Base form classes configured through options on their ``Meta``."""

from typing import Any

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
    """Metaclass mixin that collects FairDM options from a form's ``Meta``.

    The options are merged with those of the base classes and stored on the form
    class as ``_custom_conf``. They are removed from ``Meta`` so Django never sees
    them. ``Meta.fields`` is flattened, or taken from ``Meta.fieldsets`` when set.
    """

    def __new__(cls, name, bases, attrs):
        """Build the form class with its merged FairDM options attached."""
        meta = attrs.get("Meta", None)

        meta_fields = getattr(meta, "fields", [])

        custom_conf = {
            "formfield_overrides": {},
            "field_overrides": {},
            "explicit_fields": None,
            "fieldsets": None,
            "form_attrs": {},
            "helper_attrs": {},
            "help_text": None,
        }

        for base in reversed(bases):
            base_conf = getattr(base, "_custom_conf", {})
            for key, value in base_conf.items():
                if isinstance(value, dict):
                    custom_conf[key].update(value)
                elif value is not None:
                    custom_conf[key] = value

        if meta := attrs.get("Meta", None):
            for key in custom_conf:
                val = cls._get_conf_and_remove(meta, key)
                if isinstance(custom_conf[key], dict) and isinstance(val, dict):
                    custom_conf[key].update(val)
                elif val:
                    custom_conf[key] = val

            # The nested form is kept for get_layout(); Meta.fields is flattened below.
            custom_conf["fields"] = meta_fields

            if custom_conf["fieldsets"]:
                meta.fields = flatten_fieldsets(custom_conf["fieldsets"])
            else:
                meta.fields = flatten(meta_fields)

        new_class = super().__new__(cls, name, bases, attrs)

        new_class._custom_conf = custom_conf

        return new_class

    def _get_conf_and_remove(meta, attr):
        """Pop an option off ``Meta``, returning ``None`` when it is not defined."""
        if hasattr(meta, attr):
            value = getattr(meta, attr)
            delattr(meta, attr)
            return value


class FairDMModelFormMetaclass(BaseMetaClass, ModelFormMetaclass):
    """Metaclass for :class:`ModelForm` that reads FairDM ``Meta`` options."""

    pass


class FairDMFormMetaclass(BaseMetaClass, DeclarativeFieldsMetaclass):
    """Metaclass for :class:`Form` that reads FairDM ``Meta`` options."""

    pass


class FairDMFormMixin:
    """Mixin that applies the FairDM ``Meta`` options to a form.

    The options are read by :class:`BaseMetaClass` into ``_custom_conf``:

    - ``formfield_overrides``: maps a model field type to the form field class
      used for it. Fields declared on the form are left alone.
    - ``field_overrides``: maps a field name to a dict of attributes set on that
      field.
    - ``explicit_fields``: when ``True``, drop every field not in ``Meta.fields``.
    - ``fieldsets``: grouped fields, used for the crispy layout and ``Meta.fields``.
    - ``form_attrs``: HTML attributes for the ``<form>`` element.
    - ``helper_attrs``: attributes set on the crispy ``FormHelper``.
    - ``help_text``: HTML shown above the form fields.
    """

    _custom_conf: dict[str, Any] = {}

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
                    continue

                model_field = self._meta.model._meta.get_field(name)

                for model_field_type, form_class in formfield_overrides.items():
                    if isinstance(model_field, model_field_type):
                        self.fields[name] = model_field.formfield(form_class=form_class)
                        break

        for name, kwargs in self._custom_conf.get("field_overrides").items():
            for key, value in kwargs.items():
                setattr(self.fields[name], key, value)

        self.helper = self._helper()

    def _helper(self):
        """Build the crispy ``FormHelper`` for this form.

        Returns:
            A helper carrying the configured attributes, form id and layout.
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
        """Build the crispy layout for this form.

        Uses ``fieldsets`` when configured, then the configured ``fields``, then
        ``Meta.fields``. Override it to provide a custom layout.

        Returns:
            The layout, empty when the form declares no fields.
        """
        if fieldsets := self._custom_conf.get("fieldsets"):
            return fieldsets_to_crispy_layout(fieldsets)
        elif fields := self._custom_conf.get("fields"):
            return fields_to_crispy_layout(fields)

        if hasattr(self, "_meta") and hasattr(self._meta, "fields"):  # noqa: SIM102
            if isinstance(self._meta.fields, list | tuple):
                return fields_to_crispy_layout(self._meta.fields)

        return Layout()

    def get_help_text(self):
        """Build the help text block shown above the form fields.

        Override it to provide custom help text.

        Returns:
            A crispy element wrapping the configured ``help_text``, or ``None``
            when none is configured.
        """
        if help_text := self._custom_conf.get("help_text"):
            return Div(HTML(help_text), css_class="mb-3")
        return None

    def get_form_id(self):
        """Return the form's HTML id, the lowercased class name by default.

        Override it to provide a custom id.

        Returns:
            The id used for the crispy helper's ``form_id``.
        """
        return f"{self.__class__.__name__.lower()}"


class Form(FairDMFormMixin, forms.Form, metaclass=FairDMFormMetaclass):
    """Base form for FairDM, configured through options on its ``Meta``."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        formfield_overrides = {
            partial_date_fields.PartialDateField: PartialDateField,
        }
        explicit_fields = True
        form_attrs: dict[str, Any] = {
            "x-data": {},
        }


class ModelForm(FairDMFormMixin, forms.ModelForm, metaclass=FairDMModelFormMetaclass):
    """Base model form for FairDM, configured through options on its ``Meta``."""

    class Meta:
        formfield_overrides = {
            partial_date_fields.PartialDateField: PartialDateField,
        }
        explicit_fields = True
        form_attrs: dict[str, Any] = {
            "x-data": {},
        }

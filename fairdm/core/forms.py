"""Base form, Selectize widget and creators field shared by the core forms."""

from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe


class ManagerOnlyFieldsMixin:
    """Leave the fields that decide who gets into a record out of its form, for anyone who cannot manage it.

    Visibility and the record a record sits under (a project's owner, a dataset's project, a
    sample's or measurement's dataset) change who holds rights over it, so only someone who can
    manage it is offered them. A form for a new record leaves nothing out.

    Attributes:
        manager_only_fields: The names of the fields to leave out.
    """

    manager_only_fields: tuple[str, ...] = ()

    def withhold_manager_only_fields(self, request):
        """Remove the manager-only fields unless the request's user can manage the record.

        Args:
            request: The current request, or None, which counts as someone who cannot manage it.
        """
        from fairdm.contrib.contributors.access import RecordAccess

        user = getattr(request, "user", None)
        if self.instance.pk is None or (
            user is not None and RecordAccess(self.instance).can_manage(user)
        ):
            return
        for name in self.manager_only_fields:
            self.fields.pop(name, None)


class BaseForm(ModelForm):
    """Model form that accepts the request and drops declared fields missing from ``Meta.fields``.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``. ``request`` is removed first and
            sets ``self.request`` and ``self.user``.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = None
        if self.request:
            self.user = self.request.user

        super().__init__(*args, **kwargs)
        allowed = set(self._meta.fields)
        for name in list(self.fields):
            if name not in allowed:
                del self.fields[name]


class SelectizeWidget(forms.SelectMultiple):
    """Multiple select widget that renders as a Selectize control with remove and drag-drop plugins.

    Args:
        *args: Positional arguments passed to ``SelectMultiple``.
        **kwargs: Keyword arguments passed to ``SelectMultiple``. ``selectize_options`` is
            removed first and stored on the widget.
    """

    def __init__(self, *args, **kwargs):
        self.selectize_options = kwargs.pop("selectize_options", {})
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        """Append the script that initialises Selectize on the rendered select."""
        output = super().render(name, value, attrs, renderer)

        selectize_script = f"""
        <script type="text/javascript">
            $(document).ready(function() {{
                $('#{attrs["id"]}').selectize({{
                    {self._generate_selectize_options()}
                }});
            }});
        </script>
        """

        return mark_safe(output + selectize_script)

    def _generate_selectize_options(self):
        options = ["'plugins': ['remove_button', 'drag_drop']"]
        return ", ".join(options)


class CreatorsFormField(forms.ModelMultipleChoiceField):
    """Ordered multiple choice field that grants and removes the Creator role as it is edited."""

    widget = SelectizeWidget

    def clean(self, value):
        """Add the Creator role to new selections, remove it from dropped ones and order the rest."""
        value = super().clean(value)
        removed = [c for c in self.initial if c not in value]

        for c in removed:
            c.roles.remove("Creator")
            c.save()

        for i, c in enumerate(value):
            if c not in self.initial:
                c.add_roles(["Creator"])
            c.to(i)
            c.save()

        return value

    def _check_values(self, value):
        """Return the objects matching each value on ``to_field_name`` (default ``uuid``), in order."""
        key = self.to_field_name or "uuid"
        qs = super()._check_values(value)
        result = []
        for uuid in value:
            result.append(qs.get(**{key: uuid}))
        return result

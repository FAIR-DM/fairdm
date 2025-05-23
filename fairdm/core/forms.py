from django import forms
from django.forms import ModelForm
from django.utils.safestring import mark_safe


class BaseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = None
        if self.request:
            self.user = self.request.user

        super().__init__(*args, **kwargs)
        # Remove explicitly declared fields if not in Meta.fields
        allowed = set(self._meta.fields)
        for name in list(self.fields):
            if name not in allowed:
                del self.fields[name]


class SelectizeWidget(forms.SelectMultiple):
    def __init__(self, *args, **kwargs):
        # You can pass any additional arguments here like the 'drag_drop' option, etc.
        self.selectize_options = kwargs.pop("selectize_options", {})
        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        # First, render the standard SelectMultiple widget
        output = super().render(name, value, attrs, renderer)

        # Add the Selectize initialization script to the output
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
        # Convert the selectize_options dictionary into JavaScript-friendly format
        options = ["'plugins': ['remove_button', 'drag_drop']"]
        # for key, value in self.selectize_options.items():
        #     if isinstance(value, str):
        #         options.append(f"'{key}': '{value}'")
        #     else:
        #         options.append(f"'{key}': {value}")
        return ", ".join(options)


class CreatorsFormField(forms.ModelMultipleChoiceField):
    widget = SelectizeWidget

    def clean(self, value):
        value = super().clean(value)
        removed = [c for c in self.initial if c not in value]

        for c in removed:
            c.roles.remove("Creator")
            c.save()

        for i, c in enumerate(value):
            if c not in self.initial:
                c.add_roles(["Creator"])
            # set order using django-ordered-model api
            c.to(i)
            c.save()

        return value

    def _check_values(self, value):
        """
        Given a list of possible PK values, return a QuerySet of the
        corresponding objects. Raise a ValidationError if a given value is
        invalid (not a valid PK, not in the queryset, etc.)
        """
        key = self.to_field_name or "uuid"
        qs = super()._check_values(value)
        result = []
        for uuid in value:
            result.append(qs.get(**{key: uuid}))
        return result

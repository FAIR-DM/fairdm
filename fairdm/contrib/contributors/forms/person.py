"""Forms for signup and merging people."""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.autocomplete.fields import PersonChoiceField

User = get_user_model()


class SignupExtraForm(forms.ModelForm):
    """Collect first and last names during allauth signup.

    Attributes:
        first_name: The given name.
        last_name: The family name.
    """

    first_name = forms.CharField(label=_("First name"), help_text=_("Your given name."))
    last_name = forms.CharField(label=_("Last name"), help_text=_("Your family name."))

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name")

    def signup(self, request, user):
        """Save the user's first and last name.

        Args:
            request: The signup request.
            user: The new user.
        """
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()


class MergePersonForm(forms.Form):
    """Choose the person that survives when another person is merged into them.

    Args:
        *args: Passed to ``Form``.
        exclude_pk: Primary key of the person being merged, who is left out of the choices.
        **kwargs: Passed to ``Form``.

    Attributes:
        merge_into: The person that survives.
    """

    merge_into = PersonChoiceField(
        label=_("Merge into"),
        help_text=_(
            "Select the Person record that should survive the merge. The current record will be deleted."
        ),
    )

    def __init__(self, *args, exclude_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        from fairdm.contrib.contributors.models import Person

        self.exclude_pk = exclude_pk

        qs = Person.objects.all()
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        self.fields["merge_into"].queryset = qs

    def choose(self, value):
        """Start the form on a person, when submitting that person would be accepted.

        Args:
            value: The primary key of the person, from outside the form. Anything the
                field would refuse, or the person being merged, chooses nothing.
        """
        try:
            keep = self.fields["merge_into"].clean(value)
        except forms.ValidationError:
            return
        if keep.pk != self.exclude_pk:
            self.initial["merge_into"] = keep.pk

    def clean_merge_into(self):
        """Refuse the person being merged as the person that survives."""
        keep = self.cleaned_data["merge_into"]
        if self.exclude_pk is not None and keep.pk == self.exclude_pk:
            raise forms.ValidationError(
                _("A person cannot be merged into themselves."), code="same_person"
            )
        return keep

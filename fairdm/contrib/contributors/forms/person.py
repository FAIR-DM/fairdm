"""Forms for signup, profile editing and merging people."""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from markdownx.fields import MarkdownxFormField

from fairdm.forms import ModelForm

User = get_user_model()


class SignupExtraForm(forms.ModelForm):
    """Collect first and last names during allauth signup.

    Attributes:
        first_name: The given name.
        last_name: The family name.
    """

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name")
        labels = {
            "first_name": _("First name"),
            "last_name": _("Last name"),
        }
        help_texts = {
            "first_name": _("Your given name."),
            "last_name": _("Your family name."),
        }

    def signup(self, request, user):
        """Save the user's first and last name.

        Args:
            request: The signup request.
            user: The new user.
        """
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()


class UserProfileForm(ModelForm):
    """Edit a person's image, names and biography.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``.

    Attributes:
        image: The profile image.
        profile: The Markdown biography.
    """

    image = forms.ImageField(
        required=False,
        label=False,
    )
    profile = MarkdownxFormField(required=False)

    class Meta:
        model = User
        fields = ["image", "name", "first_name", "last_name", "profile"]
        labels = {
            "name": _("Publishing name"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "profile": _("Biography"),
        }
        help_texts = {
            "name": _(
                "Your full name as it appears in formal research documents and citations."
            ),
            "first_name": _("Your given name."),
            "last_name": _("Your family name."),
            "profile": _(
                "A brief biography or professional summary. This will be publicly visible."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_id = "person-profile-form"


class MergePersonForm(forms.Form):
    """Choose the person that survives when another person is merged into them.

    Args:
        *args: Passed to ``Form``.
        exclude_pk: Primary key of the person being merged, who is left out of the choices.
        **kwargs: Passed to ``Form``.

    Attributes:
        merge_into: The person that survives.
    """

    merge_into = forms.ModelChoiceField(
        queryset=None,
        label=_("Merge into"),
        help_text=_(
            "Select the Person record that should survive the merge. The current record will be deleted."
        ),
    )

    def __init__(self, *args, exclude_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        from fairdm.contrib.contributors.models import Person

        qs = Person.objects.all()
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        self.fields["merge_into"].queryset = qs

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from martor.fields import MartorFormField

from fairdm.forms import ModelForm

User = get_user_model()


class SignupExtraForm(forms.ModelForm):
    """Form used by Django Allauth for collecting extra information during signup."""

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
        """Save the user's first and last name."""
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()


class UserProfileForm(ModelForm):
    """Form for editing user profile information.

    Includes image cropping, name fields, and biographical profile.
    Used in account management and contributor profile editing.
    """

    image = forms.ImageField(
        required=False,
        label=False,
    )
    profile = MartorFormField(required=False)

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
            "name": _("Your full name as it appears in formal research documents and citations."),
            "first_name": _("Your given name."),
            "last_name": _("Your family name."),
            "profile": _("A brief biography or professional summary. This will be publicly visible."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.form_id = "person-profile-form"

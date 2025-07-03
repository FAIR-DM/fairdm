from client_side_image_cropping import ClientsideCroppingWidget
from crispy_forms.layout import Column, Layout, Row
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from fairdm.forms import ModelForm

User = get_user_model()


class SignupExtraForm(forms.ModelForm):
    """Form used by Django Allauth for collecting extra information during signup."""

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)

    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name")

    def signup(self, request, user):
        """Save the user's first and last name."""
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()


class BaseUserForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]


class UserProfileForm(ModelForm):
    image = forms.ImageField(
        widget=ClientsideCroppingWidget(
            width=300,
            height=300,
            preview_width="100%",
            preview_height="auto",
            file_name="profile.jpg",
        ),
        required=False,
        label=False,
    )
    # lang = forms.ChoiceField(
    #     choices=iso_639_1_languages,
    #     initial="en",
    #     # widget=Selectize(),
    #     help_text=_("Preferred display language for this site (where possible)."),
    #     label=_("Language"),
    # )

    name = forms.CharField(
        label=_("Publishing name"),
        help_text=_("Your full name as you wish it to appear on formal research documents."),
    )

    # hopefully this can be removed when this issue is solved: https://github.com/koendewit/django-client-side-image-cropping/issues/15
    class Media:
        css = {
            "all": (
                "client_side_image_cropping/croppie.css",
                # "client_side_image_cropping/cropping_widget.css",
            ),
        }
        js = (
            "client_side_image_cropping/croppie.min.js",
            "client_side_image_cropping/cropping_widget.js",
        )

    class Meta:
        model = User
        fields = "__all__"
        fields = ["image", "name", "first_name", "last_name", "profile"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Row(
                Column(
                    "image",
                    css_class="col-md-4",
                ),
                Column(
                    "name",
                    Row(Column("first_name"), Column("last_name")),
                    "profile",
                    # "lang",
                    # "email",
                    # css_class="col-md-8",
                ),
                css_class="gx-4 flex-md-row-reverse",
            ),
        )
        self.helper.form_id = "user-profile-form"

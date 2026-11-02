"""allauth forms customised for FairDM."""

from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_forms
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(account_forms.LoginForm):
    """allauth login form with a crispy helper.

    Args:
        *args: Passed to the allauth form.
        **kwargs: Passed to the allauth form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_login"
        self.helper.form_id = "login-form"


class SignupForm(account_forms.SignupForm):
    """allauth signup form with a crispy helper.

    Args:
        *args: Passed to the allauth form.
        **kwargs: Passed to the allauth form.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_signup"
        self.helper.form_id = "signup-form"


class SocialSignupForm(social_forms.SignupForm):
    """allauth social signup form with a display name and a crispy helper.

    Args:
        *args: Passed to the allauth form.
        **kwargs: Passed to the allauth form.

    Attributes:
        name: The display name.
    """

    name = forms.CharField(
        label=_("Display name"),
        max_length=255,
        required=False,
        help_text=_("How you would like to be addressed within the portal."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "socialaccount_signup"
        self.helper.form_id = "social-signup-form"

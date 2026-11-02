"""allauth forms customised for FairDM."""

from allauth.account import forms as account_forms
from allauth.account.adapter import get_adapter
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


class UserTokenForm(account_forms.UserTokenForm):
    """allauth reset-link check that also applies ``can_reset_password``.

    The account adapter stops new mail. This stops a link sent before that, which
    stays valid for as long as the person's password is unchanged.
    """

    def clean(self):
        """Refuse the link as invalid when the person may not reset a password."""
        cleaned_data = super().clean()
        if not self.reset_user.can_reset_password():
            raise get_adapter().validation_error("invalid_password_reset")
        return cleaned_data


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

from allauth.account import forms as account_forms
from allauth.account.utils import filter_users_by_email
from allauth.socialaccount import forms as social_forms
from crispy_forms.helper import FormHelper
from django import forms
from django.utils.translation import gettext as _


class LoginForm(account_forms.LoginForm):
    """Custom login form for FairDM.

    Extends the default allauth LoginForm with custom form metadata.
    Additional validation or fields can be added as needed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_login"
        self.helper.form_id = "login-form"


class SignupForm(account_forms.SignupForm):
    """Custom signup form for FairDM.

    Extends the default allauth SignupForm with custom form metadata.
    Additional validation or fields can be added as needed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_signup"
        self.helper.form_id = "signup-form"


class SocialSignupForm(social_forms.SignupForm):
    """Social authentication signup form (ORCID, etc.).

    Includes special logic to allow ORCID signups to claim inactive accounts.
    Inactive accounts are created when contributors are added manually without
    user accounts. When they later sign up via ORCID, we link their ORCID to
    the existing contributor record.
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

    def try_save(self, request):
        """Allow ORCID signups to claim inactive contributor accounts.

        When a contributor is added manually to the system, they get an inactive
        account. If they later sign up via ORCID, this method links their ORCID
        to that existing contributor record instead of creating a duplicate.

        This bypasses the default email conflict check for ORCID signups when
        an inactive account with the same email exists.
        """
        # NOTE: this exists only to bypass the default try_save method IF the sociallogin is for ORCID and the account
        # is not marked as inactive (default for user-added contributors).
        if self.account_already_exists and self.sociallogin.account.provider == "orcid":
            existing = filter_users_by_email(self.cleaned_data["email"])
            if existing and not existing[0].is_active:
                self.instance = existing[0]
                user = self.save(request)
                return user, None
        return super().try_save(request)

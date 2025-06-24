from allauth.account import forms as account_forms
from allauth.socialaccount import forms as social_forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Field, Layout, Row, Submit
from django import forms


class LoginForm(account_forms.LoginForm):
    """
    Custom login form for FairDM that extends the default allauth LoginForm.
    This can be used to add custom validation or fields in the future.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_login"
        self.helper.form_id = "login-form"
        self.helper.layout = Layout(
            "login",
            "password",
            "remember",
            Submit("submit", "Login", css_class="btn btn-primary w-100"),
        )


class SignupForm(account_forms.SignupForm):
    """
    Custom login form for FairDM that extends the default allauth LoginForm.
    This can be used to add custom validation or fields in the future.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "account_signup"
        self.helper.form_id = "signup-form"
        self.helper.layout = Layout(
            "email",
            Row(
                Column(
                    "first_name",
                    css_class="col-md-6",
                ),
                Column(
                    "last_name",
                    css_class="col-md-6",
                ),
            ),
            Field("password1", css_class="form-control"),
            Field("password2", css_class="form-control"),
            Submit("submit", "Create Account", css_class="btn btn-primary w-100"),
        )


class SocialSignupForm(social_forms.SignupForm):
    name = forms.CharField(
        label="Preferred Name",
        max_length=255,
        required=False,
        help_text="This is how other will see you within the portal.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_action = "socialaccount_signup"
        self.helper.form_id = "social-signup-form"
        self.helper.layout = Layout(
            Field("email"),
            "name",
            Row(
                Column(
                    "first_name",
                    css_class="col-md-6",
                ),
                Column(
                    "last_name",
                    css_class="col-md-6",
                ),
            ),
            Submit("submit", "Confirm Details", css_class="btn btn-primary w-100"),
        )

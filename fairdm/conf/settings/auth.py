"""Authentication and Authorization Configuration

Production-ready authentication with django-allauth, password validation, and object-level permissions.

Includes configuration for:
- Password hashing (Argon2)
- Password validators
- Authentication backends (ModelBackend, allauth, guardian)
- django-allauth settings (email verification, social auth)
- django-invitations

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

# Access environment variables via shared env instance
env = globals()["env"]

# ========== Django Core Authentication ==========

# User model
AUTH_USER_MODEL = "contributors.Person"

# Login/logout URLs
LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "account_login"


# https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model

# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    "guardian.backends.ObjectPermissionBackend",
]


# ========== Django Allauth Account ==========

ACCOUNT_ADAPTER = "fairdm.contrib.contributors.adapters.AccountAdapter"
ACCOUNT_ALLOW_REGISTRATION = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_MAX_EMAIL_ADDRESSES = 4
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_SIGNUP_FORM_CLASS = "fairdm.contrib.contributors.forms.person.SignupExtraForm"
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# ========== Django Allauth Social Account ==========

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    "orcid": {
        # Use production ORCID by default, sandbox for development (override in local.py)
        "BASE_DOMAIN": env("ORCID_BASE_DOMAIN", default="orcid.org"),
        "MEMBER_API": False,
    }
}

# https://django-allauth.readthedocs.io/en/latest/configuration.html
SOCIALACCOUNT_ADAPTER = "fairdm.contrib.contributors.adapters.SocialAccountAdapter"


# ========== Django Invitations ==========
# https://django-invitations.readthedocs.io/en/latest/configuration.html

INVITATIONS_INVITATION_ONLY = False
INVITATIONS_ADAPTER = ACCOUNT_ADAPTER

# django-organizations backends
INVITATION_BACKEND = "organizations.backends.defaults.InvitationBackend"
REGISTRATION_BACKEND = "organizations.backends.defaults.RegistrationBackend"

# https://django-allauth.readthedocs.io/en/latest/forms.html
ACCOUNT_FORMS = {
    "login": "fairdm.contrib.contributors.forms.account.LoginForm",
    "signup": "fairdm.contrib.contributors.forms.account.SignupForm",
    # "add_email": "fairdm.contrib.users.forms.AddEmailForm",
    # "change_password": "fairdm.contrib.users.forms.ChangePasswordForm",
    # "set_password": "fairdm.contrib.users.forms.SetPasswordForm",
    # "reset_password": "fairdm.contrib.users.forms.ResetPasswordForm",
    # "reset_password_from_key": "fairdm.contrib.users.forms.ResetPasswordKeyForm",
    # "disconnect": "allauth.socialaccount.forms.DisconnectForm",
}

SOCIALACCOUNT_FORMS = {
    # "disconnect": "allauth.socialaccount.forms.DisconnectForm",
    "signup": "fairdm.contrib.contributors.forms.account.SocialSignupForm",
}

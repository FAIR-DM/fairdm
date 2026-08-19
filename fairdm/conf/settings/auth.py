"""Authentication and Authorization Configuration

Owns: password hashing (Argon2 first), password validators, authentication
backends (ModelBackend, allauth, guardian, FairDM's own object-level
backends), django-allauth account/social settings, and django-invitations —
none of it environment-dependent (FR-002, FR-003). Leaves to a portal:
``SOCIALACCOUNT_PROVIDERS`` beyond ORCID, and its own custom account/signup
forms via ``ACCOUNT_FORMS``/``SOCIALACCOUNT_FORMS``.

This is the production baseline. Environment-specific overrides in development.py (FairDM) or a same-named module beside the portal's settings module.
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
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model

# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    # Replaces raw guardian: normalises a polymorphic instance (Sample, Measurement,
    # Organization/Person) to its base before the object-level check. Registered directly, not
    # reached by delegation through one of the record-specific backends below, so datasets,
    # projects and organisations keep resolving even if one of those backends is ever narrowed to
    # answer only for its own record type (decisions.md D-018).
    "fairdm.core.permissions.PolymorphicObjectPermissionBackend",
    "fairdm.contrib.contributors.permissions.OrganizationPermissionBackend",  # Organization ownership via OWNER affiliation
    "fairdm.core.sample.permissions.SamplePermissionBackend",  # Sample permission inheritance
    "fairdm.core.measurement.permissions.MeasurementPermissionBackend",  # Measurement permission inheritance
]

# guardian.W001 fires when its own backend path is absent from the list above. Every backend in
# that list derives from it, so object permissions are hooked — the check is a literal string
# comparison, not a capability test, and cannot see a subclass. Silenced here rather than by
# re-adding the raw backend, which would let a check reach guardian without the normalisation and
# raise on a portal-defined specimen type (decisions.md D-018).
SILENCED_SYSTEM_CHECKS = ["guardian.W001"]


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
        # Use production ORCID by default, sandbox for development (override in development.py)
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

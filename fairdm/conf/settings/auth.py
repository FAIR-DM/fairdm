"""Authentication and authorization settings.

Owns password hashing (Argon2 first), password validators, authentication
backends (ModelBackend, allauth, guardian, FairDM's own object-level
backends), django-allauth account and social settings, and the FairDM signup
gate. A portal supplies ``SOCIALACCOUNT_PROVIDERS`` beyond ORCID, its own
account and signup forms via ``ACCOUNT_FORMS``/``SOCIALACCOUNT_FORMS``, and its own profile
editing forms via ``FAIRDM_PROFILE_FORMS``.
"""

env = globals()["env"]

# The person record is the account, so the framework has no separate account model.
AUTH_USER_MODEL = "contributors.Person"

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "account_login"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
    # Replaces raw guardian: normalises a polymorphic instance to its base before the
    # object-level check. Registered directly so it does not depend on the backends below.
    "fairdm.core.permissions.PolymorphicObjectPermissionBackend",
    "fairdm.contrib.contributors.permissions.OrganizationPermissionBackend",
    "fairdm.contrib.contributors.permissions.RecordLevelBackend",
    "fairdm.core.sample.permissions.SamplePermissionBackend",
    "fairdm.core.measurement.permissions.MeasurementPermissionBackend",
    # Registered last so an explicit stored grant is consulted first.
    "fairdm.permissions.PortalRolePermissionBackend",
]

# guardian.W001 compares backend paths as strings and cannot see the subclasses listed above.
# Re-adding the raw backend would bypass the polymorphic normalisation.
SILENCED_SYSTEM_CHECKS = ["guardian.W001"]


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

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_PROVIDERS = {
    "orcid": {
        # Production ORCID by default; the sandbox is for development.
        "BASE_DOMAIN": env("ORCID_BASE_DOMAIN", default="orcid.org"),
        "MEMBER_API": False,
    }
}

SOCIALACCOUNT_ADAPTER = "fairdm.contrib.contributors.adapters.SocialAccountAdapter"

# When True, self-service signup is closed and administrators create accounts (#266).
FAIRDM_INVITATION_ONLY_SIGNUP = False

ACCOUNT_FORMS = {
    "login": "fairdm.contrib.contributors.forms.account.LoginForm",
    "signup": "fairdm.contrib.contributors.forms.account.SignupForm",
}

SOCIALACCOUNT_FORMS = {
    "signup": "fairdm.contrib.contributors.forms.account.SocialSignupForm",
}

# The form each kind of profile is edited with. A portal names its own subclass to change the
# fields; a kind left out keeps the shipped form.
FAIRDM_PROFILE_FORMS = {
    "person": "fairdm.contrib.contributors.forms.profile.PersonProfileForm",
    "organization": "fairdm.contrib.contributors.forms.profile.OrganizationProfileForm",
}

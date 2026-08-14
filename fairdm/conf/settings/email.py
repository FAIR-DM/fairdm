"""Email Configuration

Owns: the SMTP email backend and the from/server addresses, composed from
``EMAIL_*`` and ``DJANGO_SITE_DOMAIN``/``DJANGO_SITE_NAME`` (FR-002, FR-003).
Leaves to a portal: the mail server itself, and ``DJANGO_DEFAULT_FROM_EMAIL``/
``DJANGO_SERVER_EMAIL`` when the derived address isn't what it wants.

This is the production baseline. Environment-specific overrides in development.py (FairDM) or a same-named module beside the portal's settings module.
"""

# Access environment variables via shared env instance
env = globals()["env"]


site_name = env("DJANGO_SITE_NAME", default=None)

# https://docs.djangoproject.com/en/dev/ref/settings/#default-from-email
if env("DJANGO_DEFAULT_FROM_EMAIL", default=None):
    from_email = env("DJANGO_DEFAULT_FROM_EMAIL")
else:
    from_email = f"noreply@{env('DJANGO_SITE_DOMAIN')}"

DEFAULT_FROM_EMAIL = f"{site_name} <{from_email}>"

# https://docs.djangoproject.com/en/dev/ref/settings/#server-email
if env("DJANGO_SERVER_EMAIL", default=None):
    server_email = env("DJANGO_SERVER_EMAIL")
else:
    # This is the email address that error messages come from.
    # It should be a valid email address on your server.
    # If you don't set this, Django will use DEFAULT_FROM_EMAIL.
    server_email = f"server@{env('DJANGO_SITE_DOMAIN')}"

SERVER_EMAIL = f"{site_name} Server <{server_email}>"

# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = env("EMAIL_HOST")

# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = env("EMAIL_PORT")

# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env("EMAIL_BACKEND")

# https://docs.djangoproject.com/en/dev/ref/settings/#email-timeout
EMAIL_TIMEOUT = 5
""""""

# https://docs.djangoproject.com/en/dev/ref/settings/#email-subject-prefix
EMAIL_SUBJECT_PREFIX = f"[{env('DJANGO_SITE_NAME') or env('DJANGO_SITE_DOMAIN')}]"
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

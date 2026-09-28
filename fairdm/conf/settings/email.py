"""Email settings: the SMTP backend and the from and server addresses.

Owns the email backend and addresses, composed from ``EMAIL_*`` and
``DJANGO_SITE_DOMAIN``/``DJANGO_SITE_NAME``. A portal supplies the mail server, and
``DJANGO_DEFAULT_FROM_EMAIL``/``DJANGO_SERVER_EMAIL`` when the derived addresses are not
what it wants.
"""

env = globals()["env"]

site_name = env("DJANGO_SITE_NAME", default=None)

if env("DJANGO_DEFAULT_FROM_EMAIL", default=None):
    from_email = env("DJANGO_DEFAULT_FROM_EMAIL")
else:
    from_email = f"noreply@{env('DJANGO_SITE_DOMAIN')}"

DEFAULT_FROM_EMAIL = f"{site_name} <{from_email}>"

if env("DJANGO_SERVER_EMAIL", default=None):
    server_email = env("DJANGO_SERVER_EMAIL")
else:
    server_email = f"server@{env('DJANGO_SITE_DOMAIN')}"

SERVER_EMAIL = f"{site_name} Server <{server_email}>"

EMAIL_HOST = env("EMAIL_HOST")

EMAIL_PORT = env("EMAIL_PORT")

EMAIL_BACKEND = env("EMAIL_BACKEND")

EMAIL_TIMEOUT = 5
""""""

EMAIL_SUBJECT_PREFIX = f"[{env('DJANGO_SITE_NAME') or env('DJANGO_SITE_DOMAIN')}]"
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env("EMAIL_USE_TLS")

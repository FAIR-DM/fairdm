"""Security settings: SECRET_KEY, ALLOWED_HOSTS, DEBUG and the HTTPS, cookie and HSTS headers.

Owns these settings and applies them unconditionally, without branching on the environment.
Relaxing them for local development is ``development.py``'s job. A portal supplies
CSRF_TRUSTED_ORIGINS beyond what ALLOWED_HOSTS implies, and any additional security
middleware.

Neither SECRET_KEY nor the site domain has a working default. An unset value resolves to an
unusable sentinel and the read never raises; ``fairdm.conf.checks`` refuses a production
boot on the result.
"""

env = globals()["env"]

SECRET_KEY = env("DJANGO_SECRET_KEY")

# Truthy entries only: an unset DJANGO_SITE_DOMAIN must yield [] rather than [""], or
# fairdm.E003 can never fire.
ALLOWED_HOSTS = [
    host for host in [env("DJANGO_SITE_DOMAIN"), *env("DJANGO_ALLOWED_HOSTS")] if host
]

CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]

DEBUG = env.bool("DJANGO_DEBUG", default=False)

SESSION_COOKIE_HTTPONLY = True

# Scripts read the CSRF token for AJAX requests.
CSRF_COOKIE_HTTPONLY = False

SECURE_BROWSER_XSS_FILTER = True

X_FRAME_OPTIONS = "DENY"

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True

SESSION_COOKIE_NAME = "__Secure-sessionid"

CSRF_COOKIE_SECURE = True

CSRF_COOKIE_NAME = "__Secure-csrftoken"

SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)

# Raise to 518400 once 60 seconds is proven to work.
SECURE_HSTS_SECONDS = 60

SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
    default=True,
)

SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
    default=True,
)

"""Security Configuration

Production-ready security hardening with HTTPS, secure cookies, and HSTS.

Production/Staging: Requires SECRET_KEY, ALLOWED_HOSTS (fails fast if missing)
Local/Development: Relaxes security requirements (DEBUG=True, no HTTPS)

This is the production baseline. Environment-specific overrides in local.py/staging.py.
"""

# Access environment variables via shared env instance
env = globals()["env"]

# CORE SECURITY SETTINGS (Required for Production)
# These settings MUST be provided via environment variables

# Django secret key - MUST be unique per portal and kept secret
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")

# Allowed hosts - domains that this Django site can serve
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [env("DJANGO_SITE_DOMAIN")] + env("DJANGO_ALLOWED_HOSTS")

# CSRF trusted origins - domains trusted for cross-site requests
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-trusted-origins
CSRF_TRUSTED_ORIGINS = [f"https://{domain}" for domain in ALLOWED_HOSTS]

# Debug mode - MUST be False in production
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool("DJANGO_DEBUG", default=False)

# COOKIE SECURITY
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie

# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False  # CSRF token needs to be accessible by JS for AJAX

# BROWSER SECURITY HEADERS
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS filtering

# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"  # Prevent clickjacking attacks

# HTTPS/SSL SECURITY (Production Only)
# These settings enforce HTTPS and secure cookies in production
if env("DJANGO_SECURE"):
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)

    # https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
    # SECURE_PROXY_SSL_HEADER = env("DJANGO_SECURE_PROXY_SSL_HEADER", default=None)
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
    SESSION_COOKIE_SECURE = True

    # https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-name
    SESSION_COOKIE_NAME = "__Secure-sessionid"

    # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
    CSRF_COOKIE_SECURE = True

    # https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-name
    CSRF_COOKIE_NAME = "__Secure-csrftoken"

    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
    SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=True)

    # https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
    # TODO: set this to 60 seconds first and then to 518400 once you prove the former works
    SECURE_HSTS_SECONDS = 60

    # https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
        "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS",
        default=True,
    )

    # https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
    SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
        "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF",
        default=True,
    )

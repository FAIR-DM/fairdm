"""Contains security settings for the project."""

env = globals()["env"]


# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True

# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = False

# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True

# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"
# X_FRAME_OPTIONS = "SAMEORIGIN"

# ------------------------------------------------------------------------------
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

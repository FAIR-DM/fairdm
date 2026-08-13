import logging

from environ import Env

env = Env(
    # when False, discussion tabs are hidden from the detail views
    FAIRDM_ALLOW_PUBLIC_REGISTRATION=(bool, True),
    # when False, registrations are only allowed by invitation
    # DJANGO
    DJANGO_ADMIN_URL=(str, "admin/"),
    DJANGO_SUPERUSER_EMAIL=(str, "super.user@example.com"),
    # No working default (FR-004, research R6) — an unset admin password
    # resolves to an empty string, not a published or guessable one. The
    # production-critical checks, not this read, are what refuse a boot.
    DJANGO_SUPERUSER_PASSWORD=(str, ""),
    DJANGO_ALLOWED_HOSTS=(list, []),
    DJANGO_CACHE=(bool, True),
    DJANGO_DEBUG=(bool, False),
    DJANGO_READ_DOT_ENV_FILE=(bool, False),
    # No working default (FR-004, research R6) — an unset secret key resolves
    # to an empty string rather than a value published in FairDM's own
    # source. See fairdm.conf.checks.check_secret_key_exists (fairdm.E001).
    DJANGO_SECRET_KEY=(str, ""),
    # No working default (FR-004, research R6) — an unset site domain
    # resolves to an empty string, not "localhost:8000". settings/security.py
    # composes ALLOWED_HOSTS from truthy entries only, so this stays an empty
    # list rather than [""] (research R6, T055).
    DJANGO_SITE_DOMAIN=(str, ""),
    DJANGO_SITE_ID=(int, 1),
    DJANGO_SITE_NAME=(str, "FairDM Demo"),
    DJANGO_TIME_ZONE=(str, "UTC"),
    DJANGO_ROOT_URLCONF=(str, "config.urls"),
    # SECURITY
    DJANGO_SECURE=(bool, True),
    DJANGO_SECURE_HSTS_SECONDS=(int, 60),
    # DATABASE
    DATABASE_URL=(str, ""),
    POSTGRES_DB=(str, ""),
    POSTGRES_PASSWORD=(str, ""),
    POSTGRES_USER=(str, "postgres"),
    POSTGRES_HOST=(str, "postgres"),
    POSTGRES_PORT=(int, 5432),
    # EMAIL
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_BACKEND=(str, "django.core.mail.backends.smtp.EmailBackend"),
    # STORAGE
    S3_REGION_NAME=(str, ""),
    S3_BUCKET_NAME=(str, ""),
    S3_ACCESS_KEY_ID=(str, ""),
    S3_SECRET_ACCESS_KEY=(str, ""),
    # MISCELLANEOUS
    REDIS_URL=(str, ""),
    # REDIS_URL=(str, "redis://redis:6379/0"),
    USE_DOCKER=(bool, False),
    # SENTRY — shared here so settings/logging.py doesn't declare its own Env
    # (contracts/settings-sections.md).
    SENTRY_DSN=(str, ""),
    DJANGO_SENTRY_LOG_LEVEL=(int, logging.INFO),
    SENTRY_ENVIRONMENT=(str, "production"),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.0),
)

"""The shared ``environ.Env`` reader and its declared variables."""

import logging

from environ import Env

env = Env(
    FAIRDM_ALLOW_PUBLIC_REGISTRATION=(bool, True),
    DJANGO_ADMIN_URL=(str, "admin/"),
    DJANGO_SUPERUSER_EMAIL=(str, "super.user@example.com"),
    # No working default: an unset admin password resolves to an empty string. The
    # production-critical checks, not this read, refuse a boot.
    DJANGO_SUPERUSER_PASSWORD=(str, ""),
    DJANGO_ALLOWED_HOSTS=(list, []),
    DJANGO_CACHE=(bool, True),
    DJANGO_DEBUG=(bool, False),
    DJANGO_READ_DOT_ENV_FILE=(bool, False),
    # No working default, so no key is published in FairDM's source (fairdm.E001).
    DJANGO_SECRET_KEY=(str, ""),
    # An unset domain stays empty so ALLOWED_HOSTS composes to [] rather than [""].
    DJANGO_SITE_DOMAIN=(str, ""),
    DJANGO_SITE_ID=(int, 1),
    DJANGO_SITE_NAME=(str, "FairDM Demo"),
    DJANGO_TIME_ZONE=(str, "UTC"),
    DJANGO_ROOT_URLCONF=(str, "config.urls"),
    DJANGO_SECURE=(bool, True),
    DJANGO_SECURE_HSTS_SECONDS=(int, 60),
    DATABASE_URL=(str, ""),
    POSTGRES_DB=(str, ""),
    POSTGRES_PASSWORD=(str, ""),
    POSTGRES_USER=(str, "postgres"),
    POSTGRES_HOST=(str, "postgres"),
    POSTGRES_PORT=(int, 5432),
    EMAIL_HOST=(str, ""),
    EMAIL_HOST_USER=(str, ""),
    EMAIL_HOST_PASSWORD=(str, ""),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_BACKEND=(str, "django.core.mail.backends.smtp.EmailBackend"),
    S3_REGION_NAME=(str, ""),
    S3_BUCKET_NAME=(str, ""),
    S3_ACCESS_KEY_ID=(str, ""),
    S3_SECRET_ACCESS_KEY=(str, ""),
    REDIS_URL=(str, ""),
    USE_DOCKER=(bool, False),
    # Declared here so settings/logging.py needn't build its own Env.
    SENTRY_DSN=(str, ""),
    DJANGO_SENTRY_LOG_LEVEL=(int, logging.INFO),
    SENTRY_ENVIRONMENT=(str, "production"),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.0),
)

import os
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import logging
import environ

localenv = environ.Env(
    SENTRY_DSN=(str, ""),
    DJANGO_SENTRY_LOG_LEVEL=(int, logging.INFO),
    SENTRY_ENVIRONMENT=(str, "production"),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.0),
)

DEBUG = globals().get("DEBUG", False)
SENTRY_DSN = localenv("SENTRY_DSN")
SENTRY_LOG_LEVEL = localenv.int("DJANGO_SENTRY_LOG_LEVEL", logging.INFO)
if SENTRY_DSN and not DEBUG:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            LoggingIntegration(
                level=SENTRY_LOG_LEVEL,
                event_level=logging.ERROR,
            ),
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
        ],
        environment=localenv("SENTRY_ENVIRONMENT", default="production"),
        traces_sample_rate=localenv.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
    )


# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# LOGGING
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#logging
# See https://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s",
        },
    },
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"level": "INFO", "handlers": ["console"]},
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "django.security.DisallowedHost": {
            "level": "ERROR",
            "handlers": ["console", "mail_admins"],
            "propagate": True,
        },
    },
}

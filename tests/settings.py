"""Test-specific Django settings for FairDM test suite."""

import logging
import os
import sys
import tempfile

# Development-shaped, so it says so: an unset DJANGO_ENV resolves to production, which refuses to
# boot on this configuration. pytest-env supplies it for the suite, but the mypy plugin, IDEs and
# plain shells import this module without it.
os.environ.setdefault("DJANGO_ENV", "development")

logging.disable(logging.CRITICAL)

import fairdm

fairdm.setup(
    apps=["demo"],
    addons=[],  # No addons needed for unit tests
)

from config.settings import *

# A test-only app hosting concrete Sample and Measurement subclasses. The registry
# refuses the polymorphic bases, so the suite needs concrete types to register, and
# a model under an uninstalled label breaks admin and URL resolution.
INSTALLED_APPS = [*INSTALLED_APPS, "tests.registry_models"]

# Inherits the PostGIS config from base settings. Tests run against a real PostGIS instance
# (.devcontainer/docker-compose.yml locally, .github/workflows/ci.yml in CI).


class DisableMigrations:
    """Disable migrations by returning None for all apps."""

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

    def setdefault(self, key, default=None):
        """Support setdefault() for compatibility with debug toolbar."""
        return None


MIGRATION_MODULES = DisableMigrations()


PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "select2": {  # Required by django-select2
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}


EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# A per-process fallback for code that reads these settings outside a test. The
# `_media_root_under_tmp_path` fixture in the root conftest.py points every test at its own
# tmp_path, so the suite never writes here (#323).
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), f"fairdm-test-media-{os.getpid()}")
STATIC_ROOT = os.path.join(tempfile.gettempdir(), f"fairdm-test-static-{os.getpid()}")

# django-orbit records a row per query and per signal through the connection of the page under
# test, which swamps query-count budgets. Turned off, its watchers are never installed.
ORBIT = {"ENABLED": False}


CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True


DEBUG = True
SECRET_KEY = "test-secret-key-not-for-production-use-only"
ALLOWED_HOSTS = ["*"]

CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "ERROR",
    },
}


RANDOM_SEED = 42

TEST_RUNNER = "django.test.runner.DiscoverRunner"

ROOT_URLCONF = "fairdm.conf.urls"

# Keep the mvp context processors: an earlier filter also removed mvp_config, so every page
# rendered with an empty shell configuration.


FAIRDM_FACTORIES = {
    "demo.CustomSample": "demo.factories.CustomSampleFactory",
    "demo.CustomParentSample": "demo.factories.CustomParentSampleFactory",
    "demo.ExampleMeasurement": "demo.factories.ExampleMeasurementFactory",
}

"""
Test-specific Django settings for FairDM test suite.

This settings module:
- Imports base FairDM configuration
- Inherits the PostGIS database config (no SQLite/SpatiaLite override)
- Disables migrations for faster test database setup
- Configures minimal logging
- Disables non-essential features for testing

Tests run against a real PostGIS instance (dev container or CI service).

Used automatically by pytest-django via pyproject.toml configuration.
"""

import logging
import os
import sys
import tempfile

# This module is development-shaped, so it has to say so: an unset DJANGO_ENV
# resolves to production, which refuses to boot on a configuration like this
# one. pytest supplies the same value through pytest-env, but the mypy hook's
# django-stubs plugin, an IDE and a plain shell all import this module without
# it.
os.environ.setdefault("DJANGO_ENV", "development")

# Silence noisy loggers during tests
logging.disable(logging.CRITICAL)

# Import base FairDM settings
import fairdm

# Setup FairDM with demo app for testing
fairdm.setup(
    apps=["demo"],
    addons=[],  # No addons needed for unit tests
)

# Import all settings from base configuration
from config.settings import *

# A test-only app hosting concrete Sample and Measurement subclasses. The registry
# refuses the polymorphic bases, so the suite needs concrete types to register, and
# a model under an uninstalled label breaks admin and URL resolution.
INSTALLED_APPS = [*INSTALLED_APPS, "tests.registry_models"]

# ==============================================================================
# DATABASE
# ==============================================================================
# No override — inherits PostGIS config from base settings (stack.env provides
# POSTGRES_* vars). Tests run against a real PostGIS instance:
#   - Dev container: the `postgres` service in .devcontainer/docker-compose.yml
#   - CI: the `postgres` service container in .github/workflows/ci.yml

# ==============================================================================
# MIGRATION SETTINGS
# ==============================================================================
# Disable migrations for faster test database creation
# Tests will use direct model table creation instead


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

# ==============================================================================
# PASSWORD HASHING
# ==============================================================================
# Use fast (insecure) password hasher for test speed

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ==============================================================================
# CACHING
# ==============================================================================
# Use dummy cache backend (no actual caching in tests)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "select2": {  # Required by django-select2
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

# ==============================================================================
# EMAIL
# ==============================================================================
# Use in-memory email backend for testing

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ==============================================================================
# STATIC FILES & MEDIA
# ==============================================================================
# Disable static file compression in tests

COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False

# A per-process path, not created here. This is only the fallback for code
# that reads these settings outside a test (a management command, an IDE's
# static analysis, the mypy django-stubs plugin); the
# `_media_root_under_tmp_path` fixture in the root `conftest.py` points every
# test at its own `tmp_path` before any test body runs, so nothing in the
# suite ever writes here. A fixed shared path here is what issue #323 was:
# every run wrote into it and nothing ever removed it. Naming a path without
# calling `mkdtemp` means storage only creates it (`os.makedirs`) if
# something actually writes to it — which the suite never does — so there is
# nothing left over to clean up, per process or per run.
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), f"fairdm-test-media-{os.getpid()}")
STATIC_ROOT = os.path.join(tempfile.gettempdir(), f"fairdm-test-static-{os.getpid()}")

# ==============================================================================
# OBSERVABILITY
# ==============================================================================
# django-orbit is a development dashboard; nothing in the suite reads what it
# records. Left on, it writes one row per SQL query and one per signal for
# every request, through a global monkeypatch of `Signal.send` that `repr()`s
# every kwarg it receives — which, under Django's `instrumented_test_render`,
# reprs the render context and can re-evaluate a queryset still held there.
# Those writes go through the same connection as the page under test, so any
# query count taken with `CaptureQueriesContext` includes them alongside the
# page's own queries, at a volume that swamps a five-query budget. `orbit.apps.
# OrbitConfig.ready` reads this setting at startup, so turning it off here
# also keeps the watchers from being installed at all.
ORBIT = {"ENABLED": False}

# ==============================================================================
# CELERY
# ==============================================================================
# Run tasks synchronously in tests (no background workers)

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ==============================================================================
# SECURITY
# ==============================================================================
# Disable security features that slow down tests

DEBUG = True
SECRET_KEY = "test-secret-key-not-for-production-use-only"
ALLOWED_HOSTS = ["*"]

# Disable CSRF for testing
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

# ==============================================================================
# LOGGING
# ==============================================================================
# Minimal logging during tests (errors only)

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

# ==============================================================================
# TEST-SPECIFIC SETTINGS
# ==============================================================================

# Make tests deterministic
RANDOM_SEED = 42

# Speed up tests by reducing iteration counts
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Override ROOT_URLCONF if needed
ROOT_URLCONF = "fairdm.conf.urls"

# ==============================================================================
# TEMPLATES
# ==============================================================================
# The suite used to strip every `mvp.context_processors.*` entry here, to work
# around one processor - `page_config` - that the installed django-mvp no longer
# ships. The filter matched the module rather than that name, so it also removed
# `mvp_config`, and every page the suite rendered was drawn with an empty shell
# configuration: no sidebar title, no footer widgets, no theme settings, none of
# the navbar actions. A test could assert the shell rendered a control it is not
# configured to draw, or miss one it is. The settings FairDM ships are what the
# suite renders now.

# ==============================================================================
# FACTORIES
# ==============================================================================
# Factory boy configuration for test data generation

FAIRDM_FACTORIES = {
    "demo.CustomSample": "demo.factories.CustomSampleFactory",
    "demo.CustomParentSample": "demo.factories.CustomParentSampleFactory",
    "demo.ExampleMeasurement": "demo.factories.ExampleMeasurementFactory",
}

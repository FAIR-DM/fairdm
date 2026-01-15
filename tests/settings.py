"""
Test-specific Django settings for FairDM test suite.

This settings module:
- Imports base FairDM configuration
- Overrides database to use in-memory SQLite for speed
- Disables migrations for faster test database setup
- Configures minimal logging
- Disables non-essential features for testing

Used automatically by pytest-django via pyproject.toml configuration.
"""

import logging
import sys
import tempfile
from pathlib import Path

# Silence noisy loggers during tests
logging.disable(logging.CRITICAL)

# Import base FairDM settings
import fairdm  # noqa: E402

# Setup FairDM with demo app for testing
fairdm.setup(
    apps=["fairdm_demo"],
    addons=[],  # No addons needed for unit tests
)

# Import all settings from base configuration
from config.settings import *  # noqa: E402

# ==============================================================================
# TEST DATABASE CONFIGURATION
# ==============================================================================
# Use in-memory SQLite for fast test execution
# This completely overrides the database configuration from base settings

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # In-memory database for speed
        "ATOMIC_REQUESTS": True,
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

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

# Use temporary directories for media files in tests
MEDIA_ROOT = Path(tempfile.gettempdir()) / "fairdm_test_media"
STATIC_ROOT = Path(tempfile.gettempdir()) / "fairdm_test_static"

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

# Disable debug toolbar in tests if it's installed
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: False,
}

# Override ROOT_URLCONF if needed
ROOT_URLCONF = "fairdm.conf.urls"

# ==============================================================================
# TEMPLATES
# ==============================================================================
# Remove mvp.context_processors.page_config which doesn't exist in test environment

for template_config in TEMPLATES:
    if "OPTIONS" in template_config and "context_processors" in template_config["OPTIONS"]:
        template_config["OPTIONS"]["context_processors"] = [
            cp for cp in template_config["OPTIONS"]["context_processors"]
            if "mvp.context_processors" not in cp
        ]

# ==============================================================================
# FACTORIES
# ==============================================================================
# Factory boy configuration for test data generation

FAIRDM_FACTORIES = {
    "fairdm_demo.CustomSample": "fairdm_demo.factories.CustomSampleFactory",
    "fairdm_demo.CustomParentSample": "fairdm_demo.factories.CustomParentSampleFactory",
    "fairdm_demo.ExampleMeasurement": "fairdm_demo.factories.ExampleMeasurementFactory",
}

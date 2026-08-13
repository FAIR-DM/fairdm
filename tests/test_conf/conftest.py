"""
Shared fixtures for tests/test_conf.

Fixtures used by more than one test module in this package live here so
each module keeps only the fixtures it alone depends on.
"""

import importlib.util
import itertools
import os

import pytest


@pytest.fixture
def settings_module(tmp_path):
    """Write and execute a portal settings module that calls ``fairdm.setup()``.

    Returns a callable so a test can build more than one resolution. Each
    call writes ``directory/filename`` (default ``tmp_path/settings.py``)
    containing ``import fairdm`` followed by ``setup_call``, then ``after``,
    executes it, and returns the resulting module object.
    """
    counter = itertools.count()

    def _make(setup_call="fairdm.setup()", after="", directory=None, filename="settings.py"):
        target_dir = directory or tmp_path
        target_dir.mkdir(parents=True, exist_ok=True)
        settings_file = target_dir / filename
        settings_file.write_text(f"import fairdm\n\n{setup_call}\n{after}\n")

        module_name = f"_test_conf_settings_module_{next(counter)}"
        spec = importlib.util.spec_from_file_location(module_name, settings_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return _make


@pytest.fixture
def production_env(tmp_path):
    """Provide complete production environment variables."""
    env_vars = {
        "DJANGO_ENV": "production",
        "DJANGO_SECRET_KEY": "a" * 60,  # Long enough for production
        "DJANGO_SITE_DOMAIN": "example.com",
        "DJANGO_SITE_NAME": "Test Portal",
        "DJANGO_ALLOWED_HOSTS": "example.com,www.example.com",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
        "REDIS_URL": "redis://localhost:6379/0",
        "SENTRY_DSN": "https://fake@sentry.io/123456",
        "EMAIL_HOST": "smtp.example.com",
        "EMAIL_PORT": "587",
        "EMAIL_HOST_USER": "test@example.com",
        "EMAIL_HOST_PASSWORD": "password",
        "S3_ACCESS_KEY_ID": "",
        "S3_SECRET_ACCESS_KEY": "",
        "S3_BUCKET_NAME": "",
        "S3_REGION_NAME": "",
    }

    # Save original env
    original_env = os.environ.copy()

    # Clear Django-related env vars
    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    # Set test environment
    os.environ.update(env_vars)

    yield env_vars

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

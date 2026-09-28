"""Shared fixtures for tests/test_conf."""

import importlib.util
import itertools
import os

import pytest

#: Prefixes of every environment variable fairdm's settings baseline reads.
#: Isolation fixtures clear and restore exactly this set, so a test's
#: environment can never leak into, or inherit from, another test.
ENV_VAR_PREFIXES = (
    "DJANGO_",
    "DATABASE_",
    "POSTGRES_",
    "REDIS_",
    "EMAIL_",
    "S3_",
    "SENTRY_",
)


@pytest.fixture
def isolated_env():
    original_env = os.environ.copy()
    for key in list(os.environ.keys()):
        if key.startswith(ENV_VAR_PREFIXES):
            del os.environ[key]

    yield

    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def settings_module(tmp_path):
    counter = itertools.count()

    def _make(
        setup_call="fairdm.setup()", after="", directory=None, filename="settings.py"
    ):
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

    original_env = os.environ.copy()

    for key in list(os.environ.keys()):
        if key.startswith(
            ("DJANGO_", "DATABASE_", "REDIS_", "POSTGRES_", "EMAIL_", "S3_", "SENTRY_")
        ):
            del os.environ[key]

    os.environ.update(env_vars)

    yield env_vars

    os.environ.clear()
    os.environ.update(original_env)

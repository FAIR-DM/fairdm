"""
Shared fixtures for tests/test_conf.

Fixtures used by more than one test module in this package live here so
each module keeps only the fixtures it alone depends on.
"""

import os

import pytest


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

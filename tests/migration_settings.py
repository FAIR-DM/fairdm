"""Settings for the from-empty migration test: real migrations, throwaway databases."""

import os
from pathlib import Path

# Development-shaped, so it has to say so: an unset DJANGO_ENV resolves to
# production, which refuses to boot on a configuration like this one.
os.environ.setdefault("DJANGO_ENV", "development")

import fairdm

fairdm.setup(apps=["demo"], addons=[])

from config.settings import *

MIGRATION_TEST_DIR = Path(os.environ["FAIRDM_MIGRATION_TEST_DIR"])

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(MIGRATION_TEST_DIR / "default.sqlite3"),
    },
    "migration_check": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(MIGRATION_TEST_DIR / "migrated.sqlite3"),
    },
}

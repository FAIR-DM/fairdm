"""
Settings for the from-empty migration test: real migrations, throwaway databases.

``tests.settings`` disables migrations so the suite can build its database
straight from the models. This module is the same configuration with that
disabling left off, pointed at SQLite files under the directory named by
``FAIRDM_MIGRATION_TEST_DIR``. It exists so ``manage.py migrate`` can be run the
way a new installation runs it.

There are two databases on purpose. A data migration that queries through the
ORM without routing to ``schema_editor.connection.alias`` reads ``default``
instead of the database being migrated, which is a failure no single-database
run can show. The test migrates ``default`` first and ``migration_check``
second, so an unrouted query in the second run meets a database that is already
past the migration doing the asking.
"""

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

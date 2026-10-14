"""Settings for the from-empty migration test: real migrations, throwaway databases."""

import os

# Development-shaped, so it has to say so: an unset DJANGO_ENV resolves to
# production, which refuses to boot on a configuration like this one.
os.environ.setdefault("DJANGO_ENV", "development")

import fairdm

fairdm.setup(apps=["demo"], addons=[])

from config.settings import *

# Two empty databases on the suite's own PostGIS server, created and dropped by the test.
DATABASES = {
    "default": {
        **DATABASES["default"],
        "NAME": os.environ["FAIRDM_MIGRATION_TEST_DATABASE"],
    },
    "migration_check": {
        **DATABASES["default"],
        "NAME": os.environ["FAIRDM_MIGRATION_CHECK_DATABASE"],
    },
}

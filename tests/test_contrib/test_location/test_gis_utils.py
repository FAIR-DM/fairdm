"""Tests for the djangorestframework-gis import guard (issue #111).

djangorestframework-gis lives behind the optional ``gis`` extra rather than as
a hard dependency, because it pulls in GDAL. This package is not installed in
this environment or in CI, so these tests assert the guard's behaviour under
that reality: importing ``fairdm.contrib.location.gis_utils`` without the extra
must raise ``ImproperlyConfigured`` naming the extra to install, not a bare
``ModuleNotFoundError``.
"""

import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured


class TestGisUtilsImportGuard:
    """``fairdm.contrib.location.gis_utils`` guards its rest_framework_gis import."""

    def test_import_without_gis_extra_raises_improperly_configured(self):
        """Importing without djangorestframework-gis raises ImproperlyConfigured
        naming the 'gis' extra, instead of a bare ModuleNotFoundError."""
        sys.modules.pop("fairdm.contrib.location.gis_utils", None)

        with pytest.raises(ImproperlyConfigured) as excinfo:
            importlib.import_module("fairdm.contrib.location.gis_utils")

        message = str(excinfo.value)
        assert "gis" in message
        assert "pip install fairdm[gis]" in message
        assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)

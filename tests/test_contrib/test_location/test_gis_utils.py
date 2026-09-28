"""Tests for the djangorestframework-gis import guard (issue #111)."""

import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured


class TestGisUtilsImportGuard:
    def test_import_without_gis_extra_raises_improperly_configured(self):
        sys.modules.pop("fairdm.contrib.location.gis_utils", None)

        with pytest.raises(ImproperlyConfigured) as excinfo:
            importlib.import_module("fairdm.contrib.location.gis_utils")

        message = str(excinfo.value)
        assert "gis" in message
        assert "pip install fairdm[gis]" in message
        assert isinstance(excinfo.value.__cause__, ModuleNotFoundError)

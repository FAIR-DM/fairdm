"""Tests for plugin visibility helpers."""

import pytest
from django.test import RequestFactory

from fairdm.contrib.plugins.visibility import is_instance_of
from fairdm.core.sample.models import Sample
from fairdm.factories import SampleFactory

pytestmark = pytest.mark.django_db


class TestIsInstanceOf:
    """Tests for is_instance_of() visibility helper."""

    def test_is_instance_of_single_model(self, rf: RequestFactory):
        """is_instance_of should create check function for single model."""
        check = is_instance_of(Sample)
        sample = SampleFactory()
        request = rf.get("/")

        # Should pass for instances of the specified model
        assert check(request, sample) is True

    def test_is_instance_of_multiple_models(self, rf: RequestFactory):
        """is_instance_of should accept instances of any specified model."""
        # Using Sample as both types for simplicity
        check = is_instance_of(Sample, Sample)
        sample = SampleFactory()
        request = rf.get("/")

        assert check(request, sample) is True

    def test_is_instance_of_wrong_type(self, rf: RequestFactory):
        """is_instance_of should reject instances of other models."""
        from fairdm.core.dataset.models import Dataset
        from fairdm.factories.core import DatasetFactory

        check = is_instance_of(Sample)
        dataset = DatasetFactory()
        request = rf.get("/")

        # Should fail for instances of different models
        assert check(request, dataset) is False

    def test_is_instance_of_none_object(self, rf: RequestFactory):
        """is_instance_of should return True for None (model-level access)."""
        check = is_instance_of(Sample)
        request = rf.get("/")

        # None means model-level access (e.g., list view), should allow
        assert check(request, None) is True

    def test_is_instance_of_callable_signature(self):
        """is_instance_of should return a callable with correct signature."""
        check = is_instance_of(Sample)

        # Should be callable
        assert callable(check)

        # Should accept request and obj parameters
        import inspect

        sig = inspect.signature(check)
        assert "request" in sig.parameters
        assert "obj" in sig.parameters

    def test_is_instance_of_with_inheritance(self, rf: RequestFactory):
        """is_instance_of should work with model inheritance."""
        # Sample inherits from Django Model
        # Create a check for the base Sample model
        check = is_instance_of(Sample)
        sample = SampleFactory()
        request = rf.get("/")

        # Even though SampleFactory might create a subclass, it should still pass
        assert check(request, sample) is True

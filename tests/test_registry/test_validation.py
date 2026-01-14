"""T014: Unit tests for registration-time validation.

Tests that invalid registrations fail with clear error messages at registration time.
"""

import pytest
from django.db import models

from fairdm.registry.config import ModelConfiguration
from fairdm.core.models import Sample
from fairdm.registry import registry
from fairdm.registry.exceptions import (
    ConfigurationError,
    DuplicateRegistrationError,
    FieldValidationError,
)


class TestRegistrationValidation:
    """Test registration-time validation for ModelConfiguration."""

    @pytest.fixture
    def clean_registry(self):
        """Clean the registry before and after each test."""
        registry._registry.clear()
        yield registry
        registry._registry.clear()

    def test_model_required(self):
        """Test that ModelConfiguration requires a model."""
        with pytest.raises(ConfigurationError, match="model is required"):
            ModelConfiguration(model=None)

    def test_model_must_inherit_from_sample_or_measurement(self, clean_registry):
        """Test that only Sample/Measurement subclasses can be registered."""

        class InvalidModel(models.Model):
            """Regular Django model (not Sample/Measurement)."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError, match="must inherit from Sample or Measurement"):
            clean_registry.register(InvalidModel)

    def test_duplicate_registration_rejected(self, clean_registry):
        """Test that registering the same model twice raises DuplicateRegistrationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # First registration should succeed
        clean_registry.register(RockSample)

        # Second registration should fail
        with pytest.raises(DuplicateRegistrationError, match="already registered"):
            clean_registry.register(RockSample)

    def test_invalid_field_name_in_list_fields(self):
        """Test that invalid field names in fields raise FieldValidationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError, match="Invalid field: nonexistent_field"):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent_field"],
            )

    def test_invalid_field_name_in_component_specific_fields(self):
        """Test that invalid field names in component-specific fields raise FieldValidationError."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        with pytest.raises(FieldValidationError, match="Invalid field: bad_field"):
            ModelConfiguration(
                model=RockSample,
                table_fields=["rock_type", "bad_field"],
            )

    def test_invalid_related_field_path(self):
        """Test that related field paths are validated for base field only.
        
        Note: We only validate that the base field (e.g., 'related') exists on the model.
        We do not validate the full path (e.g., 'related__title') because:
        1. It would require recursive model introspection
        2. Django will raise clear errors at runtime if the path is invalid
        3. The path might be valid for some querysets but not others (e.g., prefetch_related)
        """

        class RelatedModel(models.Model):
            """Related model."""

            title = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        class RockSample(Sample):
            """Test Sample with foreign key."""

            rock_type = models.CharField(max_length=100)
            related = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)

            class Meta:
                app_label = "test_app"

        # Valid path with base field existing should work
        config = ModelConfiguration(
            model=RockSample,
            fields=["rock_type", "related__title"],
        )
        assert "related__title" in config.fields

        # Path with nonexistent base field should fail
        with pytest.raises(FieldValidationError, match="Invalid field"):
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "nonexistent__title"],
            )


class TestFieldValidationWithFuzzyMatching:
    """Test fuzzy field name matching for helpful error messages."""

    def test_fuzzy_match_suggests_close_field_names(self):
        """Test that FieldValidationError suggests similar field names."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)
            mineral_content = models.TextField()

            class Meta:
                app_label = "test_app"

        # Typo: "mineral_contnt" instead of "mineral_content"
        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "mineral_contnt"],
            )

        # Error message should suggest the correct field
        assert "mineral_contnt" in str(exc_info.value)
        assert "Did you mean" in str(exc_info.value)
        assert "mineral_content" in str(exc_info.value)

    def test_no_suggestions_when_no_close_matches(self):
        """Test that no suggestions are given when no close matches exist."""

        class RockSample(Sample):
            """Test Sample model."""

            rock_type = models.CharField(max_length=100)

            class Meta:
                app_label = "test_app"

        # Completely wrong field name
        with pytest.raises(FieldValidationError) as exc_info:
            ModelConfiguration(
                model=RockSample,
                fields=["rock_type", "xyz123"],
            )

        # Error message should not suggest anything
        assert "xyz123" in str(exc_info.value)
        assert "Did you mean" not in str(exc_info.value)

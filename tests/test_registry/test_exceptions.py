"""Tests for the registry's errors."""

import pytest
from django.db import models

from fairdm.core.sample.models import Sample
from fairdm.registry.config import ModelConfiguration
from fairdm.registry.exceptions import (
    ConfigurationError,
    DuplicateRegistrationError,
    FieldValidationError,
    NotRegisteredError,
    RegistryError,
)


@pytest.fixture
def rock_sample():
    class RockSample(Sample):
        rock_type = models.CharField(max_length=100)

        class Meta:
            app_label = "test_app"

    return RockSample


class TestHierarchy:
    @pytest.mark.parametrize(
        "error",
        [
            ConfigurationError,
            FieldValidationError,
            DuplicateRegistrationError,
            NotRegisteredError,
        ],
    )
    def test_every_error_is_a_registry_error(self, error):
        assert issubclass(error, RegistryError)

    def test_not_registered_is_also_a_key_error(self):
        assert issubclass(NotRegisteredError, KeyError)


class TestFieldValidationError:
    def test_it_names_model_attribute_value_and_suggestion(self, rock_sample):
        with pytest.raises(FieldValidationError) as caught:
            ModelConfiguration(model=rock_sample, table_fields=["rock_typ"])

        error = caught.value
        assert error.field_name == "rock_typ"
        assert error.model is rock_sample
        assert error.attribute == "table_fields"
        assert "rock_type" in error.suggestion

        message = str(error)
        assert "RockSample.table_fields" in message
        assert "'rock_typ'" in message

    def test_no_suggestion_when_nothing_is_close(self, rock_sample):
        with pytest.raises(FieldValidationError) as caught:
            ModelConfiguration(model=rock_sample, fields=["zzzzzzzz"])

        assert not caught.value.suggestion


class TestDuplicateRegistrationError:
    def test_it_names_the_first_registration_location(self, clean_registry):
        class GraniteSample(Sample):
            class Meta:
                app_label = "test_app"

        clean_registry.register(GraniteSample)

        with pytest.raises(DuplicateRegistrationError) as caught:
            clean_registry.register(GraniteSample)

        error = caught.value
        assert error.model is GraniteSample
        # Import order decides which arrives first, so the location is the only way
        # a developer can find the other registration.
        assert "test_exceptions" in error.original_location
        assert error.original_location != "Unknown"
        assert "GraniteSample" in str(error)


class TestNotRegisteredError:
    def test_it_names_the_model(self, clean_registry, rock_sample):
        with pytest.raises(NotRegisteredError) as caught:
            clean_registry.get_for_model(rock_sample)

        assert "RockSample" in str(caught.value)

    def test_the_message_is_not_a_quoted_key(self, clean_registry, rock_sample):
        with pytest.raises(NotRegisteredError) as caught:
            clean_registry.get_for_model(rock_sample)

        message = str(caught.value)
        assert not message.startswith("'")
        assert not message.endswith("'")

    def test_there_is_no_shortcut_on_the_model(self, rock_sample):
        assert not hasattr(rock_sample, "config")


class TestConfigurationError:
    def test_a_missing_model_is_refused(self):
        with pytest.raises(ConfigurationError):
            ModelConfiguration()

    def test_an_ineligible_model_names_both_permitted_bases(self, clean_registry):
        class NotASample(models.Model):
            class Meta:
                app_label = "test_app"

        with pytest.raises(ConfigurationError) as caught:
            clean_registry.register(NotASample, ModelConfiguration(model=NotASample))

        message = str(caught.value)
        assert "Sample" in message
        assert "Measurement" in message


class TestRefusedRegistrationLeavesNothingBehind:
    def test_the_mapping_is_untouched(self, clean_registry):
        class NotASample(models.Model):
            class Meta:
                app_label = "test_app"

        before = dict(clean_registry._registry)

        with pytest.raises(ConfigurationError):
            clean_registry.register(NotASample, ModelConfiguration(model=NotASample))

        assert clean_registry._registry == before
        assert NotASample not in clean_registry._registry


class TestAdminRegistration:
    def test_a_hand_written_admin_registration_wins(self, clean_registry):
        from django.contrib import admin as dj_admin

        from fairdm.core.sample.admin import SampleChildAdmin

        class SlateSample(Sample):
            class Meta:
                app_label = "test_app"

        class SlateSampleAdmin(SampleChildAdmin):
            base_model = SlateSample

        dj_admin.site.register(SlateSample, SlateSampleAdmin)

        clean_registry.register(SlateSample)

        assert isinstance(dj_admin.site._registry[SlateSample], SlateSampleAdmin)

    def test_a_broken_admin_class_is_not_swallowed(self, clean_registry):
        class BasaltSample(Sample):
            class Meta:
                app_label = "test_app"

        class BrokenConfig(ModelConfiguration):
            model = BasaltSample

            def get_admin_class(self):
                raise RuntimeError("this admin class cannot be built")

        with pytest.raises(RuntimeError, match="cannot be built"):
            clean_registry.register(BasaltSample, BrokenConfig())

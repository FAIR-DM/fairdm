"""Tests for contributor validators (FS-009 US1 T010).

Tests cover:
- validate_iso_639_1_language_code: refuses a code outside ISO 639-1, passes a
  valid one (FR-004, SC-002)
- The validator wired to Contributor.lang, so an invalid code in the field is
  actually refused rather than merely rejected in isolation (FR-004)
"""

import pytest
from django.core.exceptions import ValidationError

from fairdm.contrib.contributors.validators import (
    validate_iso_639_1_language_code,
    validate_iso_639_1_language_codes,
)
from fairdm.factories import PersonFactory

# ── T010: ISO 639-1 validator ────────────────────────────────────────────────


class TestISO6391Validator:
    """Verify the standalone ISO 639-1 code validator."""

    def test_invalid_code_raises_with_value_in_message_params(self):
        """A code outside ISO 639-1 raises, with the offending value interpolated."""
        with pytest.raises(ValidationError) as excinfo:
            validate_iso_639_1_language_code("xx")

        assert excinfo.value.params == {"value": "xx"}
        assert "xx" in str(excinfo.value.message % excinfo.value.params)

    def test_valid_code_passes(self):
        """A valid ISO 639-1 code raises nothing."""
        validate_iso_639_1_language_code("en")


class TestISO6391ListValidator:
    """Verify the list-wrapping validator that Contributor.lang actually uses."""

    def test_invalid_code_anywhere_in_list_raises(self):
        """An invalid code anywhere in the list is refused."""
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_codes(["en", "xx"])

    def test_all_valid_codes_pass(self):
        """A list of only valid codes raises nothing."""
        validate_iso_639_1_language_codes(["en", "fr", "es"])

    def test_empty_or_none_passes(self):
        """No codes at all is not an invalid code."""
        validate_iso_639_1_language_codes([])
        validate_iso_639_1_language_codes(None)


# ── T017: the validator attached to the field ────────────────────────────────


class TestContributorLanguageFieldValidation:
    """Verify the validator is actually attached to Contributor.lang, not just defined."""

    @pytest.mark.django_db
    def test_invalid_language_code_refused_on_full_clean(self):
        """A person carrying an invalid language code is refused, on the lang field."""
        person = PersonFactory(lang=["xx"])
        with pytest.raises(ValidationError) as excinfo:
            person.full_clean(validate_unique=False)

        assert "lang" in excinfo.value.message_dict

    @pytest.mark.django_db
    def test_valid_language_codes_do_not_trigger_lang_errors(self):
        """A person carrying only valid language codes raises nothing for lang."""
        person = PersonFactory(lang=["en", "fr"])
        field = person._meta.get_field("lang")
        field.clean(person.lang, person)

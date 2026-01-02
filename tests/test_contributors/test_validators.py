"""Tests for contributors validators."""

import pytest
from django.core.exceptions import ValidationError

from fairdm.contrib.contributors.validators import validate_iso_639_1_language_code


class TestIso6391LanguageCodeValidator:
    """Tests for validate_iso_639_1_language_code validator."""

    def test_valid_common_language_codes(self):
        """Test that common language codes are accepted."""
        valid_codes = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ar"]

        for code in valid_codes:
            # Should not raise ValidationError
            validate_iso_639_1_language_code(code)

    def test_valid_other_language_codes(self):
        """Test that other valid ISO 639-1 codes are accepted."""
        valid_codes = ["aa", "ko", "nl", "pl", "sv", "th", "vi", "zu"]

        for code in valid_codes:
            # Should not raise ValidationError
            validate_iso_639_1_language_code(code)

    def test_invalid_language_code_raises_error(self):
        """Test that invalid language codes raise ValidationError."""
        invalid_codes = ["eng", "xx", "zz", "123", "EN", "e", "english", ""]

        for code in invalid_codes:
            with pytest.raises(ValidationError) as exc_info:
                validate_iso_639_1_language_code(code)

            # Check error message contains the invalid value
            assert code in str(exc_info.value) or "not a valid ISO 639-1" in str(exc_info.value)

    def test_error_message_format(self):
        """Test that error message is properly formatted."""
        with pytest.raises(ValidationError) as exc_info:
            validate_iso_639_1_language_code("xxx")

        error_message = str(exc_info.value)
        assert "xxx" in error_message
        assert "ISO 639-1" in error_message
        assert "two-letter code" in error_message

    def test_case_sensitive(self):
        """Test that validation is case-sensitive (only lowercase accepted)."""
        # Lowercase should work
        validate_iso_639_1_language_code("en")

        # Uppercase should fail
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("EN")

        # Mixed case should fail
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("En")

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValidationError."""
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("")

    def test_three_letter_code_raises_error(self):
        """Test that three-letter codes (ISO 639-2) are rejected."""
        # These are valid ISO 639-2 codes but should be rejected
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("eng")

        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("spa")

    def test_numeric_codes_raise_error(self):
        """Test that numeric codes raise ValidationError."""
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("12")

        with pytest.raises(ValidationError):
            validate_iso_639_1_language_code("99")

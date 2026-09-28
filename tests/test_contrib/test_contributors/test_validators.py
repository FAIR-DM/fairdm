"""Tests for contributor validators."""

import pytest
from django.core.exceptions import ValidationError

from fairdm.contrib.contributors.validators import (
    validate_iso_639_1_language_code,
    validate_iso_639_1_language_codes,
)
from fairdm.factories import PersonFactory


class TestISO6391Validator:
    def test_invalid_code_raises_with_value_in_message_params(self):
        with pytest.raises(ValidationError) as excinfo:
            validate_iso_639_1_language_code("xx")

        assert excinfo.value.params == {"value": "xx"}
        assert "xx" in str(excinfo.value.message % excinfo.value.params)

    def test_valid_code_passes(self):
        validate_iso_639_1_language_code("en")


class TestISO6391ListValidator:
    def test_invalid_code_anywhere_in_list_raises(self):
        with pytest.raises(ValidationError):
            validate_iso_639_1_language_codes(["en", "xx"])

    def test_all_valid_codes_pass(self):
        validate_iso_639_1_language_codes(["en", "fr", "es"])

    def test_empty_or_none_passes(self):
        validate_iso_639_1_language_codes([])
        validate_iso_639_1_language_codes(None)


class TestContributorLanguageFieldValidation:
    @pytest.mark.django_db
    def test_invalid_language_code_refused_on_full_clean(self):
        person = PersonFactory(lang=["xx"])
        with pytest.raises(ValidationError) as excinfo:
            person.full_clean(validate_unique=False)

        assert "lang" in excinfo.value.message_dict

    @pytest.mark.django_db
    def test_valid_language_codes_do_not_trigger_lang_errors(self):
        person = PersonFactory(lang=["en", "fr"])
        field = person._meta.get_field("lang")
        field.clean(person.lang, person)

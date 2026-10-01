"""Tests for the profile editing forms: the list field and the person's form."""

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import URLValidator

from fairdm.contrib.contributors.forms.profile import LinesField, PersonProfileForm
from fairdm.core import image_utils
from fairdm.factories import PersonFactory


class TestLinesField:
    def test_each_line_is_one_entry(self):
        assert LinesField().clean("first\nsecond\nthird") == ["first", "second", "third"]

    def test_blank_lines_are_dropped(self):
        assert LinesField().clean("first\n\n   \nsecond\n") == ["first", "second"]

    def test_a_repeated_entry_is_kept_once_in_the_order_first_seen(self):
        assert LinesField().clean("b\na\nb\nc\na") == ["b", "a", "c"]

    def test_spaces_around_an_entry_are_trimmed(self):
        assert LinesField().clean("  first  \n\tsecond ") == ["first", "second"]

    def test_a_browser_submission_with_windows_line_endings_splits_the_same_way(self):
        assert LinesField().clean("first\r\nsecond\r\n") == ["first", "second"]

    def test_entries_that_differ_only_by_surrounding_spaces_are_one_entry(self):
        assert LinesField().clean("first\n first ") == ["first"]

    def test_a_list_given_as_the_initial_value_is_shown_one_entry_per_line(self):
        assert LinesField().prepare_value(["first", "second"]) == "first\nsecond"

    def test_no_initial_value_is_shown_as_an_empty_box(self):
        assert LinesField().prepare_value(None) == ""

    def test_an_optional_field_with_nothing_typed_gives_an_empty_list(self):
        assert LinesField(required=False).clean("  \n ") == []

    def test_a_required_field_with_nothing_typed_is_refused(self):
        with pytest.raises(ValidationError) as refused:
            LinesField(required=True).clean("  \n ")

        assert refused.value.code == "required"

    def test_the_entry_validator_names_the_first_entry_at_fault(self):
        field = LinesField(entry_validator=URLValidator(schemes=["http", "https"]))

        with pytest.raises(ValidationError) as refused:
            field.clean("https://example.org\nnot a link\nalso not a link")

        assert refused.value.code == "invalid_entry"
        assert refused.value.params == {"entry": "not a link"}

    def test_entries_the_validator_accepts_pass_through(self):
        field = LinesField(entry_validator=URLValidator(schemes=["http", "https"]))

        assert field.clean("https://example.org\nhttp://example.net") == [
            "https://example.org",
            "http://example.net",
        ]


@pytest.mark.django_db
class TestPersonProfileForm:
    def test_the_form_offers_the_photo_name_alternative_names_biography_links_and_languages_only(
        self, person
    ):
        form = PersonProfileForm(instance=person)

        assert set(form.fields) == {
            "image",
            "name",
            "alternative_names",
            "profile",
            "links",
            "lang",
        }

    def test_a_valid_form_saves_every_field(self, person, profile_data, image_upload):
        form = PersonProfileForm(
            profile_data, {"image": image_upload()}, instance=person
        )

        assert form.is_valid(), form.errors
        form.save()

        person.refresh_from_db()
        assert person.name == "Dr. Ada Lovelace"
        assert person.alternative_names == ["A. Lovelace", "Augusta Ada King"]
        assert person.profile == "Mathematician and writer."
        assert person.links == ["https://example.org/ada", "http://example.org/notes"]
        assert person.lang == ["en", "fr"]
        assert person.image

    def test_the_stored_lists_are_shown_one_entry_per_line_when_the_form_opens(
        self, person
    ):
        person.alternative_names = ["A. Lovelace", "Augusta Ada King"]
        person.links = ["https://example.org/ada"]
        person.save()

        form = PersonProfileForm(instance=person)

        assert form["alternative_names"].value() == "A. Lovelace\nAugusta Ada King"
        assert form["links"].value() == "https://example.org/ada"

    def test_empty_and_repeated_entries_are_not_stored(self, person, profile_data):
        profile_data["alternative_names"] = "A. Lovelace\n\nA. Lovelace\n"
        profile_data["lang"] = ["en", "en"]
        form = PersonProfileForm(profile_data, instance=person)

        assert form.is_valid(), form.errors
        form.save()

        person.refresh_from_db()
        assert person.alternative_names == ["A. Lovelace"]
        assert person.lang == ["en"]

    def test_a_name_is_required(self, person, profile_data):
        profile_data["name"] = ""
        form = PersonProfileForm(profile_data, instance=person)

        assert form.has_error("name", code="required")

    @pytest.mark.parametrize(
        "link",
        ["example.org/ada", "ftp://example.org/ada", "javascript:alert(1)", "not a link"],
    )
    def test_a_link_that_is_not_an_http_or_https_address_is_refused_on_the_links_field(
        self, person, profile_data, link
    ):
        profile_data["links"] = f"https://example.org/ok\n{link}"
        form = PersonProfileForm(profile_data, instance=person)

        assert form.has_error("links", code="invalid_entry")
        assert form.errors["links"].as_data()[0].params == {"entry": link}
        assert not form.has_error("name")

    def test_a_language_outside_iso_639_1_is_refused_on_the_languages_field(
        self, person, profile_data
    ):
        profile_data["lang"] = ["en", "xx"]
        form = PersonProfileForm(profile_data, instance=person)

        assert form.has_error("lang", code="invalid_choice")

    def test_a_file_that_is_not_an_image_is_refused_on_the_photo_field(
        self, person, profile_data
    ):
        upload = SimpleUploadedFile("notes.txt", b"not an image", "text/plain")
        form = PersonProfileForm(profile_data, {"image": upload}, instance=person)

        assert form.has_error("image", code="invalid_image")

    def test_an_image_over_the_size_limit_is_refused_on_the_photo_field(
        self, person, profile_data, image_upload, monkeypatch
    ):
        monkeypatch.setattr(image_utils, "MAX_IMAGE_UPLOAD_BYTES", 10)
        form = PersonProfileForm(
            profile_data, {"image": image_upload()}, instance=person
        )

        assert form.has_error("image")
        assert not form.has_error("name")

    def test_a_refused_form_keeps_what_was_typed_in_the_other_fields(
        self, person, profile_data
    ):
        profile_data["name"] = ""
        form = PersonProfileForm(profile_data, instance=person)

        assert form["profile"].value() == "Mathematician and writer."
        assert form["links"].value() == "https://example.org/ada\nhttp://example.org/notes"

    def test_a_cleared_photo_is_removed(self, profile_data):
        person = PersonFactory(with_image=True)
        profile_data["image-clear"] = "on"
        form = PersonProfileForm(profile_data, instance=person)

        assert form.is_valid(), form.errors
        form.save()

        person.refresh_from_db()
        assert not person.image

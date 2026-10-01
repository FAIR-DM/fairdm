"""Tests for the profile editing forms: the list field, the person's form and the organization's."""

from types import SimpleNamespace

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import URLValidator

from fairdm.contrib.contributors.forms.profile import (
    LinesField,
    OrganizationProfileForm,
    PersonProfileForm,
)
from fairdm.contrib.contributors.models import ContributorIdentifier
from fairdm.core import image_utils
from fairdm.factories import OrganizationFactory, PersonFactory


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


@pytest.mark.django_db
class TestOrganizationProfileForm:
    def test_the_form_offers_the_logo_name_alternative_names_type_parent_city_country_description_website_and_links_only(
        self, organization
    ):
        form = OrganizationProfileForm(instance=organization)

        assert set(form.fields) == {
            "image",
            "name",
            "alternative_names",
            "type",
            "parent",
            "city",
            "country",
            "profile",
            "website",
            "links",
        }

    def test_a_valid_form_saves_every_field(
        self, organization, organization_profile_data, image_upload
    ):
        parent = OrganizationFactory()
        organization_profile_data["parent"] = parent.pk
        form = OrganizationProfileForm(
            organization_profile_data, {"image": image_upload()}, instance=organization
        )

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert organization.name == "Potsdam Research Institute"
        assert organization.alternative_names == ["PRI", "Institut Potsdam"]
        assert organization.type == "education"
        assert organization.parent == parent
        assert organization.city == "Potsdam"
        assert organization.country == "DE"
        assert organization.profile == "Studies the Earth system."
        assert organization.image

    def test_the_website_is_shown_from_the_first_stored_link_and_the_rest_as_other_links(
        self, organization
    ):
        organization.links = ["https://example.org", "https://example.net/wiki"]
        organization.save()

        form = OrganizationProfileForm(instance=organization)

        assert form["website"].value() == "https://example.org"
        assert form["links"].value() == "https://example.net/wiki"

    def test_an_organization_with_no_links_shows_no_website(self, organization):
        organization.links = []
        organization.save()

        form = OrganizationProfileForm(instance=organization)

        assert not form["website"].value()
        assert not form["links"].value()

    def test_the_website_is_saved_as_the_first_link_with_the_other_links_after_it_and_no_repeat(
        self, organization, organization_profile_data
    ):
        # The other links repeat the website, as a person might type it.
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert organization.links == [
            "https://example.org",
            "https://example.net/wiki",
            "https://example.org/news",
        ]

    def test_the_same_address_typed_as_website_and_among_the_other_links_is_stored_once(
        self, organization, organization_profile_data
    ):
        organization_profile_data["links"] = "https://example.org\nhttps://example.net"
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert organization.links == ["https://example.org", "https://example.net"]

    def test_clearing_the_website_keeps_the_other_links(
        self, organization, organization_profile_data
    ):
        organization_profile_data["website"] = ""
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert organization.links == [
            "https://example.net/wiki",
            "https://example.org/news",
        ]

    def test_clearing_the_website_and_the_other_links_leaves_no_links(
        self, organization, organization_profile_data
    ):
        organization.links = ["https://example.org"]
        organization.save()
        organization_profile_data["website"] = ""
        organization_profile_data["links"] = ""
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert organization.links == []

    @pytest.mark.parametrize("field", ["website", "links"])
    def test_an_address_that_is_not_http_or_https_is_refused_on_its_field(
        self, organization, organization_profile_data, field
    ):
        organization_profile_data[field] = "ftp://example.org/files"
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.has_error(field)
        assert not form.has_error("name")

    def test_a_name_is_required(self, organization, organization_profile_data):
        organization_profile_data["name"] = ""
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.has_error("name", code="required")

    def test_a_type_outside_the_list_is_refused_on_the_type_field(
        self, organization, organization_profile_data
    ):
        organization_profile_data["type"] = "spaceship"
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.has_error("type", code="invalid_choice")

    def test_a_country_outside_the_list_is_refused_on_the_country_field(
        self, organization, organization_profile_data
    ):
        organization_profile_data["country"] = "XX"
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.has_error("country", code="invalid_choice")

    def test_a_type_and_a_country_may_be_left_empty(
        self, organization, organization_profile_data
    ):
        organization_profile_data["type"] = ""
        organization_profile_data["country"] = ""
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors

    def test_the_organization_itself_is_refused_as_its_parent_with_the_reason_on_the_field(
        self, organization, organization_profile_data
    ):
        organization_profile_data["parent"] = organization.pk
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.has_error("parent", code="parent_loop")
        assert not form.has_error("name")

    def test_an_organization_beneath_it_is_refused_as_its_parent_with_the_reason_on_the_field(
        self, organization, organization_profile_data
    ):
        child = OrganizationFactory(parent=organization)
        grandchild = OrganizationFactory(parent=child)

        for beneath in (child, grandchild):
            organization_profile_data["parent"] = beneath.pk
            form = OrganizationProfileForm(
                organization_profile_data, instance=organization
            )

            assert form.has_error("parent", code="parent_loop")

    def test_a_refused_parent_stores_nothing_and_keeps_what_was_typed_in_the_other_fields(
        self, organization, organization_profile_data
    ):
        before = organization.name
        organization_profile_data["parent"] = organization.pk
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert not form.is_valid()
        assert form["profile"].value() == "Studies the Earth system."
        assert form["city"].value() == "Potsdam"
        organization.refresh_from_db()
        assert organization.name == before

    def test_an_unrelated_organization_and_one_with_children_of_its_own_are_accepted_as_parent(
        self, organization, organization_profile_data
    ):
        unrelated = OrganizationFactory()
        with_children = OrganizationFactory()
        OrganizationFactory(parent=with_children)

        for parent in (unrelated, with_children):
            organization_profile_data["parent"] = parent.pk
            form = OrganizationProfileForm(
                organization_profile_data, instance=organization
            )

            assert form.is_valid(), form.errors

    def test_clearing_the_parent_leaves_the_sub_organizations_as_they_were(
        self, organization_profile_data
    ):
        parent = OrganizationFactory()
        organization = OrganizationFactory(parent=parent)
        child = OrganizationFactory(parent=organization)
        organization_profile_data["parent"] = ""
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        child.refresh_from_db()
        assert organization.parent is None
        assert child.parent == organization
        assert list(organization.sub_organizations.all()) == [child]

    def test_the_form_opens_with_the_stored_parent_chosen(self):
        parent = OrganizationFactory()
        organization = OrganizationFactory(parent=parent)

        form = OrganizationProfileForm(instance=organization)

        assert form["parent"].value() == parent.pk

    def test_a_cleared_logo_is_removed(self, organization_profile_data):
        organization = OrganizationFactory(with_image=True)
        organization_profile_data["image-clear"] = "on"
        form = OrganizationProfileForm(organization_profile_data, instance=organization)

        assert form.is_valid(), form.errors
        form.save()

        organization.refresh_from_db()
        assert not organization.image

    def test_an_image_over_the_size_limit_is_refused_on_the_logo_field(
        self, organization, organization_profile_data, image_upload, monkeypatch
    ):
        monkeypatch.setattr(image_utils, "MAX_IMAGE_UPLOAD_BYTES", 10)
        form = OrganizationProfileForm(
            organization_profile_data, {"image": image_upload()}, instance=organization
        )

        assert form.has_error("image")
        assert not form.has_error("name")


@pytest.fixture(params=["person", "organization"])
def stored_record_failing_validation(request, db, profile_data, organization_profile_data):
    """A record whose stored identifier fails the model's validation, and the form for it.

    The identifier is not a field of either form, so the failure is one the form lacks a field
    for. A malformed value can only be stored by bypassing ``ContributorIdentifier.clean``.
    """
    if request.param == "person":
        record = PersonFactory(name="Before")
        ContributorIdentifier.objects.create(
            related=record, type="ORCID", value="not-an-orcid"
        )
        return SimpleNamespace(
            record=record,
            form_class=PersonProfileForm,
            data={**profile_data, "name": "After"},
        )
    record = OrganizationFactory(name="Before")
    ContributorIdentifier.objects.create(related=record, type="ROR", value="not-a-ror")
    return SimpleNamespace(
        record=record,
        form_class=OrganizationProfileForm,
        data={**organization_profile_data, "name": "After"},
    )


@pytest.mark.django_db
class TestProfileFormsWhenTheStoredRecordFailsValidation:
    def test_the_form_is_invalid_instead_of_raising(
        self, stored_record_failing_validation
    ):
        stored = stored_record_failing_validation
        form = stored.form_class(stored.data, instance=stored.record)

        assert form.is_valid() is False

    def test_the_problem_is_reported_as_a_form_level_error(
        self, stored_record_failing_validation
    ):
        stored = stored_record_failing_validation
        form = stored.form_class(stored.data, instance=stored.record)

        assert form.non_field_errors()
        assert "identifiers" not in form.errors

    def test_no_field_the_form_has_is_blamed(self, stored_record_failing_validation):
        stored = stored_record_failing_validation
        form = stored.form_class(stored.data, instance=stored.record)

        assert set(form.errors) == {"__all__"}

    def test_nothing_is_saved(self, stored_record_failing_validation):
        stored = stored_record_failing_validation
        form = stored.form_class(stored.data, instance=stored.record)

        form.is_valid()

        stored.record.refresh_from_db()
        assert stored.record.name == "Before"

    def test_an_error_on_a_field_the_form_has_still_lands_on_that_field(
        self, stored_record_failing_validation
    ):
        stored = stored_record_failing_validation
        data = {**stored.data, "name": ""}
        form = stored.form_class(data, instance=stored.record)

        assert form.has_error("name", code="required")
        assert form.non_field_errors()


class PersonFormWithoutLanguages(PersonProfileForm):
    class Meta(PersonProfileForm.Meta):
        fields = [f for f in PersonProfileForm.Meta.fields if f != "lang"]


class OrganizationFormWithoutWebsite(OrganizationProfileForm):
    class Meta(OrganizationProfileForm.Meta):
        fields = [f for f in OrganizationProfileForm.Meta.fields if f != "website"]


class OrganizationFormWithoutParent(OrganizationProfileForm):
    class Meta(OrganizationProfileForm.Meta):
        fields = [f for f in OrganizationProfileForm.Meta.fields if f != "parent"]


@pytest.mark.django_db
class TestFormsWithADroppedField:
    """A portal drops a field by leaving it out of ``Meta.fields``, as the guide says it may."""

    def test_a_person_form_without_languages_builds_and_saves(self, profile_data):
        person = PersonFactory(lang=["de"])

        form = PersonFormWithoutLanguages(profile_data, instance=person)

        assert "lang" not in form.fields
        assert form.is_valid(), form.errors
        form.save()
        person.refresh_from_db()
        assert person.name == "Dr. Ada Lovelace"
        assert person.lang == ["de"]

    def test_an_organization_form_without_a_website_builds_and_saves(
        self, organization_profile_data
    ):
        organization = OrganizationFactory(links=["https://example.org/old"])

        form = OrganizationFormWithoutWebsite(
            organization_profile_data, instance=organization
        )

        assert "website" not in form.fields
        assert form.is_valid(), form.errors
        form.save()
        organization.refresh_from_db()
        assert organization.name == "Potsdam Research Institute"
        assert organization.links == [
            "https://example.net/wiki",
            "https://example.org/news",
        ]

    def test_an_organization_form_without_a_website_shows_every_stored_link(self):
        organization = OrganizationFactory(
            links=["https://example.org/first", "https://example.org/second"]
        )

        form = OrganizationFormWithoutWebsite(instance=organization)

        assert form["links"].value() == (
            "https://example.org/first\nhttps://example.org/second"
        )

    def test_an_organization_form_without_a_parent_builds_and_saves(
        self, organization_profile_data
    ):
        parent = OrganizationFactory()
        organization = OrganizationFactory(parent=parent)

        form = OrganizationFormWithoutParent(
            organization_profile_data, instance=organization
        )

        assert "parent" not in form.fields
        assert form.is_valid(), form.errors
        form.save()
        organization.refresh_from_db()
        assert organization.name == "Potsdam Research Institute"
        assert organization.parent == parent


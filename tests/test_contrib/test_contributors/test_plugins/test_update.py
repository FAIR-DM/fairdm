"""Tests for the profile editing page, opened and submitted through the test client.

Who may open it is decided by the model's ``is_editable_by``. These tests check that the page
asks on every request, shows the right form, and stores nothing when it refuses. Nothing here
asserts a sentence, a width or an order of fields.
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from fairdm.contrib.contributors.forms.profile import PersonProfileForm
from fairdm.factories import PersonFactory, ProjectFactory
from fairdm.utils.choices import Visibility


class ExtraFieldPersonForm(PersonProfileForm):
    """A portal's own person form, named in ``FAIRDM_PROFILE_FORMS`` by the tests below."""


def _update_url(contributor):
    return reverse("contributor:overview-update", kwargs={"uuid": contributor.uuid})


def _page(response):
    return BeautifulSoup(response.content.decode(), "html.parser")


@pytest.fixture
def keeper(db):
    """A person with an active account and a profile with something to change."""
    return PersonFactory(
        is_active=True,
        is_claimed=True,
        password="x",
        name="Original Name",
        profile="Original biography.",
        links=["https://example.org/original"],
    )


@pytest.fixture
def stranger(db):
    return PersonFactory(is_active=True, password="x")


@pytest.fixture
def signed_in():
    """A browser signed in as the given person."""

    def sign_in(person):
        browser = Client()
        browser.force_login(person)
        return browser

    return sign_in


def _stored(person):
    person.refresh_from_db()
    return (person.name, person.profile, person.links, person.alternative_names)


@pytest.mark.django_db
class TestPersonUpdate:
    # Scenario 2
    def test_a_save_returns_to_the_overview_and_says_it_was_saved(
        self, signed_in, keeper, profile_data
    ):
        response = signed_in(keeper).post(_update_url(keeper), profile_data)

        assert response.status_code == 302
        assert response.url == keeper.get_absolute_url()
        levels = [m.level for m in get_messages(response.wsgi_request)]
        assert levels == [messages.SUCCESS]

    def test_a_save_stores_every_field(self, signed_in, keeper, profile_data):
        signed_in(keeper).post(_update_url(keeper), profile_data)

        keeper.refresh_from_db()
        assert keeper.name == "Dr. Ada Lovelace"
        assert keeper.alternative_names == ["A. Lovelace", "Augusta Ada King"]
        assert keeper.profile == "Mathematician and writer."
        assert keeper.links == ["https://example.org/ada", "http://example.org/notes"]
        assert keeper.lang == ["en", "fr"]

    def test_a_new_photo_is_stored(self, signed_in, keeper, profile_data, image_upload):
        signed_in(keeper).post(
            _update_url(keeper), {**profile_data, "image": image_upload()}
        )

        keeper.refresh_from_db()
        assert keeper.image

    def test_the_form_opens_with_what_is_stored(self, signed_in, keeper):
        response = signed_in(keeper).get(_update_url(keeper))

        form = response.context["form"]
        assert form["name"].value() == "Original Name"
        assert form["links"].value() == "https://example.org/original"

    # Scenario 4
    def test_a_cleared_name_stores_nothing_and_keeps_what_else_was_typed(
        self, signed_in, keeper, profile_data
    ):
        before = _stored(keeper)

        response = signed_in(keeper).post(
            _update_url(keeper), {**profile_data, "name": ""}
        )

        assert response.status_code == 200
        form = response.context["form"]
        assert form.has_error("name", code="required")
        assert form["profile"].value() == "Mathematician and writer."
        assert form["links"].value() == "https://example.org/ada\nhttp://example.org/notes"
        assert _stored(keeper) == before

    # Scenario 5
    @pytest.mark.parametrize(
        ("field", "value", "code"),
        [
            ("links", "https://example.org/ok\nexample.org/missing-scheme", "invalid_entry"),
            ("lang", ["en", "xx"], "invalid_choice"),
        ],
    )
    def test_a_refused_entry_stores_nothing_and_is_reported_on_its_field(
        self, signed_in, keeper, profile_data, field, value, code
    ):
        before = _stored(keeper)

        response = signed_in(keeper).post(
            _update_url(keeper), {**profile_data, field: value}
        )

        assert response.status_code == 200
        assert response.context["form"].has_error(field, code=code)
        assert _stored(keeper) == before

    def test_a_file_that_is_not_an_image_stores_nothing_and_is_reported_on_the_photo(
        self, signed_in, keeper, profile_data
    ):
        before = _stored(keeper)
        upload = SimpleUploadedFile("notes.txt", b"not an image", "text/plain")

        response = signed_in(keeper).post(
            _update_url(keeper), {**profile_data, "image": upload}
        )

        assert response.status_code == 200
        assert response.context["form"].has_error("image", code="invalid_image")
        assert _stored(keeper) == before

    # Scenario 6
    def test_a_removed_photo_leaves_the_profile_without_one(
        self, signed_in, profile_data
    ):
        person = PersonFactory(
            is_active=True, password="x", with_image=True, name="Has A Photo"
        )

        signed_in(person).post(_update_url(person), {**profile_data, "image-clear": "on"})

        person.refresh_from_db()
        assert not person.image

    # Scenario 11
    def test_opening_the_page_and_leaving_changes_nothing(self, signed_in, keeper):
        before = _stored(keeper)
        modified = keeper.modified

        signed_in(keeper).get(_update_url(keeper))

        assert _stored(keeper) == before
        keeper.refresh_from_db()
        assert keeper.modified == modified

    # Scenario 10
    def test_the_page_offers_no_way_to_change_the_account_or_what_it_does_not_cover(
        self, signed_in, keeper
    ):
        response = signed_in(keeper).get(_update_url(keeper))

        page = _page(response)
        names = {
            control["name"]
            for control in page.select("form [name]")
            if control["name"] != "csrfmiddlewaretoken"
        }
        assert names == {
            "image",
            "image-clear",
            "name",
            "alternative_names",
            "profile",
            "links",
            "lang",
        }
        for forbidden in ("email", "password", "orcid", "affiliations", "roles"):
            assert not any(forbidden in name for name in names)
        assert "is_active" not in names
        assert "is_claimed" not in names

    def test_the_page_links_to_the_account_centre(self, signed_in, keeper):
        response = signed_in(keeper).get(_update_url(keeper))

        hrefs = [a["href"] for a in _page(response).select("a[href]")]
        assert reverse("account-center") in hrefs

    # Scenario 9
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_visitor_is_sent_to_sign_in_and_nothing_is_stored(
        self, keeper, profile_data, method
    ):
        before = _stored(keeper)

        response = getattr(Client(), method)(_update_url(keeper), profile_data)

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert _stored(keeper) == before

    # Scenario 8
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_signed_in_stranger_is_refused_and_nothing_is_stored(
        self, signed_in, keeper, stranger, profile_data, method
    ):
        before = _stored(keeper)

        response = getattr(signed_in(stranger), method)(
            _update_url(keeper), profile_data
        )

        assert response.status_code == 403
        assert _stored(keeper) == before

    def test_a_superuser_who_is_somebody_else_is_refused_too(
        self, signed_in, keeper, profile_data
    ):
        superuser = PersonFactory(
            is_active=True, is_staff=True, is_superuser=True, password="x"
        )
        before = _stored(keeper)

        response = signed_in(superuser).post(_update_url(keeper), profile_data)

        assert response.status_code == 403
        assert _stored(keeper) == before

    def test_a_profile_that_does_not_exist_answers_not_found(self, signed_in, keeper):
        url = _update_url(keeper).replace(keeper.uuid, "cDoesNotExist")

        response = signed_in(keeper).get(url)

        assert response.status_code == 404

    # Scenario 3
    def test_a_changed_name_shows_on_a_record_the_person_is_credited_on(
        self, signed_in, keeper, profile_data
    ):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        keeper.add_to(project, roles=["Creator"])

        signed_in(keeper).post(_update_url(keeper), profile_data)

        response = Client().get(project.get_absolute_url())
        assert "Dr. Ada Lovelace" in response.content.decode()
        assert "Original Name" not in response.content.decode()


@pytest.mark.django_db
class TestProfileFormsSetting:
    def test_the_shipped_form_is_used_when_the_setting_is_absent(
        self, signed_in, keeper, settings
    ):
        del settings.FAIRDM_PROFILE_FORMS

        response = signed_in(keeper).get(_update_url(keeper))

        assert type(response.context["form"]) is PersonProfileForm

    def test_the_shipped_form_is_used_when_the_setting_names_only_the_other_kind(
        self, signed_in, keeper, settings
    ):
        settings.FAIRDM_PROFILE_FORMS = {
            "organization": "tests.not_imported.OrganizationForm"
        }

        response = signed_in(keeper).get(_update_url(keeper))

        assert type(response.context["form"]) is PersonProfileForm

    def test_the_portals_own_form_is_used_when_the_setting_names_one(
        self, signed_in, keeper, settings
    ):
        settings.FAIRDM_PROFILE_FORMS = {
            "person": f"{__name__}.ExtraFieldPersonForm",
        }

        response = signed_in(keeper).get(_update_url(keeper))

        assert type(response.context["form"]) is ExtraFieldPersonForm

    def test_the_shipped_setting_names_the_shipped_person_form(self, settings):
        assert settings.FAIRDM_PROFILE_FORMS["person"] == (
            "fairdm.contrib.contributors.forms.profile.PersonProfileForm"
        )

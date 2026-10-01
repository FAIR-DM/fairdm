"""Tests for the profile editing page, opened and submitted through the test client.

Who may open it is decided by the model's ``is_editable_by``. These tests check that the page
asks on every request, shows the right form, and stores nothing when it refuses. Nothing here
asserts a sentence, a width or an order of fields.
"""

from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.forms.profile import (
    OrganizationProfileForm,
    PersonProfileForm,
)
from fairdm.contrib.contributors.models import (
    Affiliation,
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.factories import (
    AffiliationFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.portal_roles import PortalRoles
from fairdm.utils.choices import Visibility


class ExtraNamesPersonForm(PersonProfileForm):
    """The portal form the contributors guide shows, named in ``FAIRDM_PROFILE_FORMS`` below."""

    class Meta(PersonProfileForm.Meta):
        fields = [*PersonProfileForm.Meta.fields, "first_name", "last_name"]


class PortalOrganizationForm(OrganizationProfileForm):
    """A portal's own organization form, named in ``FAIRDM_PROFILE_FORMS`` below."""


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

    def test_a_posted_value_for_a_field_the_page_does_not_carry_is_ignored(
        self, signed_in, keeper, profile_data
    ):
        email = keeper.email

        response = signed_in(keeper).post(
            _update_url(keeper),
            {
                **profile_data,
                "email": "taken.over@example.com",
                "is_active": "",
                "is_claimed": "",
                "is_superuser": "on",
                "is_staff": "on",
                "first_name": "Replaced",
                "password": "replaced",
            },
        )

        assert response.status_code == 302
        stored = Person.objects.get(pk=keeper.pk)
        assert stored.name == profile_data["name"]
        assert stored.email.lower() == email.lower()
        assert stored.is_active
        assert stored.is_claimed
        assert not stored.is_superuser
        assert not stored.is_staff
        assert stored.first_name == keeper.first_name
        assert stored.password == keeper.password

    # Scenario 10
    def test_the_page_offers_no_way_to_change_the_account_or_what_it_does_not_cover(
        self, signed_in
    ):
        person = PersonFactory(is_active=True, password="x", with_image=True)

        response = signed_in(person).get(_update_url(person))

        form = _page(response).select_one(f"form[action='{_update_url(person)}']")
        names = {
            control["name"]
            for control in form.select("[name]")
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
            "person": f"{__name__}.ExtraNamesPersonForm",
        }

        response = signed_in(keeper).get(_update_url(keeper))

        assert type(response.context["form"]) is ExtraNamesPersonForm

    def test_a_field_the_portals_form_adds_is_saved_with_the_rest(
        self, signed_in, keeper, profile_data, settings
    ):
        settings.FAIRDM_PROFILE_FORMS = {
            "person": f"{__name__}.ExtraNamesPersonForm",
        }

        signed_in(keeper).post(
            _update_url(keeper),
            {**profile_data, "first_name": "Ada", "last_name": "Lovelace"},
        )

        keeper.refresh_from_db()
        assert (keeper.first_name, keeper.last_name) == ("Ada", "Lovelace")
        assert keeper.name == "Dr. Ada Lovelace"

    def test_the_shipped_setting_names_the_shipped_person_form(self, settings):
        assert settings.FAIRDM_PROFILE_FORMS["person"] == (
            "fairdm.contrib.contributors.forms.profile.PersonProfileForm"
        )

    def test_the_shipped_setting_names_the_shipped_organization_form(self, settings):
        assert settings.FAIRDM_PROFILE_FORMS["organization"] == (
            "fairdm.contrib.contributors.forms.profile.OrganizationProfileForm"
        )

    def test_the_shipped_organization_form_is_used_when_the_setting_is_absent(
        self, signed_in, kept_organization, settings
    ):
        del settings.FAIRDM_PROFILE_FORMS

        response = signed_in(kept_organization.owner).get(
            _update_url(kept_organization.organization)
        )

        assert type(response.context["form"]) is OrganizationProfileForm

    def test_the_portals_own_organization_form_is_used_when_the_setting_names_one(
        self, signed_in, kept_organization, settings
    ):
        settings.FAIRDM_PROFILE_FORMS = {
            "organization": f"{__name__}.PortalOrganizationForm",
        }

        response = signed_in(kept_organization.owner).get(
            _update_url(kept_organization.organization)
        )

        assert type(response.context["form"]) is PortalOrganizationForm


def _organization_stored(organization):
    organization.refresh_from_db()
    return (
        organization.name,
        organization.profile,
        organization.links,
        organization.city,
        organization.parent_id,
    )


def _join(organization, type, **kwargs):
    person = PersonFactory(is_active=True, is_claimed=True, password="x")
    AffiliationFactory(person=person, organization=organization, type=type, **kwargs)
    return person


@pytest.fixture
def kept_organization(db):
    """An organization with something to change and one of each kind of person around it."""
    organization = OrganizationFactory(
        name="Original Institute",
        profile="Original description.",
        links=["https://example.org/original"],
        city="Berlin",
    )
    deactivated = _join(organization, Affiliation.MembershipType.ADMIN)
    deactivated.is_active = False
    deactivated.save()
    curator = PersonFactory(is_active=True, password="x")
    curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
    return SimpleNamespace(
        organization=organization,
        owner=_join(organization, Affiliation.MembershipType.OWNER),
        admin=_join(organization, Affiliation.MembershipType.ADMIN),
        member=_join(organization, Affiliation.MembershipType.MEMBER),
        former_admin=_join(
            organization,
            Affiliation.MembershipType.ADMIN,
            start_date="2010",
            end_date="2014",
        ),
        deactivated_admin=deactivated,
        stranger=PersonFactory(is_active=True, password="x"),
        curator=curator,
        superuser=PersonFactory(
            is_active=True, is_staff=True, is_superuser=True, password="x"
        ),
    )


@pytest.mark.django_db
class TestOrganizationUpdate:
    # Scenario 2
    @pytest.mark.parametrize("who", ["owner", "admin"])
    def test_a_save_returns_to_the_overview_and_says_it_was_saved(
        self, signed_in, kept_organization, organization_profile_data, who
    ):
        organization = kept_organization.organization

        response = signed_in(getattr(kept_organization, who)).post(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 302
        assert response.url == organization.get_absolute_url()
        levels = [m.level for m in get_messages(response.wsgi_request)]
        assert levels == [messages.SUCCESS]

    @pytest.mark.parametrize("who", ["owner", "admin"])
    def test_a_save_stores_every_field_and_the_overview_shows_them(
        self, signed_in, kept_organization, organization_profile_data, image_upload, who
    ):
        organization = kept_organization.organization
        parent = OrganizationFactory(name="Parent Institute")
        browser = signed_in(getattr(kept_organization, who))

        browser.post(
            _update_url(organization),
            {
                **organization_profile_data,
                "parent": parent.pk,
                "image": image_upload(),
            },
        )

        organization.refresh_from_db()
        assert organization.name == "Potsdam Research Institute"
        assert organization.alternative_names == ["PRI", "Institut Potsdam"]
        assert organization.type == "education"
        assert organization.parent == parent
        assert organization.city == "Potsdam"
        assert organization.country == "DE"
        assert organization.profile == "Studies the Earth system."
        assert organization.links[0] == "https://example.org"
        assert organization.image
        shown = browser.get(organization.get_absolute_url()).context["organization"]
        assert shown.name == "Potsdam Research Institute"

    def test_the_form_is_the_organization_form_opened_with_what_is_stored(
        self, signed_in, kept_organization
    ):
        organization = kept_organization.organization

        response = signed_in(kept_organization.owner).get(_update_url(organization))

        form = response.context["form"]
        assert type(form) is OrganizationProfileForm
        assert form["name"].value() == "Original Institute"
        assert form["website"].value() == "https://example.org/original"
        assert form["city"].value() == "Berlin"

    # Scenario 3
    def test_a_changed_name_shows_on_a_project_the_organization_owns_and_on_a_members_profile(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        project = ProjectFactory(owner=organization, visibility=Visibility.PUBLIC)
        member = kept_organization.member
        Affiliation.objects.filter(person=member, organization=organization).update(
            is_primary=True
        )

        signed_in(kept_organization.owner).post(
            _update_url(organization), organization_profile_data
        )

        on_project = Client().get(project.get_absolute_url()).content.decode()
        on_member = Client().get(member.get_absolute_url()).content.decode()
        assert "Potsdam Research Institute" in on_project
        assert "Original Institute" not in on_project
        assert "Potsdam Research Institute" in on_member
        assert "Original Institute" not in on_member

    # Scenario 4
    @pytest.mark.parametrize("beneath", ["itself", "child", "grandchild"])
    def test_a_parent_that_would_form_a_loop_stores_nothing_and_is_reported_on_the_field(
        self, signed_in, kept_organization, organization_profile_data, beneath
    ):
        organization = kept_organization.organization
        child = OrganizationFactory(parent=organization)
        grandchild = OrganizationFactory(parent=child)
        chosen = {"itself": organization, "child": child, "grandchild": grandchild}[
            beneath
        ]
        before = _organization_stored(organization)

        response = signed_in(kept_organization.owner).post(
            _update_url(organization), {**organization_profile_data, "parent": chosen.pk}
        )

        assert response.status_code == 200
        assert response.context["form"].has_error("parent", code="parent_loop")
        assert _organization_stored(organization) == before

    # Scenario 5
    def test_clearing_the_parent_makes_the_organization_part_of_nothing_and_leaves_its_children(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        organization.parent = OrganizationFactory()
        organization.save()
        child = OrganizationFactory(parent=organization)

        signed_in(kept_organization.owner).post(
            _update_url(organization), {**organization_profile_data, "parent": ""}
        )

        organization.refresh_from_db()
        child.refresh_from_db()
        assert organization.parent is None
        assert child.parent == organization

    # Scenario 6
    def test_a_cleared_name_stores_nothing_and_keeps_what_else_was_typed(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = signed_in(kept_organization.owner).post(
            _update_url(organization), {**organization_profile_data, "name": ""}
        )

        assert response.status_code == 200
        form = response.context["form"]
        assert form.has_error("name", code="required")
        assert form["profile"].value() == "Studies the Earth system."
        assert form["city"].value() == "Potsdam"
        assert _organization_stored(organization) == before

    @pytest.mark.parametrize(
        ("field", "value", "code"),
        [
            ("type", "spaceship", "invalid_choice"),
            ("country", "XX", "invalid_choice"),
            ("links", "https://example.org/ok\nnot a link", "invalid_entry"),
        ],
    )
    def test_a_refused_entry_stores_nothing_and_is_reported_on_its_field(
        self, signed_in, kept_organization, organization_profile_data, field, value, code
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = signed_in(kept_organization.owner).post(
            _update_url(organization), {**organization_profile_data, field: value}
        )

        assert response.status_code == 200
        assert response.context["form"].has_error(field, code=code)
        assert _organization_stored(organization) == before

    def test_a_removed_logo_leaves_the_organization_without_one(
        self, signed_in, organization_profile_data
    ):
        organization = OrganizationFactory(with_image=True)
        owner = _join(organization, Affiliation.MembershipType.OWNER)

        signed_in(owner).post(
            _update_url(organization),
            {**organization_profile_data, "image-clear": "on"},
        )

        organization.refresh_from_db()
        assert not organization.image

    # Scenario 7
    def test_a_field_filled_in_from_the_checklist_is_counted_as_in_place_after_the_save(
        self, signed_in, organization_profile_data, image_upload
    ):
        organization = OrganizationFactory(
            profile="", type="", city="", country="", links=[], location=None
        )
        owner = _join(organization, Affiliation.MembershipType.OWNER)
        browser = signed_in(owner)
        before = browser.get(organization.get_absolute_url()).context["readiness"]

        browser.post(
            _update_url(organization),
            {**organization_profile_data, "image": image_upload()},
        )
        after = browser.get(organization.get_absolute_url()).context["readiness"]

        done_before = [item["done"] for item in before["items"]]
        done_after = [item["done"] for item in after["items"]]
        # Every item but the ROR identifier, which the page does not edit.
        assert done_before[1:] == [False] * 5
        assert done_after[1:] == [True] * 5
        assert done_after[0] == done_before[0]

    # Scenario 8
    @pytest.mark.parametrize("who", ["member", "stranger", "curator", "superuser"])
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_someone_who_does_not_keep_the_record_is_refused_and_nothing_is_stored(
        self, signed_in, kept_organization, organization_profile_data, who, method
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = getattr(signed_in(getattr(kept_organization, who)), method)(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 403
        assert _organization_stored(organization) == before

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_visitor_is_sent_to_sign_in_and_nothing_is_stored(
        self, kept_organization, organization_profile_data, method
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = getattr(Client(), method)(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert _organization_stored(organization) == before

    # Scenario 9
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_an_administrator_whose_affiliation_has_ended_is_refused_and_nothing_is_stored(
        self, signed_in, kept_organization, organization_profile_data, method
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = getattr(signed_in(kept_organization.former_admin), method)(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 403
        assert _organization_stored(organization) == before

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_deactivated_administrator_is_signed_out_and_nothing_is_stored(
        self, signed_in, kept_organization, organization_profile_data, method
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)

        response = getattr(signed_in(kept_organization.deactivated_admin), method)(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 302
        assert response.url.startswith(reverse("account_login"))
        assert _organization_stored(organization) == before

    # Scenario 10
    def test_the_page_offers_no_way_to_change_the_ror_identifier_the_members_or_the_owner(
        self, signed_in, kept_organization
    ):
        organization = kept_organization.organization

        response = signed_in(kept_organization.owner).get(_update_url(organization))

        form = _page(response).select_one(f"form[action='{_update_url(organization)}']")
        names = {
            control["name"]
            for control in form.select("[name]")
            if control["name"] != "csrfmiddlewaretoken"
        }
        assert names == {
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

    def test_a_posted_value_for_a_field_the_page_does_not_carry_is_ignored(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        members_before = set(organization.affiliations.values_list("pk", flat=True))
        synced_before = organization.synced_data

        response = signed_in(kept_organization.owner).post(
            _update_url(organization),
            {
                **organization_profile_data,
                "synced_data": '{"id": "https://ror.org/000000000"}',
                "location": "1",
                "uuid": "c-replaced",
                "identifiers": "x",
                "members": "x",
            },
        )

        assert response.status_code == 302
        stored = Organization.objects.get(pk=organization.pk)
        assert stored.name == organization_profile_data["name"]
        assert stored.synced_data == synced_before
        assert stored.location_id is None
        assert stored.uuid == organization.uuid
        assert not stored.identifiers.exists()
        assert set(stored.affiliations.values_list("pk", flat=True)) == members_before

    # Scenario 11
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_an_organization_nobody_keeps_is_refused_to_anyone_who_is_not_a_community_manager(
        self, signed_in, organization_profile_data, method
    ):
        organization = OrganizationFactory(name="Nobody's Institute")
        member = _join(organization, Affiliation.MembershipType.MEMBER)
        curator = PersonFactory(is_active=True, password="x")
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        superuser = PersonFactory(
            is_active=True, is_staff=True, is_superuser=True, password="x"
        )
        before = _organization_stored(organization)

        for user in (member, curator, superuser):
            response = getattr(signed_in(user), method)(
                _update_url(organization), organization_profile_data
            )

            assert response.status_code == 403
        assert _organization_stored(organization) == before

    def test_opening_the_page_and_leaving_changes_nothing(
        self, signed_in, kept_organization
    ):
        organization = kept_organization.organization
        before = _organization_stored(organization)
        modified = organization.modified

        signed_in(kept_organization.owner).get(_update_url(organization))

        assert _organization_stored(organization) == before
        organization.refresh_from_db()
        assert organization.modified == modified


@pytest.mark.django_db
class TestReturnToTheOverview:
    def test_the_page_a_save_returns_to_opens_and_shows_the_saved_message_for_a_person(
        self, signed_in, keeper, profile_data
    ):
        response = signed_in(keeper).post(
            _update_url(keeper), profile_data, follow=True
        )

        assert response.status_code == 200
        assert response.redirect_chain == [(keeper.get_absolute_url(), 302)]
        assert [m.level for m in response.context["messages"]] == [messages.SUCCESS]

    def test_the_page_a_save_returns_to_opens_and_shows_the_saved_message_for_an_organization(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization

        response = signed_in(kept_organization.owner).post(
            _update_url(organization), organization_profile_data, follow=True
        )

        assert response.status_code == 200
        assert response.redirect_chain == [(organization.get_absolute_url(), 302)]
        assert [m.level for m in response.context["messages"]] == [messages.SUCCESS]


@pytest.mark.django_db
class TestStoredRecordThatFailsValidation:
    def test_a_person_whose_stored_identifier_is_malformed_gets_a_form_error_not_a_server_error(
        self, signed_in, keeper, profile_data
    ):
        ContributorIdentifier.objects.create(
            related=keeper, type="ORCID", value="not-an-orcid"
        )
        before = _stored(keeper)

        response = signed_in(keeper).post(_update_url(keeper), profile_data)

        assert response.status_code == 200
        assert response.context["form"].non_field_errors()
        assert _stored(keeper) == before

    def test_an_organization_whose_stored_identifier_is_malformed_gets_a_form_error_not_a_server_error(
        self, signed_in, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        ContributorIdentifier.objects.create(
            related=organization, type="ROR", value="not-a-ror"
        )
        before = _organization_stored(organization)

        response = signed_in(kept_organization.owner).post(
            _update_url(organization), organization_profile_data
        )

        assert response.status_code == 200
        assert response.context["form"].non_field_errors()
        assert _organization_stored(organization) == before


def _account_state(person):
    person.refresh_from_db()
    return (
        person.is_active,
        person.is_claimed,
        person.last_login,
        person.email,
        person.account_state,
    )


def _unclaimed():
    return PersonFactory(
        name="Unclaimed Person", is_active=True, is_claimed=False, email=None
    )


def _invited():
    return PersonFactory(
        name="Invited Person",
        email="invited@example.org",
        is_active=True,
        is_claimed=False,
    )


def _inactive():
    return PersonFactory(
        name="Inactive Person",
        email="inactive@example.org",
        is_active=False,
        is_claimed=True,
        password="x",
        last_login=timezone.now(),
    )


@pytest.mark.django_db
class TestCommunityManagerUpdate:
    @pytest.mark.parametrize("make", [_unclaimed, _invited, _inactive])
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_community_manager_may_open_and_save_a_person_who_has_no_active_account(
        self, signed_in, community_manager, profile_data, make, method
    ):
        person = make()

        response = getattr(signed_in(community_manager), method)(
            _update_url(person), profile_data
        )

        assert response.status_code == (200 if method == "get" else 302)

    @pytest.mark.parametrize("make", [_unclaimed, _invited, _inactive])
    def test_a_save_stores_every_field_and_the_profile_shows_it(
        self, signed_in, community_manager, profile_data, make
    ):
        person = make()

        response = signed_in(community_manager).post(
            _update_url(person), profile_data, follow=True
        )

        person.refresh_from_db()
        assert response.status_code == 200
        assert (person.name, person.profile, person.links, person.lang) == (
            "Dr. Ada Lovelace",
            "Mathematician and writer.",
            ["https://example.org/ada", "http://example.org/notes"],
            ["en", "fr"],
        )
        assert response.context["person"] == person

    # FR-009
    def test_the_form_is_the_one_the_keeper_gets_with_the_same_fields(
        self, signed_in, community_manager, keeper
    ):
        own = signed_in(keeper).get(_update_url(keeper)).context["form"]

        theirs = (
            signed_in(community_manager).get(_update_url(_unclaimed())).context["form"]
        )

        assert type(theirs) is type(own)
        assert list(theirs.fields) == list(own.fields)

    def test_the_form_for_an_organization_is_the_one_its_owner_gets(
        self, signed_in, community_manager, kept_organization
    ):
        organization = kept_organization.organization
        own = signed_in(kept_organization.owner).get(_update_url(organization))

        theirs = signed_in(community_manager).get(_update_url(organization))

        assert type(theirs.context["form"]) is type(own.context["form"])
        assert list(theirs.context["form"].fields) == list(own.context["form"].fields)

    # Scenario 1, FR-020
    def test_saving_an_unclaimed_profile_leaves_it_unclaimed(
        self, signed_in, community_manager, profile_data
    ):
        person = _invited()
        before = _account_state(person)

        signed_in(community_manager).post(_update_url(person), profile_data)

        assert _account_state(person) == before
        assert person.account_state == AccountState.INVITED

    # Scenario 3, FR-020
    def test_saving_an_inactive_profile_leaves_the_account_inactive(
        self, signed_in, community_manager, profile_data
    ):
        person = _inactive()
        before = _account_state(person)

        signed_in(community_manager).post(_update_url(person), profile_data)

        assert _account_state(person) == before
        assert person.is_active is False

    # Scenario 4
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_person_with_an_active_account_is_refused_and_nothing_is_stored(
        self, signed_in, community_manager, keeper, profile_data, method
    ):
        before = _stored(keeper)

        response = getattr(signed_in(community_manager), method)(
            _update_url(keeper), profile_data
        )

        assert response.status_code == 403
        assert _stored(keeper) == before

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_an_active_account_that_signed_in_without_being_marked_claimed_is_refused(
        self, signed_in, community_manager, profile_data, method
    ):
        person = PersonFactory(
            name="Superuser Made",
            is_active=True,
            is_claimed=False,
            password="x",
            last_login=timezone.now(),
        )
        before = _stored(person)

        response = getattr(signed_in(community_manager), method)(
            _update_url(person), profile_data
        )

        assert response.status_code == 403
        assert _stored(person) == before

    # Scenario 5
    def test_a_profile_claimed_after_the_page_was_opened_refuses_the_save(
        self, signed_in, community_manager, profile_data
    ):
        person = _invited()
        browser = signed_in(community_manager)
        assert browser.get(_update_url(person)).status_code == 200
        before = _stored(person)
        person.is_claimed = True
        person.last_login = timezone.now()
        person.save()

        response = browser.post(_update_url(person), profile_data)

        assert response.status_code == 403
        assert _stored(person) == before

    def test_an_account_made_active_after_the_page_was_opened_refuses_the_save(
        self, signed_in, community_manager, profile_data
    ):
        person = _inactive()
        browser = signed_in(community_manager)
        assert browser.get(_update_url(person)).status_code == 200
        before = _stored(person)
        person.is_active = True
        person.save()

        response = browser.post(_update_url(person), profile_data)

        assert response.status_code == 403
        assert _stored(person) == before

    # Scenario 6
    def test_after_reactivation_the_person_edits_and_sees_the_community_managers_changes(
        self, signed_in, community_manager, profile_data
    ):
        person = _inactive()
        signed_in(community_manager).post(_update_url(person), profile_data)
        Person.objects.filter(pk=person.pk).update(is_active=True)
        person.refresh_from_db()

        own = signed_in(person)
        page = own.get(_update_url(person))
        saved = own.post(_update_url(person), {**profile_data, "name": "Back Again"})

        assert page.status_code == 200
        assert page.context["form"]["profile"].value() == "Mathematician and writer."
        assert saved.status_code == 302
        person.refresh_from_db()
        assert person.name == "Back Again"
        assert person.profile == "Mathematician and writer."

    def test_after_reactivation_a_community_manager_is_refused(
        self, signed_in, community_manager, profile_data
    ):
        person = _inactive()
        person.is_active = True
        person.save()
        before = _stored(person)

        for method in ("get", "post"):
            response = getattr(signed_in(community_manager), method)(
                _update_url(person), profile_data
            )

            assert response.status_code == 403
        assert _stored(person) == before

    # Scenario 7
    def test_saving_an_organization_leaves_its_affiliations_unchanged(
        self, signed_in, community_manager, kept_organization, organization_profile_data
    ):
        organization = kept_organization.organization
        affiliations = list(
            organization.affiliations.order_by("pk").values_list(
                "pk", "person_id", "type", "end_date"
            )
        )

        response = signed_in(community_manager).post(
            _update_url(organization), organization_profile_data
        )

        organization.refresh_from_db()
        assert response.status_code == 302
        assert organization.name == "Potsdam Research Institute"
        assert organization.city == "Potsdam"
        assert (
            list(
                organization.affiliations.order_by("pk").values_list(
                    "pk", "person_id", "type", "end_date"
                )
            )
            == affiliations
        )

    def test_an_organization_whose_ror_is_stored_as_the_full_address_saves(
        self, signed_in, community_manager, organization_profile_data
    ):
        organization = OrganizationFactory(name="Created From ROR")
        ContributorIdentifier.objects.create(
            related=organization, type="ROR", value="https://ror.org/02nr0ka47"
        )

        response = signed_in(community_manager).post(
            _update_url(organization), organization_profile_data
        )

        organization.refresh_from_db()
        assert response.status_code == 302
        assert organization.name == "Potsdam Research Institute"

    def test_an_organization_nobody_keeps_opens_and_saves(
        self, signed_in, community_manager, organization_profile_data
    ):
        organization = OrganizationFactory(name="Nobody's Institute")

        opened = signed_in(community_manager).get(_update_url(organization))
        saved = signed_in(community_manager).post(
            _update_url(organization), organization_profile_data
        )

        assert opened.status_code == 200
        assert saved.status_code == 302
        organization.refresh_from_db()
        assert organization.name == "Potsdam Research Institute"
        assert not organization.affiliations.exists()

    # Scenario 8
    @pytest.mark.parametrize("make", [_unclaimed, _inactive])
    def test_nothing_on_a_corrected_profile_names_the_community_manager(
        self, signed_in, community_manager, profile_data, make
    ):
        community_manager.name = "Zebulon Quillfeather"
        community_manager.email = "zebulon@example.org"
        community_manager.save()
        person = make()

        response = signed_in(community_manager).post(
            _update_url(person), profile_data, follow=True
        )
        visitor = Client().get(person.get_absolute_url()).content.decode()

        assert response.status_code == 200
        assert "Zebulon" not in visitor
        assert "zebulon@example.org" not in visitor

    # Scenario 9
    @pytest.mark.parametrize("role", ["Data Curator", "Developer"])
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_data_curator_or_developer_is_refused_a_person_and_an_organization(
        self, signed_in, profile_data, organization_profile_data, role, method
    ):
        holder = PersonFactory(is_active=True, password="x")
        holder.groups.add(Group.objects.get(name=role))
        organization = OrganizationFactory(name="Nobody's Institute")
        person = _unclaimed()
        person_before = _stored(person)
        organization_before = _organization_stored(organization)

        for contributor, data in (
            (person, profile_data),
            (organization, organization_profile_data),
        ):
            response = getattr(signed_in(holder), method)(
                _update_url(contributor), data
            )

            assert response.status_code == 403
        assert _stored(person) == person_before
        assert _organization_stored(organization) == organization_before

    # Scenario 10
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_someone_removed_from_the_role_is_refused(
        self, signed_in, community_manager, profile_data, method
    ):
        person = _unclaimed()
        before = _stored(person)
        community_manager.groups.clear()

        response = getattr(signed_in(community_manager), method)(
            _update_url(person), profile_data
        )

        assert response.status_code == 403
        assert _stored(person) == before

    def test_a_role_removed_after_the_page_was_opened_refuses_the_save(
        self, signed_in, community_manager, profile_data
    ):
        person = _unclaimed()
        browser = signed_in(community_manager)
        assert browser.get(_update_url(person)).status_code == 200
        before = _stored(person)
        community_manager.groups.clear()

        response = browser.post(_update_url(person), profile_data)

        assert response.status_code == 403
        assert _stored(person) == before

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_profile_that_does_not_exist_answers_not_found(
        self, signed_in, community_manager, profile_data, method
    ):
        person = _unclaimed()
        url = _update_url(person)
        person.delete()

        response = getattr(signed_in(community_manager), method)(url, profile_data)

        assert response.status_code == 404

    def test_the_line_about_where_the_account_is_managed_is_not_shown_to_a_community_manager(
        self, signed_in, community_manager, keeper
    ):
        own = signed_in(keeper).get(_update_url(keeper))
        theirs = signed_in(community_manager).get(_update_url(_unclaimed()))

        centre = reverse("account-center")
        assert _page(own).select(f"[role=alert] a[href='{centre}']")
        assert not _page(theirs).select(f"[role=alert] a[href='{centre}']")


ACCOUNTS = {
    "owner": "regular.user@example.com",
    "administrator": "admin.user@example.com",
    "member": "member.user@example.com",
    "former_administrator": "former-admin.user@example.com",
    "community_manager": "community-manager.user@example.com",
    "data_curator": "data-curator.user@example.com",
    "staff": "staff.user@example.com",
    "superuser": "super.user@example.com",
}


@pytest.fixture
def world(db):
    """The seeded accounts, one of each kind of profile and the organizations they relate to."""
    call_command("seed_profiles", verbosity=0)
    accounts = {key: Person.objects.get(email=email) for key, email in ACCOUNTS.items()}
    seeded = Person.objects.filter(config__seed="profiles")
    return SimpleNamespace(
        accounts=accounts,
        people={
            "active_other": seeded.filter(
                is_active=True, is_claimed=True, first_name="Anna"
            ).get(),
            "unclaimed": next(
                p for p in seeded if p.account_state == AccountState.GHOST
            ),
            "invited": PersonFactory(
                name="Invited Person",
                email="invited@example.org",
                is_active=True,
                is_claimed=False,
            ),
            "inactive": seeded.get(is_active=False),
            "signed_in_unmarked": PersonFactory(
                name="Superuser Made",
                is_active=True,
                is_claimed=False,
                password="x",
                last_login=timezone.now(),
            ),
        },
        organizations={
            "owned": Organization.objects.get(
                affiliations__person=accounts["owner"],
                affiliations__type=Affiliation.MembershipType.OWNER,
            ),
            "nobody_keeps": Organization.objects.get(
                name="Rhine Graben Geothermal Working Group"
            ),
            "other": Organization.objects.get(name="Karlsruhe Institute of Technology"),
        },
    )


def _who_may_edit(account, profile_key):
    """FR-001 to FR-003a, written out for the seeded accounts."""
    if profile_key == "own":
        return account != "visitor"
    if profile_key in ("unclaimed", "invited", "inactive"):
        return account == "community_manager"
    if profile_key in ("active_other", "signed_in_unmarked"):
        return False
    if profile_key == "owned":
        return account in ("owner", "administrator", "community_manager")
    return account == "community_manager"


def _profiles(world, account):
    """Every profile the table asks about, for one account, as ``(key, contributor)``."""
    profiles = list(world.people.items()) + list(world.organizations.items())
    if account != "visitor":
        profiles.append(("own", world.accounts[account]))
    return profiles


@pytest.mark.django_db
class TestWhoMayEdit:
    """SC-003: every seeded account against every kind of profile."""

    @pytest.mark.parametrize("method", ["get", "post"])
    def test_the_editing_page_opens_exactly_where_the_rules_say_and_is_refused_everywhere_else(
        self, world, profile_data, organization_profile_data, method
    ):
        wrong = []
        for account in ("visitor", *ACCOUNTS):
            browser = Client()
            if account != "visitor":
                browser.force_login(world.accounts[account])
            for key, contributor in _profiles(world, account):
                is_person = isinstance(contributor, Person)
                data = profile_data if is_person else organization_profile_data
                stored = _stored if is_person else _organization_stored
                before = stored(contributor)

                response = getattr(browser, method)(_update_url(contributor), data)

                opened = 200 if method == "get" else 302
                refused = 302 if account == "visitor" else 403
                expected = opened if _who_may_edit(account, key) else refused
                if response.status_code != expected:
                    wrong.append((account, key, response.status_code, expected))
                elif expected == refused and stored(contributor) != before:
                    wrong.append((account, key, "stored something", expected))

        assert wrong == []

    def test_a_visitor_is_sent_to_sign_in(self, world):
        for contributor in (*world.people.values(), *world.organizations.values()):
            response = Client().get(_update_url(contributor))

            assert response.url.startswith(reverse("account_login"))


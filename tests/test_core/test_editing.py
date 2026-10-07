"""Tests for the editing pages every record shares: edit details and descriptions.

Each page is requested through the test client on a project, a dataset, and a sample and a
measurement of the demo portal's registered types, so a registered type is what is tested.
"""

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.messages import SUCCESS, get_messages
from django.shortcuts import resolve_url
from django.test import Client
from django.urls import NoReverseMatch, reverse

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset, DatasetDescription
from fairdm.core.measurement.models import Measurement, MeasurementDescription
from fairdm.core.project.models import Project, ProjectDescription
from fairdm.core.sample.models import Sample, SampleDescription
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility

KINDS = ("project", "dataset", "sample", "measurement")
PAGES = ("edit", "descriptions")
DESCRIPTION_MODELS = {
    "project": ProjectDescription,
    "dataset": DatasetDescription,
    "sample": SampleDescription,
    "measurement": MeasurementDescription,
}
CORE_MODELS = {
    "project": Project,
    "dataset": Dataset,
    "sample": Sample,
    "measurement": Measurement,
}
# The field a refused value is entered in, the value, and a second field whose value must survive.
INVALID = {
    "project": ("name", "", "status"),
    "dataset": ("name", "", "license"),
    "sample": ("rock_type", "", "mineral_content"),
    "measurement": ("integer_field", "not a number", "char_field"),
}


class Case:
    """One record of a kind, with the addresses of its pages."""

    def __init__(self, kind, record):
        self.kind = kind
        self.record = record

    def url(self, page):
        """Return the address of one of the record's pages."""
        return reverse(f"{self.kind}:{page}", kwargs={"uuid": self.record.uuid})

    @property
    def own_url(self):
        """Return the address of the record's own page."""
        return self.record.get_absolute_url()


@pytest.fixture
def make_case(db):
    """Build a record of a kind inside a project, a dataset and a sample of the same state."""

    def build(kind, *, public=True):
        visibility = Visibility.PUBLIC if public else Visibility.PRIVATE
        project = ProjectFactory(visibility=visibility)
        dataset = DatasetFactory(
            project=project, visibility=visibility, published=public
        )
        record = {"project": project, "dataset": dataset}.get(kind)
        if record is None:
            sample = RockSampleFactory(
                dataset=dataset, name="Basalt", rock_type="basalt"
            )
            record = (
                sample
                if kind == "sample"
                else ExampleMeasurementFactory(
                    dataset=dataset, sample=sample, char_field="a note"
                )
            )
        return Case(kind, record)

    return build


@pytest.fixture
def person_at(db):
    """Make a person who can sign in, credited on a record at a level (none for no credit)."""

    def make(case=None, level=None):
        person = PersonFactory(is_active=True, is_claimed=True, password="x")
        if level is not None:
            ContributionFactory(
                content_object=case.record, contributor=person, level=level
            )
        return person

    return make


def browser_as(person=None):
    """Return a test client signed in as a person, or a visitor's client."""
    client = Client()
    if person is not None:
        client.force_login(person)
    return client


def soup_of(response):
    """Parse a response's HTML."""
    return BeautifulSoup(response.content.decode(), "html.parser")


def form_payload(form):
    """Collect what a browser would submit from a rendered form, as the form stands."""
    data = {}
    for control in form.select("input, select, textarea"):
        name = control.get("name")
        if not name:
            continue
        if control.name == "input":
            kind = control.get("type", "text")
            if kind in {"submit", "button", "file", "image", "reset"}:
                continue
            if kind in {"checkbox", "radio"}:
                if control.has_attr("checked"):
                    data[name] = control.get("value", "on")
                continue
            data[name] = control.get("value", "")
        elif control.name == "select":
            chosen = control.select("option[selected]")
            if control.has_attr("multiple"):
                data[name] = [option.get("value", "") for option in chosen]
            else:
                option = chosen[0] if chosen else control.select_one("option")
                if option is not None:
                    data[name] = option.get("value", "")
        else:
            data[name] = control.text.removeprefix("\n")
    return data


def main_form(response):
    """Return the one form in the page's content, as a parsed element."""
    forms = soup_of(response).select_one("main").select("form")
    assert len(forms) == 1
    return forms[0]


def manage_menu(response):
    """Return the Manage menu element of an overview page, or None when it has none."""
    return soup_of(response).select_one('[data-menu="manage"]')


def hrefs(element):
    """List the link targets inside an element."""
    return [a["href"] for a in element.select("a[href]")]


@pytest.mark.django_db
class TestRegistration:
    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_the_page_sits_beneath_the_records_own_address(
        self, make_case, kind, page
    ):
        case = make_case(kind)

        assert case.url(page) == f"{case.own_url}{page}/"

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_the_page_is_not_a_tab(self, kind, page):
        model = CORE_MODELS[kind]
        plugins.registry.get_urls_for_model(model)
        menu = plugins.registry.get_plugin_menu_for_model(model)

        assert f"{kind}:{page}" not in [item.view_name for item in menu.children]

    @pytest.mark.parametrize(
        "name",
        [
            "project:overview-update",
            "project:overview-descriptions",
            "dataset:overview-update",
            "dataset:overview-descriptions",
            "sample:basic-information",
        ],
    )
    def test_the_pages_they_replace_are_gone(self, name):
        with pytest.raises(NoReverseMatch):
            reverse(name, kwargs={"uuid": "00000000-0000-0000-0000-000000000000"})


@pytest.mark.django_db
class TestAccess:
    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_a_person_who_may_edit_opens_the_page(
        self, make_case, person_at, kind, page
    ):
        case = make_case(kind, public=False)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url(page))

        assert response.status_code == 200

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_a_person_who_may_only_view_is_refused_and_nothing_changes(
        self, make_case, person_at, kind, page
    ):
        case = make_case(kind, public=False)
        reader = person_at(case, ContributionLevel.VIEW)
        client = browser_as(reader)
        description_model = DESCRIPTION_MODELS[kind]
        first_type = description_model.VOCABULARY.values[0]

        assert client.get(case.url(page)).status_code == 403
        response = client.post(
            case.url(page), {"name": "Changed", first_type: "A description"}
        )

        assert response.status_code == 403
        case.record.refresh_from_db()
        assert case.record.name != "Changed"
        assert not description_model.objects.filter(related=case.record).exists()

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_a_signed_in_person_with_no_level_on_a_public_record_is_refused(
        self, make_case, person_at, kind, page
    ):
        case = make_case(kind, public=True)
        stranger = person_at()

        response = browser_as(stranger).get(case.url(page))

        assert response.status_code == 403

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_a_visitor_to_a_public_record_is_sent_to_sign_in(
        self, make_case, kind, page
    ):
        case = make_case(kind, public=True)

        response = browser_as().get(case.url(page))

        assert response.status_code == 302
        assert response.url.startswith(resolve_url(settings.LOGIN_URL))

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    @pytest.mark.parametrize("signed_in", [True, False])
    def test_a_person_who_may_not_see_the_record_gets_not_found(
        self, make_case, person_at, kind, page, signed_in
    ):
        case = make_case(kind, public=False)
        client = browser_as(person_at() if signed_in else None)

        assert client.get(case.url(page)).status_code == 404
        assert client.post(case.url(page), {"name": "Changed"}).status_code == 404
        case.record.refresh_from_db()
        assert case.record.name != "Changed"

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_a_level_removed_after_the_page_was_opened_refuses_the_save(
        self, make_case, person_at, kind, page
    ):
        case = make_case(kind, public=True)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        first_type = DESCRIPTION_MODELS[kind].VOCABULARY.values[0]
        opened = client.get(case.url(page))
        payload = form_payload(main_form(opened))
        payload.update({"name": "Changed", first_type: "A description"})

        editor.contributions.all().delete()
        response = client.post(case.url(page), payload)

        assert response.status_code == 403
        case.record.refresh_from_db()
        assert case.record.name != "Changed"
        assert not DESCRIPTION_MODELS[kind].objects.filter(related=case.record).exists()


@pytest.mark.django_db
class TestManageMenu:
    @pytest.mark.parametrize("kind", KINDS)
    def test_a_person_who_may_edit_is_offered_both_pages(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.own_url)

        assert response.status_code == 200
        menu = manage_menu(response)
        assert menu is not None
        assert {case.url("edit"), case.url("descriptions")} <= set(hrefs(menu))
        offered = {entry["url"] for entry in response.context["manage_menu"]}
        assert {case.url("edit"), case.url("descriptions")} <= offered

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_person_who_may_only_view_is_offered_no_menu(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        reader = person_at(case, ContributionLevel.VIEW)

        response = browser_as(reader).get(case.own_url)

        assert response.status_code == 200
        assert manage_menu(response) is None
        assert list(response.context["manage_menu"]) == []

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_visitor_is_offered_no_menu(self, make_case, kind):
        case = make_case(kind)

        response = browser_as().get(case.own_url)

        assert manage_menu(response) is None

    def test_the_project_menu_has_no_contributors_entry(self, make_case, person_at):
        case = make_case("project")
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.own_url)

        contributors = reverse("project:contribution-list", kwargs={"uuid": case.record.uuid})
        assert contributors not in hrefs(manage_menu(response))

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_the_delete_page_stays_in_the_menu_and_opens(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)

        response = client.get(case.own_url)

        delete = reverse(f"{kind}:overview-delete", kwargs={"uuid": case.record.uuid})
        assert delete in hrefs(manage_menu(response))
        assert client.get(delete).status_code == 200

    def test_the_sample_key_dates_and_keywords_pages_stay_in_the_menu_and_open(
        self, make_case, person_at
    ):
        case = make_case("sample")
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)

        response = client.get(case.own_url)

        for page in ("key-dates", "keywords"):
            assert case.url(page) in hrefs(manage_menu(response))
            assert client.get(case.url(page)).status_code == 200


@pytest.mark.django_db
class TestEditDetails:
    @pytest.mark.parametrize("kind", KINDS)
    def test_a_valid_save_returns_to_the_record_with_a_message(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        payload = form_payload(main_form(client.get(case.url("edit"))))
        payload["name"] = "Renamed"

        response = client.post(case.url("edit"), payload)

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        case.record.refresh_from_db()
        assert case.record.name == "Renamed"
        shown = client.get(response.url)
        assert shown.context["record"].name == "Renamed"

    @pytest.mark.parametrize("kind", KINDS)
    def test_an_invalid_save_stores_nothing_and_keeps_the_other_values(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        broken, bad_value, kept = INVALID[kind]
        form = main_form(client.get(case.url("edit")))
        payload = form_payload(form)
        control = form.select_one(f'[name="{kept}"]')
        if control.name == "select":
            payload[kept] = next(
                option["value"]
                for option in control.select("option[value]")
                if option["value"] and option["value"] != payload[kept]
            )
        else:
            payload[kept] = "A changed value"
        payload[broken] = bad_value
        before = type(case.record).objects.get(pk=case.record.pk)

        response = client.post(case.url("edit"), payload)

        assert response.status_code == 200
        bound = response.context["form"]
        assert broken in bound.errors
        assert str(bound[kept].value()) == payload[kept]
        after = type(case.record).objects.get(pk=case.record.pk)
        assert getattr(after, broken) == getattr(before, broken)
        assert str(getattr(after, kept)) == str(getattr(before, kept))

    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_offers_the_types_own_fields_with_their_values(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url("edit"))

        form = response.context["form"]
        assert form["name"].value() == case.record.name
        if kind == "sample":
            assert form["rock_type"].value() == "basalt"
        if kind == "measurement":
            assert form["char_field"].value() == "a note"
        assert "dataset" not in form.fields or kind in {"project", "dataset"}
        assert "sample" not in form.fields

    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_holds_one_form_with_its_submit_control_inside(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url("edit"))

        form = main_form(response)
        assert form.select('[type="submit"]')

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    @pytest.mark.parametrize(
        ("level", "offered"),
        [(ContributionLevel.EDIT, False), (ContributionLevel.MANAGE, True)],
    )
    def test_visibility_is_offered_to_a_manager_only(
        self, make_case, person_at, kind, level, offered
    ):
        case = make_case(kind)
        person = person_at(case, level)

        response = browser_as(person).get(case.url("edit"))

        assert ("visibility" in response.context["form"].fields) is offered


@pytest.mark.django_db
class TestEditDescriptions:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_has_one_area_per_type_filled_with_what_is_recorded(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        model = DESCRIPTION_MODELS[kind]
        recorded = model.VOCABULARY.values[0]
        model.objects.create(related=case.record, type=recorded, value="Written down")

        response = browser_as(editor).get(case.url("descriptions"))

        form = response.context["form"]
        assert list(form.fields) == list(model.VOCABULARY.values)
        assert form[recorded].value() == "Written down"

    @pytest.mark.parametrize("kind", KINDS)
    def test_filling_an_area_records_it_and_emptying_one_removes_it(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        model = DESCRIPTION_MODELS[kind]
        first, second = model.VOCABULARY.values[:2]
        model.objects.create(related=case.record, type=second, value="To be removed")

        response = client.post(
            case.url("descriptions"), {first: "Newly written", second: ""}
        )

        assert response.status_code == 302
        stored = dict(
            model.objects.filter(related=case.record).values_list("type", "value")
        )
        assert stored == {first: "Newly written"}

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_save_returns_to_the_record_with_a_message(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        first = DESCRIPTION_MODELS[kind].VOCABULARY.values[0]

        response = browser_as(editor).post(case.url("descriptions"), {first: "Text"})

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]


@pytest.mark.django_db
class TestOverviewPrompts:
    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_the_prompt_for_a_missing_description_leads_to_the_shared_page(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.own_url)

        outside_menu = [
            a["href"]
            for a in soup_of(response).select_one("main").select("a[href]")
            if a.find_parent(attrs={"data-menu": "manage"}) is None
        ]
        assert case.url("descriptions") in outside_menu

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_the_prompt_to_change_visibility_leads_to_the_shared_page(
        self, make_case, person_at, kind
    ):
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.own_url)

        outside_menu = [
            a["href"]
            for a in soup_of(response).select_one("main").select("a[href]")
            if a.find_parent(attrs={"data-menu": "manage"}) is None
        ]
        assert case.url("edit") in outside_menu

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_the_readiness_items_carry_the_shared_addresses(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        if kind == "dataset":
            case.record.published = False
            case.record.save()
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.own_url)

        addresses = {item["url"] for item in response.context["readiness"]["items"]}
        assert {case.url("edit"), case.url("descriptions")} <= addresses
        assert f"{case.own_url}update/" not in addresses

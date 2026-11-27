"""Tests for the editing pages every record shares: details, descriptions, key dates, identifiers.

Each page is requested through the test client on a project, a dataset, and a sample and a
measurement of the demo portal's registered types, so a registered type is what is tested.
"""

import pytest
from bs4 import BeautifulSoup
from controlled_vocabularies.models import Record
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit
from django.conf import settings
from django.contrib.messages import SUCCESS, get_messages
from django.db import connection
from django.shortcuts import resolve_url
from django.test import Client, RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from partial_dates import Precision

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
)
from fairdm.core.editing import EDITING_PAGES, edit_links
from fairdm.core.measurement.models import (
    Measurement,
    MeasurementDate,
    MeasurementDescription,
    MeasurementIdentifier,
)
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.core.sample.models import (
    Sample,
    SampleDate,
    SampleDescription,
    SampleIdentifier,
    SampleRelation,
)
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, DATE_TYPES, IDENTIFIER_TYPES
from fairdm.factories import (
    ContributionFactory,
    DatasetDateFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    MeasurementDateFactory,
    MeasurementIdentifierFactory,
    PersonFactory,
    ProjectDateFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleDateFactory,
    SampleIdentifierFactory,
    SampleRelationFactory,
)
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

KINDS = ("project", "dataset", "sample", "measurement")
PAGES = ("edit", "descriptions", "keywords", "key-dates", "identifiers")
# The part of the record each editing page changes, as the overview page keys its links.
PARTS = {
    "details": "edit",
    "descriptions": "descriptions",
    "keywords": "keywords",
    "dates": "key-dates",
    "identifiers": "identifiers",
    "delete": "delete",
}
ROLES = CONTRIBUTOR_ROLES
# Per record type: the setting that names its keyword vocabularies and the key it sits under.
KEYWORD_SETTINGS = {
    "project": ("FAIRDM_PROJECT", "keywords"),
    "dataset": ("FAIRDM_DATASET", "keyword_vocabularies"),
    "sample": ("FAIRDM_SAMPLE", "keywords"),
    "measurement": ("FAIRDM_MEASUREMENT", "keywords"),
}
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
# Per record type: the model of a date row, the factory that makes one, and two of its types.
DATES = {
    "project": (
        ProjectDate,
        ProjectDateFactory,
        f"{DATE_TYPES}/start",
        f"{DATE_TYPES}/end",
    ),
    "dataset": (
        DatasetDate,
        DatasetDateFactory,
        f"{DATE_TYPES}/collection-start",
        f"{DATE_TYPES}/collection-end",
    ),
    "sample": (
        SampleDate,
        SampleDateFactory,
        f"{DATE_TYPES}/collected",
        f"{DATE_TYPES}/prepared",
    ),
    "measurement": (
        MeasurementDate,
        MeasurementDateFactory,
        f"{DATE_TYPES}/setup",
        f"{DATE_TYPES}/tear-down",
    ),
}
# Per record type: the model of an identifier row and the factory that makes one. Every
# vocabulary offers a DOI.
IDENTIFIERS = {
    "project": (ProjectIdentifier, ProjectIdentifierFactory),
    "dataset": (DatasetIdentifier, DatasetIdentifierFactory),
    "sample": (SampleIdentifier, SampleIdentifierFactory),
    "measurement": (MeasurementIdentifier, MeasurementIdentifierFactory),
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


def rows_payload(prefix, rows, initial=0):
    """Build what a browser submits for a row set: the management form and one entry per row."""
    data = {
        f"{prefix}-TOTAL_FORMS": str(len(rows)),
        f"{prefix}-INITIAL_FORMS": str(initial),
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }
    for index, row in enumerate(rows):
        for name, value in row.items():
            data[f"{prefix}-{index}-{name}"] = value
    return data


def only_row_set(response, prefix):
    """Return the one row set the page draws, checking it is the one asked for."""
    row_sets = response.context["inlines"]
    assert [row_set.prefix for row_set in row_sets] == [prefix]
    return row_sets[0]


def row_set_errors(row_set):
    """Gather every error a row set reports, on the set and on its rows, as one string."""
    errors = list(row_set.non_form_errors())
    for form in row_set.forms:
        errors.extend(str(message) for message in form.errors.values())
    return " ".join(str(error) for error in errors)


@pytest.fixture
def with_vocabulary(settings):
    """Configure the roles vocabulary as the keyword vocabulary of one record type."""

    def configure(kind):
        name, key = KEYWORD_SETTINGS[kind]
        setattr(settings, name, {key: [ROLES]})

    return configure


@pytest.fixture
def without_vocabularies(settings):
    """Leave every record type with no keyword setting at all."""
    for name, _key in KEYWORD_SETTINGS.values():
        if hasattr(settings, name):
            delattr(settings, name)


def roles(count=2):
    """Return concepts of the roles vocabulary to use as keywords."""
    found = list(
        Record.objects.filter(scheme__uri=CONTRIBUTOR_ROLES, type=Record.Type.CONCEPT)[
            :count
        ]
    )
    assert len(found) == count
    return found


def delete_confirmation(case):
    """Return what a person types to confirm deleting the record: its name, else its portal ID."""
    return case.record.name or str(case.record.uuid)


def still_exists(record):
    """Say whether the record is still stored, whatever its visibility."""
    model = type(record)
    return getattr(model, "all_objects", model.objects).filter(pk=record.pk).exists()


def hrefs(element):
    """List the link targets inside an element."""
    return [a["href"] for a in element.select("a[href]")]


@pytest.mark.django_db
class TestRegistration:
    @pytest.mark.parametrize("kind", KINDS)
    def test_every_page_sits_beneath_the_records_address(self, make_case, kind):
        case = make_case(kind)

        wrong = {
            page: case.url(page)
            for page in (*PAGES, "delete")
            if case.url(page) != f"{case.own_url}{page}/"
        }

        assert not wrong

    def test_no_editing_page_is_a_tab(self):
        tabs = []
        for kind, model in CORE_MODELS.items():
            plugins.registry.get_urls_for_model(model)
            menu = plugins.registry.get_plugin_menu_for_model(model)
            names = {item.view_name for item in menu.children}
            tabs += [
                f"{kind}:{page}"
                for page in (*PAGES, "delete")
                if f"{kind}:{page}" in names
            ]

        assert not tabs


@pytest.mark.django_db
class TestAccess:
    """One verdict decides every page, so each outcome is checked on the edit page of every kind
    (the kinds decide who may see a record by different rules) and on one kind where nothing about
    the kind matters. A grid over every kind and page checks each page is wired to the verdict."""

    @pytest.mark.parametrize("kind", KINDS)
    @pytest.mark.parametrize("page", PAGES)
    def test_every_page_opens_for_an_editor_and_refuses_a_reader_and_nothing_changes(
        self, make_case, person_at, kind, page
    ):
        case = make_case(kind, public=False)
        editor = person_at(case, ContributionLevel.EDIT)
        reader = person_at(case, ContributionLevel.VIEW)
        description_model = DESCRIPTION_MODELS[kind]
        first_type = next(
            concept.uri for concept in description_model.get_type_concepts()
        )

        assert browser_as(editor).get(case.url(page)).status_code == 200
        client = browser_as(reader)
        assert client.get(case.url(page)).status_code == 403
        response = client.post(
            case.url(page), {"name": "Changed", first_type: "A description"}
        )

        assert response.status_code == 403
        case.record.refresh_from_db()
        assert case.record.name != "Changed"
        assert not description_model.objects.filter(related=case.record).exists()

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_signed_in_person_with_no_level_on_a_public_record_is_refused(
        self, make_case, person_at, kind
    ):
        case = make_case(kind, public=True)

        response = browser_as(person_at()).get(case.url("edit"))

        assert response.status_code == 403

    def test_a_visitor_to_a_public_record_is_sent_to_sign_in(self, make_case):
        case = make_case("project", public=True)

        response = browser_as().get(case.url("edit"))

        assert response.status_code == 302
        assert response.url.startswith(resolve_url(settings.LOGIN_URL))

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_person_who_may_not_see_the_record_gets_not_found(
        self, make_case, person_at, kind
    ):
        case = make_case(kind, public=False)
        client = browser_as(person_at())

        assert client.get(case.url("edit")).status_code == 404
        assert client.post(case.url("edit"), {"name": "Changed"}).status_code == 404
        case.record.refresh_from_db()
        assert case.record.name != "Changed"

    def test_a_visitor_who_may_not_see_the_record_gets_not_found(self, make_case):
        case = make_case("project", public=False)
        client = browser_as()

        assert client.get(case.url("edit")).status_code == 404
        assert client.post(case.url("edit"), {"name": "Changed"}).status_code == 404

    def test_a_level_removed_after_the_page_was_opened_refuses_the_save(
        self, make_case, person_at
    ):
        case = make_case("project", public=True)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        payload = form_payload(main_form(client.get(case.url("edit"))))
        payload["name"] = "Changed"

        editor.contributions.all().delete()
        response = client.post(case.url("edit"), payload)

        assert response.status_code == 403
        case.record.refresh_from_db()
        assert case.record.name != "Changed"

    @pytest.mark.parametrize("kind", KINDS)
    def test_a_manager_opens_the_delete_page_and_an_editor_is_refused_and_nothing_is_deleted(
        self, make_case, person_at, kind
    ):
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)

        assert browser_as(manager).get(case.url("delete")).status_code == 200
        assert client.get(case.url("delete")).status_code == 403
        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 403
        assert still_exists(case.record)

    def test_a_signed_in_person_with_no_level_is_refused_the_delete_page(
        self, make_case, person_at
    ):
        case = make_case("project", public=True)
        client = browser_as(person_at())

        assert client.get(case.url("delete")).status_code == 403
        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 403
        assert still_exists(case.record)

    def test_a_person_who_may_not_see_the_record_gets_not_found_from_the_delete_page(
        self, make_case, person_at
    ):
        case = make_case("project", public=False)
        client = browser_as(person_at())

        assert client.get(case.url("delete")).status_code == 404
        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 404
        assert still_exists(case.record)

    def test_a_level_removed_after_the_delete_page_was_opened_refuses_the_deletion(
        self, make_case, person_at
    ):
        case = make_case("project", public=True)
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)
        assert client.get(case.url("delete")).status_code == 200

        manager.contributions.all().delete()
        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 403
        assert still_exists(case.record)


@pytest.mark.django_db
class TestEditLinks:
    @pytest.mark.parametrize("kind", KINDS)
    def test_a_person_who_may_manage_is_offered_every_part_and_delete(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.own_url)

        assert response.context["edit"] == {
            part: case.url(page) for part, page in PARTS.items()
        }
        offered = hrefs(soup_of(response))
        for page in ("edit", "keywords", "identifiers", "delete"):
            assert case.url(page) in offered

    def test_the_links_ask_whether_the_viewer_may_see_the_record_once(
        self, make_case, person_at
    ):
        case = make_case("sample", public=False)
        manager = person_at(case, ContributionLevel.MANAGE)
        request = RequestFactory().get(case.own_url)
        request.user = manager
        edit_links(request, case.record)  # warm one-time caches
        with CaptureQueriesContext(connection) as together:
            edit_links(request, case.record)
        with CaptureQueriesContext(connection) as apart:
            for page in EDITING_PAGES:
                page.may_be_used_by(request, case.record)

        assert len(together) < len(apart)

    def test_a_person_who_may_only_edit_is_offered_every_part_but_delete(
        self, make_case, person_at
    ):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.own_url)

        assert "delete" not in response.context["edit"]
        assert response.context["edit"]["details"] == case.url("edit")
        assert case.url("delete") not in hrefs(soup_of(response))

    def test_a_person_who_may_only_view_is_offered_no_editing_page(
        self, make_case, person_at
    ):
        case = make_case("project")
        reader = person_at(case, ContributionLevel.VIEW)

        response = browser_as(reader).get(case.own_url)

        assert response.status_code == 200
        assert response.context["edit"] == {}
        offered = hrefs(soup_of(response))
        assert not any(case.url(page) in offered for page in PARTS.values())

    def test_a_visitor_is_offered_no_editing_page(self, make_case):
        case = make_case("project")

        response = browser_as().get(case.own_url)

        offered = hrefs(soup_of(response))
        assert not any(case.url(page) in offered for page in PARTS.values())


@pytest.mark.django_db
class TestEditDetails:
    def test_a_form_built_on_the_record_mixin_receives_the_request(
        self, make_case, person_at
    ):
        case = make_case("sample")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url("edit"))

        assert response.context["form"].request.user == editor

    @pytest.mark.parametrize("kind", ["project", "dataset", "sample"])
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

    @pytest.mark.parametrize("kind", ["project", "sample"])
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

    @pytest.mark.parametrize(
        ("kind", "field", "value"),
        [("sample", "rock_type", "basalt"), ("measurement", "char_field", "a note")],
    )
    def test_the_page_offers_the_types_own_fields_with_their_values(
        self, make_case, person_at, kind, field, value
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url("edit"))

        form = response.context["form"]
        assert form["name"].value() == case.record.name
        assert form[field].value() == value
        assert "dataset" not in form.fields
        assert "sample" not in form.fields

    @pytest.mark.parametrize("page", ["edit", "keywords"])
    def test_the_page_holds_one_form_with_its_submit_control_inside(
        self, make_case, person_at, page
    ):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url(page))

        form = main_form(response)
        assert form.select('[type="submit"]')

    def test_a_form_whose_helper_draws_its_own_tag_and_button_still_gives_one_form(
        self, make_case, person_at, monkeypatch
    ):
        case = make_case("sample")
        editor = person_at(case, ContributionLevel.EDIT)
        config = registry.get_for_model(type(case.record))
        built = config.get_form_class()

        class WithHelper(built):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.helper = FormHelper()
                self.helper.layout = Layout("name")
                self.helper.add_input(Submit("own_submit", "Save"))

        monkeypatch.setattr(config, "get_form_class", lambda: WithHelper)

        response = browser_as(editor).get(case.url("edit"))

        form = main_form(response)
        assert not form.select('[name="own_submit"]')
        assert form.select('[type="submit"]')

    @pytest.mark.parametrize(
        ("level", "offered"),
        [(ContributionLevel.EDIT, False), (ContributionLevel.MANAGE, True)],
    )
    def test_visibility_is_offered_to_a_manager_only(
        self, make_case, person_at, level, offered
    ):
        case = make_case("project")
        person = person_at(case, level)

        response = browser_as(person).get(case.url("edit"))

        assert ("visibility" in response.context["form"].fields) is offered

    def test_a_manager_cannot_move_a_measurement(self, make_case, person_at):
        case = make_case("measurement")
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)
        other = make_case("measurement")
        before = {"dataset": case.record.dataset_id, "sample": case.record.sample_id}
        stray = {"dataset": other.record.dataset_id, "sample": other.record.sample_id}
        payload = form_payload(main_form(client.get(case.url("edit"))))
        payload.update({name: str(pk) for name, pk in stray.items()})

        response = client.post(case.url("edit"), payload)

        assert response.status_code == 302
        case.record.refresh_from_db()
        assert {name: getattr(case.record, f"{name}_id") for name in before} == before

    def test_an_editor_cannot_move_a_dataset_or_change_its_visibility(
        self, make_case, person_at
    ):
        case = make_case("dataset", public=False)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        other = make_case("dataset", public=True)
        project_id = case.record.project_id
        payload = form_payload(main_form(client.get(case.url("edit"))))
        payload.update(
            project=str(other.record.project_id), visibility=str(Visibility.PUBLIC)
        )

        response = client.post(case.url("edit"), payload)

        assert response.status_code == 302
        case.record.refresh_from_db()
        assert case.record.project_id == project_id
        assert case.record.visibility == Visibility.PRIVATE

    def test_rows_submitted_to_the_page_are_not_stored(self, make_case, person_at):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        _model, _factory, date_type, _other = DATES[kind]
        payload = form_payload(main_form(client.get(case.url("edit"))))
        payload.update(
            rows_payload("dates", [{"type": date_type, "value": "2020-01-01"}])
        )
        payload.update(
            rows_payload(
                "identifiers",
                [{"type": f"{IDENTIFIER_TYPES}/doi", "value": "10.1/stray"}],
            )
        )

        response = client.post(case.url("edit"), payload)

        assert response.status_code == 302
        assert not case.record.dates.exists()
        assert not case.record.identifiers.exists()


@pytest.mark.django_db
class TestEditKeyDates:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_offers_the_types_of_the_vocabulary_and_shows_the_dates_recorded(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        model, factory, recorded, _other = DATES[kind]
        factory(related=case.record, type=recorded, value="2020-01-01")

        response = browser_as(editor).get(case.url("key-dates"))

        assert response.status_code == 200
        row_set = only_row_set(response, "dates")
        offered = [value for value, _label in row_set.empty_form.fields["type"].choices]
        assert [value for value in offered if value] == [
            concept.uri for concept in model.get_type_concepts()
        ]
        assert row_set.initial_form_count() == 1
        assert len(row_set.forms) == 1
        assert row_set.forms[0]["type"].value() == recorded
        assert str(row_set.forms[0]["value"].value()) == "2020-01-01"

    def test_the_page_edits_rows_alone(self, make_case, person_at):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).get(case.url("key-dates"))

        names = [c["name"] for c in main_form(response).select("[name]")]
        assert {n for n in names if not n.startswith("dates-")} <= {
            "csrfmiddlewaretoken",
            "default_next",
        }

    @pytest.mark.parametrize("kind", ["project", "measurement"])
    def test_adding_a_date_stores_it_and_returns_to_the_record(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        _model, _factory, added, _other = DATES[kind]

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload("dates", [{"type": added, "value": "2020-06-01"}]),
        )

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        stored = case.record.dates.get()
        assert (stored.type_id, str(stored.value)) == (added, "2020-06-01")

    @pytest.mark.parametrize("remove", [False, True])
    def test_a_row_of_another_record_is_left_as_it_was(
        self, make_case, person_at, remove
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        _model, factory, recorded, _other = DATES[kind]
        foreign = factory(
            related=make_case(kind).record, type=recorded, value="2020-01-01"
        )
        row = {"id": foreign.pk, "type": recorded, "value": "2031-12-31"}
        if remove:
            row["DELETE"] = "on"

        response = browser_as(editor).post(
            case.url("key-dates"), rows_payload("dates", [row], initial=1)
        )

        assert response.status_code == 302
        foreign.refresh_from_db()
        assert str(foreign.value) == "2020-01-01"
        assert not case.record.dates.exists()

    def test_changing_a_date_stores_the_new_value_and_removing_one_deletes_it(
        self, make_case, person_at
    ):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)
        _model, factory, kept_type, doomed_type = DATES["project"]
        kept = factory(related=case.record, type=kept_type, value="2020-01-01")
        doomed = factory(related=case.record, type=doomed_type, value="2021-01-01")

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload(
                "dates",
                [
                    {"id": kept.pk, "type": kept_type, "value": "2020-06-15"},
                    {
                        "id": doomed.pk,
                        "type": doomed_type,
                        "value": "2021-01-01",
                        "DELETE": "on",
                    },
                ],
                initial=2,
            ),
        )

        assert response.status_code == 302
        kept.refresh_from_db()
        assert str(kept.value) == "2020-06-15"
        assert list(case.record.dates.all()) == [kept]

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_an_end_before_the_start_stores_nothing_and_names_the_end(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        _model, _factory, start, end = DATES[kind]

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload(
                "dates",
                [
                    {"type": start, "value": "2020-06-01"},
                    {"type": end, "value": "2010-01-01"},
                ],
            ),
        )

        assert response.status_code == 200
        assert "2010-01-01" in row_set_errors(only_row_set(response, "dates"))
        assert not case.record.dates.exists()

    def test_an_end_before_a_start_already_stored_stores_nothing(
        self, make_case, person_at
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        _model, factory, start, end = DATES[kind]
        stored = factory(related=case.record, type=start, value="2020-06-01")

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload(
                "dates",
                [
                    {"id": stored.pk, "type": start, "value": "2020-06-01"},
                    {"type": end, "value": "2010-01-01"},
                ],
                initial=1,
            ),
        )

        assert response.status_code == 200
        assert "2010-01-01" in row_set_errors(only_row_set(response, "dates"))
        assert not case.record.dates.filter(type=end).exists()

    def test_a_start_with_no_end_is_stored(self, make_case, person_at):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        _model, _factory, start, _end = DATES[kind]

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload("dates", [{"type": start, "value": "2020-06-01"}]),
        )

        assert response.status_code == 302
        assert case.record.dates.filter(type=start).exists()

    def test_a_measurements_teardown_may_fall_before_its_setup(
        self, make_case, person_at
    ):
        case = make_case("measurement")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).post(
            case.url("key-dates"),
            rows_payload(
                "dates",
                [
                    {"type": f"{DATE_TYPES}/setup", "value": "2020-06-01"},
                    {"type": f"{DATE_TYPES}/tear-down", "value": "2010-01-01"},
                ],
            ),
        )

        assert response.status_code == 302
        assert case.record.dates.count() == 2

    @pytest.mark.parametrize(
        ("entered", "precision"),
        [("2019", Precision.YEAR), ("2019-06", Precision.MONTH)],
    )
    def test_a_date_is_kept_and_read_back_as_precisely_as_it_was_entered(
        self, make_case, person_at, entered, precision
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        _model, _factory, added, _other = DATES[kind]

        response = client.post(
            case.url("key-dates"),
            rows_payload("dates", [{"type": added, "value": entered}]),
        )

        assert response.status_code == 302
        stored = case.record.dates.get()
        assert stored.value.precision is precision
        assert str(stored.value) == entered
        shown = only_row_set(client.get(case.url("key-dates")), "dates")
        assert str(shown.forms[0]["value"].value()) == entered


@pytest.mark.django_db
class TestEditIdentifiers:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_offers_the_types_of_the_vocabulary_and_shows_the_identifiers_recorded(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        model, factory = IDENTIFIERS[kind]
        factory(
            related=case.record,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/recorded",
        )

        response = browser_as(editor).get(case.url("identifiers"))

        assert response.status_code == 200
        row_set = only_row_set(response, "identifiers")
        offered = [value for value, _label in row_set.empty_form.fields["type"].choices]
        assert [value for value in offered if value] == [
            concept.uri for concept in model.get_type_concepts()
        ]
        assert row_set.initial_form_count() == 1
        assert len(row_set.forms) == 1
        assert row_set.forms[0]["type"].value() == f"{IDENTIFIER_TYPES}/doi"
        assert row_set.forms[0]["value"].value() == "10.1/recorded"

    @pytest.mark.parametrize("kind", ["project", "measurement"])
    def test_adding_an_identifier_stores_it_and_returns_to_the_record(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).post(
            case.url("identifiers"),
            rows_payload(
                "identifiers",
                [{"type": f"{IDENTIFIER_TYPES}/doi", "value": "10.1/added"}],
            ),
        )

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        stored = case.record.identifiers.get()
        assert (stored.type_id, stored.value) == (
            f"{IDENTIFIER_TYPES}/doi",
            "10.1/added",
        )

    def test_changing_an_identifier_stores_the_new_value_and_removing_one_deletes_it(
        self, make_case, person_at
    ):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)
        _model, factory = IDENTIFIERS["project"]
        kept = factory(
            related=case.record,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/original",
        )
        doomed = factory(
            related=case.record,
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="10.1/doomed",
        )

        response = browser_as(editor).post(
            case.url("identifiers"),
            rows_payload(
                "identifiers",
                [
                    {
                        "id": kept.pk,
                        "type": f"{IDENTIFIER_TYPES}/doi",
                        "value": "10.1/changed",
                    },
                    {
                        "id": doomed.pk,
                        "type": f"{IDENTIFIER_TYPES}/grant-number",
                        "value": "10.1/doomed",
                        "DELETE": "on",
                    },
                ],
                initial=2,
            ),
        )

        assert response.status_code == 302
        kept.refresh_from_db()
        assert kept.value == "10.1/changed"
        assert list(case.record.identifiers.all()) == [kept]

    def test_a_value_held_by_another_record_is_refused_and_stores_nothing(
        self, make_case, person_at
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        other = make_case(kind)
        _model, factory = IDENTIFIERS[kind]
        factory(
            related=other.record, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1/taken"
        )

        response = browser_as(editor).post(
            case.url("identifiers"),
            rows_payload(
                "identifiers",
                [{"type": f"{IDENTIFIER_TYPES}/doi", "value": "10.1/taken"}],
            ),
        )

        assert response.status_code == 200
        row_set = only_row_set(response, "identifiers")
        assert "value" in row_set.forms[0].errors
        assert not case.record.identifiers.exists()

    def test_one_value_entered_twice_is_refused_and_stores_nothing(
        self, make_case, person_at
    ):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).post(
            case.url("identifiers"),
            rows_payload(
                "identifiers",
                [
                    {"type": f"{IDENTIFIER_TYPES}/doi", "value": "10.1/twice"},
                    {"type": f"{IDENTIFIER_TYPES}/grant-number", "value": "10.1/twice"},
                ],
            ),
        )

        assert response.status_code == 200
        assert only_row_set(response, "identifiers").non_form_errors()
        assert not case.record.identifiers.exists()

    def test_one_invalid_row_stores_none_of_the_rows(self, make_case, person_at):
        case = make_case("project")
        editor = person_at(case, ContributionLevel.EDIT)

        response = browser_as(editor).post(
            case.url("identifiers"),
            rows_payload(
                "identifiers",
                [
                    {"type": f"{IDENTIFIER_TYPES}/doi", "value": "10.1/valid"},
                    {"type": f"{IDENTIFIER_TYPES}/grant-number", "value": ""},
                ],
            ),
        )

        assert response.status_code == 200
        assert not case.record.identifiers.exists()

    def test_the_portal_id_is_not_among_the_rows_and_cannot_be_changed(
        self, make_case, person_at
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        _model, factory = IDENTIFIERS[kind]
        recorded = factory(
            related=case.record,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1/recorded",
        )
        portal_id = case.record.uuid

        opened = client.get(case.url("identifiers"))

        row_set = only_row_set(opened, "identifiers")
        assert str(portal_id) not in [str(f["value"].value()) for f in row_set.forms]
        assert "uuid" not in row_set.empty_form.fields
        names = [c["name"] for c in main_form(opened).select("[name]")]
        assert "uuid" not in names

        payload = rows_payload(
            "identifiers",
            [
                {
                    "id": recorded.pk,
                    "type": f"{IDENTIFIER_TYPES}/doi",
                    "value": "10.1/another",
                }
            ],
            initial=1,
        )
        payload["uuid"] = "00000000-0000-4000-8000-000000000000"
        response = client.post(case.url("identifiers"), payload)

        assert response.status_code == 302
        case.record.refresh_from_db()
        assert case.record.uuid == portal_id


@pytest.mark.django_db
class TestEditDescriptions:
    @pytest.mark.parametrize("kind", KINDS)
    def test_the_page_has_one_area_per_type_filled_with_what_is_recorded(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        model = DESCRIPTION_MODELS[kind]
        recorded = next(concept.uri for concept in model.get_type_concepts())
        model.objects.create(
            related=case.record, type_id=recorded, value="Written down"
        )

        response = browser_as(editor).get(case.url("descriptions"))

        form = response.context["form"]
        assert list(form.fields) == [
            concept.uri for concept in model.get_type_concepts()
        ]
        assert form[recorded].value() == "Written down"

    @pytest.mark.parametrize("kind", ["project", "measurement"])
    def test_filling_an_area_records_it_and_emptying_one_removes_it(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        model = DESCRIPTION_MODELS[kind]
        first, second = [concept.uri for concept in model.get_type_concepts()][:2]
        model.objects.create(related=case.record, type_id=second, value="To be removed")

        response = client.post(
            case.url("descriptions"), {first: "Newly written", second: ""}
        )

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        stored = dict(
            model.objects.filter(related=case.record).values_list("type", "value")
        )
        assert stored == {first: "Newly written"}


@pytest.mark.django_db
class TestEditKeywords:
    @pytest.mark.parametrize("kind", ["project", "sample"])
    def test_adding_and_removing_keywords_is_stored_and_shown_on_the_record(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        case.record.tags.add("old", "kept")
        opened = client.get(case.url("keywords"))
        assert set(opened.context["form"]["tags"].value()) == {"old", "kept"}
        payload = form_payload(main_form(opened))
        payload["tags"] = ["kept", "new"]

        response = client.post(case.url("keywords"), payload)

        assert response.status_code == 302
        assert response.url == case.own_url
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        stored = type(case.record).objects.get(pk=case.record.pk)
        assert sorted(stored.tags.names()) == ["kept", "new"]

    def test_saving_with_nothing_chosen_removes_every_free_keyword(
        self, make_case, person_at
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        case.record.tags.add("old")

        response = browser_as(editor).post(case.url("keywords"), {})

        assert response.status_code == 302
        assert not case.record.tags.exists()

    def test_saving_leaves_the_vocabulary_keywords_as_they_were(
        self, make_case, person_at, with_vocabulary
    ):
        kind = "project"
        with_vocabulary(kind)
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        first, second = roles()
        case.record.keywords.add(first, second)

        response = browser_as(editor).post(
            case.url("keywords"), {"tags": ["new"], "FairDMRoles": [str(first.pk)]}
        )

        assert response.status_code == 302
        assert set(case.record.keywords.all()) == {first, second}

    def test_the_page_opens_and_saves_where_no_vocabulary_is_configured(
        self, make_case, person_at, without_vocabularies
    ):
        kind = "project"
        case = make_case(kind)
        editor = person_at(case, ContributionLevel.EDIT)
        client = browser_as(editor)
        case.record.tags.add("old")

        opened = client.get(case.url("keywords"))

        assert opened.status_code == 200
        assert opened.context["form"]["tags"].value() == ["old"]
        payload = form_payload(main_form(opened))
        payload["tags"] = ["old", "added"]
        response = client.post(case.url("keywords"), payload)
        assert response.status_code == 302
        stored = type(case.record).objects.get(pk=case.record.pk)
        assert sorted(stored.tags.names()) == ["added", "old"]


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
    def test_the_readiness_items_carry_the_shared_editing_pages(
        self, make_case, person_at, kind
    ):
        case = make_case(kind)
        if kind == "dataset":
            case.record.published = False
            case.record.save()
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.own_url)

        addresses = {item["url"] for item in response.context["readiness"]["items"]}
        assert {
            case.url("edit"),
            case.url("descriptions"),
            case.url("keywords"),
            case.url("key-dates"),
        } <= addresses
        assert f"{case.own_url}update/" not in addresses


def landing_for(case):
    """Return where deleting the record leads: its dataset's page, or a list page."""
    if case.kind in {"sample", "measurement"}:
        return case.record.dataset.get_absolute_url()
    return reverse(f"{case.kind}-list")


def dataset_of(case):
    """Return the dataset a record belongs to, the dataset itself for a dataset."""
    return case.record if case.kind == "dataset" else case.record.dataset


@pytest.mark.django_db
class TestDeleteRecord:
    def test_opening_the_page_deletes_nothing_and_asks_for_confirmation(
        self, make_case, person_at
    ):
        kind = "project"
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        assert response.status_code == 200
        assert response.context["is_protected"] is False
        assert "confirmation" in form_payload(main_form(response))
        assert still_exists(case.record)

    def test_a_wrong_confirmation_deletes_nothing(self, make_case, person_at):
        kind = "project"
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).post(
            case.url("delete"), {"confirmation": "something else"}
        )

        assert response.status_code == 200
        assert response.context["form"].errors.get("confirmation")
        assert still_exists(case.record)
        assert list(get_messages(response.wsgi_request)) == []

    @pytest.mark.parametrize("kind", KINDS)
    def test_confirming_deletes_the_record_and_lands_on_a_page_that_exists(
        self, make_case, person_at, kind
    ):
        case = make_case(kind, public=False)
        held = (
            Case("dataset", dataset_of(case))
            if kind in {"sample", "measurement"}
            else case
        )
        manager = person_at(held, ContributionLevel.MANAGE)
        client = browser_as(manager)
        landing = landing_for(case)

        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 302
        assert response.url == landing
        assert not still_exists(case.record)
        assert [m.level for m in get_messages(response.wsgi_request)] == [SUCCESS]
        assert client.get(response.url).status_code == 200

    def test_a_person_who_may_not_open_the_dataset_lands_on_the_dataset_list(
        self, make_case, person_at
    ):
        kind = "sample"
        case = make_case(kind, public=False)
        holder = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(holder)
        assert client.get(dataset_of(case).get_absolute_url()).status_code == 404

        response = client.post(
            case.url("delete"), {"confirmation": delete_confirmation(case)}
        )

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not still_exists(case.record)

    def test_a_dataset_counts_what_goes_with_it_by_record_type(
        self, make_case, person_at
    ):
        case = make_case("dataset", public=False)
        RockSampleFactory(dataset=case.record)
        sample = RockSampleFactory(dataset=case.record)
        ExampleMeasurementFactory(dataset=case.record, sample=sample)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        groups = response.context["related_objects"]
        assert len(groups) == 2
        assert any("(2)" in line for line in groups[0][1])
        assert any("(1)" in line for line in groups[1][1])

    def test_a_project_counts_its_datasets_samples_and_measurements(
        self, make_case, person_at
    ):
        case = make_case("project", public=False)
        dataset = Dataset.all_objects.get(project=case.record)
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        groups = response.context["related_objects"]
        assert len(groups) == 3
        assert all(any("(1)" in line for line in lines) for _, lines, _ in groups)

    def test_a_sample_and_a_measurement_list_the_rows_that_go_with_them(
        self, make_case, person_at
    ):
        kind = "sample"
        case = make_case(kind, public=False)
        factory = {"sample": SampleDateFactory, "measurement": MeasurementDateFactory}[
            kind
        ]
        row = factory(related=case.record)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        listed = [
            item
            for _, items, _ in response.context["related_objects"]
            for item in items
        ]
        assert row in listed

    def test_the_page_does_not_list_the_record_itself(self, make_case, person_at):
        kind = "sample"
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        base = CORE_MODELS[kind]
        listed = [
            item
            for _, items, _ in response.context["related_objects"]
            for item in items
        ]
        assert not [
            item for item in listed if type(item) is base and item.pk == case.record.pk
        ]

    def test_a_sample_does_not_name_a_related_sample_the_viewer_may_not_see(
        self, make_case, person_at
    ):
        case = make_case("sample", public=False)
        elsewhere = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        hidden = RockSampleFactory(dataset=elsewhere, name="Secret sample")
        SampleRelationFactory(source=hidden, target=case.record)
        manager = person_at(
            Case("dataset", case.record.dataset), ContributionLevel.MANAGE
        )

        response = browser_as(manager).get(case.url("delete"))

        assert response.status_code == 200
        page = response.content.decode()
        assert hidden.name not in page
        assert str(hidden.uuid) not in page
        assert not [
            item
            for _, items, _ in response.context["related_objects"]
            for item in items
            if isinstance(item, SampleRelation)
        ]
        assert response.context["related_unlisted"] == 1

    def test_a_sample_lists_a_relation_to_a_sample_the_viewer_may_see(
        self, make_case, person_at
    ):
        case = make_case("sample", public=False)
        neighbour = RockSampleFactory(dataset=case.record.dataset)
        relation = SampleRelationFactory(source=case.record, target=neighbour)
        manager = person_at(
            Case("dataset", case.record.dataset), ContributionLevel.MANAGE
        )

        response = browser_as(manager).get(case.url("delete"))

        listed = [
            item
            for _, items, _ in response.context["related_objects"]
            for item in items
        ]
        assert relation in listed
        assert response.context["related_unlisted"] == 0

    def test_a_project_with_a_public_dataset_lists_it_and_offers_no_confirmation(
        self, make_case, person_at
    ):
        case = make_case("project", public=True)
        public = case.record.datasets.get()
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)

        response = client.get(case.url("delete"))

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert public in response.context["protected_objects"]
        assert response.context["form"] is None
        assert 'name="confirmation"' not in response.content.decode()

        response = client.post(case.url("delete"), {"confirmation": case.record.name})

        assert response.status_code == 200
        assert Project.objects.filter(pk=case.record.pk).exists()

    def test_a_sample_with_measurements_names_those_the_viewer_may_see_and_counts_the_rest(
        self, make_case, person_at
    ):
        measured = make_case("measurement", public=False)
        sample = measured.record.sample
        measured.record.name = "Visible run"
        measured.record.save()
        unnamed = ExampleMeasurementFactory(
            dataset=sample.dataset, sample=sample, name="", char_field="plain value"
        )
        elsewhere = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        hidden = ExampleMeasurementFactory(
            dataset=elsewhere,
            sample=sample,
            name="Secret run",
            char_field="secret value",
        )
        case = Case("sample", sample)
        manager = ContributionFactory(
            content_object=sample.dataset,
            contributor=PersonFactory(is_active=True, is_claimed=True, password="x"),
            level=ContributionLevel.MANAGE,
        ).contributor
        client = browser_as(manager)

        response = client.get(case.url("delete"))

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert response.context["form"] is None
        page = response.content.decode()
        assert "Visible run" in page
        assert str(unnamed.uuid) in page
        for private in ("Secret run", "secret value", str(hidden.uuid)):
            assert private not in page
        assert response.context["protected_unlisted"] == 1

        response = client.post(case.url("delete"), {"confirmation": sample.name})

        assert response.status_code == 200
        assert Sample.objects.filter(pk=sample.pk).exists()
        assert Measurement.objects.filter(pk=hidden.pk).exists()

    def test_a_dataset_whose_sample_is_measured_in_another_dataset_shows_the_protected_state(
        self, make_case, person_at
    ):
        case = make_case("dataset", public=False)
        sample = RockSampleFactory(dataset=case.record)
        elsewhere = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        ExampleMeasurementFactory(dataset=elsewhere, sample=sample)
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)

        response = client.get(case.url("delete"))

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert response.context["form"] is None
        assert response.context["protected_unlisted"] == 1

        response = client.post(case.url("delete"), {"confirmation": case.record.name})

        assert response.status_code == 200
        assert still_exists(case.record)
        assert Sample.objects.filter(pk=sample.pk).exists()

    def test_a_project_that_became_protected_after_the_page_was_opened_is_not_deleted(
        self, make_case, person_at
    ):
        case = make_case("project", public=False)
        dataset = Dataset.all_objects.get(project=case.record)
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)
        assert client.get(case.url("delete")).context["is_protected"] is False

        dataset.visibility = Visibility.PUBLIC
        dataset.save()
        response = client.post(case.url("delete"), {"confirmation": case.record.name})

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert dataset in response.context["protected_objects"]
        assert Project.objects.filter(pk=case.record.pk).exists()

    def test_a_sample_that_became_protected_after_the_page_was_opened_is_not_deleted(
        self, make_case, person_at
    ):
        case = make_case("sample", public=False)
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)
        assert client.get(case.url("delete")).context["is_protected"] is False

        ExampleMeasurementFactory(dataset=case.record.dataset, sample=case.record)
        response = client.post(case.url("delete"), {"confirmation": case.record.name})

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert Sample.objects.filter(pk=case.record.pk).exists()

    def test_a_measurement_without_a_name_is_confirmed_by_its_portal_id(
        self, make_case, person_at
    ):
        case = make_case("measurement", public=False)
        case.record.name = ""
        case.record.save()
        manager = person_at(case, ContributionLevel.MANAGE)
        client = browser_as(manager)

        refused = client.post(case.url("delete"), {"confirmation": "a note"})

        assert refused.status_code == 200
        assert Measurement.objects.filter(pk=case.record.pk).exists()

        response = client.post(
            case.url("delete"), {"confirmation": str(case.record.uuid)}
        )

        assert response.status_code == 302
        assert not Measurement.objects.filter(pk=case.record.pk).exists()

    def test_the_back_control_leads_to_the_records_own_page(self, make_case, person_at):
        kind = "project"
        case = make_case(kind, public=False)
        manager = person_at(case, ContributionLevel.MANAGE)

        response = browser_as(manager).get(case.url("delete"))

        assert response.context["back_url"] == case.own_url

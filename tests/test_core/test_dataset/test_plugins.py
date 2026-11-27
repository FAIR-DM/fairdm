"""Tests for the dataset's registered pages: update, descriptions, deletion, menu and links."""

import codecs
import json
import re
from datetime import UTC, date, datetime

import latexcodec  # noqa: F401  (registers the "ulatex" codec)
import pytest
import rispy
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.test import RequestFactory
from django.urls import reverse
from django.utils.formats import date_format
from licensing.models import License
from partial_dates import PartialDate
from pybtex.database import parse_string
from pytest_django.asserts import assertContains

from demo.factories import RockSampleFactory
from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.contrib.plugins.access import can_open
from fairdm.contrib.plugins.base import Plugin
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDescription,
    DatasetLiteratureRelation,
)
from fairdm.core.dataset.plugins import Overview
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
)
from fairdm.factories import (
    ContributionFactory,
    DatasetDateFactory,
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    DatasetLiteratureRelationFactory,
    LiteratureItemFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

# `DatasetFactory()` produces private datasets unless told otherwise.

pytestmark = pytest.mark.django_db


def _request_for(user, path="/"):
    request = RequestFactory().get(path)
    request.user = user
    return request


def _entry_view_names(model):
    """Return the view name of each entry in the model's plugin menu."""
    plugins.registry.get_urls_for_model(model)
    menu = plugins.registry.get_plugin_menu_for_model(model)
    return [item.view_name for item in menu.children]


def _dataset_field_data(dataset):
    """Return the attributes form's field values, unchanged from `dataset`."""
    return {
        "name": dataset.name,
        "project": dataset.project_id or "",
        "license": dataset.license_id,
        "visibility": dataset.visibility,
    }


def _identifier_management_data(total=0, initial=0):
    """Return management-form data for the identifiers row set."""
    return {
        "identifiers-TOTAL_FORMS": str(total),
        "identifiers-INITIAL_FORMS": str(initial),
        "identifiers-MIN_NUM_FORMS": "0",
        "identifiers-MAX_NUM_FORMS": "1000",
    }


def _date_management_data(total=0, initial=0):
    """Return management-form data for the dates row set."""
    return {
        "dates-TOTAL_FORMS": str(total),
        "dates-INITIAL_FORMS": str(initial),
        "dates-MIN_NUM_FORMS": "0",
        "dates-MAX_NUM_FORMS": "1000",
    }


class TestUpdatePageDoesNotDiscloseAPrivateDataset:
    def test_a_model_level_grant_adds_nothing_to_a_view_level(self, client):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        url = reverse("dataset:edit", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 403


class TestUpdatePageAttributesPersist:
    def test_changing_name_project_license_visibility_and_reference_each_persists(
        self, client
    ):
        original_project = None
        license_a = License.objects.get_or_create(name="CC BY 4.0")[0]
        license_b = License.objects.get_or_create(name="CC0 1.0")[0]
        reference = LiteratureItemFactory()
        user = UserFactory()

        from fairdm.factories import ProjectFactory

        changed_project = ProjectFactory()
        ContributionFactory(
            content_object=changed_project,
            contributor=user,
            level=ContributionLevel.EDIT,
        )

        changes = {
            "name": "Changed Name",
            "license": license_b.pk,
            "visibility": Visibility.PUBLIC,
            "reference": reference.pk,
            "project": changed_project.pk,
        }

        for field, new_value in changes.items():
            dataset = DatasetFactory(
                name="Original Name",
                license=license_a,
                visibility=Visibility.PRIVATE,
                project=original_project,
            )
            ContributionFactory(
                content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
            )
            client.force_login(user)
            url = reverse("dataset:edit", kwargs={"uuid": dataset.uuid})
            data = {
                **_dataset_field_data(dataset),
                field: new_value,
                **_identifier_management_data(),
                **_date_management_data(),
            }

            response = client.post(url, data=data)

            assert response.status_code == 302, response.context["form"].errors
            dataset.refresh_from_db()
            if field in ("project", "license", "reference"):
                assert getattr(dataset, f"{field}_id") == new_value
            else:
                assert getattr(dataset, field) == new_value


class TestUpdatePageProjectField:
    def test_the_project_field_is_narrowed_to_the_researchers_own_projects(
        self, client
    ):
        from fairdm.factories import ProjectFactory

        dataset = DatasetFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)

        own_project = ProjectFactory(name="Researcher's Own Project")
        other_project = ProjectFactory(name="Someone Else's Project")
        ContributionFactory(
            content_object=own_project,
            contributor=user,
            level=ContributionLevel.EDIT,
        )

        url = reverse("dataset:edit", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        project_queryset = response.context["form"].fields["project"].queryset
        assert own_project in project_queryset
        assert other_project not in project_queryset


@pytest.mark.django_db
class TestDescriptionsPageAreasAreLabelledFromTheVocabulary:
    def test_the_first_areas_label_and_help_text_match_its_concept(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        concept = DatasetDescription.get_type_concepts()[0]
        first_type = concept.uri

        url = reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.display_label()
        assert form.fields[first_type].help_text == concept.first_value(
            "skos:definition"
        )


@pytest.mark.django_db
class TestEditingAnExistingDescriptionPersists:
    def test_the_changed_text_persists(self, client, user_with_change_permission):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = next(
            concept.uri for concept in DatasetDescription.get_type_concepts()
        )
        row = DatasetDescription.objects.create(
            related=dataset, type_id=first_type, value="Original text."
        )

        url = reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "Changed text."})

        row.refresh_from_db()
        assert row.value == "Changed text."
        assert DatasetDescription.objects.filter(related=dataset).count() == 1


@pytest.mark.django_db
class TestEmptyAndWhitespaceOnlyAreasCreateNothing:
    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = next(
            concept.uri for concept in DatasetDescription.get_type_concepts()
        )
        DatasetDescription.objects.create(
            related=dataset, type_id=first_type, value="Existing text."
        )

        url = reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "   \n  "})

        assert not DatasetDescription.objects.filter(
            related=dataset, type=first_type
        ).exists()


def _hrefs(content: str) -> list[str]:
    """Return every ``href`` attribute value in rendered HTML, in document order."""
    return re.findall(r'href="([^"]*)"', content)


class TestEachOfTheFourPagesStatesItsOwnPermission:
    def test_a_page_stating_no_permission_does_not_inherit_its_owners(self):
        class _OwnerWithPermission(Plugin):
            permission = "dataset.delete_dataset"

        class _ChildStatingNone(Plugin):
            plugin_class = _OwnerWithPermission
            check = staticmethod(lambda request, obj: True)

        request = _request_for(AnonymousUser())
        assert can_open(_ChildStatingNone, request, None) is True


@pytest.mark.django_db
class TestEachOfTheFourPagesGuardsAPrivateDatasetsVisibility:
    def test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record(
        self, client
    ):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        for name in (
            "dataset:overview",
            "dataset:edit",
            "dataset:descriptions",
            "dataset:delete",
        ):
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 404, name


@pytest.mark.django_db
class TestTheDatasetsPagesContributeExactlyOneNavigationEntry:
    def test_overview_contributes_exactly_one_entry(self):
        assert _entry_view_names(Dataset).count("dataset:overview") == 1


@pytest.mark.django_db
class TestEveryLinkTheDatasetsPagesDrawResolvesToARealAddress:
    def _permitted_user(self, dataset):
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        return user

    def test_the_datasets_own_page_draws_no_empty_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)


@pytest.mark.django_db
class TestUpdateDescriptionsAndDeletionEachLinkBackToTheDataset:
    def test_the_update_page_links_back_to_the_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = client.get(reverse("dataset:edit", kwargs={"uuid": dataset.uuid}))

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')


@pytest.fixture
def in_private_project():
    """A public, published dataset inside a private project."""
    return DatasetFactory(
        project=ProjectFactory(visibility=Visibility.PRIVATE),
        visibility=Visibility.PUBLIC,
        published=True,
    )


@pytest.mark.django_db
class TestAPrivateProjectHidesThePublicDatasetsInIt:
    ADDRESSES = (
        "dataset:overview",
        "dataset:edit",
        "dataset:descriptions",
        "dataset:delete",
    )

    def addresses_of(self, dataset):
        overview = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        return [
            *(reverse(name, kwargs={"uuid": dataset.uuid}) for name in self.ADDRESSES),
            f"{overview}contributors/",
        ]

    def test_an_anonymous_visitor_gets_not_found_at_every_address(
        self, client, in_private_project
    ):
        for address in self.addresses_of(in_private_project):
            assert client.get(address).status_code == 404, address

    def test_a_signed_in_stranger_gets_not_found_at_every_address(
        self, client, in_private_project
    ):
        client.force_login(UserFactory())

        for address in self.addresses_of(in_private_project):
            assert client.get(address).status_code == 404, address

    @pytest.mark.parametrize("held_on", ["dataset", "project"])
    def test_a_level_on_the_dataset_or_its_project_opens_the_dataset(
        self, client, in_private_project, held_on
    ):
        user = UserFactory()
        record = (
            in_private_project if held_on == "dataset" else in_private_project.project
        )
        ContributionFactory(
            content_object=record, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": in_private_project.uuid})
        )

        assert response.status_code == 200

    def test_a_sample_inside_is_not_found_for_a_visitor(
        self, client, in_private_project
    ):
        sample = RockSampleFactory(dataset=in_private_project)

        assert client.get(sample.get_absolute_url()).status_code == 404


def _page(client, dataset):
    """Open the dataset's page and return the response with its parsed HTML."""
    response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _context(dataset, user=None):
    """Return the overview's context, built straight from the plugin with no page render."""
    request = RequestFactory().get(
        reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
    )
    request.user = user or AnonymousUser()
    request.site = Site.objects.get_current()  # what the site middleware sets
    view = Overview()
    view.setup(request, uuid=dataset.uuid)
    view.base_object = Dataset.all_objects.get(pk=dataset.pk)
    return view.get_context_data()


def _figures(page):
    """The values of the four figures, in the order they are drawn."""
    return [figure.get_text(strip=True) for figure in page.select(".ov-figure__value")]


def _tab_figures(page, dataset):
    """Return the Samples and Measurements figures as ``{tab: value}``, found by their link."""
    figures = {}
    for kind in ("samples", "measurements"):
        url = reverse(f"dataset:{kind}", kwargs={"uuid": dataset.uuid})
        figure = page.select_one(f'a.ov-figure[href="{url}"]')
        if figure is not None:
            figures[kind] = figure.select_one(".ov-figure__value").get_text(strip=True)
    return figures


def _tab_total(client, dataset, kind):
    """Return how many records the tab lists, added up across its types."""
    response = client.get(reverse(f"dataset:{kind}", kwargs={"uuid": dataset.uuid}))
    return sum(entry["count"] for entry in response.context["type_entries"])


def _json_ld(page):
    return json.loads(page.head.find("script", type="application/ld+json").string)


def _team_member(dataset, *permissions):
    """Return a signed-in-ready user listed on the dataset at the lowest level that holds the permissions."""
    user = UserFactory()
    level = ContributionLevel.VIEW
    if "change_dataset" in permissions:
        level = ContributionLevel.EDIT
    if "delete_dataset" in permissions:
        level = ContributionLevel.MANAGE
    ContributionFactory(content_object=dataset, contributor=user, level=level)
    return user


@pytest.fixture(scope="class")
def holding(django_db_setup, django_db_blocker):
    """A public, unpublished dataset holding two rock samples and two XRF measurements.

    Built once per test class inside a transaction that rolls back when the class
    ends. Each test runs in a savepoint of it, so a test that changes the dataset
    leaves it as it was for the next one.
    """
    from datetime import UTC, datetime

    from django.db import transaction

    from demo.factories import RockSampleFactory, XRFMeasurementFactory
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

    with django_db_blocker.unblock():
        outer = transaction.atomic()
        outer.__enter__()
        try:
            dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
            rocks = [
                RockSampleFactory(dataset=dataset, name=f"Zq-{n}-4471 rift core")
                for n in (1, 2)
            ]
            XRFMeasurementFactory.create_batch(2, dataset=dataset, sample=rocks[0])
            Sample.objects.filter(dataset=dataset).update(
                added=datetime(2026, 1, 15, tzinfo=UTC)
            )
            Measurement.objects.filter(dataset=dataset).update(
                added=datetime(2026, 3, 15, tzinfo=UTC)
            )
            yield dataset
        finally:
            transaction.set_rollback(True)
            outer.__exit__(None, None, None)


class TestOverviewWhatAVisitorSeesBeforePublication:
    """US-2 scenarios 1 to 3 and FR-022, FR-024."""

    def test_the_team_sees_the_counts_and_both_charts_and_a_notice(
        self, client, holding
    ):
        client.force_login(_team_member(holding))

        response = _page(client, holding)

        assert _figures(response.page)[:2] == ["2", "2"]
        assert response.page.select_one(".ov-mix") is not None
        assert response.page.find(id="dataset-growth") is not None
        assert len(response.page.select(".alert")) == 1

    def test_a_visitor_sees_the_notice_and_no_counts_or_charts(self, client, holding):
        response = _page(client, holding)

        assert _tab_figures(response.page, holding) == {}
        assert response.page.select_one(".ov-mix") is None
        assert response.page.find(id="dataset-growth") is None
        assert len(response.page.select(".alert")) == 1

    def test_a_visitor_is_shown_the_abstract(self, client, holding):
        DatasetDescriptionFactory(
            related=holding,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Cores from the rift.",
        )

        response = _page(client, holding)

        assertContains(response, "Cores from the rift.")

    def test_the_team_of_an_unpublished_dataset_sees_the_checklist(
        self, client, holding
    ):
        client.force_login(_team_member(holding, "change_dataset"))

        response = _page(client, holding)

        assert response.page.select_one('[data-card="readiness"]') is not None

    def test_a_visitor_sees_no_checklist(self, client, holding):
        response = _page(client, holding)

        assert response.page.select_one('[data-card="readiness"]') is None

    def test_a_published_dataset_shows_its_team_no_checklist_and_no_notice(
        self, client, holding
    ):
        Dataset.all_objects.filter(pk=holding.pk).update(published=True)
        client.force_login(_team_member(holding, "change_dataset"))

        response = _page(client, holding)

        assert response.page.select_one('[data-card="readiness"]') is None
        assert response.page.select(".alert") == []


class TestOverviewEmptyCardFollowsWhatTheViewerMaySee:
    """FR-022: an unpublished dataset's overview says nothing of whether it holds records."""

    def test_the_team_sees_the_empty_card_on_an_empty_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(_team_member(dataset))

        response = _page(client, dataset)

        assert response.page.find(id="dataset-no-records") is not None

    def test_a_visitor_sees_the_card_on_neither_an_empty_nor_a_full_dataset(
        self, client, holding
    ):
        empty = DatasetFactory(visibility=Visibility.PUBLIC, published=False)

        assert _page(client, empty).page.find(id="dataset-no-records") is None
        assert _page(client, holding).page.find(id="dataset-no-records") is None


class TestOverviewEmptyCardImportButton:
    """The Import data button of an empty dataset opens the dialog of types."""

    def test_the_team_gets_a_dialog_of_sample_and_measurement_types(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(_team_member(dataset, "change_dataset"))

        card = _page(client, dataset).page.find(id="dataset-no-records")

        button = card.select_one("button[aria-haspopup=dialog]")
        assert button is not None
        dialog = card.select_one("dialog")
        assert dialog is not None
        assert dialog.select_one(".record-sample") is not None
        assert dialog.select_one(".record-measurement") is not None
        assert card.select_one("[disabled]") is None

    def test_a_dialog_entry_leads_to_the_import_page_of_its_type(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(_team_member(dataset, "change_dataset"))

        card = _page(client, dataset).page.find(id="dataset-no-records")

        links = [a["href"] for a in card.select("dialog a[href]")]
        assert links
        assert all("/import/" in href for href in links)
        assert all(str(dataset.uuid) in href for href in links)

    def test_a_viewer_who_may_not_manage_gets_no_button(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        client.force_login(_team_member(dataset))

        page = _page(client, dataset).page

        assert page.select_one("#dataset-no-records button") is None
        assert page.select("dialog[id^=ie-import-]") == []


class TestOverviewReadinessChecklist:
    """FR-033: seven required items and three recommended ones."""

    def test_a_complete_but_private_dataset_is_ready_because_publishing_makes_it_public(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        DatasetDescriptionFactory(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract", value="Cores."
        )
        DatasetDescriptionFactory(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/methods", value="Drilled."
        )
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/collection-start",
            value=PartialDate.fromisoformat("2024-01-01"),
        )
        dataset.add_contributor(
            PersonFactory(is_active=True),
            with_roles=[
                f"{CONTRIBUTOR_ROLES}/creator",
                f"{CONTRIBUTOR_ROLES}/contact-person",
            ],
        )
        from demo.factories import RockSampleFactory

        RockSampleFactory(dataset=dataset)
        user = _team_member(dataset, "change_dataset")

        readiness = _context(dataset, user)["readiness"]

        assert readiness["ready"] is True
        assert readiness["missing_required"] == 0


class TestOverviewCitation:
    """US-2 scenario 4."""

    def _citation(self, dataset):
        formats = _context(dataset)["citation"]["formats"]
        return next(entry["value"] for entry in formats if entry["key"] == "text")

    def test_without_a_doi_the_schema_org_identifier_is_the_permalink(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        data = _json_ld(_page(client, dataset).page)

        assert data["identifier"] == f"http://testserver/{dataset.uuid}/"

    def test_creators_are_named_in_the_order_credited_people_before_organizations(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        partner = OrganizationFactory(name="Acme Lab")
        dataset.add_contributor(partner, with_roles=[f"{CONTRIBUTOR_ROLES}/creator"])
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            moving = dataset.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        Crediting(dataset).move(moving, "up")

        assert self._citation(dataset).startswith(
            "Oliveira, T., Keller, A. & Acme Lab ("
        )

    def test_a_person_left_out_of_the_citation_is_not_named_in_any_format(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            left_out = dataset.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        left_out.in_citation = False
        left_out.save()

        shown = _context(dataset)["citation"]["formats"]
        formats = {f["key"]: f["value"] for f in shown}
        assert self._citation(dataset).startswith("Keller, A. (")
        assert "Oliveira" not in formats["bibtex"]
        assert "Oliveira" not in formats["ris"]

    def test_a_person_left_out_of_the_citation_is_still_in_the_header_and_people(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        credit = dataset.add_contributor(
            PersonFactory(first_name="Tomas", last_name="Oliveira", is_active=True),
            with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
        )
        credit.in_citation = False
        credit.save()

        header_people = _context(dataset)["header_people"]

        assert [p.pk for p in header_people] == [credit.contributor_id]

    def test_with_every_person_left_out_the_citation_names_the_organizations(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.add_contributor(
            OrganizationFactory(name="Acme Lab"),
            with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
        )
        credit = dataset.add_contributor(
            PersonFactory(first_name="Anna", last_name="Keller", is_active=True),
            with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
        )
        credit.in_citation = False
        credit.save()

        assert self._citation(dataset).startswith("Acme Lab (")

    def test_a_person_left_out_of_the_citation_is_not_a_schema_org_creator(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            left_out = dataset.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        left_out.in_citation = False
        left_out.save()

        data = _json_ld(_page(client, dataset).page)

        assert [c["familyName"] for c in data["creator"]] == ["Keller"]

    def test_without_one_the_year_is_the_published_date(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/published",
            value=PartialDate.fromisoformat("2021-05-04"),
        )
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/available",
            value=PartialDate.fromisoformat("2022-01-01"),
        )

        assert "(2021)" in self._citation(dataset)

    def test_without_a_published_date_the_year_is_the_available_date(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/available",
            value=PartialDate.fromisoformat("2022-01-01"),
        )

        assert "(2022)" in self._citation(dataset)

    def test_without_either_the_year_is_when_the_record_was_added(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        assert f"({dataset.added.year})" in self._citation(dataset)


class TestOverviewCharts:
    """US-2 scenarios 5 to 7."""

    def test_the_records_by_type_count_every_type_samples_and_measurements_apart(
        self, client, holding
    ):
        mix = _context(holding, _team_member(holding))["mix"]

        assert mix["samples"] == [("Rock Samples", 2)]
        assert mix["measurements"] == [("XRF Measurements", 2)]

    def test_records_within_one_month_draw_no_growth_chart(self, client, holding):
        from datetime import UTC, datetime

        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        Sample.objects.update(added=datetime(2026, 1, 15, tzinfo=UTC))
        Measurement.objects.update(added=datetime(2026, 1, 20, tzinfo=UTC))
        context = _context(holding, _team_member(holding))

        assert context["mix"] is not None
        assert context["growth_chart"] is None

    def test_a_type_the_registry_no_longer_holds_is_left_out(
        self, client, holding, monkeypatch
    ):
        from demo.models import XRFMeasurement
        from fairdm.registry import registry

        held = {
            model: config
            for model, config in registry._registry.items()
            if model is not XRFMeasurement
        }
        monkeypatch.setattr(registry, "_registry", held)
        mix = _context(holding, _team_member(holding))["mix"]

        assert mix["measurements"] == []
        assert mix["samples"] == [("Rock Samples", 2)]


class TestOverviewHeaderFacts:
    """FR-030: the licence and the resolving identifier are key facts in the header."""

    def header_of(self, client, dataset):
        return _page(client, dataset).page.find("h1").find_parent("header")

    def test_the_licence_is_named_and_the_doi_linked(self, client):
        licence = License.objects.get(name="CC BY 4.0")
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, license=licence)
        DatasetIdentifierFactory(related=dataset, value="10.1/ds")

        header = self.header_of(client, dataset)

        assert licence.name in header.get_text()
        assert header.find("a", href="https://doi.org/10.1/ds") is not None

    def test_a_dataset_with_no_licence_shows_a_dash_and_no_identifier(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, license=None)

        facts = self.header_of(client, dataset).select_one(".ov-facts")

        assert "—" in facts.get_text()
        assert facts.find("a", href=re.compile("doi.org")) is None


class TestOverviewFiguresLeadToTheirLists:
    """FR-031: the contributors figure leads to the contributors tab.

    The publications figure leads to the Related publications panel.
    """

    def test_the_contributors_figure_links_to_the_contributors_tab(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        url = reverse("dataset:contribution-list", kwargs={"uuid": dataset.uuid})

        page = _page(client, dataset).page

        assert page.select_one(f'a.ov-figure[href="{url}"]') is not None

    def test_the_publications_figure_links_to_the_publications_panel(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        page = _page(client, dataset).page

        assert page.select_one('a.ov-figure[href="#publications"]') is not None
        assert page.find(id="publications")["data-card"] == "publications"


class TestOverviewFiguresLeadToTheTabs:
    """The Samples and Measurements figures link to the tabs and agree with them."""

    @pytest.fixture
    def published(self):
        from demo.factories import (
            SoilSampleFactory,
            XRFMeasurementFactory,
        )

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        rocks = RockSampleFactory.create_batch(3, dataset=dataset)
        SoilSampleFactory.create_batch(2, dataset=dataset)
        XRFMeasurementFactory.create_batch(4, dataset=dataset, sample=rocks[0])
        return dataset

    def test_a_visitor_and_the_team_get_figures_equal_to_the_tabs_totals(
        self, client, published
    ):
        for user in (None, _team_member(published)):
            if user is not None:
                client.force_login(user)

            figures = _tab_figures(_page(client, published).page, published)

            assert figures == {
                "samples": str(_tab_total(client, published, "samples")),
                "measurements": str(_tab_total(client, published, "measurements")),
            }
            assert figures == {"samples": "5", "measurements": "4"}


class TestOverviewFirstRun:
    """US-2 scenario 6."""

    def _unavailable_actions(self, client, dataset):
        page = _page(client, dataset).page
        return len(page.find_all("button", disabled=True))

    def test_the_import_data_button_of_an_empty_dataset_is_not_an_unavailable_step(
        self, client, holding
    ):
        Dataset.all_objects.filter(pk=holding.pk).update(published=True)
        empty = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        client.force_login(_team_member(holding, "change_dataset"))
        with_data = self._unavailable_actions(client, holding)
        client.force_login(_team_member(empty, "change_dataset"))

        assert self._unavailable_actions(client, empty) == with_data

    def test_an_empty_dataset_draws_no_chart(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        client.force_login(_team_member(dataset, "change_dataset"))

        response = _page(client, dataset)

        assert response.page.find(attrs={"data-mvp-chart": True}) is None
        assert response.page.select_one(".ov-mix") is None
        assert response.page.find(id="dataset-growth") is None


class TestOverviewTimeline:
    """US-2 scenarios 8 and 9."""

    def _steps(self, page):
        """The date each timeline step shows, in the order they are drawn."""
        panel = page.select_one('[data-card="timeline"]')
        return [
            item.select_one(".ov-step__date").get_text(strip=True)
            for item in panel.select("ol > li")
        ]

    def test_the_dates_are_listed_in_the_order_they_happened(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        Dataset.all_objects.filter(pk=dataset.pk).update(
            added=datetime(2022, 11, 10, tzinfo=UTC)
        )
        for type_, value in (
            (f"{DATE_TYPES}/available", "2025-06-01"),
            (f"{DATE_TYPES}/published", "2025-05-01"),
            (f"{DATE_TYPES}/submitted", "2025-04-01"),
            (f"{DATE_TYPES}/collection-start", "2023-02-01"),
            (f"{DATE_TYPES}/collection-end", "2023-09-30"),
        ):
            DatasetDateFactory(
                related=dataset, type_id=type_, value=PartialDate.fromisoformat(value)
            )

        steps = self._steps(_page(client, dataset).page)

        assert steps[0] == date_format(date(2022, 11, 10), "SHORT_DATE_FORMAT")
        assert steps[1].startswith(date_format(date(2023, 2, 1), "SHORT_DATE_FORMAT"))
        assert steps[2:] == [
            date_format(day, "SHORT_DATE_FORMAT")
            for day in (date(2025, 4, 1), date(2025, 5, 1), date(2025, 6, 1))
        ]

    def test_a_withdrawn_dataset_says_so_and_the_withdrawal_ends_its_timeline(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/withdrawn",
            value=PartialDate.fromisoformat("2999-01-01"),
        )
        when = date_format(date(2999, 1, 1), "SHORT_DATE_FORMAT")

        response = _page(client, dataset)

        assert when in response.page.select_one(".alert").get_text()
        assert self._steps(response.page)[-1] == when

    def test_a_collection_period_is_shown_as_precisely_as_it_was_recorded(self, client):
        year_only = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        month_only = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetDateFactory(
            related=year_only,
            type_id=f"{DATE_TYPES}/collection-start",
            value=PartialDate.fromisoformat("2023"),
        )
        DatasetDateFactory(
            related=month_only,
            type_id=f"{DATE_TYPES}/collection-start",
            value=PartialDate.fromisoformat("2023-02"),
        )

        year_steps = self._steps(_page(client, year_only).page)
        month_steps = self._steps(_page(client, month_only).page)

        assert "2023 \u2013" in year_steps[0]
        assert date_format(date(2023, 1, 1), "SHORT_DATE_FORMAT") not in year_steps[0]
        assert month_steps[0].startswith(
            date_format(date(2023, 2, 1), "YEAR_MONTH_FORMAT")
        )
        assert date_format(date(2023, 2, 1), "SHORT_DATE_FORMAT") not in month_steps[0]

    def test_a_withdrawal_recorded_to_the_year_is_shown_as_the_year(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/withdrawn",
            value=PartialDate.fromisoformat("2999"),
        )

        response = _page(client, dataset)

        notice = response.page.select_one(".alert").get_text()
        assert "2999" in notice
        assert date_format(date(2999, 1, 1), "SHORT_DATE_FORMAT") not in notice
        assert self._steps(response.page)[-1] == "2999"

    def test_an_unpublished_dataset_ends_on_a_publication_still_to_come(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)

        last = _context(dataset)["lifecycle"][-1]

        assert (last["done"], last["date"]) == (False, None)

    def test_a_published_dataset_with_no_published_date_has_the_step_done_and_undated(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        response = _page(client, dataset)

        last = response.context["lifecycle"][-1]
        assert (last["done"], last["date"]) == (True, None)
        assert self._steps(response.page)[-1].startswith("—")

    def test_a_recorded_published_date_is_the_only_publication_step(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/published",
            value=PartialDate.fromisoformat("2025-05-01"),
        )

        steps = _context(dataset)["lifecycle"]

        assert [step["done"] for step in steps] == [True, True]

    def test_an_undated_publication_comes_before_a_withdrawal(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/withdrawn",
            value=PartialDate.fromisoformat("2999-01-01"),
        )

        steps = _context(dataset)["lifecycle"]

        assert [step["date"] is None for step in steps] == [False, True, False]
        assert [step["alert"] for step in steps] == [False, False, True]


class TestOverviewRelatedPublications:
    """US-2 scenario 10."""

    def test_each_relation_is_worded_from_the_publications_side_and_the_closest_come_first(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        items = {}
        for relation in ("Cites", "IsCitedBy", "IsDescribedBy"):
            items[relation] = LiteratureItemFactory()
            DatasetLiteratureRelationFactory(
                dataset=dataset,
                literature_item=items[relation],
                relationship_type=relation,
            )

        response = _page(client, dataset)

        panel = response.page.select_one('[data-card="publications"]')
        listed = panel.select("ul > li")
        order = [
            next(name for name, item in items.items() if str(item) in li.get_text())
            for li in listed
        ]
        assert order == ["IsDescribedBy", "IsCitedBy", "Cites"]
        for name, li in zip(order, listed, strict=True):
            dataset_side = DatasetLiteratureRelation(relationship_type=name)
            relation = li.select_one(".ov-awards__title").get_text(strip=True)
            assert relation.split(" · ")[0] != (
                dataset_side.get_relationship_type_display()
            )


class TestOverviewProject:
    """US-2 scenario 11."""

    def test_a_project_the_viewer_may_not_see_is_neither_named_nor_linked(self, client):
        project = ProjectFactory(
            visibility=Visibility.PRIVATE, name="Secret Rift Programme"
        )
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, project=project)
        viewer = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=viewer, level=ContributionLevel.VIEW
        )
        client.force_login(viewer)

        response = _page(client, dataset)

        assert project.name not in response.content.decode()
        assert project.get_absolute_url() not in response.content.decode()
        assert "isPartOf" not in _json_ld(response.page)

    def test_a_project_the_viewer_may_see_is_named_and_linked(self, client):
        project = ProjectFactory(
            visibility=Visibility.PUBLIC, name="Open Rift Programme"
        )
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, project=project)

        response = _page(client, dataset)

        assert response.page.find("a", href=project.get_absolute_url()) is not None
        assert _json_ld(response.page)["isPartOf"]["name"] == "Open Rift Programme"


@pytest.mark.django_db
class TestOverviewProjectSiblingCount:
    """SC-003: the count of other datasets in the project never includes one the viewer cannot open."""

    @pytest.fixture
    def project(self):
        return ProjectFactory(visibility=Visibility.PUBLIC)

    @pytest.fixture
    def team_dataset(self, project):
        return DatasetFactory(visibility=Visibility.PUBLIC, project=project)

    @pytest.fixture
    def hidden(self, project):
        return DatasetFactory(visibility=Visibility.PRIVATE, project=project)

    def _siblings(self, user, dataset):
        return _context(dataset, user)["project_info"]["siblings"]

    def test_a_team_member_is_not_told_about_a_private_dataset_they_cannot_open(
        self, client, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")

        assert self._siblings(user, team_dataset) == 0

    def test_a_private_dataset_the_viewer_may_open_is_counted(
        self, client, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")
        ContributionFactory(
            content_object=hidden, contributor=user, level=ContributionLevel.VIEW
        )

        assert self._siblings(user, team_dataset) == 1

    def test_a_private_dataset_with_only_a_stored_row_is_not_counted(
        self, client, team_dataset, hidden
    ):
        from fairdm.core.utils import assign_perm

        user = _team_member(team_dataset, "change_dataset")
        assign_perm("view_dataset", user, hidden)

        assert self._siblings(user, team_dataset) == 0

    def test_a_private_dataset_under_a_level_on_the_project_is_counted(
        self, client, project, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.VIEW
        )

        assert self._siblings(user, team_dataset) == 1

    def test_a_public_dataset_is_counted(self, client, project, team_dataset):
        DatasetFactory(visibility=Visibility.PUBLIC, project=project)
        user = _team_member(team_dataset, "change_dataset")

        assert self._siblings(user, team_dataset) == 1

    def test_someone_who_manages_the_project_counts_every_dataset(
        self, client, project, team_dataset, hidden
    ):
        user = _team_member(team_dataset)
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )

        assert self._siblings(user, team_dataset) == 1


class TestOverviewSchemaOrgDescription:
    """FR-034 and FR-056."""

    def test_a_visitor_to_a_public_unpublished_dataset_gets_no_variables(
        self, client, holding
    ):
        data = _json_ld(_page(client, holding).page)

        assert data["@type"] == "Dataset"
        assert "variableMeasured" not in data

    def test_the_team_of_a_public_unpublished_dataset_names_its_variables_and_carries_no_values(
        self, client, holding
    ):
        from demo.models import XRFMeasurement
        from fairdm.core.sample.models import Sample

        client.force_login(_team_member(holding))
        response = _page(client, holding)

        data = _json_ld(response.page)
        assert data["@type"] == "Dataset"
        assert data["variableMeasured"]
        serialised = json.dumps(data)
        for sample in Sample.objects.filter(dataset=holding):
            assert sample.name not in serialised
        for measurement in XRFMeasurement.objects.filter(dataset=holding):
            assert str(measurement.concentration_ppm) not in serialised

    def test_a_dataset_holding_nothing_names_no_variables(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        assert "variableMeasured" not in _json_ld(_page(client, dataset).page)

    def test_it_carries_no_contributor_email_address(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        person = PersonFactory(is_active=True)
        dataset.add_contributor(person, with_roles=[f"{CONTRIBUTOR_ROLES}/creator"])

        response = _page(client, dataset)

        assert person.email not in response.content.decode()


@pytest.mark.django_db
class TestOverviewCardsAlwaysShown:
    """FR-003 and the Edge Cases: a card the page has is shown even with nothing to put in it."""

    def test_a_bare_dataset_shows_every_side_card_to_a_visitor(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)

        response = _page(client, dataset)

        for card in [
            "details",
            "timeline",
            "people",
            "identifiers",
            "citation",
            "publications",
        ]:
            assert response.page.select_one(f'[data-card="{card}"]') is not None, card


class TestOverviewSampleMap:
    @pytest.fixture
    def published(self):
        """A public, published dataset: two located samples and one with no location."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))
        RockSampleFactory(dataset=dataset, location=Point(8.1, 49.0, srid=4326))
        RockSampleFactory(dataset=dataset, location=None)
        return dataset

    def test_a_visitor_to_a_published_dataset_gets_its_samples(self, published):
        context = _context(published)
        sample_map = context["sample_map"]

        assert sample_map["located"] == 2
        assert sample_map["missing"] == 1
        assert sample_map["bounds"] == [7.9, 48.9, 8.1, 49.0]
        assert (
            sample_map["located"] + sample_map["missing"]
            == (context["counts"]["samples"])
        )
        assert context["has_map"] is True

    def test_the_points_address_is_the_datasets_own(self, published):
        sample_map = _context(published)["sample_map"]

        assert sample_map["points_url"] == reverse(
            "dataset:overview-sample-points", kwargs={"uuid": published.uuid}
        )

    def test_a_visitor_to_a_public_unpublished_dataset_gets_no_map(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))

        context = _context(dataset)

        assert context["sample_map"] is None
        assert "has_map" not in context

    def test_the_team_of_an_unpublished_dataset_gets_the_map(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))

        context = _context(dataset, _team_member(dataset))

        assert context["sample_map"]["located"] == 1
        assert context["has_map"] is True

    def test_a_level_on_one_sample_of_an_unpublished_dataset_maps_nothing(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        sample = RockSampleFactory(
            dataset=dataset, location=Point(7.9, 48.9, srid=4326)
        )
        user = UserFactory()
        ContributionFactory(
            content_object=sample, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        points = client.get(
            reverse("dataset:overview-sample-points", kwargs={"uuid": dataset.uuid})
        )

        assert _context(dataset, user)["sample_map"] is None
        assert points.json()["features"] == []

    def test_the_points_address_of_an_unpublished_dataset_gives_a_visitor_nothing(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))

        response = client.get(
            reverse("dataset:overview-sample-points", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 200
        assert response.json() == {"type": "FeatureCollection", "features": []}

    def test_samples_none_of_which_is_located_give_none_located_and_no_map_script(
        self,
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory.create_batch(2, dataset=dataset, location=None)

        context = _context(dataset)

        assert context["sample_map"]["located"] == 0
        assert "has_map" not in context


@pytest.fixture
def portal_name(db):
    """Name the site, which a citation gives as its publisher."""
    Site.objects.filter(pk=Site.objects.get_current().pk).update(
        name="Acme Data Portal"
    )
    Site.objects.clear_cache()
    yield "Acme Data Portal"
    Site.objects.clear_cache()


class TestOverviewCitationFormats:
    """The dataset's citation as BibTeX and RIS, as the Cite panel offers it."""

    def make_dataset(self, **kwargs):
        dataset = DatasetFactory(
            visibility=Visibility.PUBLIC, name="Borehole logs", **kwargs
        )
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            dataset.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=[f"{CONTRIBUTOR_ROLES}/creator"],
            )
        DatasetDateFactory(
            related=dataset,
            type_id=f"{DATE_TYPES}/published",
            value=PartialDate.fromisoformat("2022-06-09"),
        )
        return dataset

    def formats_of(self, dataset):
        citation = _context(dataset)["citation"]
        return {entry["key"]: entry["value"] for entry in citation["formats"]}

    def entry_of(self, formats):
        data = parse_string(formats["bibtex"], "bibtex")
        assert len(data.entries) == 1
        key, entry = next(iter(data.entries.items()))
        return key, entry, rispy.loads(formats["ris"])[0]

    def test_the_text_and_both_files_give_the_same_people_year_title_and_publisher(
        self, client, portal_name
    ):
        dataset = self.make_dataset()

        formats = self.formats_of(dataset)
        key, entry, ris = self.entry_of(formats)

        assert formats["text"].startswith("Keller, A. & Oliveira, T. (2022). ")
        assert "Borehole logs. Acme Data Portal." in formats["text"]
        assert [(p.last_names, p.first_names) for p in entry.persons["author"]] == [
            (["Keller"], ["Anna"]),
            (["Oliveira"], ["Tomas"]),
        ]
        assert entry.fields["year"] == "2022"
        assert codecs.decode(entry.fields["title"], "ulatex") == "Borehole logs"
        assert codecs.decode(entry.fields["publisher"], "ulatex") == portal_name
        assert key == str(dataset.uuid)
        assert ris["authors"] == ["Keller, Anna", "Oliveira, Tomas"]
        assert (ris["year"], ris["title"], ris["publisher"]) == (
            "2022",
            "Borehole logs",
            portal_name,
        )

    def test_without_a_doi_the_files_give_the_permalink_and_no_doi(self, client):
        dataset = self.make_dataset()
        permalink = f"http://testserver/{dataset.uuid}/"

        formats = self.formats_of(dataset)
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith(permalink)
        assert entry.fields["url"] == permalink
        assert "doi" not in entry.fields
        assert ris["urls"] == [permalink]
        assert "doi" not in ris

    def test_with_a_doi_the_files_give_the_doi_and_its_link(self, client):
        dataset = self.make_dataset()
        DatasetIdentifierFactory(related=dataset, value="10.5555/ds_1")

        formats = self.formats_of(dataset)
        entry, ris = self.entry_of(formats)[1:]

        assert formats["text"].endswith("https://doi.org/10.5555/ds_1")
        assert entry.fields["doi"] == "10.5555/ds_1"
        assert entry.fields["url"] == "https://doi.org/10.5555/ds_1"
        assert ris["doi"] == "10.5555/ds_1"
        assert ris["urls"] == ["https://doi.org/10.5555/ds_1"]

    def test_a_dataset_is_a_dataset_entry_and_a_data_reference(self, client):
        formats = self.formats_of(self.make_dataset())
        entry, ris = self.entry_of(formats)[1:]

        assert entry.type == "dataset"
        assert ris["type_of_reference"] == "DATA"

    def test_with_nobody_credited_no_author_is_given(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        formats = self.formats_of(dataset)
        entry, ris = self.entry_of(formats)[1:]

        assert "author" not in entry.persons
        assert "authors" not in ris
        assert formats["text"].startswith("(")

    def test_a_data_publication_gives_its_own_citation_in_text_and_both_files(
        self, client
    ):
        title = (
            "Deep drilling records of the Rhine graben, with the borehole logs, "
            "cores and fluid samples taken between 2015 and 2019"
        )
        reference = LiteratureItemFactory(
            title=title,
            type="article-journal",
            doi="10.1234/pub_x",
            year=2020,
            authors=(("Brandt", "Lena"), ("Weiss", "Jan")),
        )
        reference.publisher = "Journal of Rhine Studies"
        reference.save()
        dataset = self.make_dataset(reference=reference)

        formats = self.formats_of(dataset)
        key, entry, ris = self.entry_of(formats)

        assert formats["text"] == (
            f"Brandt, L. & Weiss, J. (2020). {title}. Journal of Rhine Studies. "
            "https://doi.org/10.1234/pub_x"
        )
        assert [(p.last_names, p.first_names) for p in entry.persons["author"]] == [
            (["Brandt"], ["Lena"]),
            (["Weiss"], ["Jan"]),
        ]
        assert entry.type == "article"
        assert key == str(dataset.uuid)
        assert entry.fields["year"] == "2020"
        assert codecs.decode(entry.fields["title"], "ulatex") == title
        assert (
            codecs.decode(entry.fields["publisher"], "ulatex")
            == "Journal of Rhine Studies"
        )
        assert entry.fields["doi"] == "10.1234/pub_x"
        assert entry.fields["url"] == "https://doi.org/10.1234/pub_x"
        assert ris["type_of_reference"] == "JOUR"
        assert ris["authors"] == ["Brandt, Lena", "Weiss, Jan"]
        assert (ris["year"], ris["title"], ris["publisher"]) == (
            "2020",
            title,
            "Journal of Rhine Studies",
        )
        assert ris["doi"] == "10.1234/pub_x"

    def test_each_format_has_an_address_beside_the_page(self, client):
        dataset = self.make_dataset()

        citation = _context(dataset)["citation"]

        assert [e["url"] for e in citation["formats"]] == [
            reverse(
                "dataset:overview-citation",
                kwargs={"uuid": dataset.uuid, "format": key},
            )
            for key in ("text", "bibtex", "ris")
        ]

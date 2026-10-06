"""Tests for the dataset's registered pages: update, descriptions, deletion, menu and links."""

import json
import re
import warnings
from datetime import UTC, date, datetime
from urllib.parse import quote

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse
from django.utils.formats import date_format
from licensing.models import License
from mvp.warnings import MVPDeprecationWarning
from partial_date import PartialDate
from pytest_django.asserts import assertContains, assertNotContains

from fairdm import plugins
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.contrib.plugins.access import can_open
from fairdm.contrib.plugins.base import Plugin
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDescription,
    DatasetLiteratureRelation,
)
from fairdm.core.dataset.plugins import Delete, Descriptions, Overview, Update
from fairdm.core.descriptions import VocabularyDescriptionsForm
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


class TestUpdateIsAnExtraViewOfTheOverview:
    def test_the_update_page_resolves_as_an_extra_view_of_the_overview(self):
        dataset = DatasetFactory()
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        assert url.endswith(f"{dataset.uuid}/update/")

    def test_the_dataset_menu_carries_no_entry_for_update(self):
        assert "dataset:overview-update" not in _entry_view_names(Dataset)

    def test_update_uses_the_shared_inlines_mixin_not_a_hand_written_formset(self):
        from mvp.views.inline import InlineFormSet, InlinesMixin

        assert issubclass(Update, InlinesMixin)
        assert len(Update.inlines) == 2
        for declaration in Update.inlines:
            assert issubclass(declaration, InlineFormSet)


class TestUpdateStatesItsOwnPermission:
    def test_refuses_a_signed_in_user_without_change_permission(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        request = _request_for(user)
        assert can_open(Update, request, dataset) is False

    def test_admits_a_user_holding_change_permission(self):
        dataset = DatasetFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        request = _request_for(user)
        assert can_open(Update, request, dataset) is True

    def test_refuses_an_anonymous_request(self):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        request = _request_for(AnonymousUser())
        assert can_open(Update, request, dataset) is False


class TestUpdatePageDoesNotDiscloseAPrivateDataset:
    def test_a_model_level_holder_with_no_record_level_grant_is_refused(self, client):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_model_level_holder_with_view_rights_is_admitted(self, client):
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

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 200


class TestUpdatePageFieldSet:
    ATTRIBUTES_FIELDS = {
        "image",
        "name",
        "project",
        "license",
        "reference",
        "visibility",
    }
    EXCLUDED_FIELDS = {"descriptions", "keywords", "tags", "contributors"}

    def test_the_rendered_form_offers_exactly_the_attributes_field_set(self, client):
        dataset = DatasetFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        assert set(response.context["form"].fields) == self.ATTRIBUTES_FIELDS

    def test_the_declared_form_class_offers_no_excluded_field(self):
        fields = set(DatasetForm.Meta.fields)
        assert not fields & self.EXCLUDED_FIELDS

    def test_exactly_one_page_offers_the_attributes_field_set(self):
        pages = []
        for plugin_cls, _kwargs in plugins.registry.get_plugins_for_model(Dataset):
            pages.append(plugin_cls)
            pages.extend(plugin_cls.get_extra_views())

        offering_pages = []
        for page in pages:
            form_class = getattr(page, "form_class", None)
            fields = getattr(getattr(form_class, "Meta", None), "fields", None)
            if fields and self.ATTRIBUTES_FIELDS & set(fields):
                offering_pages.append(page)

        assert offering_pages == [Update]


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
            url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
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

    def test_submitting_an_empty_name_reports_an_error_and_saves_nothing(self, client):
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "",
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 200
        assert "name" in response.context["form"].errors
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


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

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        project_queryset = response.context["form"].fields["project"].queryset
        assert own_project in project_queryset
        assert other_project not in project_queryset


@pytest.mark.django_db
class TestAttributesIdentifierRowSet:
    def test_existing_identifiers_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        DatasetIdentifierFactory(related=dataset, type="DOI", value="10.1/existing")
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        identifier_formset = formsets["identifiers"]
        assert identifier_formset.initial_form_count() == 1
        assert len(identifier_formset.forms) == 1

    def test_adding_an_identifier_of_a_chosen_type_records_it_against_the_dataset(
        self, client
    ):
        dataset = DatasetFactory(name="No Identifiers Yet", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/new-identifier",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.identifiers.filter(
            type="DOI", value="10.1/new-identifier"
        ).exists()

    def test_changing_an_existing_identifiers_value_persists(self, client):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        identifier = DatasetIdentifierFactory(
            related=dataset, type="DOI", value="10.1/original"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/changed",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        identifier.refresh_from_db()
        assert identifier.value == "10.1/changed"

    def test_removing_an_identifier_row_deletes_it_from_the_dataset(self, client):
        dataset = DatasetFactory(name="Has Identifier", project=None)
        identifier = DatasetIdentifierFactory(
            related=dataset, type="DOI", value="10.1/to-remove"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(total=1, initial=1),
                **_date_management_data(),
                "identifiers-0-id": identifier.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/to-remove",
                "identifiers-0-DELETE": "on",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert not dataset.identifiers.filter(pk=identifier.pk).exists()

    def test_a_value_already_recorded_against_a_different_dataset_is_refused(
        self, client
    ):
        other_dataset = DatasetFactory(name="Other Dataset")
        DatasetIdentifierFactory(related=other_dataset, type="DOI", value="10.1/taken")
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1/taken",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert "value" in formsets["identifiers"].forms[0].errors
        assert not dataset.identifiers.filter(value="10.1/taken").exists()
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


@pytest.mark.django_db
class TestAttributesDateRowSet:
    def test_existing_dates_are_presented_one_row_each_with_no_blank_row_beyond_them(
        self, client
    ):
        dataset = DatasetFactory(name="Has Date", project=None)
        DatasetDateFactory(related=dataset, type="CollectionStart", value="2020-01-01")
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        date_formset = formsets["dates"]
        assert date_formset.initial_form_count() == 1
        assert len(date_formset.forms) == 1

    def test_adding_a_date_of_a_chosen_type_records_it_against_the_dataset(
        self, client
    ):
        dataset = DatasetFactory(name="No Dates Yet", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-01-01",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.dates.filter(type="CollectionStart", value="2020-01-01").exists()

    def test_changing_an_existing_dates_value_persists(self, client):
        dataset = DatasetFactory(name="Has Date", project=None)
        date = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-01-01"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2021-06-15",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        date.refresh_from_db()
        assert str(date.value) == "2021-06-15"

    def test_removing_a_date_row_deletes_it_from_the_dataset(self, client):
        dataset = DatasetFactory(name="Has Date", project=None)
        date = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-01-01"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=1),
                "dates-0-id": date.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-01-01",
                "dates-0-DELETE": "on",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert not dataset.dates.filter(pk=date.pk).exists()

    def test_a_backwards_pair_both_newly_added_is_refused_and_saves_nothing(
        self, client
    ):
        dataset = DatasetFactory(name="Backwards Pair", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "CollectionEnd",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert formsets["dates"].non_form_errors()
        assert not dataset.dates.exists()

    def test_a_backwards_pair_with_the_start_already_stored_is_refused_and_saves_nothing(
        self, client
    ):
        dataset = DatasetFactory(name="Backwards Pair", project=None)
        start = DatasetDateFactory(
            related=dataset, type="CollectionStart", value="2020-06-01"
        )
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=2, initial=1),
                "dates-0-id": start.pk,
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
                "dates-1-type": "CollectionEnd",
                "dates-1-value": "2010-01-01",
            },
        )

        assert response.status_code == 200
        formsets = {formset.prefix: formset for formset in response.context["inlines"]}
        assert not formsets["dates"].is_valid()
        assert not dataset.dates.filter(type="CollectionEnd").exists()

    def test_a_start_date_with_no_end_date_is_accepted(self, client):
        dataset = DatasetFactory(name="Start Only", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                **_identifier_management_data(),
                **_date_management_data(total=1, initial=0),
                "dates-0-type": "CollectionStart",
                "dates-0-value": "2020-06-01",
            },
        )

        assert response.status_code == 302, response.context["form"].errors
        assert dataset.dates.filter(type="CollectionStart", value="2020-06-01").exists()


class TestAttributesSaveIsOneAtomicSubmission:
    def test_an_invalid_identifier_row_blocks_the_datasets_own_field_changes_too(
        self, client
    ):
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(total=1, initial=0),
                **_date_management_data(),
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "",
            },
        )

        assert response.status_code == 200
        assert dataset.identifiers.count() == 0
        dataset.refresh_from_db()
        assert dataset.name == "Original Name"


class TestASuccessfulSubmissionRedirectsToTheDatasetsOwnPage:
    def test_the_redirect_target_is_the_datasets_own_overview_url(self, client):
        dataset = DatasetFactory(name="Original Name", project=None)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.post(
            url,
            data={
                **_dataset_field_data(dataset),
                "name": "Renamed",
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "dataset:overview", kwargs={"uuid": dataset.uuid}
        )


class TestUpdatePageEmitsExactlyOneFormElement:
    def test_the_form_declares_no_form_tag(self):
        # `BaseMetaClass` moves `helper_attrs` from `Meta` to `_custom_conf`.
        assert DatasetForm._custom_conf["helper_attrs"] == {"form_tag": False}
        form = DatasetForm()
        assert form.helper.form_tag is False

    def test_the_rendered_page_carries_exactly_one_form_element(self, client):
        dataset = DatasetFactory()
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        # Count within <main>: the shell adds a hidden log-out form to the sidebar.
        main = BeautifulSoup(response.content, "html.parser").find("main")
        assert main is not None
        assert len(re.findall(r"<form[ >]", str(main))) == 1


@pytest.mark.django_db
class TestDescriptionsIsAnExtraViewNotARegistrationOfItsOwn:
    def test_reversed_by_name_it_resolves_at_an_address_keyed_by_the_datasets_identifier(
        self, public_dataset
    ):
        url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": public_dataset.uuid}
        )
        assert url == f"/datasets/{public_dataset.uuid}/descriptions/"

    def test_an_anonymous_visitor_is_redirected_to_sign_in(
        self, client, public_dataset
    ):
        url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": public_dataset.uuid}
        )
        response = client.get(url)
        assert response.status_code == 302
        assert reverse("account_login") in response.url


@pytest.mark.django_db
class TestDescriptionsPageStatesItsOwnPermission:
    def test_refuses_a_signed_in_user_without_change_permission(
        self, public_dataset, user_with_no_permission
    ):
        request = _request_for(user_with_no_permission)
        assert can_open(Descriptions, request, public_dataset) is False

    def test_admits_a_user_holding_change_permission(self, user_with_change_permission):
        request = _request_for(user_with_change_permission)
        assert (
            can_open(Descriptions, request, user_with_change_permission.dataset) is True
        )

    def test_refuses_an_anonymous_request(self, public_dataset):
        request = _request_for(AnonymousUser())
        assert can_open(Descriptions, request, public_dataset) is False


@pytest.mark.django_db
class TestDescriptionsPageDoesNotDiscloseAPrivateDataset:
    def test_a_model_level_holder_with_no_record_level_grant_is_refused(self, client):
        from django.contrib.auth.models import Permission

        dataset = DatasetFactory()
        user = UserFactory()
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )
        client.force_login(user)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 404

    def test_a_model_level_holder_with_view_rights_is_admitted(self, client):
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

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        assert response.status_code == 200

    def test_an_anonymous_visitor_to_a_private_dataset_gets_not_found(self, client):
        dataset = DatasetFactory()
        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404


@pytest.mark.django_db
class TestDescriptionsPageOffersOneAreaPerVocabularyType:
    def test_the_field_set_matches_the_vocabulary_exactly(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert list(form.fields) == list(DatasetDescription.VOCABULARY.values)

    def test_every_area_starts_empty_for_a_dataset_with_no_descriptions(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert all(field.initial in (None, "") for field in form)


@pytest.mark.django_db
class TestDescriptionsPageAreasAreLabelledFromTheVocabulary:
    def test_the_first_areas_label_and_help_text_match_its_concept(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        concept = DatasetDescription.VOCABULARY.get_concept(first_type)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].label == concept.label()
        assert form.fields[first_type].help_text == concept.definition()


@pytest.mark.django_db
class TestSavingTextIntoOneAreaRecordsOnlyThatType:
    def test_saving_one_area_creates_exactly_one_description_of_that_type(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "Some abstract text."})

        assert DatasetDescription.objects.filter(related=dataset).count() == 1
        row = DatasetDescription.objects.get(related=dataset)
        assert row.type == first_type
        assert row.value == "Some abstract text."


@pytest.mark.django_db
class TestExistingDescriptionsShowInTheirOwnArea:
    def test_the_existing_description_appears_in_its_own_area_and_others_stay_empty(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type, second_type = DatasetDescription.VOCABULARY.values[:2]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing abstract."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.get(url)

        form = response.context["form"]
        assert form.fields[first_type].initial == "Existing abstract."
        assert form.fields[second_type].initial in (None, "")


@pytest.mark.django_db
class TestEditingAnExistingDescriptionPersists:
    def test_the_changed_text_persists(self, client, user_with_change_permission):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        row = DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Original text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "Changed text."})

        row.refresh_from_db()
        assert row.value == "Changed text."
        assert DatasetDescription.objects.filter(related=dataset).count() == 1


@pytest.mark.django_db
class TestRepeatSubmissionNeverDuplicatesAType:
    def test_submitting_the_same_area_three_times_leaves_exactly_one_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "First."})
        client.post(url, data={first_type: "Second."})
        client.post(url, data={first_type: "Third."})

        assert (
            DatasetDescription.objects.filter(related=dataset, type=first_type).count()
            == 1
        )
        assert (
            DatasetDescription.objects.get(related=dataset, type=first_type).value
            == "Third."
        )


@pytest.mark.django_db
class TestClearingAnAreaRemovesTheDescription:
    def test_clearing_the_area_deletes_the_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: ""})

        assert not DatasetDescription.objects.filter(
            related=dataset, type=first_type
        ).exists()


@pytest.mark.django_db
class TestEmptyAndWhitespaceOnlyAreasCreateNothing:
    def test_leaving_an_area_empty_creates_no_description(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={})

        assert not DatasetDescription.objects.filter(related=dataset).exists()

    def test_whitespace_only_is_treated_as_empty_and_removes_a_stored_row(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]
        DatasetDescription.objects.create(
            related=dataset, type=first_type, value="Existing text."
        )

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        client.post(url, data={first_type: "   \n  "})

        assert not DatasetDescription.objects.filter(
            related=dataset, type=first_type
        ).exists()


@pytest.mark.django_db
class TestASuccessfulSubmissionRedirectsToTheDatasetsPage:
    def test_the_redirect_target_is_the_datasets_own_overview_url(
        self, client, user_with_change_permission
    ):
        dataset = user_with_change_permission.dataset
        client.force_login(user_with_change_permission)
        first_type = DatasetDescription.VOCABULARY.values[0]

        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={first_type: "Some text."})

        assert response.status_code == 302
        assert response.url == reverse(
            "dataset:overview", kwargs={"uuid": dataset.uuid}
        )


class TestDescriptionsUsesTheVocabularyDrivenForm:
    def test_the_declared_form_class_is_the_vocabulary_driven_form(self):
        assert Descriptions.form_class is VocabularyDescriptionsForm

    def test_the_page_is_not_built_on_the_generic_row_based_plugin(self):
        from fairdm.contrib.generic.plugins import DescriptionsPlugin

        assert not issubclass(Descriptions, DescriptionsPlugin)


def _hrefs(content: str) -> list[str]:
    """Return every ``href`` attribute value in rendered HTML, in document order."""
    return re.findall(r'href="([^"]*)"', content)


@pytest.mark.django_db
class TestUpdatePageOffersTheDeletionLink:
    def test_a_user_who_may_delete_the_dataset_is_offered_the_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )

    def test_a_user_who_may_change_but_not_delete_is_offered_no_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert not any(
            href.startswith(delete_url) for href in _hrefs(response.content.decode())
        )

    def test_the_link_returns_to_the_update_page_when_deletion_is_abandoned(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)

        update_url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(update_url)
        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        link = next(
            href
            for href in _hrefs(response.content.decode())
            if href.startswith(delete_url)
        )

        assert f"back={quote(update_url, safe='')}" in link

        deletion_page = client.get(link)

        assert update_url in _hrefs(deletion_page.content.decode())


class TestTheSingularAddressNoLongerAnswers:
    def test_a_request_to_the_singular_address_is_not_found(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(f"/dataset/{dataset.uuid}/")
        assert response.status_code == 404


class TestEachOfTheFourPagesStatesItsOwnPermission:
    # An additional view inherits its owner's `check` but never its `permission` (#279).
    def test_the_overview_states_no_permission_of_its_own(self):
        assert "permission" not in Overview.__dict__

    def test_update_delete_and_descriptions_each_declare_their_own_permission(self):
        assert Update.__dict__.get("permission") == "dataset.change_dataset"
        assert Delete.__dict__.get("permission") == "dataset.delete_dataset"
        assert Descriptions.__dict__.get("permission") == "dataset.change_dataset"

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
            "dataset:overview-update",
            "dataset:overview-descriptions",
            "dataset:overview-delete",
        ):
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 404, name


@pytest.mark.django_db
class TestTheDatasetsPagesContributeExactlyOneNavigationEntry:
    def test_overview_contributes_exactly_one_entry(self):
        assert _entry_view_names(Dataset).count("dataset:overview") == 1

    def test_update_descriptions_and_deletion_contribute_no_entry_of_their_own(self):
        view_names = _entry_view_names(Dataset)
        assert "dataset:overview-update" not in view_names
        assert "dataset:overview-descriptions" not in view_names
        assert "dataset:overview-delete" not in view_names


@pytest.mark.django_db
class TestTheDatasetsOwnPageOffersUpdateAndDescriptionsLinks:
    def test_a_user_who_may_change_the_dataset_is_offered_both_links(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        update_url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        descriptions_url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": dataset.uuid}
        )
        assertContains(response, f'href="{update_url}"')
        assertContains(response, f'href="{descriptions_url}"')

    def test_a_signed_in_user_who_may_not_change_it_is_offered_neither(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        update_url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        descriptions_url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": dataset.uuid}
        )
        assertNotContains(response, f'href="{update_url}"')
        assertNotContains(response, f'href="{descriptions_url}"')


@pytest.mark.django_db
class TestTheDatasetsOwnPageOffersTheDeletionLink:
    def test_a_user_who_may_delete_the_dataset_is_offered_the_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{delete_url}"')

    def test_a_signed_in_user_who_may_not_delete_it_is_not_offered_the_link(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assertNotContains(response, f'href="{delete_url}"')


@pytest.mark.django_db
class TestNoLinkIsOfferedForAnActionTheViewerCannotUse:
    def test_a_user_who_may_only_view_sees_no_update_or_descriptions_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.VIEW
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        update_url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        descriptions_url = reverse(
            "dataset:overview-descriptions", kwargs={"uuid": dataset.uuid}
        )
        assertNotContains(response, f'href="{update_url}"')
        assertNotContains(response, f'href="{descriptions_url}"')

    def test_a_user_who_may_change_but_not_delete_sees_no_deletion_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assertNotContains(response, f'href="{delete_url}"')


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

    def test_the_update_page_draws_no_empty_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_descriptions_page_draws_no_empty_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))

        response = client.get(
            reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        )

        hrefs = _hrefs(response.content.decode())
        assert hrefs
        assert all(href.strip() != "" for href in hrefs)

    def test_the_deletion_page_draws_no_empty_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))

        response = client.get(
            reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
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

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')

    def test_the_descriptions_page_links_back_to_the_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.EDIT
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        )

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')

    def test_the_deletion_page_links_back_to_the_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        )

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')


@pytest.mark.django_db
class TestRenderingEachOfTheDatasetsPagesEmitsNoDeprecationWarning:
    def _permitted_user(self, dataset):
        user = UserFactory()
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        return user

    def _assert_no_deprecation_warning(self, client, url):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            response = client.get(url)
        assert response.status_code == 200
        assert not any(issubclass(w.category, MVPDeprecationWarning) for w in caught)

    def test_the_datasets_own_page_emits_no_deprecation_warning(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))
        url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        self._assert_no_deprecation_warning(client, url)

    def test_the_update_page_emits_no_deprecation_warning(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        self._assert_no_deprecation_warning(client, url)

    def test_the_descriptions_page_emits_no_deprecation_warning(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))
        url = reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        self._assert_no_deprecation_warning(client, url)

    def test_the_deletion_page_emits_no_deprecation_warning(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(self._permitted_user(dataset))
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        self._assert_no_deprecation_warning(client, url)


@pytest.mark.django_db
class TestNoAddressDisclosesAPrivateDatasetsExistence:
    # A sign-in redirect or a 403 would confirm the dataset exists, so the refusal is a
    # 404.
    ADDRESSES = (
        "dataset:overview",
        "dataset:overview-update",
        "dataset:overview-descriptions",
        "dataset:overview-delete",
    )
    PERMISSION_BEARING_ADDRESSES = (
        "dataset:overview-update",
        "dataset:overview-descriptions",
        "dataset:overview-delete",
    )

    def test_an_anonymous_visitor_gets_not_found_at_every_address(self, client):
        dataset = DatasetFactory()
        for name in self.ADDRESSES:
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 404, name

    def test_a_signed_in_stranger_gets_not_found_at_every_address(self, client):
        dataset = DatasetFactory()
        user = UserFactory()
        client.force_login(user)
        for name in self.ADDRESSES:
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 404, name

    def test_a_public_dataset_a_stranger_may_not_change_refuses_with_a_permission_response_instead(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        client.force_login(user)

        for name in self.PERMISSION_BEARING_ADDRESSES:
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 403, name

        overview_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assert client.get(overview_url).status_code == 200

    def test_the_same_public_dataset_refuses_an_anonymous_visitor_with_a_sign_in_redirect_instead(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        for name in self.PERMISSION_BEARING_ADDRESSES:
            url = reverse(name, kwargs={"uuid": dataset.uuid})
            response = client.get(url)
            assert response.status_code == 302, name
            assert "/login/" in response.url or "/accounts/login/" in response.url


@pytest.mark.django_db
class TestRetiredManagementPages:
    RETIRED_ADDRESSES = ("dataset:keywords", "dataset:key-dates")
    RETIRED_PATHS = ("keywords", "key-dates")

    def test_no_address_resolves_for_either_retired_page(self):
        for name in self.RETIRED_ADDRESSES:
            with pytest.raises(NoReverseMatch):
                reverse(name, kwargs={"uuid": DatasetFactory.build().uuid})

    def test_neither_retired_address_answers(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        overview = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})

        for segment in self.RETIRED_PATHS:
            response = client.get(f"{overview}{segment}/")
            assert response.status_code == 404, segment

    def test_the_dataset_menu_carries_one_entry(self):
        assert _entry_view_names(Dataset) == [
            "dataset:overview",
            "dataset:contribution-list",
        ]


def _page(client, dataset):
    """Open the dataset's page and return the response with its parsed HTML."""
    response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))
    assert response.status_code == 200
    response.page = BeautifulSoup(response.content, "html.parser")
    return response


def _figures(page):
    """The values of the four figures, in the order they are drawn."""
    return [figure.get_text(strip=True) for figure in page.select(".stat-value")]


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


@pytest.fixture
def holding():
    """A public, unpublished dataset holding two rock samples and two XRF measurements."""
    from datetime import UTC, datetime

    from demo.factories import RockSampleFactory, XRFMeasurementFactory
    from fairdm.core.measurement.models import Measurement
    from fairdm.core.sample.models import Sample

    dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
    rocks = [
        RockSampleFactory(dataset=dataset, name=f"Zq-{n}-4471 rift core")
        for n in (1, 2)
    ]
    XRFMeasurementFactory.create_batch(2, dataset=dataset, sample=rocks[0])
    Sample.objects.update(added=datetime(2026, 1, 15, tzinfo=UTC))
    Measurement.objects.update(added=datetime(2026, 3, 15, tzinfo=UTC))
    return dataset


class TestOverviewWhatAVisitorSeesBeforePublication:
    """US-2 scenarios 1 to 3 and FR-022, FR-024."""

    def test_a_visitor_sees_the_counts_and_both_charts_and_a_notice(
        self, client, holding
    ):
        response = _page(client, holding)

        assert _figures(response.page)[:2] == ["2", "2"]
        assert response.page.find(id="dataset-composition") is not None
        assert response.page.find(id="dataset-growth") is not None
        assert len(response.page.select(".alert")) == 1

    def test_a_visitor_is_shown_the_abstract(self, client, holding):
        DatasetDescriptionFactory(
            related=holding, type="Abstract", value="Cores from the rift."
        )

        response = _page(client, holding)

        assertContains(response, "Cores from the rift.")

    def test_the_team_of_an_unpublished_dataset_sees_the_checklist(
        self, client, holding
    ):
        client.force_login(_team_member(holding, "change_dataset"))

        response = _page(client, holding)

        assert response.page.find("progress", attrs={"max": "10"}) is not None

    def test_a_visitor_sees_no_checklist(self, client, holding):
        response = _page(client, holding)

        assert response.page.find("progress") is None

    def test_a_published_dataset_shows_its_team_no_checklist_and_no_notice(
        self, client, holding
    ):
        Dataset.all_objects.filter(pk=holding.pk).update(published=True)
        client.force_login(_team_member(holding, "change_dataset"))

        response = _page(client, holding)

        assert response.page.find("progress") is None
        assert response.page.select(".alert") == []


class TestOverviewReadinessChecklist:
    """FR-033: seven required items and three recommended ones."""

    def test_the_checklist_has_seven_required_and_three_recommended_items(
        self, client, holding
    ):
        client.force_login(_team_member(holding, "change_dataset"))

        response = _page(client, holding)

        items = response.context["readiness"]["items"]
        assert sum(1 for item in items if item["required"]) == 7
        assert sum(1 for item in items if not item["required"]) == 3

    def test_a_complete_but_private_dataset_is_ready_because_publishing_makes_it_public(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        DatasetDescriptionFactory(related=dataset, type="Abstract", value="Cores.")
        DatasetDescriptionFactory(related=dataset, type="Methods", value="Drilled.")
        DatasetDateFactory(
            related=dataset, type="CollectionStart", value=PartialDate("2024-01-01")
        )
        dataset.add_contributor(
            PersonFactory(is_active=True), with_roles=["Creator", "ContactPerson"]
        )
        from demo.factories import RockSampleFactory

        RockSampleFactory(dataset=dataset)
        client.force_login(_team_member(dataset, "change_dataset"))

        readiness = _page(client, dataset).context["readiness"]

        assert readiness["ready"] is True
        assert readiness["missing_required"] == 0


class TestOverviewCitation:
    """US-2 scenario 4."""

    def _citation(self, client, dataset):
        return _page(client, dataset).page.find(id="citation-text").get_text(strip=True)

    def test_a_data_publication_is_cited_in_place_of_the_dataset(self, client):
        reference = LiteratureItemFactory()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, reference=reference)

        assert self._citation(client, dataset) == str(reference)

    def test_creators_are_named_in_the_order_credited_people_before_organizations(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        partner = OrganizationFactory(name="Acme Lab")
        dataset.add_contributor(partner, with_roles=["Creator"])
        for first, last in (("Anna", "Keller"), ("Tomas", "Oliveira")):
            moving = dataset.add_contributor(
                PersonFactory(first_name=first, last_name=last, is_active=True),
                with_roles=["Creator"],
            )
        Crediting(dataset).move(moving, "up")

        assert self._citation(client, dataset).startswith(
            "Oliveira, T., Keller, A. & Acme Lab ("
        )

    def test_without_one_the_year_is_the_published_date(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDateFactory(
            related=dataset, type="Published", value=PartialDate("2021-05-04")
        )
        DatasetDateFactory(
            related=dataset, type="Available", value=PartialDate("2022-01-01")
        )

        assert "(2021)" in self._citation(client, dataset)

    def test_without_a_published_date_the_year_is_the_available_date(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDateFactory(
            related=dataset, type="Available", value=PartialDate("2022-01-01")
        )

        assert "(2022)" in self._citation(client, dataset)

    def test_without_either_the_year_is_when_the_record_was_added(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        assert f"({dataset.added.year})" in self._citation(client, dataset)


class TestOverviewCharts:
    """US-2 scenarios 5 to 7."""

    def test_the_composition_text_lists_every_type_with_its_count(
        self, client, holding
    ):
        response = _page(client, holding)

        text = response.page.find(id="dataset-composition-description").get_text()
        assert "Rock Samples: 2" in text
        assert "XRF Measurements: 2" in text

    def test_records_within_one_month_draw_no_growth_chart(self, client, holding):
        from datetime import UTC, datetime

        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        Sample.objects.update(added=datetime(2026, 1, 15, tzinfo=UTC))
        Measurement.objects.update(added=datetime(2026, 1, 20, tzinfo=UTC))

        response = _page(client, holding)

        assert response.page.find(id="dataset-composition") is not None
        assert response.page.find(id="dataset-growth") is None

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

        response = _page(client, holding)

        text = response.page.find(id="dataset-composition-description").get_text()
        assert "XRF" not in text
        assert "Rock Samples" in text


class TestOverviewFirstRun:
    """US-2 scenario 6."""

    def _unavailable_actions(self, client, dataset):
        page = _page(client, dataset).page
        return len(page.find_all("button", disabled=True))

    def test_the_team_of_an_empty_dataset_is_offered_one_more_step_than_of_one_holding_data(
        self, client, holding
    ):
        Dataset.all_objects.filter(pk=holding.pk).update(published=True)
        empty = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        client.force_login(_team_member(holding, "change_dataset"))
        with_data = self._unavailable_actions(client, holding)
        client.force_login(_team_member(empty, "change_dataset"))

        assert self._unavailable_actions(client, empty) == with_data + 1

    def test_an_empty_dataset_draws_no_chart(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        client.force_login(_team_member(dataset, "change_dataset"))

        response = _page(client, dataset)

        assert response.page.find(attrs={"data-mvp-chart": True}) is None
        assert response.page.find(id="dataset-composition") is None
        assert response.page.find(id="dataset-growth") is None

    def test_a_visitor_to_an_empty_dataset_is_offered_no_first_step(
        self, client, holding
    ):
        Dataset.all_objects.filter(pk=holding.pk).update(published=True)
        empty = DatasetFactory(visibility=Visibility.PUBLIC, published=True)

        assert self._unavailable_actions(client, empty) == self._unavailable_actions(
            client, holding
        )


class TestOverviewTimeline:
    """US-2 scenarios 8 and 9."""

    def _steps(self, page):
        """The date each timeline step shows, in the order they are drawn."""
        card = page.find("ol", class_="timeline").find_parent(class_="card")
        return [
            item.select_one(".text-sm").get_text(strip=True)
            for item in card.select("ol > li")
        ]

    def test_the_dates_are_listed_in_the_order_they_happened(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        Dataset.all_objects.filter(pk=dataset.pk).update(
            added=datetime(2022, 11, 10, tzinfo=UTC)
        )
        for type_, value in (
            ("Available", "2025-06-01"),
            ("Published", "2025-05-01"),
            ("Submitted", "2025-04-01"),
            ("CollectionStart", "2023-02-01"),
            ("CollectionEnd", "2023-09-30"),
        ):
            DatasetDateFactory(related=dataset, type=type_, value=PartialDate(value))

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
            related=dataset, type="Withdrawn", value=PartialDate("2999-01-01")
        )
        when = date_format(date(2999, 1, 1), "SHORT_DATE_FORMAT")

        response = _page(client, dataset)

        assert when in response.page.select_one(".alert").get_text()
        assert self._steps(response.page)[-1] == when

    def test_a_collection_period_is_shown_as_precisely_as_it_was_recorded(
        self, client
    ):
        year_only = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        month_only = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        DatasetDateFactory(
            related=year_only, type="CollectionStart", value=PartialDate("2023")
        )
        DatasetDateFactory(
            related=month_only, type="CollectionStart", value=PartialDate("2023-02")
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
        DatasetDateFactory(related=dataset, type="Withdrawn", value=PartialDate("2999"))

        response = _page(client, dataset)

        notice = response.page.select_one(".alert").get_text()
        assert "2999" in notice
        assert date_format(date(2999, 1, 1), "SHORT_DATE_FORMAT") not in notice
        assert self._steps(response.page)[-1] == "2999"


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

        card = response.page.find(string=str(items["IsDescribedBy"])).find_parent(
            class_="card"
        )
        listed = card.select("ul > li")
        order = [
            next(name for name, item in items.items() if str(item) in li.get_text())
            for li in listed
        ]
        assert order == ["IsDescribedBy", "IsCitedBy", "Cites"]
        for name, li in zip(order, listed, strict=True):
            dataset_side = DatasetLiteratureRelation(relationship_type=name)
            assert li.select_one(".badge").get_text(strip=True) != (
                dataset_side.get_relationship_type_display()
            )


class TestOverviewProject:
    """US-2 scenario 11."""

    def test_a_project_the_viewer_may_not_see_is_neither_named_nor_linked(self, client):
        project = ProjectFactory(
            visibility=Visibility.PRIVATE, name="Secret Rift Programme"
        )
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, project=project)

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

    def _siblings(self, client, user, dataset):
        client.force_login(user)
        return _page(client, dataset).context["project_info"]["siblings"]

    def test_a_team_member_is_not_told_about_a_private_dataset_they_cannot_open(
        self, client, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")

        assert self._siblings(client, user, team_dataset) == 0

    def test_a_private_dataset_the_viewer_may_open_is_counted(
        self, client, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")
        ContributionFactory(
            content_object=hidden, contributor=user, level=ContributionLevel.VIEW
        )

        assert self._siblings(client, user, team_dataset) == 1

    def test_a_private_dataset_with_only_a_stored_row_is_not_counted(
        self, client, team_dataset, hidden
    ):
        from fairdm.core.utils import assign_perm

        user = _team_member(team_dataset, "change_dataset")
        assign_perm("view_dataset", user, hidden)

        assert self._siblings(client, user, team_dataset) == 0

    def test_a_private_dataset_under_a_level_on_the_project_is_counted(
        self, client, project, team_dataset, hidden
    ):
        user = _team_member(team_dataset, "change_dataset")
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.VIEW
        )

        assert self._siblings(client, user, team_dataset) == 1

    def test_a_public_dataset_is_counted(self, client, project, team_dataset):
        DatasetFactory(visibility=Visibility.PUBLIC, project=project)
        user = _team_member(team_dataset, "change_dataset")

        assert self._siblings(client, user, team_dataset) == 1

    def test_someone_who_manages_the_project_counts_every_dataset(
        self, client, project, team_dataset, hidden
    ):
        user = _team_member(team_dataset)
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )

        assert self._siblings(client, user, team_dataset) == 1


class TestOverviewSchemaOrgDescription:
    """FR-034 and FR-056."""

    def test_a_public_unpublished_dataset_names_its_variables_and_carries_no_values(
        self, client, holding
    ):
        from demo.models import XRFMeasurement
        from fairdm.core.sample.models import Sample

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
        dataset.add_contributor(person, with_roles=["Creator"])

        response = _page(client, dataset)

        assert person.email not in response.content.decode()


class TestOverviewManageMenu:
    def test_a_user_who_may_delete_the_dataset_is_offered_the_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(_team_member(dataset, "delete_dataset"))

        response = _page(client, dataset)

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert response.page.find("a", href=delete_url) is not None

    def test_a_visitor_is_offered_no_delete_link(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        response = _page(client, dataset)

        delete_url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        assert response.page.find("a", href=delete_url) is None


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

    def test_the_readiness_checklist_stays_out_of_a_visitors_page(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)

        response = _page(client, dataset)

        assert response.page.select_one('[data-card="readiness"]') is None

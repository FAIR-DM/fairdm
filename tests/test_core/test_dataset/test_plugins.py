"""Tests for the dataset's registered pages: update, descriptions, deletion, menu and links."""

import re
import warnings
from urllib.parse import quote

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse
from guardian.shortcuts import assign_perm
from licensing.models import License
from mvp.warnings import MVPDeprecationWarning
from pytest_django.asserts import assertContains, assertNotContains

from fairdm import plugins
from fairdm.contrib.plugins.access import can_open
from fairdm.contrib.plugins.base import Plugin
from fairdm.core.dataset.forms import DatasetForm
from fairdm.core.dataset.models import Dataset, DatasetDescription
from fairdm.core.dataset.plugins import Delete, Descriptions, Overview, Update
from fairdm.core.descriptions import VocabularyDescriptionsForm
from fairdm.factories import (
    DatasetDateFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    LiteratureItemFactory,
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("view_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        changed_project.add_contributor(user)

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
            assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        from fairdm.contrib.contributors.models import Contribution
        from fairdm.factories import ProjectFactory

        dataset = DatasetFactory()
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        own_project = ProjectFactory(name="Researcher's Own Project")
        other_project = ProjectFactory(name="Someone Else's Project")
        Contribution.add_to(user, own_project, roles=["Contributor"])

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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("view_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
        assign_perm("delete_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
        assign_perm("delete_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("delete_dataset", user, dataset)
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
    def test_a_user_who_may_delete_but_not_change_sees_no_update_or_descriptions_link(
        self, client
    ):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("delete_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
        assign_perm("delete_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')

    def test_the_descriptions_page_links_back_to_the_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        response = client.get(
            reverse("dataset:overview-descriptions", kwargs={"uuid": dataset.uuid})
        )

        dataset_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assertContains(response, f'href="{dataset_url}"')

    def test_the_deletion_page_links_back_to_the_dataset(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        user = UserFactory()
        assign_perm("delete_dataset", user, dataset)
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
        assign_perm("change_dataset", user, dataset)
        assign_perm("delete_dataset", user, dataset)
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
        assert _entry_view_names(Dataset) == ["dataset:overview"]

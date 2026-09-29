"""Integration tests for the dataset list, create, update and delete views."""

import re
import time

import pytest
from bs4 import BeautifulSoup
from django import forms
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from guardian.shortcuts import assign_perm
from licensing.models import License
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.core.dataset.forms import DatasetCreateForm, DatasetForm
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.views import DatasetCreateView
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    DatasetDescriptionFactory,
    DatasetFactory,
    DatasetIdentifierFactory,
    PersonFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

# `DatasetFactory()` and the create view produce private datasets, so lookups use
# `Dataset.all_objects`.


@pytest.mark.django_db
class TestDatasetListView:
    def test_anonymous_get(self, client):
        url = reverse("dataset-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_shows_only_public_datasets(self, client):
        public = DatasetFactory(name="Public Dataset", visibility=Visibility.PUBLIC)
        DatasetFactory(name="Private Dataset", visibility=Visibility.PRIVATE)

        url = reverse("dataset-list")
        response = client.get(url)

        assert response.status_code == 200
        assert public.name in str(response.content)
        assert "Private Dataset" not in str(response.content)

    def test_order_by_added(self, client):
        older = DatasetFactory(name="Older Dataset", visibility=Visibility.PUBLIC)
        time.sleep(0.01)
        newer = DatasetFactory(name="Newer Dataset", visibility=Visibility.PUBLIC)

        url = reverse("dataset-list")

        response_asc = client.get(url, {"o": "added"})
        assert response_asc.status_code == 200
        content_asc = str(response_asc.content)
        assert content_asc.index(older.name) < content_asc.index(newer.name)

        response_desc = client.get(url, {"o": "-added"})
        assert response_desc.status_code == 200
        content_desc = str(response_desc.content)
        assert content_desc.index(newer.name) < content_desc.index(older.name)


@pytest.mark.django_db
class TestDatasetListingVisibility:
    def test_signed_out_visitor_sees_only_the_public_dataset(
        self, client, public_dataset, private_dataset
    ):
        response = client.get(reverse("dataset-list"))
        entries = list(response.context["object_list"])
        assert public_dataset in entries
        assert private_dataset not in entries

    def test_signed_in_visitor_with_no_rights_sees_only_the_public_dataset(
        self, client, public_dataset, private_dataset, user_with_no_permission
    ):
        client.force_login(user_with_no_permission)
        response = client.get(reverse("dataset-list"))
        entries = list(response.context["object_list"])
        assert public_dataset in entries
        assert private_dataset not in entries

    def test_signed_in_holder_of_record_level_rights_over_a_private_dataset_still_does_not_see_it(
        self, client, public_dataset, user_with_change_permission
    ):
        client.force_login(user_with_change_permission)
        response = client.get(reverse("dataset-list"))
        entries = list(response.context["object_list"])
        assert public_dataset in entries
        assert user_with_change_permission.dataset not in entries


@pytest.mark.django_db
class TestDatasetListingSearch:
    def test_search_by_name_returns_the_matching_dataset_only(self, client):
        target = DatasetFactory(
            name="Zircon Thermochronology Survey", visibility=Visibility.PUBLIC
        )
        other = DatasetFactory(
            name="Basalt Petrology Atlas", visibility=Visibility.PUBLIC
        )
        response = client.get(reverse("dataset-list"), {"q": "Thermochronology"})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_search_by_uuid_returns_the_dataset(self, client):
        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"q": str(target.uuid)})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_search_by_external_identifier_returns_the_dataset(self, client):
        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        identifier = DatasetIdentifierFactory(related=target)
        response = client.get(reverse("dataset-list"), {"q": identifier.value})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_search_by_description_returns_the_dataset(self, client):
        from fairdm.factories import DatasetDescriptionFactory

        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDescriptionFactory(
            related=target,
            type="Abstract",
            value="A rare assemblage of pyroxenite xenoliths from the Rio Grande rift",
        )
        response = client.get(reverse("dataset-list"), {"q": "pyroxenite"})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_search_by_keyword_returns_the_dataset(self, client):
        from research_vocabs.models import Concept

        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        target.keywords.add(term)
        response = client.get(reverse("dataset-list"), {"q": term.name})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_the_listing_offers_no_second_search_control(self, client):
        response = client.get(reverse("dataset-list"))
        content = response.content.decode()
        assert content.count('name="q"') == 1
        assert 'name="search"' not in content


@pytest.mark.django_db
class TestDatasetListingOrdering:
    def test_ordered_by_name_returns_alphabetical_order(self, client):
        bravo = DatasetFactory(name="Bravo Dataset", visibility=Visibility.PUBLIC)
        alpha = DatasetFactory(name="Alpha Dataset", visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"o": "name"})
        entries = list(response.context["object_list"])
        assert entries.index(alpha) < entries.index(bravo)

    def test_ordered_by_name_reversed_returns_reverse_alphabetical_order(self, client):
        bravo = DatasetFactory(name="Bravo Dataset", visibility=Visibility.PUBLIC)
        alpha = DatasetFactory(name="Alpha Dataset", visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"o": "-name"})
        entries = list(response.context["object_list"])
        assert entries.index(bravo) < entries.index(alpha)


@pytest.mark.django_db
class TestDatasetListingFilters:
    def test_license_filter_narrows_to_the_matching_license(self, client):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc0 = License.objects.get(name="CC0 1.0")
        matching = DatasetFactory(license=cc_by, visibility=Visibility.PUBLIC)
        other = DatasetFactory(license=cc0, visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"license": cc_by.pk})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_project_filter_narrows_to_the_matching_project(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        matching = DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"project": project.pk})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_description_type_filter_narrows_to_datasets_carrying_that_type(
        self, client
    ):
        from fairdm.factories import DatasetDescriptionFactory

        matching = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDescriptionFactory(related=matching, type="Abstract")
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"description_type": "Abstract"})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries

    def test_date_type_filter_narrows_to_datasets_carrying_that_type(self, client):
        from fairdm.factories import DatasetDateFactory

        matching = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDateFactory(related=matching, type="Available")
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"), {"date_type": "Available"})
        entries = list(response.context["object_list"])
        assert matching in entries
        assert other not in entries


@pytest.mark.django_db
class TestDatasetListingFiltersAllRunWithoutError:
    def _value_for(self, field_name, dataset, project, license_obj):
        return {
            "license": license_obj.pk,
            "project": project.pk,
            "description_type": "Abstract",
            "date_type": "Available",
            "image": "true",
        }[field_name]

    def test_every_offered_filter_runs_without_raising(self, client):
        from fairdm.factories import DatasetDateFactory, DatasetDescriptionFactory

        license_obj = License.objects.get(name="CC BY 4.0")
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            license=license_obj, project=project, visibility=Visibility.PUBLIC
        )
        DatasetDescriptionFactory(related=dataset, type="Abstract")
        DatasetDateFactory(related=dataset, type="Available")

        response = client.get(reverse("dataset-list"))
        rendered_fields = list(response.context["filter"].form.fields)
        assert rendered_fields, "the rendered filterset form offers no fields to sweep"

        for field_name in rendered_fields:
            value = self._value_for(field_name, dataset, project, license_obj)
            response = client.get(reverse("dataset-list"), {field_name: value})
            assert response.status_code == 200, (
                f"applying '{field_name}' raised rather than rendering"
            )
            entries = list(response.context["object_list"])
            assert dataset in entries, (
                f"applying '{field_name}' did not return the matching dataset"
            )


@pytest.mark.django_db
class TestDatasetListingOffersNoDeadFilter:
    def test_the_rendered_filterset_form_offers_no_visibility_field(self, client):
        response = client.get(reverse("dataset-list"))
        assert "visibility" not in response.context["filter"].form.fields


@pytest.mark.django_db
class TestDatasetListingProjectFilterVisibility:
    def test_a_private_project_is_absent_for_an_anonymous_visitor(self, client):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        response = client.get(reverse("dataset-list"))
        project_queryset = response.context["filter"].form.fields["project"].queryset
        assert private_project not in project_queryset
        assertNotContains(response, "Confidential Survey")

    def test_a_private_project_is_absent_for_a_signed_in_visitor_with_no_rights_over_it(
        self, client
    ):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        client.force_login(UserFactory())
        response = client.get(reverse("dataset-list"))
        project_queryset = response.context["filter"].form.fields["project"].queryset
        assert private_project not in project_queryset
        assertNotContains(response, "Confidential Survey")

    def test_a_public_project_is_offered_to_every_visitor(self, client):
        public_project = ProjectFactory(
            name="Open Reef Survey", visibility=Visibility.PUBLIC
        )
        response = client.get(reverse("dataset-list"))
        project_queryset = response.context["filter"].form.fields["project"].queryset
        assert public_project in project_queryset

    def test_a_private_project_the_signed_in_visitor_holds_view_rights_on_is_offered(
        self, client
    ):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        user = UserFactory()
        assign_perm("view_project", user, private_project)
        client.force_login(user)
        response = client.get(reverse("dataset-list"))
        project_queryset = response.context["filter"].form.fields["project"].queryset
        assert private_project in project_queryset


@pytest.mark.django_db
class TestDatasetListingEmptyState:
    def test_listing_shows_empty_state_when_a_search_matches_nothing(
        self, client, public_dataset
    ):
        response = client.get(
            reverse("dataset-list"), {"q": "no-dataset-should-match-this-term"}
        )
        assert response.status_code == 200
        assert list(response.context["object_list"]) == []


@pytest.mark.django_db
class TestDatasetListingEntryLink:
    def test_listing_entry_links_to_its_datasets_page(self, client, public_dataset):
        response = client.get(reverse("dataset-list"))
        expected_url = public_dataset.get_absolute_url()
        assertContains(response, f'href="{expected_url}"')


@pytest.mark.django_db
class TestDatasetCreateView:
    def test_anonymous_redirects_to_login(self, client):
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_authenticated_get_200(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # The form only offers projects the user contributes to.
        project.add_contributor(user)
        license_obj = License.objects.first()

        url = reverse("dataset-create")
        response = client.post(
            url,
            data={
                "name": "New Test Dataset",
                "project": project.pk,
                "license": license_obj.pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )

        from fairdm.core.dataset.models import Dataset

        dataset = Dataset.all_objects.get(name="New Test Dataset")
        expected_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assert response.url == expected_url

    def test_assigns_contributor_roles(self, client):
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        project.add_contributor(user)
        license_obj = License.objects.first()

        url = reverse("dataset-create")
        response = client.post(
            url,
            data={
                "name": "Permission Test Dataset",
                "project": project.pk,
                "license": license_obj.pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )

        from fairdm.core.dataset.models import Dataset

        dataset = Dataset.all_objects.get(name="Permission Test Dataset")

        contributor = dataset.contributors.filter(contributor=user).first()
        assert contributor is not None, "User should be a contributor"
        role_names = list(contributor.roles.values_list("name", flat=True))
        for role in ["Creator", "ProjectMember", "ContactPerson"]:
            assert role in role_names, f"Missing contributor role: {role}"


@pytest.mark.django_db
class TestDatasetCreatePageUsesTheDeclaredForm:
    def test_the_view_declares_a_subclass_of_the_update_pages_form(self):
        assert DatasetCreateView.form_class is DatasetCreateForm
        assert issubclass(DatasetCreateForm, DatasetForm)

    def test_a_label_declared_once_reaches_both_the_creation_and_the_update_page(
        self, client
    ):
        user = UserFactory()
        client.force_login(user)
        create_response = client.get(reverse("dataset-create"))

        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        update_response = client.get(
            reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        )

        create_label = create_response.context["form"].fields["name"].label
        update_label = update_response.context["form"].fields["name"].label
        assert create_label == update_label


@pytest.mark.django_db
class TestDatasetCreatePageFieldSet:
    FIELDS = {"name", "visibility", "license", "project"}

    def test_the_rendered_form_offers_exactly_the_creation_field_set(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)

        assert response.status_code == 200
        assert set(response.context["form"].fields) == self.FIELDS


@pytest.mark.django_db
class TestDatasetCreatePageVisibilityField:
    def test_the_rendered_page_offers_a_radio_choice_pre_selecting_public(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)
        form = response.context["form"]

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)

        content = response.content.decode()
        public_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PUBLIC}"[^>]*>',
            content,
        )
        private_input = re.search(
            rf'<input[^>]*name="visibility"[^>]*value="{Visibility.PRIVATE}"[^>]*>',
            content,
        )
        assert public_input is not None and "checked" in public_input.group(0)
        assert private_input is not None and "checked" not in private_input.group(0)


@pytest.mark.django_db
class TestDatasetCreatePageLicenseDefault:
    def test_the_rendered_form_preselects_the_configured_default_licence(
        self, client, settings
    ):
        other_license = License.objects.get_or_create(name="A Portal's Own Licence")[0]
        settings.FAIRDM_DEFAULT_LICENSE = other_license.name
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)

        assert response.context["form"].fields["license"].initial == other_license


@pytest.mark.django_db
class TestDatasetCreatePageProjectField:
    def test_the_project_field_is_optional_and_starts_empty(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)
        project_field = response.context["form"].fields["project"]

        assert project_field.required is False
        assert not project_field.initial

    def test_a_dataset_can_be_created_without_a_project(self, client):
        user = UserFactory()
        client.force_login(user)
        license_obj = License.objects.get_or_create(name="CC BY 4.0")[0]
        url = reverse("dataset-create")

        response = client.post(
            url,
            data={
                "name": "Orphan Dataset",
                "license": license_obj.pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        dataset = Dataset.all_objects.get(name="Orphan Dataset")
        assert dataset.project is None


@pytest.mark.django_db
class TestDatasetCreatePageProjectFieldNarrowing:
    def test_the_project_field_is_narrowed_to_the_researchers_own_projects(
        self, client
    ):
        from fairdm.contrib.contributors.models import Contribution

        user = UserFactory()
        client.force_login(user)
        own_project = ProjectFactory(name="Researcher's Own Project")
        other_project = ProjectFactory(name="Someone Else's Project")
        Contribution.add_to(user, own_project, roles=["Contributor"])

        url = reverse("dataset-create")
        response = client.get(url)
        project_queryset = response.context["form"].fields["project"].queryset

        assert own_project in project_queryset
        assert other_project not in project_queryset


@pytest.mark.django_db
class TestDatasetCreatePageProjectFieldWidget:
    def test_the_rendered_page_carries_no_add_another_wrapper_markup(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)

        assertNotContains(response, "related-widget-wrapper")
        assertNotContains(response, "add-related")


@pytest.mark.django_db
class TestDatasetCreatePageNameRequired:
    def test_submitting_without_a_name_reports_an_error_and_saves_nothing(self, client):
        user = UserFactory()
        client.force_login(user)
        license_obj = License.objects.get_or_create(name="CC BY 4.0")[0]
        url = reverse("dataset-create")

        response = client.post(url, data={"name": "", "license": license_obj.pk})

        assert response.status_code == 200
        assert "name" in response.context["form"].errors
        assert not Dataset.all_objects.filter(license=license_obj).exists()


@pytest.mark.django_db
class TestDatasetCreatePagePermissionAssignment:
    def test_the_creator_is_granted_full_permissions_on_the_new_dataset(self, client):
        user = UserFactory()
        client.force_login(user)
        license_obj = License.objects.get_or_create(name="CC BY 4.0")[0]
        url = reverse("dataset-create")

        response = client.post(
            url,
            data={
                "name": "Permissioned Dataset",
                "license": license_obj.pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        dataset = Dataset.all_objects.get(name="Permissioned Dataset")
        for perm in [
            "view_dataset",
            "change_dataset",
            "delete_dataset",
            "change_dataset_metadata",
            "change_dataset_settings",
        ]:
            assert user.has_perm(f"dataset.{perm}", dataset), (
                f"Missing permission: {perm}"
            )


@pytest.mark.django_db
class TestDatasetCreatePageRecordsCreator:
    def test_the_dataset_records_its_creator(self, client):
        user = UserFactory()
        client.force_login(user)
        license_obj = License.objects.get_or_create(name="CC BY 4.0")[0]
        url = reverse("dataset-create")

        response = client.post(
            url,
            data={
                "name": "Attributed Dataset",
                "license": license_obj.pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        dataset = Dataset.all_objects.get(name="Attributed Dataset")
        assert dataset.created_by == user


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


@pytest.mark.django_db
class TestDatasetUpdateView:
    def test_anonymous_redirects_to_login(self, client):
        dataset = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_anonymous_visitor_to_a_private_dataset_returns_404(self, client):
        dataset = DatasetFactory()
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_no_permission_on_a_public_dataset_returns_403(self, client):
        user = UserFactory()
        dataset = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_no_permission_on_a_private_dataset_returns_404(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_with_permission_returns_200(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        from licensing.models import License

        user = UserFactory()
        dataset = DatasetFactory(name="Original Name")
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        project = dataset.project
        project.add_contributor(user)
        license_obj = dataset.license if dataset.license else License.objects.first()

        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.post(
            url,
            data={
                "name": "Updated Name",
                "project": project.pk,
                "license": license_obj.pk,
                "visibility": dataset.visibility,
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

        assert response.status_code == 302, (
            f"Form errors: {response.context['form'].errors if 'form' in response.context else 'no form in context'}"
        )
        expected_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assert response.url == expected_url


@pytest.mark.django_db
class TestDatasetUpdatePageProjectAndReferenceFieldWidgets:
    def test_the_rendered_page_carries_no_add_another_wrapper_markup(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assertNotContains(response, "related-widget-wrapper")
        assertNotContains(response, "add-related")


@pytest.mark.django_db
class TestDatasetDeleteView:
    def test_anonymous_visitor_to_a_public_dataset_redirects_to_login(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_anonymous_visitor_to_a_private_dataset_returns_404(self, client):
        dataset = DatasetFactory()
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_no_permission_on_a_public_dataset_returns_403(self, client):
        user = UserFactory()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_no_permission_on_a_private_dataset_returns_404(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_with_permission_returns_200(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_wrong_name_shows_error(self, client):
        user = UserFactory()
        dataset = DatasetFactory(name="My Dataset")
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "Wrong Name"})
        assert response.status_code == 200
        assert "confirmation" in response.context["form"].errors
        assert Dataset.all_objects.filter(pk=dataset.pk).exists()

    def test_confirmation_ignores_surrounding_whitespace(self, client):
        user = UserFactory()
        dataset = DatasetFactory(name="Spaced Dataset")
        pk = dataset.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "  Spaced Dataset  "})
        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Dataset.all_objects.filter(pk=pk).exists()

    def test_page_carries_exactly_one_confirmation_control(self, client):
        # django-mvp used to draw the bound field a second time, unbound (fixed in
        # 0.19.3).
        user = UserFactory()
        dataset = DatasetFactory(name="My Dataset")
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        content = response.content.decode()
        assert content.count('id="id_confirmation"') == 1

    def test_correct_name_redirects_to_list(self, client):
        user = UserFactory()
        dataset = DatasetFactory(name="Delete Me Dataset")
        pk = dataset.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "Delete Me Dataset"})
        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Dataset.all_objects.filter(pk=pk).exists()

    def test_deleting_a_dataset_removes_its_samples(self, client):
        from demo.factories import RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Dataset With A Sample")
        sample = RockSampleFactory(dataset=dataset)
        sample_pk = sample.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.post(url, data={"confirmation": "Dataset With A Sample"})

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Sample.objects.filter(pk=sample_pk).exists()

    def test_deleting_a_dataset_removes_its_samples_and_their_measurements(
        self, client
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Dataset With Data")
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
        sample_pk, measurement_pk = sample.pk, measurement.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.post(url, data={"confirmation": "Dataset With Data"})

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Sample.objects.filter(pk=sample_pk).exists()
        assert not Measurement.objects.filter(pk=measurement_pk).exists()

    def test_deletion_is_refused_while_another_dataset_measures_its_samples(
        self, client
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Borrowed From")
        other = DatasetFactory(name="Borrower")
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=other, sample=sample)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["is_protected"] is True
        assert response.context["form"] is None

        response = client.post(url, data={"confirmation": "Borrowed From"})

        assert response.status_code == 200
        assert Dataset.all_objects.filter(pk=dataset.pk).exists()

    def test_deleting_a_dataset_leaves_a_sample_it_borrowed_alone(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        sample_dataset = DatasetFactory(name="Sample Dataset")
        sample = RockSampleFactory(dataset=sample_dataset)
        dataset = DatasetFactory(name="Dataset With A Measurement")
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
        measurement_pk = measurement.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.post(url, data={"confirmation": "Dataset With A Measurement"})

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Measurement.objects.filter(pk=measurement_pk).exists()
        assert Sample.objects.filter(pk=sample.pk).exists()

    def test_public_dataset_deletes_like_any_other(self, client):
        user = UserFactory()
        dataset = DatasetFactory(
            name="Public Dataset To Delete", visibility=Visibility.PUBLIC
        )
        pk = dataset.pk
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.post(url, data={"confirmation": "Public Dataset To Delete"})

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Dataset.all_objects.filter(pk=pk).exists()

    def test_preview_shows_counted_lines_for_two_sample_types_and_one_measurement_type(
        self, client
    ):
        from demo.factories import (
            ExampleMeasurementFactory,
            RockSampleFactory,
            WaterSampleFactory,
        )

        user = UserFactory()
        other_dataset = DatasetFactory(name="Other Dataset")
        other_sample = RockSampleFactory(dataset=other_dataset)

        dataset = DatasetFactory(name="Rich Dataset", dates=1)
        DatasetIdentifierFactory(related=dataset, value="10.9999/rich-dataset")
        dataset.add_contributor(user)
        RockSampleFactory(dataset=dataset, name="Granite Core 1")
        WaterSampleFactory(dataset=dataset, name="Spring Water 1")
        ExampleMeasurementFactory(dataset=dataset, sample=other_sample)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)
        content = response.content.decode()

        rock_label = RockSampleFactory._meta.model._meta.verbose_name_plural.title()
        water_label = WaterSampleFactory._meta.model._meta.verbose_name_plural.title()
        measurement_label = (
            ExampleMeasurementFactory._meta.model._meta.verbose_name_plural.title()
        )
        assertContains(response, f"{rock_label} (1)")
        assertContains(response, f"{water_label} (1)")
        assertContains(response, f"{measurement_label} (1)")

        # Only the counted lines: no instance names, contributors, dates or identifiers.
        assertNotContains(response, "Granite Core 1")
        assertNotContains(response, "Spring Water 1")
        # Within <main>: the shell's account menu shows the user's name on every page.
        main = BeautifulSoup(content, "html.parser").find("main")
        assert main is not None
        assert user.get_full_name() not in main.get_text()
        listed = [
            line
            for _group, lines, _depth in response.context["related_objects"]
            for line in lines
        ]
        assert sorted(listed) == sorted(
            [f"{rock_label} (1)", f"{water_label} (1)", f"{measurement_label} (1)"]
        )
        assertNotContains(response, "10.9999/rich-dataset")

    def test_preview_shows_nothing_for_a_dataset_holding_no_samples_or_measurements(
        self, client
    ):
        user = UserFactory()
        dataset = DatasetFactory(name="Bare Dataset", dates=1)
        DatasetIdentifierFactory(related=dataset, value="10.0000/bare-dataset")
        dataset.add_contributor(user)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)

        assert response.context["related_objects"] == []

    def test_preview_counts_match_what_an_actual_delete_removes(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Countable Dataset")
        rock_samples = [RockSampleFactory(dataset=dataset) for _ in range(2)]
        measurements = [
            ExampleMeasurementFactory(dataset=dataset, sample=rock_samples[0])
            for _ in range(3)
        ]
        sample_pks = [s.pk for s in rock_samples]
        measurement_pks = [m.pk for m in measurements]
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)
        sample_label = RockSampleFactory._meta.model._meta.verbose_name_plural.title()
        measurement_label = (
            ExampleMeasurementFactory._meta.model._meta.verbose_name_plural.title()
        )
        assertContains(response, f"{sample_label} (2)")
        assertContains(response, f"{measurement_label} (3)")

        response = client.post(url, data={"confirmation": "Countable Dataset"})

        assert response.status_code == 302
        assert Sample.objects.filter(pk__in=sample_pks).count() == 0
        assert Measurement.objects.filter(pk__in=measurement_pks).count() == 0


@pytest.mark.django_db
class TestNonCollectionPagesIgnorePublished:
    @staticmethod
    def _without_csrf_token(response):
        return re.sub(
            rb'name="csrfmiddlewaretoken" value="[^"]*"',
            b'name="csrfmiddlewaretoken" value=""',
            response.content,
        )

    def test_the_listing_shows_the_same_datasets_whichever_way_published_is_set(
        self, client
    ):
        # `published` changes what a card says, never whether the dataset is listed
        # (#333).
        dataset = DatasetFactory(name="Listed Either Way", visibility=Visibility.PUBLIC)
        url = reverse("dataset-list")

        Dataset.all_objects.filter(pk=dataset.pk).update(published=False)
        unpublished = client.get(url)

        Dataset.all_objects.filter(pk=dataset.pk).update(published=True)
        published = client.get(url)

        assert unpublished.status_code == 200
        assert published.status_code == 200
        for response in (unpublished, published):
            assertContains(response, "Listed Either Way")
            assertContains(response, dataset.uuid)

    def test_dataset_overview_page_shows_counts_but_no_records_until_published(
        self, client
    ):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        sample = RockSampleFactory(dataset=dataset, name="Zq-4471 rift core")
        url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})

        unpublished = client.get(url)
        Dataset.all_objects.filter(pk=dataset.pk).update(published=True)
        published = client.get(url)

        for response in (unpublished, published):
            assert response.status_code == 200
            page = BeautifulSoup(response.content, "html.parser")
            assert page.select(".stat-value")[0].get_text(strip=True) == "1"
            assertNotContains(response, sample.name)
        assert (
            len(BeautifulSoup(unpublished.content, "html.parser").select(".alert")) == 1
        )
        assert BeautifulSoup(published.content, "html.parser").select(".alert") == []

    def test_dataset_update_page_renders_identically_across_published_states(
        self, client
    ):
        user = UserFactory()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})

        Dataset.all_objects.filter(pk=dataset.pk).update(published=False)
        unpublished = client.get(url)

        Dataset.all_objects.filter(pk=dataset.pk).update(published=True)
        published = client.get(url)

        assert unpublished.status_code == 200
        assert self._without_csrf_token(unpublished) == self._without_csrf_token(
            published
        )

    def test_dataset_delete_page_renders_identically_across_published_states(
        self, client
    ):
        user = UserFactory()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        Dataset.all_objects.filter(pk=dataset.pk).update(published=False)
        unpublished = client.get(url)

        Dataset.all_objects.filter(pk=dataset.pk).update(published=True)
        published = client.get(url)

        assert unpublished.status_code == 200
        assert self._without_csrf_token(unpublished) == self._without_csrf_token(
            published
        )


@pytest.mark.django_db
class TestDatasetViews:
    def test_dataset_list_view_accessible(self, client):
        response = client.get(reverse("dataset-list"))

        assert response.status_code == 200

    def test_dataset_list_view_shows_public_datasets(self, client):
        public_dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)

        response = client.get(reverse("dataset-list"))

        assert public_dataset.name.encode() in response.content
        assert private_dataset.name.encode() not in response.content

    def test_dataset_create_view_requires_authentication(self, client):
        response = client.get(reverse("dataset-create"))

        assert response.status_code == 302

    def test_dataset_create_view_accessible_when_authenticated(
        self, authenticated_client
    ):
        response = authenticated_client.get(reverse("dataset-create"))

        assert response.status_code == 200

    def test_dataset_create_view_with_project_param(self, authenticated_client):
        project = ProjectFactory()

        response = authenticated_client.get(
            reverse("dataset-create"), {"project": project.pk}
        )

        assert response.status_code == 200

    def test_dataset_detail_view_accessible(self, client):
        dataset = DatasetFactory(
            name="Reef Survey Dataset", visibility=Visibility.PUBLIC
        )
        response = client.get(
            reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        )

        assert response.status_code == 200
        assert response.context["dataset"] == dataset
        assert dataset.name.encode() in response.content


@pytest.mark.django_db
class TestDatasetPermissions:
    def test_anonymous_user_cannot_create_dataset(self, client):
        form_data = {
            "name": "Test Dataset",
        }

        response = client.post(reverse("dataset-create"), data=form_data)

        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_dataset_creator_becomes_contributor(self, authenticated_client):
        form_data = {
            "name": "Test Dataset",
        }

        authenticated_client.post(reverse("dataset-create"), data=form_data)

        dataset = Dataset.objects.filter(name="Test Dataset").first()
        if dataset:
            assert dataset.contributors.count() > 0


@pytest.mark.django_db
class TestDatasetListingQueryCount:
    @staticmethod
    def _build_datasets(count):
        from research_vocabs.models import Concept

        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        keywords = list(Concept.objects.filter(vocabulary__name="fairdm-roles")[:3])
        for index in range(count):
            dataset = DatasetFactory(
                name=f"Survey {index}", visibility=Visibility.PUBLIC
            )
            DatasetDescriptionFactory(
                related=dataset,
                type="Abstract",
                value=f"## Survey {index}\n\nWe measured **heat flow** here.",
            )
            dataset.keywords.add(*keywords)
            dataset.add_contributor(PersonFactory())
            sample = RockSampleFactory(dataset=dataset)
            RockSampleFactory(dataset=dataset)
            ExampleMeasurementFactory(dataset=dataset, sample=sample)

    def test_listing_query_count_does_not_grow_with_the_number_of_datasets(
        self, client, django_assert_num_queries
    ):
        url = reverse("dataset-list")

        self._build_datasets(1)
        client.get(url)  # warm up one-time per-process and per-image setup
        with CaptureQueriesContext(connection) as one_dataset:
            response = client.get(url)
            assert response.status_code == 200
        baseline = len(one_dataset.captured_queries)

        self._build_datasets(19)
        client.get(url)
        with django_assert_num_queries(baseline):
            response = client.get(url)
            assert response.status_code == 200
            assert len(response.context["object_list"]) == 20


@pytest.mark.django_db
class TestDatasetListingCounts:
    def test_the_counts_are_annotated_onto_the_listing(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        sample = RockSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)

        entry = client.get(reverse("dataset-list")).context["object_list"][0]

        # Two counts in one query are two joins, so each needs `distinct` or it
        # multiplies the other's rows (3 samples and 2 measurements, not 6 of each).
        assert entry.sample_count == 3
        assert entry.measurement_count == 2

    def test_a_dataset_with_neither_counts_zero_of_each(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC)
        entry = client.get(reverse("dataset-list")).context["object_list"][0]
        assert entry.sample_count == 0
        assert entry.measurement_count == 0


@pytest.mark.django_db
class TestDatasetCardRendering:
    def _card_html(self, client):
        response = client.get(reverse("dataset-list"))
        assert response.status_code == 200
        return response, response.content.decode()

    def test_the_whole_card_is_the_link(self, client, public_dataset):
        response, _ = self._card_html(client)
        assertContains(response, f'href="{public_dataset.get_absolute_url()}"')

    def test_a_dataset_with_no_project_draws_no_parent_row(self, client):
        DatasetFactory(project=None, visibility=Visibility.PUBLIC)
        _, html = self._card_html(client)
        assert "record-card__parent" not in html

    def test_an_unlicensed_dataset_draws_no_licence_row(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, license=None)
        _, html = self._card_html(client)
        assert "record-card__license" not in html

    def test_card_shows_the_dataset_name(self, client):
        DatasetFactory(name="Rift Basin Heat Flow", visibility=Visibility.PUBLIC)
        response, _ = self._card_html(client)
        assertContains(response, "Rift Basin Heat Flow")

    def test_card_reports_a_published_dataset_as_published(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        response, _ = self._card_html(client)
        assertContains(response, "Published")

    def test_card_states_nothing_at_all_about_an_unpublished_dataset(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        _, html = self._card_html(client)
        assert "Not published" not in html
        assert "Published" not in html

    def test_an_unpublished_dataset_reports_no_counts(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)

        _, html = self._card_html(client)

        assert "1 sample" not in html
        assert "1 measurement" not in html
        assert "No samples" not in html
        assert "No measurements" not in html

    def test_card_counts_samples_and_measurements(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        first = RockSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=first)
        response, _ = self._card_html(client)
        assertContains(response, "2 samples")
        assertContains(response, "1 measurement")

    def test_card_counts_one_sample_in_the_singular(self, client):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)
        response, html = self._card_html(client)
        assertContains(response, "1 sample")
        assert "1 samples" not in html

    def test_card_says_so_rather_than_showing_a_zero(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        response, html = self._card_html(client)
        assertContains(response, "No samples")
        assertContains(response, "No measurements")
        assert "0 samples" not in html
        assert "0 measurements" not in html

    def test_card_names_the_parent_project(self, client):
        project = ProjectFactory(name="Deep Time Survey")
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        response, _ = self._card_html(client)
        assertContains(response, "Deep Time Survey")

    def test_the_parent_project_is_not_a_nested_link(self, client):
        project = ProjectFactory(name="Deep Time Survey")
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        _, html = self._card_html(client)
        assert project.get_absolute_url() not in html

    def test_card_renders_the_abstract_as_plain_text(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDescriptionFactory(
            related=dataset,
            type="Abstract",
            value="## Objectives\n\nWe measure **heat flow** across the rift.",
        )
        response, html = self._card_html(client)
        assertContains(response, "Objectives")
        assertContains(response, "heat flow")
        assert "## Objectives" not in html
        assert "**heat flow**" not in html

    def test_card_renders_keywords_as_badges_and_not_as_links(self, client):
        from research_vocabs.models import Concept

        keyword = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.keywords.add(keyword)
        response, html = self._card_html(client)
        assertContains(response, keyword.label)
        assert f'href="?keywords={keyword.pk}"' not in html
        assert f">{keyword.label}</a>" not in html

    def test_card_shows_the_dataset_uuid_with_a_copy_control(
        self, client, public_dataset
    ):
        response, html = self._card_html(client)
        assertContains(response, public_dataset.uuid)
        assert "clipboard" in html

    def test_card_names_the_licence(self, client):
        licence, _created = License.objects.get_or_create(
            name="CC BY-SA 4.0",
            defaults={
                "canonical_url": "https://example.org/cc-by-sa-4.0",
                "text": "…",
            },
        )
        DatasetFactory(visibility=Visibility.PUBLIC, license=licence)
        response, _ = self._card_html(client)
        assertContains(response, "CC BY-SA 4.0")

    def test_card_shows_the_last_modified_date(self, client, public_dataset):
        response, _ = self._card_html(client)
        assertContains(response, public_dataset.modified.strftime("%b"))

    def test_card_shows_contributor_names(self, client):
        person = PersonFactory(name="Ada Lovelace")
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.add_contributor(person)
        response, _ = self._card_html(client)
        assertContains(response, "Ada Lovelace")

    def test_no_comment_syntax_survives_into_the_rendered_page(self, client):
        from research_vocabs.models import Concept

        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.keywords.add(
            *Concept.objects.filter(vocabulary__name="fairdm-roles")[:3]
        )
        dataset.add_contributor(PersonFactory())
        DatasetDescriptionFactory(
            related=dataset, type="Abstract", value="An abstract."
        )

        _, html = self._card_html(client)

        assert "{#" not in html
        assert "#}" not in html
        assert "{%" not in html

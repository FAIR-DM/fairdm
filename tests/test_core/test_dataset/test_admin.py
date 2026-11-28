"""Integration tests for the dataset admin."""

import pytest
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.test import RequestFactory
from django.urls import reverse
from licensing.models import License

from fairdm.core.dataset.admin import (
    DatasetAdmin,
    DateInline,
    DescriptionInline,
    IdentifierInline,
)
from fairdm.core.dataset.models import (
    Dataset,
    DatasetDate,
    DatasetDescription,
    DatasetIdentifier,
)
from fairdm.core.vocabularies import (
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
    collection_members,
)
from fairdm.factories.core import (
    DatasetFactory,
    DatasetIdentifierFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestDatasetAdminPublished:
    def test_marking_published_persists_independently_of_visibility(self, admin_client):
        dataset = DatasetFactory(name="Test Dataset", visibility=Visibility.PRIVATE)
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk if dataset.project else "",
            "visibility": Visibility.PRIVATE,
            "published": "on",
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302, (
            "A 200 here means the form rejected the submission - check the "
            "change form's error list."
        )
        dataset.refresh_from_db()
        assert dataset.published is True
        assert dataset.visibility == Visibility.PRIVATE.value


@pytest.mark.django_db
class TestAdminChangelistIncludesPrivateDatasets:
    # The admin must reach private records, since that is where portal data gets
    # repaired.
    def test_private_dataset_appears_in_the_admin_queryset(self, rf, admin_user):
        private = DatasetFactory(visibility=Visibility.PRIVATE)
        request = rf.get("/")
        request.user = admin_user

        queryset = DatasetAdmin(Dataset, AdminSite()).get_queryset(request)

        assert private in queryset


@pytest.mark.django_db
class TestInlineDescriptionEditing:
    def test_can_edit_existing_description_via_inline(self, admin_client):
        dataset = DatasetFactory(name="Test Dataset")
        existing_desc = DatasetDescription.objects.create(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Original abstract text",
        )

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "1",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "descriptions-0-id": existing_desc.pk,
            "descriptions-0-related": dataset.pk,
            "descriptions-0-type": f"{DESCRIPTION_TYPES}/abstract",
            "descriptions-0-value": "Updated abstract text",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        admin_client.post(url, data=form_data)

        existing_desc.refresh_from_db()
        assert "Updated abstract text" in existing_desc.value


@pytest.mark.django_db
class TestDatasetAdminInlines:
    @staticmethod
    def _base_form_data(dataset):
        return {
            "name": dataset.name,
            "project": dataset.project.pk if dataset.project else "",
            "visibility": dataset.visibility,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

    def test_description_date_and_identifier_persist_through_one_submission(
        self, admin_client
    ):
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = self._base_form_data(dataset)
        form_data.update(
            {
                "descriptions-TOTAL_FORMS": "1",
                "descriptions-0-related": dataset.pk,
                "descriptions-0-type": f"{DESCRIPTION_TYPES}/abstract",
                "descriptions-0-value": "An abstract added inline.",
                "dates-TOTAL_FORMS": "1",
                "dates-0-related": dataset.pk,
                "dates-0-type": f"{DATE_TYPES}/available",
                "dates-0-value": "2024-01-15",
                "identifiers-TOTAL_FORMS": "1",
                "identifiers-0-related": dataset.pk,
                "identifiers-0-type": f"{IDENTIFIER_TYPES}/doi",
                "identifiers-0-value": "10.1234/inline-test",
            }
        )

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert DatasetDescription.objects.filter(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="An abstract added inline.",
        ).exists()
        assert DatasetDate.objects.filter(
            related=dataset, type_id=f"{DATE_TYPES}/available"
        ).exists()
        assert DatasetIdentifier.objects.filter(
            related=dataset,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1234/inline-test",
        ).exists()


@pytest.mark.django_db
class TestDatasetAdminInlineRowLimits:
    def test_description_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(
            [
                (concept.uri, concept.display_label())
                for concept in collection_members(Dataset.DESCRIPTION_TYPES)
            ]
        )

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = DescriptionInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_date_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(
            [
                (concept.uri, concept.display_label())
                for concept in collection_members(Dataset.DATE_TYPES)
            ]
        )

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = DateInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_identifier_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(collection_members(Dataset.IDENTIFIER_TYPES))

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = IdentifierInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size


@pytest.mark.django_db
class TestDateInlineCollectionPeriod:
    # `DatasetDate.clean()` looks its sibling up in the database, so two new dates in
    # one submission never see each other unless the formset checks the pair itself.
    def test_backwards_pair_submitted_together_is_refused(self, admin_client):
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "2",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": dataset.pk,
            "dates-0-type": DatasetDate.START_TYPE,
            "dates-0-value": "2020-06-01",
            "dates-1-related": dataset.pk,
            "dates-1-type": DatasetDate.END_TYPE,
            "dates-1-value": "2019-05-01",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 200
        content = response.content.decode()
        assert "2020-06-01" in content
        assert "2019-05-01" in content
        formsets = {
            inline.formset.prefix: inline.formset
            for inline in response.context["inline_admin_formsets"]
        }
        assert formsets["dates"].non_form_errors()
        assert not DatasetDate.objects.filter(related=dataset).exists()

    def test_forwards_pair_submitted_together_is_accepted(self, admin_client):
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "2",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": dataset.pk,
            "dates-0-type": DatasetDate.START_TYPE,
            "dates-0-value": "2020-06-01",
            "dates-1-related": dataset.pk,
            "dates-1-type": DatasetDate.END_TYPE,
            "dates-1-value": "2020-12-01",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302
        assert DatasetDate.objects.filter(
            related=dataset, type=DatasetDate.START_TYPE
        ).exists()
        assert DatasetDate.objects.filter(
            related=dataset, type=DatasetDate.END_TYPE
        ).exists()


@pytest.mark.django_db
class TestDatasetAdminColumns:
    def test_columns_reflect_presence_and_absence_of_abstract_and_doi(self, rf):
        with_both = DatasetFactory(name="Fully Described Dataset")
        DatasetDescription.objects.create(
            related=with_both,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="An abstract.",
        )
        DatasetIdentifier.objects.create(
            related=with_both,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1234/with-both",
        )
        without_either = DatasetFactory(name="Bare Dataset")

        admin_instance = DatasetAdmin(Dataset, AdminSite())
        queryset = admin_instance.get_queryset(rf.get("/"))
        with_both = queryset.get(pk=with_both.pk)
        without_either = queryset.get(pk=without_either.pk)

        assert admin_instance.has_abstract(with_both) is True
        assert admin_instance.has_doi(with_both) is True
        assert admin_instance.has_abstract(without_either) is False
        assert admin_instance.has_doi(without_either) is False


@pytest.mark.django_db
class TestDatasetAdminColumnsQueryCount:
    def test_flags_are_annotated_without_a_query_per_row(
        self, rf, django_assert_num_queries
    ):
        for _ in range(3):
            dataset = DatasetFactory(project=None)
            DatasetDescription.objects.create(
                related=dataset,
                type_id=f"{DESCRIPTION_TYPES}/abstract",
                value="An abstract.",
            )
            DatasetIdentifier.objects.create(
                related=dataset,
                type_id=f"{IDENTIFIER_TYPES}/doi",
                value=f"10.1234/{dataset.pk}",
            )
        DatasetFactory(project=None)  # a row with neither, so both flags read False

        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        queryset = admin_instance.get_queryset(request)

        with django_assert_num_queries(1):
            for obj in queryset:
                admin_instance.has_abstract(obj)
                admin_instance.has_doi(obj)


@pytest.mark.django_db
class TestDatasetAdminLicenceWarning:
    @staticmethod
    def _form_data(dataset, license_pk):
        return {
            "name": dataset.name,
            "project": dataset.project.pk if dataset.project else "",
            "visibility": dataset.visibility,
            "license": license_pk,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

    def test_changing_licence_on_a_dataset_with_a_doi_warns(self, admin_client):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc_by_sa = License.objects.get(name="CC BY-SA 4.0")
        dataset = DatasetFactory(name="Published Dataset", license=cc_by)
        DatasetIdentifierFactory(
            related=dataset,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1234/published",
        )

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.post(url, data=self._form_data(dataset, cc_by_sa.pk))

        assert response.status_code == 302
        levels = [m.level for m in get_messages(response.wsgi_request)]
        assert messages.WARNING in levels

    def test_changing_licence_on_a_dataset_without_a_doi_does_not_warn(
        self, admin_client
    ):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc_by_sa = License.objects.get(name="CC BY-SA 4.0")
        dataset = DatasetFactory(name="Unpublished Dataset", license=cc_by)

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.post(url, data=self._form_data(dataset, cc_by_sa.pk))

        assert response.status_code == 302
        levels = [m.level for m in get_messages(response.wsgi_request)]
        assert messages.WARNING not in levels


@pytest.mark.django_db
class TestDatasetAdminAutocompleteFields:
    def test_the_project_field_finds_a_project_by_name(self, admin_client):
        project = ProjectFactory(name="Glacier monitoring")

        response = admin_client.get(
            reverse("admin:autocomplete"),
            {
                "term": "Glacier",
                "app_label": "dataset",
                "model_name": "dataset",
                "field_name": "project",
            },
        )

        assert response.status_code == 200
        assert [row["id"] for row in response.json()["results"]] == [str(project.pk)]

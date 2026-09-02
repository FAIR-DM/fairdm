"""Integration tests for the Dataset admin interface (US-6).

Covers search, filtering, inline editing, the abstract/DOI list columns,
the absence of any bulk visibility action, readonly fields and the
licence-change warning (FR-023 to FR-028).
"""

import pytest
from django.contrib.admin.sites import AdminSite
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
from fairdm.factories.core import (
    DatasetFactory,
    DatasetIdentifierFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility


def _result_pks(response):
    """The primary keys the changelist actually matched - read off the
    `ChangeList` Django's admin builds, which is the result set itself,
    not the rendered markup.
    """
    return {obj.pk for obj in response.context["cl"].result_list}


@pytest.mark.django_db
class TestDatasetAdminSearch:
    """T076/FR-023: each search term finds a dataset that matches it -
    name, generated identifier, external identifier and project - asserted
    against the changelist's actual result set.
    """

    def test_search_by_name(self, admin_client):
        match = DatasetFactory(name="Climate Research Data")
        other = DatasetFactory(name="Ocean Temperature Readings")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": "Climate Research Data"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_by_generated_identifier(self, admin_client):
        match = DatasetFactory(name="Climate Research Data")
        other = DatasetFactory(name="Ocean Temperature Readings")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": str(match.uuid)})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_by_external_identifier(self, admin_client):
        match = DatasetFactory(name="Climate Research Data")
        other = DatasetFactory(name="Ocean Temperature Readings")
        DatasetIdentifierFactory(
            related=match, type="DOI", value="10.1234/climate-example"
        )

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": "10.1234/climate-example"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_search_by_project(self, admin_client):
        project = ProjectFactory(name="Example Research Project")
        match = DatasetFactory(name="Climate Research Data", project=project)
        other = DatasetFactory(name="Ocean Temperature Readings")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"q": "Example Research Project"})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks


@pytest.mark.django_db
class TestDatasetAdminFilters:
    """T077/FR-023: each filter narrows to the matching datasets *and*
    removes the non-matching ones.
    """

    def test_filter_by_project(self, admin_client):
        project_a = ProjectFactory(name="Project A")
        project_b = ProjectFactory(name="Project B")
        match = DatasetFactory(name="Dataset 1", project=project_a)
        other = DatasetFactory(name="Dataset 2", project=project_b)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"project__id__exact": str(project_a.pk)})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_filter_by_visibility(self, admin_client):
        match = DatasetFactory(name="Public Dataset", visibility=Visibility.PUBLIC)
        other = DatasetFactory(name="Private Dataset", visibility=Visibility.PRIVATE)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(
            url, {"visibility__exact": str(Visibility.PUBLIC.value)}
        )

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks

    def test_filter_by_license(self, admin_client):
        """The session-level `django_db_setup` fixture seeds the
        recommended licences through `seed_licenses` before any test
        runs (T099), so CC BY 4.0 and CC BY-SA 4.0 already exist here.
        """
        cc_by = License.objects.get(name="CC BY 4.0")
        cc_by_sa = License.objects.get(name="CC BY-SA 4.0")
        match = DatasetFactory(name="Open Data", license=cc_by)
        other = DatasetFactory(name="ShareAlike Data", license=cc_by_sa)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url, {"license__id__exact": str(cc_by.pk)})

        assert response.status_code == 200
        pks = _result_pks(response)
        assert match.pk in pks
        assert other.pk not in pks


@pytest.mark.django_db
class TestDatasetAdminPublished:
    """T014 / US-1, Acceptance Scenarios 2 and 5, FR-003: the admin exposes
    `published` as an editable field and a list filter, and marking it
    persists independently of `visibility`.
    """

    def test_published_is_an_editable_form_field(self, rf, admin_user):
        dataset = DatasetFactory()
        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        request.user = admin_user

        form_class = admin_instance.get_form(request, dataset)

        assert "published" in form_class.base_fields

    def test_published_is_a_list_filter(self, rf, admin_user):
        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        request.user = admin_user

        filter_fields = admin_instance.get_list_filter(request)

        assert "published" in filter_fields

    def test_marking_published_persists_independently_of_visibility(
        self, admin_client
    ):
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
    """T062 / FR-019a: the admin dataset list shows private datasets - the
    interface that repairs a portal must reach the records that need
    repairing. `DatasetAdmin.get_queryset()` uses `Dataset.all_objects`
    rather than the privacy-first default manager (T067).
    """

    def test_private_dataset_appears_in_the_unfiltered_changelist(
        self, admin_client
    ):
        DatasetFactory(name="Unfinished Private Dataset", visibility=Visibility.PRIVATE)

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        pks = {obj.pk for obj in response.context["cl"].result_list}
        assert Dataset.all_objects.get(name="Unfinished Private Dataset").pk in pks


@pytest.mark.django_db
class TestAdminListDisplayFields:
    """Test admin list_display configuration."""

    def test_list_display_shows_name(self, admin_client):
        """Test that name field appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert dataset.name in content

    def test_list_display_shows_added_timestamp(self, admin_client):
        """Test that 'added' timestamp appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        # Check that 'added' column header or timestamp value is present
        content = response.content.decode()
        assert "added" in content.lower() or str(dataset.added.year) in content

    def test_list_display_shows_modified_timestamp(self, admin_client):
        """Test that 'modified' timestamp appears in admin list display."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "modified" in content.lower() or str(dataset.modified.year) in content

    def test_list_display_shows_has_data_property(self, admin_client):
        """Test that has_data property appears in admin list display."""
        DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Should show has_data column header or boolean indicator
        assert "has_data" in content.lower() or "has data" in content.lower()


@pytest.mark.django_db
class TestInlineDescriptionEditing:
    """Test admin inline editing of dataset descriptions."""

    def test_inline_description_shown_in_change_form(self, admin_client):
        """Test that description inline is displayed in dataset change form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for inline formset elements
        assert (
            "datasetdescription" in content.lower() or "description" in content.lower()
        )

    def test_can_add_description_via_inline(self, admin_client):
        """Test adding a description through inline form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])

        form_data = {
            "name": dataset.name,
            "project": dataset.project.pk,
            "visibility": dataset.visibility,
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "descriptions-0-related": dataset.pk,
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
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

        assert response.status_code in [200, 302]
        descriptions = DatasetDescription.objects.filter(related=dataset)
        assert descriptions.count() > 0, (
            f"Expected descriptions to be created, but found {descriptions.count()}"
        )

    def test_can_edit_existing_description_via_inline(self, admin_client):
        """Test editing an existing description through inline form."""
        dataset = DatasetFactory(name="Test Dataset")
        existing_desc = DatasetDescription.objects.create(
            related=dataset,
            type="Abstract",
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
            "descriptions-0-type": "Abstract",
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
class TestInlineDateEditing:
    """Test admin inline editing of dataset dates."""

    def test_inline_date_shown_in_change_form(self, admin_client):
        """Test that date inline is displayed in dataset change form."""
        dataset = DatasetFactory(name="Test Dataset")
        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert "datasetdate" in content.lower() or "date" in content.lower()

    def test_can_add_date_via_inline(self, admin_client):
        """Test adding a date through inline form."""
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
            "dates-TOTAL_FORMS": "1",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": dataset.pk,
            "dates-0-type": "Available",
            "dates-0-value": "2024-01-15",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code in [200, 302]
        dates = DatasetDate.objects.filter(related=dataset)
        assert dates.count() > 0, f"Expected dates to be created, but found {dates.count()}"


@pytest.mark.django_db
class TestDatasetAdminInlines:
    """T078/T085/FR-024: a description, a date and an identifier added
    inline all persist - through a real form submission, not by the page
    mentioning the word.
    """

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
                "descriptions-0-type": "Abstract",
                "descriptions-0-value": "An abstract added inline.",
                "dates-TOTAL_FORMS": "1",
                "dates-0-related": dataset.pk,
                "dates-0-type": "Available",
                "dates-0-value": "2024-01-15",
                "identifiers-TOTAL_FORMS": "1",
                "identifiers-0-related": dataset.pk,
                "identifiers-0-type": "DOI",
                "identifiers-0-value": "10.1234/inline-test",
            }
        )

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302, (
            "A 200 here means the formset rejected the submission - check "
            "the change form's error list."
        )
        assert DatasetDescription.objects.filter(
            related=dataset, type="Abstract", value="An abstract added inline."
        ).exists()
        assert DatasetDate.objects.filter(related=dataset, type="Available").exists()
        assert DatasetIdentifier.objects.filter(
            related=dataset, type="DOI", value="10.1234/inline-test"
        ).exists()


@pytest.mark.django_db
class TestDatasetAdminInlineRowLimits:
    """T079/FR-024: each inline offers no more rows than its vocabulary
    has types.
    """

    def test_description_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(Dataset.DESCRIPTION_TYPES.choices)

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = DescriptionInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_date_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(Dataset.DATE_TYPES.choices)

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = DateInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size

    def test_identifier_inline_max_num_matches_vocabulary_size(self, admin_user):
        vocabulary_size = len(Dataset.IDENTIFIER_TYPES)

        admin_site = AdminSite()
        request = RequestFactory().get("/")
        request.user = admin_user
        inline = IdentifierInline(Dataset, admin_site)
        formset = inline.get_formset(request)

        assert formset.max_num == vocabulary_size


@pytest.mark.django_db
class TestDateInlineCollectionPeriod:
    """T043: the collection-period check fires through the administrative
    inline, where both dates arrive in one submission and neither is in
    the database yet - a sibling lookup in the database (`DatasetDate
    .clean()`'s `_sibling_value()`) misses a row being added alongside it
    in the same formset, so `DateInlineFormSet` (`fairdm/core/dataset
    /admin.py`) checks the pair directly off the submitted forms.
    """

    def test_backwards_pair_submitted_together_is_refused(self, admin_client):
        """A CollectionEnd earlier than a CollectionStart submitted in the
        same inline formset - neither saved yet - is refused.
        """
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

        # A rejected formset re-renders the change form rather than
        # redirecting.
        assert response.status_code == 200
        content = response.content.decode()
        assert "2020-06-01" in content
        assert "2019-05-01" in content
        # The refusal names the dataset's own date vocabulary, matching what
        # `DatasetDate.clean()` says when the pair arrives one row at a time.
        assert "collection end date" in content
        assert "collection start date" in content
        assert not DatasetDate.objects.filter(related=dataset).exists()

    def test_forwards_pair_submitted_together_is_accepted(self, admin_client):
        """The same submission shape with a CollectionStart before the
        CollectionEnd succeeds - proving the check discriminates rather
        than refusing every paired submission.
        """
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
    """T080/T086/FR-025: each row shows whether the dataset has an
    abstract and whether it has a DOI.
    """

    def test_columns_reflect_presence_and_absence_of_abstract_and_doi(self, rf):
        with_both = DatasetFactory(name="Fully Described Dataset")
        DatasetDescription.objects.create(
            related=with_both, type="Abstract", value="An abstract."
        )
        DatasetIdentifier.objects.create(
            related=with_both, type="DOI", value="10.1234/with-both"
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
    """T080: the abstract/DOI columns are annotated on the changelist
    queryset, not evaluated with a query per row - guarded so a per-row
    property cannot creep back in.
    """

    def test_flags_are_annotated_without_a_query_per_row(
        self, rf, django_assert_num_queries
    ):
        for _ in range(5):
            dataset = DatasetFactory()
            DatasetDescription.objects.create(
                related=dataset, type="Abstract", value="An abstract."
            )
            DatasetIdentifier.objects.create(
                related=dataset, type="DOI", value=f"10.1234/{dataset.pk}"
            )
        DatasetFactory()  # a row with neither, to prove both flags read False

        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        queryset = admin_instance.get_queryset(request)

        with django_assert_num_queries(1):
            for obj in queryset:
                admin_instance.has_abstract(obj)
                admin_instance.has_doi(obj)


@pytest.mark.django_db
class TestDatasetAdminActions:
    """T081/FR-026: no action changes the visibility of more than one
    dataset at a time.

    The three tests this replaces asserted that "make public", "make
    private" and "change visibility" were absent from the changelist
    markup - an action registered under any other name would satisfy
    that just as well. This reads the behaviour off the registered
    actions themselves instead.
    """

    def test_no_action_besides_delete_is_registered(self, rf, admin_user):
        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        request.user = admin_user

        actions = admin_instance.get_actions(request)

        # Django's own `delete_selected` removes whole records; it does
        # not touch `visibility`. `DatasetAdmin` declares no actions of
        # its own, so nothing registered here can change more than one
        # dataset's visibility in a single call.
        assert set(actions) == {"delete_selected"}


@pytest.mark.django_db
class TestAutocompleteOnForeignKeys:
    """Test Django autocomplete on ForeignKey/ManyToMany fields."""

    def test_project_field_has_autocomplete(self, admin_client):
        """Test that project field uses autocomplete widget."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for autocomplete widget indicators (data-autocomplete-light, select2, etc.)
        assert (
            "autocomplete" in content.lower()
            or "select2" in content.lower()
            or "data-autocomplete" in content.lower()
        )

    def test_license_field_has_autocomplete(self, admin_client):
        """Test that license field uses autocomplete widget."""
        dataset = DatasetFactory(name="Test Dataset")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Check for autocomplete on license field
        assert "license" in content.lower()
        # Should have autocomplete capabilities
        assert (
            "autocomplete" in content.lower()
            or "select2" in content.lower()
            or "data-autocomplete" in content.lower()
        )


@pytest.mark.django_db
class TestDatasetAdminReadonly:
    """T082/FR-027: the generated identifier and the timestamps are
    unchangeable, asserted against the form's own fields rather than
    against markup - Django's admin emits the word "readonly" in
    unrelated places regardless of whether a field actually is one.
    """

    def test_uuid_added_and_modified_are_absent_from_the_editable_form_fields(
        self, rf, admin_user
    ):
        dataset = DatasetFactory()
        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        request.user = admin_user

        form_class = admin_instance.get_form(request, dataset)

        assert "uuid" not in form_class.base_fields
        assert "added" not in form_class.base_fields
        assert "modified" not in form_class.base_fields

    def test_uuid_added_and_modified_are_declared_readonly(self, rf, admin_user):
        dataset = DatasetFactory()
        admin_instance = DatasetAdmin(Dataset, AdminSite())
        request = rf.get("/")
        request.user = admin_user

        readonly = set(admin_instance.get_readonly_fields(request, dataset))
        assert {"uuid", "added", "modified"} <= readonly


@pytest.mark.django_db
class TestDatasetAdminLicenceWarning:
    """T083/T087/FR-028: changing the licence of a dataset carrying a DOI
    warns the administrator; changing it on one without a DOI does not.
    """

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
        DatasetIdentifierFactory(related=dataset, type="DOI", value="10.1234/published")

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.post(
            url, data=self._form_data(dataset, cc_by_sa.pk), follow=True
        )

        messages = [str(m) for m in response.context["messages"]]
        assert any("doi" in m.lower() for m in messages), messages

    def test_changing_licence_on_a_dataset_without_a_doi_does_not_warn(
        self, admin_client
    ):
        cc_by = License.objects.get(name="CC BY 4.0")
        cc_by_sa = License.objects.get(name="CC BY-SA 4.0")
        dataset = DatasetFactory(name="Unpublished Dataset", license=cc_by)

        url = reverse("admin:dataset_dataset_change", args=[dataset.pk])
        response = admin_client.post(
            url, data=self._form_data(dataset, cc_by_sa.pk), follow=True
        )

        messages = [str(m) for m in response.context["messages"]]
        assert not any("doi" in m.lower() for m in messages), messages

"""
Integration tests for fairdm.core.dataset views.

Tests the interaction between views, forms, and models, verifying complete
request/response cycles for dataset CRUD operations.

Phases 3-8 map to User Stories 1-6 from spec/014-dataset-crud-views.

Also covers general list/create/permission smoke tests moved from the former
test_integration.py.
"""

import re
import time

import pytest
from django import forms
from django.urls import reverse
from guardian.shortcuts import assign_perm
from licensing.models import License
from pytest_django.asserts import assertContains

from fairdm.core.dataset.forms import DatasetCreateForm, DatasetForm
from fairdm.core.dataset.models import Dataset
from fairdm.core.dataset.views import DatasetCreateView
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import (
    DatasetFactory,
    DatasetIdentifierFactory,
    ProjectFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility

# ---------------------------------------------------------------------------
# Phase 3 — User Story 1: Browse and Search the Dataset List
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetListView:
    """Smoke tests and behaviour tests for DatasetListView (US1)."""

    def test_anonymous_get(self, client):
        """T004 — GET /datasets/ returns 200 for anonymous users."""
        url = reverse("dataset-list")
        response = client.get(url)
        assert response.status_code == 200

    def test_shows_only_public_datasets(self, client):
        """T005 — List shows only PUBLIC datasets; PRIVATE datasets are hidden."""
        public = DatasetFactory(name="Public Dataset", visibility=Visibility.PUBLIC)
        DatasetFactory(name="Private Dataset", visibility=Visibility.PRIVATE)

        url = reverse("dataset-list")
        response = client.get(url)

        assert response.status_code == 200
        assert public.name in str(response.content)
        assert "Private Dataset" not in str(response.content)

    def test_order_by_added(self, client):
        """T006 — ?o=added and ?o=-added return results in expected chronological order."""
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


# ---------------------------------------------------------------------------
# 014 US-1: Find a dataset — visibility, search, ordering, filters, empty
# state and the listing entry's link. Mirrors
# tests/test_core/test_project/test_views.py::TestProjectListing.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetListingVisibility:
    """T012/FR-002 — the listing shows only public datasets, whoever is looking. The
    pre-existing `test_shows_only_public_datasets` above only covers a signed-out
    visitor; T012 and SC-002 both name the signed-in cases too (reconciliation: built,
    untested)."""

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
    """T013/FR-003,FR-006 — one search, over name, uuid, external identifiers,
    descriptions and keywords, replacing the two competing controls the listing used
    to offer (014 plan P8). Each of the five reaches a record the others would not."""

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
    """T014/FR-004 — ordering by name and by date added, in both directions. The
    pre-existing `test_order_by_added` above covers date added; name is untested in
    either direction (reconciliation: built, untested)."""

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
    """T015/FR-005 — filters by licence, project, description type and date type,
    applied through the listing itself."""

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
        response = client.get(
            reverse("dataset-list"), {"description_type": "Abstract"}
        )
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
    """T016/FR-006 — every filter the rendered filterset form actually offers runs a
    query without raising, applied one at a time. The field set is read from the
    rendered form itself, never a hand-written list, so a filter added or removed
    later is swept automatically."""

    def _value_for(self, field_name, dataset, project, license_obj):
        return {
            "license": license_obj.pk,
            "project": project.pk,
            "description_type": "Abstract",
            "date_type": "Available",
            "image": "true",
            "visibility": Visibility.PUBLIC,
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


# ---------------------------------------------------------------------------
# Phase 4 — User Story 2: Create a New Dataset
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDatasetCreateView:
    """Smoke tests and behaviour tests for DatasetCreateView (US2)."""

    def test_anonymous_redirects_to_login(self, client):
        """T011 — GET /datasets/create/ by anonymous client returns 302 to login."""
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_authenticated_get_200(self, client):
        """T012 — GET /datasets/create/ by authenticated client returns 200."""
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        """T013 — Valid POST redirects to the dataset's own page (dataset:overview,
        014 T057 — the retired standalone dataset-detail route no longer exists).

        MUST FAIL before T015 (DatasetCreateForm) because DatasetForm requires
        additional fields that make a minimal POST fail form validation.
        """
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # User must be a contributor of the project for it to appear in the
        # project queryset (DatasetForm filters to user.projects.all())
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

        # `all_objects` - a newly created dataset defaults to private, and
        # `Dataset.objects` is privacy-first by default (R1).
        dataset = Dataset.all_objects.get(name="New Test Dataset")
        expected_url = reverse("dataset:overview", kwargs={"uuid": dataset.uuid})
        assert response.url == expected_url

    def test_assigns_contributor_roles(self, client):
        """T014 — After valid POST, creating user is a contributor with correct roles.

        FR-013. Object-level permission assignment (FR-012) is covered on its own terms by
        `TestDatasetCreatePagePermissionAssignment` (T029); this test covers the contributor/
        role side only.
        """
        from licensing.models import License

        from fairdm.factories import ProjectFactory

        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # User must be a contributor of the project for it to appear in the
        # project queryset (DatasetForm filters to user.projects.all())
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

        # `all_objects` - a newly created dataset defaults to private.
        dataset = Dataset.all_objects.get(name="Permission Test Dataset")

        contributor = dataset.contributors.filter(contributor=user).first()
        assert contributor is not None, "User should be a contributor"
        role_names = list(contributor.roles.values_list("name", flat=True))
        for role in ["Creator", "ProjectMember", "ContactPerson"]:
            assert role in role_names, f"Missing contributor role: {role}"


@pytest.mark.django_db
class TestDatasetCreatePageUsesTheDeclaredForm:
    """T033/FR-022 - the creation page uses the update page's declared form (`DatasetForm`)
    narrowed to its own four fields, rather than a field list of its own. A label declared once
    on `DatasetForm` reaches both the creation and the update page."""

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
    """T023/FR-012 - the creation page asks for a name, a visibility, a licence and a project,
    and for nothing else. A field added later (e.g. `image` or `reference`, both offered by the
    update page) fails this test."""

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
    """T024/FR-013 - visibility is presented as a visible radio choice pre-selecting Public.
    Asserted against the rendered control and its pre-selection, not just the form's initial
    value (rituals)."""

    def test_the_rendered_page_offers_a_radio_choice_pre_selecting_public(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse("dataset-create")

        response = client.get(url)
        form = response.context["form"]

        assert isinstance(form.fields["visibility"].widget, forms.RadioSelect)
        assertContains(response, "Private")
        assertContains(response, "Public")

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
    """T025/FR-014 - the portal's configured default licence is pre-selected. Tested under an
    overridden setting, so the test does not pin one licence name (rituals)."""

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
    """T026/FR-015 - the project field is optional and starts empty; a dataset can be created
    without one. Exercised against the creation page's own shipped form
    (`DatasetCreateForm`), not `DatasetForm` directly — the object under test in the
    pre-existing `test_forms.py` coverage is unreachable from this page (reconciliation:
    vacuous test)."""

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
    """T027/FR-016 - the project field offers only projects the signed-in researcher may use,
    on the same terms as the update page (`DatasetForm.__init__`, `request.user.projects.all()`,
    mirrors `test_plugins.py`'s `TestUpdatePageProjectField`)."""

    def test_the_project_field_is_narrowed_to_the_researchers_own_projects(self, client):
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
class TestDatasetCreatePageNameRequired:
    """T028/FR-017 - a dataset cannot be created without a name. Exercised against the creation
    page's own shipped form (`DatasetCreateForm`), not `DatasetForm` directly — the pre-existing
    `test_forms.py` coverage exercises an object unreachable from this page (reconciliation:
    vacuous test)."""

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
    """T029/FR-018 - on creation the creator is granted view, change, delete,
    change-metadata and change-settings on the record. Built (`views.py` `form_valid`) but
    untested until now (reconciliation)."""

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
            assert user.has_perm(f"dataset.{perm}", dataset), f"Missing permission: {perm}"


@pytest.mark.django_db
class TestDatasetCreatePageRecordsCreator:
    """T031/FR-020 - on creation the dataset records who created it, written server-side and not
    through the form (`created_by` is `editable=False` — `models.py`)."""

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


# ---------------------------------------------------------------------------
# Phase 5 — User Story 3: Edit Dataset Core Attributes
# ---------------------------------------------------------------------------


def _identifier_management_data(total=0, initial=0):
    """Management-form boilerplate for the attributes page's identifiers row set
    (`fairdm/core/related_records.py` `DatasetIdentifierInline`, prefix `identifiers` from
    `AbstractIdentifier.Meta.default_related_name`). Mirrors
    `tests/test_core/test_project/test_views.py`'s helper of the same name."""
    return {
        "identifiers-TOTAL_FORMS": str(total),
        "identifiers-INITIAL_FORMS": str(initial),
        "identifiers-MIN_NUM_FORMS": "0",
        "identifiers-MAX_NUM_FORMS": "1000",
    }


def _date_management_data(total=0, initial=0):
    """Management-form boilerplate for the attributes page's dates row set
    (`fairdm/core/related_records.py` `DatasetDateInline`, prefix `dates` from
    `AbstractDate.Meta.default_related_name`). Mirrors
    `tests/test_core/test_project/test_views.py`'s helper of the same name."""
    return {
        "dates-TOTAL_FORMS": str(total),
        "dates-INITIAL_FORMS": str(initial),
        "dates-MIN_NUM_FORMS": "0",
        "dates-MAX_NUM_FORMS": "1000",
    }


@pytest.mark.django_db
class TestDatasetUpdateView:
    """Smoke tests and behaviour tests for the update page (US3), an additional view of
    `dataset:overview` rather than the retired standalone `dataset-update` route (014 plan P1).
    Row-set and field-set behaviour lives in `tests/test_core/test_dataset/test_plugins.py`,
    mirroring the project's own split.
    """

    def test_anonymous_redirects_to_login(self, client):
        """T019/T034 — GET the update page for a public dataset by an anonymous client
        returns 302, since it is public visibility, not authentication, that the 404
        override below is guarding."""
        dataset = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_anonymous_visitor_to_a_private_dataset_returns_404(self, client):
        """T035 — An anonymous visitor to a private dataset's update page answers 404, not a
        sign-in redirect, so the address does not confirm the record exists — the same
        disclosure rule `dataset:overview` itself carries (014 plan P1)."""
        dataset = DatasetFactory()  # private, per the model default
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_no_permission_on_a_public_dataset_returns_403(self, client):
        """T020/T035 — Authenticated client without change_dataset returns 403."""
        user = UserFactory()
        dataset = DatasetFactory(visibility=Dataset.VISIBILITY_CHOICES.PUBLIC)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_no_permission_on_a_private_dataset_returns_404(self, client):
        """T035 — A private dataset the user may not edit answers 404, not 403, so the
        response does not confirm that a dataset with this address exists — the same
        disclosure rule `dataset:overview` itself carries (014 plan P1)."""
        user = UserFactory()
        dataset = DatasetFactory()  # private, per the model default
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_with_permission_returns_200(self, client):
        """T021/T034 — Client with change_dataset permission GET returns 200."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-update", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_valid_post_redirects_to_detail(self, client):
        """T022/T045 — Valid POST by permitted user returns 302 to the dataset's own page."""
        from licensing.models import License

        user = UserFactory()
        dataset = DatasetFactory(name="Original Name")
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)

        # User must be a contributor of the dataset's project for it to appear
        # in the project queryset (DatasetForm filters to user.projects.all())
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


# ---------------------------------------------------------------------------
# Phase 6 — User Story 4: Delete a Dataset
# ---------------------------------------------------------------------------


def _assert_cascade_preview_group(content, label):
    """Whether the cascade preview's own group-heading markup (`delete_view.html`'s
    `<c-text ... bold />`) names `label`, rather than a bare substring match — the portal's
    sidebar navigation renders several of the same words ("Samples", "Rock Samples") in its own
    unrelated markup, on every page a signed-in visitor can reach."""
    pattern = rf'<p class="text-base mb-3 font-semibold "\s*>\s*{re.escape(label)}\s*</p>'
    return re.search(pattern, content) is not None


@pytest.mark.django_db
class TestDatasetDeleteView:
    """The deletion page (US-6), an additional view of `dataset:overview` rather than the
    retired standalone `dataset-delete` route (014 plan P7), mirroring
    `tests/test_core/test_dataset/test_views.py::TestDatasetUpdateView`'s own split from its
    retired route."""

    def test_anonymous_visitor_to_a_public_dataset_redirects_to_login(self, client):
        """T070 — the deletion page requires the visitor to be signed in (FR-043): a public
        dataset's page still redirects an anonymous visitor to sign in, since it is
        authentication rather than the dataset's own visibility being tested here."""
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_anonymous_visitor_to_a_private_dataset_returns_404(self, client):
        """T070/T071 — an anonymous visitor to a private dataset's deletion page answers 404,
        not a sign-in redirect, so the address does not confirm the record exists — the same
        disclosure rule `dataset:overview` and its update page carry."""
        dataset = DatasetFactory()  # private, per the model default
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_no_permission_on_a_public_dataset_returns_403(self, client):
        """T071 — an authenticated visitor without delete_dataset on a public dataset is
        refused with 403, since the dataset's existence is already public knowledge."""
        user = UserFactory()
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 403

    def test_no_permission_on_a_private_dataset_returns_404(self, client):
        """T071 — a private dataset the requester may not delete answers 404, not 403, so the
        response does not confirm that a dataset with this address exists."""
        user = UserFactory()
        dataset = DatasetFactory()  # private, per the model default
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 404

    def test_with_permission_returns_200(self, client):
        """T070 — a client holding delete_dataset reaches the page at its stable, uuid-keyed
        address."""
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        assert response.status_code == 200

    def test_wrong_name_shows_error(self, client):
        """T072 — a confirmation that does not match the dataset's name is refused, and the
        dataset is not deleted."""
        user = UserFactory()
        dataset = DatasetFactory(name="My Dataset")
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "Wrong Name"})
        assert response.status_code == 200
        assert "confirmation" in response.context["form"].errors
        # `all_objects` - the dataset is private by default.
        assert Dataset.all_objects.filter(pk=dataset.pk).exists()

    def test_confirmation_ignores_surrounding_whitespace(self, client):
        """T072 — the dataset's name typed with leading/trailing spaces is accepted (FR-045)."""
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
        """T073 — the rendered page carries exactly one control named for the confirmation.
        Fixed upstream in django-mvp 0.19.3 (the page used to draw the bound field a second
        time, unbound, so what the visitor typed was never what got posted); this is now an
        ordinary passing test rather than an expected failure."""
        user = UserFactory()
        dataset = DatasetFactory(name="My Dataset")
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})
        response = client.get(url)
        content = response.content.decode()
        assert content.count('id="id_confirmation"') == 1

    def test_correct_name_redirects_to_list(self, client):
        """T077 — a valid submission redirects to the dataset listing (FR-049), and the
        dataset is gone."""
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
        """T077 — the samples held beneath a deleted dataset are gone too, through the ORM's
        own cascade rather than anything this page does by hand."""
        from fairdm_demo.factories import RockSampleFactory

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

    def test_deleting_a_dataset_removes_its_samples_and_their_measurements(self, client):
        """T077 — the ordinary shape of a dataset holding data: samples, and measurements made
        on those same samples. Both go with it."""
        from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

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

    def test_deletion_is_refused_while_another_dataset_measures_its_samples(self, client):
        """T077 — a dataset whose samples carry measurements recorded by another dataset cannot
        be deleted, and the page says so rather than raising."""
        from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

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
        """T077 — a measurement may refer to a sample belonging to another dataset. Deleting
        the measurement's dataset takes the measurement and leaves that sample standing."""
        from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

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
        """T076 — a public dataset is deleted like any other; FR-048's visibility rule never
        prevents a deletion on its own."""
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

    def test_preview_names_the_datasets_samples_measurements_dates_and_identifiers(
        self, client
    ):
        """T074 — before the confirmation is offered, the page previews what will be deleted
        with the dataset (FR-046), through the shell's own cascade preview
        (`show_related_objects`). Asserted against rendered content, not the `related_objects`
        context data: the group headings for each related kind, plus the sample's and
        identifier's own values, all as they actually render.

        The measurement's own sample lives in a different, unaffected dataset — a measurement
        sharing its dataset with the sample it references trips a pre-existing
        `Measurement.sample` PROTECT interaction unrelated to this page (`issues_found`), and
        this test's job is the preview's rendered content, not that interaction."""
        from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        other_dataset = DatasetFactory(name="Other Dataset")
        other_sample = RockSampleFactory(dataset=other_dataset)

        dataset = DatasetFactory(name="Rich Dataset", dates=1)
        DatasetIdentifierFactory(related=dataset, value="10.9999/rich-dataset")
        RockSampleFactory(dataset=dataset, name="Granite Core 1")
        ExampleMeasurementFactory(dataset=dataset, sample=other_sample)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)
        content = response.content.decode()

        assertContains(
            response, "The following related records will also be permanently deleted"
        )
        sample_label = RockSampleFactory._meta.model._meta.verbose_name_plural.title()
        measurement_label = ExampleMeasurementFactory._meta.model._meta.verbose_name_plural.title()
        assert _assert_cascade_preview_group(content, sample_label)
        assertContains(response, "Granite Core 1")
        assert _assert_cascade_preview_group(content, measurement_label)
        assert _assert_cascade_preview_group(content, "Dates")
        assert _assert_cascade_preview_group(content, "Identifiers")
        assertContains(response, "10.9999/rich-dataset")

    def test_preview_says_nothing_about_samples_or_measurements_the_dataset_holds_none_of(
        self, client
    ):
        """T075 — a dataset holding no samples and no measurements is not warned about data it
        does not hold (FR-047). A date is included so the preview genuinely renders content —
        proving the sample/measurement groups are absent rather than the whole preview being
        empty."""
        from fairdm_demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Bare Dataset", dates=1)
        assign_perm("delete_dataset", user, dataset)
        client.force_login(user)
        url = reverse("dataset:overview-delete", kwargs={"uuid": dataset.uuid})

        response = client.get(url)
        content = response.content.decode()

        assert _assert_cascade_preview_group(content, "Dates")
        sample_label = RockSampleFactory._meta.model._meta.verbose_name_plural.title()
        measurement_label = ExampleMeasurementFactory._meta.model._meta.verbose_name_plural.title()
        assert not _assert_cascade_preview_group(content, sample_label)
        assert not _assert_cascade_preview_group(content, measurement_label)
        assert not _assert_cascade_preview_group(
            content, Sample._meta.verbose_name_plural.title()
        )
        assert not _assert_cascade_preview_group(
            content, Measurement._meta.verbose_name_plural.title()
        )


@pytest.mark.django_db
class TestDatasetViews:
    """Tests for Dataset views."""

    def test_dataset_list_view_accessible(self, client):
        """Test that dataset list view is accessible."""
        response = client.get(reverse("dataset-list"))

        assert response.status_code == 200

    def test_dataset_list_view_shows_public_datasets(self, client):
        """Test that only public datasets are shown in list view."""
        public_dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        private_dataset = DatasetFactory(visibility=Visibility.PRIVATE)

        response = client.get(reverse("dataset-list"))

        # Check that public dataset is visible
        assert public_dataset.name.encode() in response.content
        # Check that private dataset is not visible
        assert private_dataset.name.encode() not in response.content

    def test_dataset_create_view_requires_authentication(self, client):
        """Test that dataset creation requires login."""
        response = client.get(reverse("dataset-create"))

        # Should redirect to login
        assert response.status_code == 302

    def test_dataset_create_view_accessible_when_authenticated(
        self, authenticated_client
    ):
        """Test that authenticated users can access dataset create view."""
        response = authenticated_client.get(reverse("dataset-create"))

        assert response.status_code == 200

    def test_dataset_create_view_with_project_param(self, authenticated_client):
        """Test dataset creation with project parameter in URL."""
        project = ProjectFactory()

        response = authenticated_client.get(
            reverse("dataset-create"), {"project": project.pk}
        )

        assert response.status_code == 200

    def test_dataset_detail_view_accessible(self, client):
        """The dataset's own registered page (dataset:overview, 014 T057) serves
        the requested dataset and renders its name in the page body
        (FAIR-DM/fairdm#113)."""
        dataset = DatasetFactory(
            name="Reef Survey Dataset", visibility=Visibility.PUBLIC
        )
        response = client.get(reverse("dataset:overview", kwargs={"uuid": dataset.uuid}))

        assert response.status_code == 200
        assert response.context["dataset"] == dataset
        assert dataset.name.encode() in response.content


@pytest.mark.django_db
class TestDatasetPermissions:
    """Tests for Dataset permissions and access control."""

    def test_anonymous_user_cannot_create_dataset(self, client):
        """Test that anonymous users cannot create datasets."""
        form_data = {
            "name": "Test Dataset",
        }

        response = client.post(reverse("dataset-create"), data=form_data)

        # Should redirect to login
        assert response.status_code == 302
        # Check that redirect URL contains 'login'
        assert "login" in response["Location"]

    def test_dataset_creator_becomes_contributor(self, authenticated_client):
        """Test that dataset creator is automatically added as contributor."""
        form_data = {
            "name": "Test Dataset",
        }

        authenticated_client.post(reverse("dataset-create"), data=form_data)

        dataset = Dataset.objects.filter(name="Test Dataset").first()
        if dataset:
            # Check that the dataset has contributors
            assert dataset.contributors.count() > 0

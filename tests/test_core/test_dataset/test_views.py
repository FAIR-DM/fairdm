"""Integration tests for the dataset list, create, update and delete views."""

import pytest
from bs4 import BeautifulSoup
from django.db import connection
from django.template.defaultfilters import date as date_filter
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils.timezone import localtime
from licensing.models import License
from pytest_django.asserts import assertContains, assertNotContains

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, DATE_TYPES, DESCRIPTION_TYPES
from fairdm.factories import (
    ContributionFactory,
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
#
# Who may open the edit and delete pages is tested once for every kind of record in
# `tests/test_core/test_editing.py`. What follows is what is particular to datasets.


def _keywords(count=3):
    from controlled_vocabularies.models import Record

    return list(
        Record.objects.filter(
            scheme__uri=CONTRIBUTOR_ROLES, type=Record.Type.CONCEPT
        ).order_by("pk")[:count]
    )


@pytest.mark.django_db
class TestDatasetListView:
    def test_a_public_dataset_in_a_private_project_is_left_out(self, client):
        hidden = DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PRIVATE),
            visibility=Visibility.PUBLIC,
        )

        response = client.get(reverse("dataset-list"))

        assert hidden not in list(response.context["object_list"])


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
        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDescriptionFactory(
            related=target,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="A rare assemblage of pyroxenite xenoliths from the Rio Grande rift",
        )
        response = client.get(reverse("dataset-list"), {"q": "pyroxenite"})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_search_by_keyword_returns_the_dataset(self, client):
        target = DatasetFactory(visibility=Visibility.PUBLIC)
        other = DatasetFactory(visibility=Visibility.PUBLIC)
        term = _keywords(1)[0]
        target.keywords.add(term)
        response = client.get(reverse("dataset-list"), {"q": term.pref_label})
        entries = list(response.context["object_list"])
        assert target in entries
        assert other not in entries

    def test_the_listing_offers_no_second_search_control(self, client):
        # The shell draws no toolbar, and so no search box, over an empty listing.
        DatasetFactory(visibility=Visibility.PUBLIC)
        response = client.get(reverse("dataset-list"))
        content = response.content.decode()
        page = BeautifulSoup(content, "html.parser")
        # The header's site search dialog has its own field, which is not the listing's.
        controls = [
            field
            for field in page.select('input[name="q"]')
            if field.find_parent(id="mvp-search") is None
        ]
        assert len(controls) == 1
        assert 'name="search"' not in content


@pytest.mark.django_db
class TestDatasetListingOrdering:
    def test_ordering_by_name_runs_in_both_directions(self, client):
        bravo = DatasetFactory(name="Bravo Dataset", visibility=Visibility.PUBLIC)
        alpha = DatasetFactory(name="Alpha Dataset", visibility=Visibility.PUBLIC)

        ascending = list(
            client.get(reverse("dataset-list"), {"o": "name"}).context["object_list"]
        )
        descending = list(
            client.get(reverse("dataset-list"), {"o": "-name"}).context["object_list"]
        )

        assert ascending.index(alpha) < ascending.index(bravo)
        assert descending.index(bravo) < descending.index(alpha)


@pytest.mark.django_db
class TestDatasetListingFilters:
    # Narrowing by each filter is tested on the filterset in `test_filters.py`. This
    # checks that the listing applies every filter it offers.
    def test_every_offered_filter_is_applied_by_the_listing(self, client):
        from fairdm.factories import DatasetDateFactory

        license_obj = License.objects.get(name="CC BY 4.0")
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            name="Zirconium Survey",
            license=license_obj,
            project=project,
            visibility=Visibility.PUBLIC,
        )
        DatasetDescriptionFactory(
            related=dataset, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )
        DatasetDateFactory(related=dataset, type_id=f"{DATE_TYPES}/available")
        other = DatasetFactory(
            name="Basalt Atlas",
            license=License.objects.get(name="CC0 1.0"),
            project=None,
            visibility=Visibility.PUBLIC,
        )
        values = {
            "q": "Zirconium",
            "o": "name",
            "license": license_obj.pk,
            "project": project.pk,
            "description_type": f"{DESCRIPTION_TYPES}/abstract",
            "date_type": f"{DATE_TYPES}/available",
            "image": "true",
        }

        response = client.get(reverse("dataset-list"))
        offered = list(response.context["filter"].form.fields)
        assert offered, "the listing's filter form offers no fields to sweep"
        assert "visibility" not in offered

        for field_name in offered:
            response = client.get(
                reverse("dataset-list"), {field_name: values[field_name]}
            )
            assert response.status_code == 200, field_name
            entries = list(response.context["object_list"])
            assert dataset in entries, field_name
            if field_name not in ("o", "image"):
                assert other not in entries, field_name


@pytest.mark.django_db
class TestDatasetListingProjectFilterVisibility:
    def test_a_private_project_is_absent_for_an_anonymous_visitor(self, client):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        response = client.get(reverse("dataset-list"))
        offered = response.context["filter"].form.fields["project"].offered()
        assert private_project not in offered
        assertNotContains(response, "Confidential Survey")

    def test_a_private_project_is_absent_for_a_signed_in_visitor_with_no_rights_over_it(
        self, client
    ):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        client.force_login(UserFactory())
        response = client.get(reverse("dataset-list"))
        offered = response.context["filter"].form.fields["project"].offered()
        assert private_project not in offered
        assertNotContains(response, "Confidential Survey")

    def test_a_public_project_is_offered_to_every_visitor(self, client):
        public_project = ProjectFactory(
            name="Open Reef Survey", visibility=Visibility.PUBLIC
        )
        response = client.get(reverse("dataset-list"))
        offered = response.context["filter"].form.fields["project"].offered()
        assert public_project in offered

    def test_a_private_project_the_signed_in_visitor_holds_view_rights_on_is_not_offered(
        self, client
    ):
        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        user = UserFactory()
        ContributionFactory(
            content_object=private_project,
            contributor=user,
            level=ContributionLevel.VIEW,
        )
        client.force_login(user)
        response = client.get(reverse("dataset-list"))
        offered = response.context["filter"].form.fields["project"].offered()
        assert private_project not in offered

    def test_a_private_project_the_visitor_holds_only_a_stored_row_on_is_not_offered(
        self, client
    ):
        from fairdm.core.utils import assign_perm

        private_project = ProjectFactory(
            name="Confidential Survey", visibility=Visibility.PRIVATE
        )
        user = UserFactory()
        assign_perm("view_project", user, private_project)
        client.force_login(user)
        response = client.get(reverse("dataset-list"))
        offered = response.context["filter"].form.fields["project"].offered()
        assert private_project not in offered


@pytest.mark.django_db
class TestDatasetListingEntryLink:
    def test_listing_entry_links_to_its_datasets_page(self, client, public_dataset):
        response = client.get(reverse("dataset-list"))
        expected_url = public_dataset.get_absolute_url()
        assertContains(response, f'href="{expected_url}"')


@pytest.mark.django_db
class TestDatasetCreateView:
    def test_anonymous_redirects_to_login(self, client):
        response = client.get(reverse("dataset-create"))
        assert response.status_code == 302
        assert "/login/" in response.url or "/accounts/login/" in response.url

    def test_authenticated_get_200(self, client):
        client.force_login(UserFactory())
        response = client.get(reverse("dataset-create"))
        assert response.status_code == 200

    def test_a_valid_post_redirects_and_credits_the_creator_in_every_role(
        self, client
    ):
        user = UserFactory()
        client.force_login(user)
        project = ProjectFactory()
        # The form only offers projects the user contributes to.
        ContributionFactory(
            content_object=project, contributor=user, level=ContributionLevel.EDIT
        )

        response = client.post(
            reverse("dataset-create"),
            data={
                "name": "New Test Dataset",
                "project": project.pk,
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        dataset = Dataset.all_objects.get(name="New Test Dataset")
        assert response.url == reverse(
            "dataset:overview", kwargs={"uuid": dataset.uuid}
        )
        roles = set(
            dataset.contributors.get(contributor=user).roles.values_list(
                "uri", flat=True
            )
        )
        assert {
            f"{CONTRIBUTOR_ROLES}/creator",
            f"{CONTRIBUTOR_ROLES}/project-member",
            f"{CONTRIBUTOR_ROLES}/contact-person",
        } <= roles


@pytest.mark.django_db
class TestDatasetCreatePageVisibilityField:
    def test_the_page_pre_selects_public(self, client):
        client.force_login(UserFactory())

        response = client.get(reverse("dataset-create"))

        assert response.context["form"]["visibility"].value() == Visibility.PUBLIC


@pytest.mark.django_db
class TestDatasetCreatePageLicenseDefault:
    def test_the_rendered_form_preselects_the_configured_default_licence(
        self, client, settings
    ):
        other_license = License.objects.get_or_create(name="A Portal's Own Licence")[0]
        settings.FAIRDM_DEFAULT_LICENSE = other_license.name
        client.force_login(UserFactory())

        response = client.get(reverse("dataset-create"))

        assert response.context["form"].fields["license"].initial == other_license


@pytest.mark.django_db
class TestDatasetCreatePageProjectField:
    def test_a_dataset_can_be_created_without_a_project(self, client):
        client.force_login(UserFactory())

        response = client.post(
            reverse("dataset-create"),
            data={
                "name": "Orphan Dataset",
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        assert Dataset.all_objects.get(name="Orphan Dataset").project is None

    def test_the_project_field_is_narrowed_to_the_researchers_own_projects(
        self, client
    ):
        user = UserFactory()
        client.force_login(user)
        own_project = ProjectFactory(name="Researcher's Own Project")
        other_project = ProjectFactory(name="Someone Else's Project")
        ContributionFactory(
            content_object=own_project,
            contributor=user,
            level=ContributionLevel.EDIT,
        )

        response = client.get(reverse("dataset-create"))
        project_queryset = response.context["form"].fields["project"].queryset

        assert own_project in project_queryset
        assert other_project not in project_queryset


@pytest.mark.django_db
class TestDatasetCreatePagePermissionAssignment:
    def test_the_creator_is_recorded_and_granted_full_permissions_on_the_new_dataset(
        self, client
    ):
        user = UserFactory()
        client.force_login(user)

        response = client.post(
            reverse("dataset-create"),
            data={
                "name": "Permissioned Dataset",
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PUBLIC,
            },
        )

        assert response.status_code == 302, (
            response.context["form"].errors if "form" in response.context else None
        )
        dataset = Dataset.all_objects.get(name="Permissioned Dataset")
        assert dataset.created_by == user
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

    def test_the_creator_is_listed_at_the_manage_level_with_no_stored_row(self, client):
        from guardian.models import UserObjectPermission

        from fairdm.contrib.contributors.access import RecordAccess

        user = UserFactory()
        client.force_login(user)

        response = client.post(
            reverse("dataset-create"),
            data={
                "name": "Managed Dataset",
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PRIVATE,
            },
        )

        assert response.status_code == 302
        dataset = Dataset.all_objects.get(name="Managed Dataset")
        assert RecordAccess(dataset).own_level(user) == ContributionLevel.MANAGE
        assert not UserObjectPermission.objects.exists()
        roles = dataset.contributors.get(contributor=user).roles
        assert {
            f"{CONTRIBUTOR_ROLES}/creator",
            f"{CONTRIBUTOR_ROLES}/contact-person",
        } <= set(roles.values_list("uri", flat=True))

    def test_a_superuser_creates_a_dataset_without_being_credited(self, client):
        admin = UserFactory(is_superuser=True, is_staff=True)
        client.force_login(admin)

        response = client.post(
            reverse("dataset-create"),
            data={
                "name": "Admin Dataset",
                "license": License.objects.get(name="CC BY 4.0").pk,
                "visibility": Visibility.PRIVATE,
            },
        )

        assert response.status_code == 302
        dataset = Dataset.all_objects.get(name="Admin Dataset")
        assert dataset.contributors.count() == 0


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
    def _post_changes(self, client, user, dataset, project):
        client.force_login(user)
        url = reverse("dataset:edit", kwargs={"uuid": dataset.uuid})
        return client.post(
            url,
            data={
                "name": "Renamed",
                "project": project.pk,
                "license": dataset.license.pk,
                "visibility": Visibility.PUBLIC,
                **_identifier_management_data(),
                **_date_management_data(),
            },
        )

    def _setup(self, user, level):
        own_project = ProjectFactory()
        other_project = ProjectFactory()
        dataset = DatasetFactory(
            name="Original",
            project=own_project,
            visibility=Visibility.PRIVATE,
            license=License.objects.get(name="CC BY 4.0"),
        )
        ContributionFactory(content_object=dataset, contributor=user, level=level)
        for project in (own_project, other_project):
            ContributionFactory(
                content_object=project, contributor=user, level=ContributionLevel.EDIT
            )
        return dataset, own_project, other_project

    def test_an_editor_changes_the_dataset_but_not_its_visibility_or_project(
        self, client
    ):
        user = UserFactory()
        dataset, own_project, other_project = self._setup(user, ContributionLevel.EDIT)

        response = self._post_changes(client, user, dataset, other_project)

        assert response.status_code == 302
        assert response.url == reverse(
            "dataset:overview", kwargs={"uuid": dataset.uuid}
        )
        dataset.refresh_from_db()
        assert dataset.name == "Renamed"
        assert dataset.visibility == Visibility.PRIVATE
        assert dataset.project_id == own_project.pk

    def test_the_form_an_editor_is_given_leaves_out_visibility_and_project(
        self, client
    ):
        user = UserFactory()
        dataset, _own, _other = self._setup(user, ContributionLevel.EDIT)
        client.force_login(user)

        response = client.get(reverse("dataset:edit", kwargs={"uuid": dataset.uuid}))

        assert {"name", "license"} <= set(response.context["form"].fields)
        assert not {"visibility", "project"} & set(response.context["form"].fields)

    def test_a_manager_changes_visibility_and_project(self, client):
        user = UserFactory()
        dataset, _own, other_project = self._setup(user, ContributionLevel.MANAGE)

        response = self._post_changes(client, user, dataset, other_project)

        assert response.status_code == 302
        dataset.refresh_from_db()
        assert dataset.visibility == Visibility.PUBLIC
        assert dataset.project_id == other_project.pk

    def test_a_data_curator_changes_visibility_and_project(self, client):
        from django.contrib.auth.models import Group

        from fairdm.portal_roles import PortalRoles

        PortalRoles.reconcile()
        curator = UserFactory()
        curator.groups.add(Group.objects.get(name=PortalRoles.DATA_CURATOR.name))
        other_project = ProjectFactory()
        dataset = DatasetFactory(
            visibility=Visibility.PRIVATE,
            license=License.objects.get(name="CC BY 4.0"),
        )
        ContributionFactory(
            content_object=other_project,
            contributor=curator,
            level=ContributionLevel.VIEW,
        )

        response = self._post_changes(client, curator, dataset, other_project)

        assert response.status_code == 302
        dataset.refresh_from_db()
        assert dataset.visibility == Visibility.PUBLIC
        assert dataset.project_id == other_project.pk


@pytest.mark.django_db
class TestDatasetDeleteView:
    def test_confirmation_ignores_surrounding_whitespace(self, client):
        user = UserFactory()
        dataset = DatasetFactory(name="Spaced Dataset")
        pk = dataset.pk
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})
        response = client.post(url, data={"confirmation": "  Spaced Dataset  "})
        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Dataset.all_objects.filter(pk=pk).exists()

    def test_deleting_a_dataset_removes_its_samples_and_their_measurements(
        self, client
    ):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        user = UserFactory()
        dataset = DatasetFactory(name="Dataset With Data")
        sample = RockSampleFactory(dataset=dataset)
        measurement = ExampleMeasurementFactory(dataset=dataset, sample=sample)
        sample_pk, measurement_pk = sample.pk, measurement.pk
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

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
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

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
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

        response = client.post(url, data={"confirmation": "Dataset With A Measurement"})

        assert response.status_code == 302
        assert response.url == reverse("dataset-list")
        assert not Measurement.objects.filter(pk=measurement_pk).exists()
        assert Sample.objects.filter(pk=sample.pk).exists()

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
        RockSampleFactory(dataset=dataset, name="Granite Core 1")
        WaterSampleFactory(dataset=dataset, name="Spring Water 1")
        ExampleMeasurementFactory(dataset=dataset, sample=other_sample)
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

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
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

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
        ContributionFactory(
            content_object=dataset, contributor=user, level=ContributionLevel.MANAGE
        )
        client.force_login(user)
        url = reverse("dataset:delete", kwargs={"uuid": dataset.uuid})

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
class TestListingIgnoresPublished:
    def test_the_listing_shows_the_same_datasets_whichever_way_published_is_set(
        self, client
    ):
        # `published` changes what a card says, never whether the dataset is listed.
        dataset = DatasetFactory(name="Listed Either Way", visibility=Visibility.PUBLIC)
        url = reverse("dataset-list")

        Dataset.all_objects.filter(pk=dataset.pk).update(published=False)
        unpublished = client.get(url)

        Dataset.all_objects.filter(pk=dataset.pk).update(published=True)
        published = client.get(url)

        for response in (unpublished, published):
            assert response.status_code == 200
            assert dataset in list(response.context["object_list"])


@pytest.mark.django_db
class TestDatasetListingQueryCount:
    @staticmethod
    def _build_datasets(count, project):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        keywords = _keywords()
        for index in range(count):
            dataset = DatasetFactory(
                name=f"Survey {index}", project=project, visibility=Visibility.PUBLIC
            )
            DatasetDescriptionFactory(
                related=dataset,
                type_id=f"{DESCRIPTION_TYPES}/abstract",
                value=f"## Survey {index}\n\nWe measured **heat flow** here.",
            )
            dataset.keywords.add(*keywords)
            dataset.add_contributor(PersonFactory())
            sample = RockSampleFactory(dataset=dataset)
            ExampleMeasurementFactory(dataset=dataset, sample=sample)

    def test_listing_query_count_does_not_grow_with_the_number_of_datasets(
        self, client
    ):
        url = reverse("dataset-list")
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        self._build_datasets(1, project)
        client.get(url)  # warm up one-time per-process and per-image setup
        with CaptureQueriesContext(connection) as one_dataset:
            assert client.get(url).status_code == 200

        self._build_datasets(2, project)
        client.get(url)
        with CaptureQueriesContext(connection) as three_datasets:
            response = client.get(url)

        assert len(response.context["object_list"]) == 3
        assert len(three_datasets.captured_queries) == len(one_dataset.captured_queries)


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
    @staticmethod
    def _card(client):
        """Return the text of the one card on the listing, and its markup."""
        response = client.get(reverse("dataset-list"))
        assert response.status_code == 200
        cards = BeautifulSoup(response.content, "html.parser").select("a.record-card")
        assert len(cards) == 1
        return " ".join(cards[0].get_text().split()), str(cards[0])

    def test_a_dataset_with_no_project_draws_no_parent_row(self, client):
        DatasetFactory(project=None, visibility=Visibility.PUBLIC)
        _, markup = self._card(client)
        assert "record-card__parent" not in markup

    def test_an_unlicensed_dataset_draws_no_licence_row(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, license=None)
        _, markup = self._card(client)
        assert "record-card__license" not in markup

    def test_card_shows_the_dataset_name(self, client):
        DatasetFactory(name="Rift Basin Heat Flow", visibility=Visibility.PUBLIC)
        text, _ = self._card(client)
        assert "Rift Basin Heat Flow" in text

    def test_card_reports_a_published_dataset_as_published(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        text, _ = self._card(client)
        assert "Published" in text

    def test_card_states_nothing_at_all_about_an_unpublished_dataset(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        _, markup = self._card(client)
        card = BeautifulSoup(markup, "html.parser")
        assert card.find_all("span", string="Published") == []

    def test_an_unpublished_dataset_reports_no_counts(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=False)
        sample = RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=sample)

        text, _ = self._card(client)

        assert "1 sample" not in text
        assert "1 measurement" not in text
        assert "No samples" not in text
        assert "No measurements" not in text

    def test_card_counts_samples_and_measurements(self, client):
        from demo.factories import ExampleMeasurementFactory, RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        first = RockSampleFactory(dataset=dataset)
        RockSampleFactory(dataset=dataset)
        ExampleMeasurementFactory(dataset=dataset, sample=first)
        text, _ = self._card(client)
        assert "2 samples" in text
        assert "1 measurement" in text

    def test_card_counts_one_sample_in_the_singular(self, client):
        from demo.factories import RockSampleFactory

        dataset = DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        RockSampleFactory(dataset=dataset)
        text, _ = self._card(client)
        assert "1 sample" in text
        assert "1 samples" not in text

    def test_card_says_so_rather_than_showing_a_zero(self, client):
        DatasetFactory(visibility=Visibility.PUBLIC, published=True)
        text, _ = self._card(client)
        assert "No samples" in text
        assert "No measurements" in text
        assert "0 samples" not in text
        assert "0 measurements" not in text

    def test_card_names_the_parent_project_without_linking_to_it(self, client):
        project = ProjectFactory(name="Deep Time Survey", visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        text, markup = self._card(client)
        assert "Deep Time Survey" in text
        # The whole card is one link, so a second link inside it would nest.
        assert project.get_absolute_url() not in markup

    def test_card_renders_the_abstract_as_plain_text(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        DatasetDescriptionFactory(
            related=dataset,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="## Objectives\n\nWe measure **heat flow** across the rift.",
        )
        text, _ = self._card(client)
        assert "Objectives" in text
        assert "heat flow" in text
        assert "## Objectives" not in text
        assert "**heat flow**" not in text

    def test_card_renders_keywords_as_badges_and_not_as_links(self, client):
        keyword = _keywords(1)[0]
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.keywords.add(keyword)
        text, markup = self._card(client)
        block = BeautifulSoup(markup, "html.parser").select_one(
            ".record-card__keywords"
        )
        assert keyword.display_label() in text
        assert block.get_text(strip=True) == keyword.display_label()
        assert block.find(href=True) is None

    def test_card_names_the_licence(self, client):
        DatasetFactory(
            visibility=Visibility.PUBLIC, license=License.objects.get(name="CC0 1.0")
        )
        text, _ = self._card(client)
        assert "CC0 1.0" in text

    def test_card_shows_the_last_modified_date(self, client):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        text, _ = self._card(client)
        modified = date_filter(localtime(dataset.modified), "M j, Y")
        assert f"Last updated {modified}" in text

    def test_card_shows_contributor_names(self, client):
        person = PersonFactory(name="Ada Lovelace")
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)
        dataset.add_contributor(person)
        text, _ = self._card(client)
        assert "Ada Lovelace" in text

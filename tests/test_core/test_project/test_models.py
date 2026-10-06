"""Tests for the project models, their querysets, permissions and metadata records."""

import time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse

from fairdm.core.choices import ProjectStatus
from fairdm.core.project.forms import ProjectCreateForm, ProjectForm
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.factories import (
    DatasetFactory,
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectModel:
    def test_project_creation_with_required_fields(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        assert project.pk is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.CONCEPT
        assert project.visibility == Visibility.PRIVATE
        assert project.owner == owner
        assert project.uuid is not None
        assert project.uuid.startswith("p")

    def test_project_uuid_is_unique(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        project1 = Project.objects.create(
            name="Project 1",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        project2 = Project.objects.create(
            name="Project 2",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        assert project1.uuid != project2.uuid
        assert project1.uuid.startswith("p")
        assert project2.uuid.startswith("p")

    def test_project_status_choices(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        valid_statuses = [
            ProjectStatus.CONCEPT,
            ProjectStatus.PLANNING,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.COMPLETE,
        ]

        for status in valid_statuses:
            project = Project.objects.create(
                name=f"Project {status}",
                status=status,
                visibility=Visibility.PRIVATE,
                owner=owner,
            )
            assert project.status == status

    def test_project_visibility_choices(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        valid_visibilities = [
            Visibility.PRIVATE,
            Visibility.PUBLIC,
        ]

        for visibility in valid_visibilities:
            project = Project.objects.create(
                name=f"Project {visibility}",
                status=ProjectStatus.CONCEPT,
                visibility=visibility,
                owner=owner,
            )
            assert project.visibility == visibility

    def test_cannot_delete_project_with_public_datasets(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import PublicDatasetsProtect

        owner = Organization.objects.create(name="Test Organization")

        project = Project.objects.create(
            name="Project with Public Dataset",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        Dataset.objects.create(
            name="Public Dataset",
            project=project,
            visibility=Visibility.PUBLIC,
        )

        with pytest.raises(PublicDatasetsProtect):
            project.delete()


@pytest.mark.django_db
class TestProjectIdentifierField:
    def test_uuid_field_is_not_editable(self):
        assert Project._meta.get_field("uuid").editable is False


@pytest.mark.django_db
class TestProjectRequiredFields:
    def test_project_without_owner_is_valid(self):
        project = Project(
            name="No Owner Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
        )
        project.full_clean()

    def test_project_without_name_is_invalid(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")
        project = Project(
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )
        with pytest.raises(ValidationError):
            project.full_clean()


@pytest.mark.django_db
class TestProjectDefaultOrdering:
    def test_default_ordering_is_most_recently_modified_first(self):
        first = ProjectFactory()
        time.sleep(0.01)
        second = ProjectFactory()
        time.sleep(0.01)
        third = ProjectFactory()

        # Re-saving `first` last shows the ordering is by `modified`, not creation
        # order.
        time.sleep(0.01)
        first.save()

        assert list(Project.objects.all()) == [first, third, second]


@pytest.mark.django_db
class TestProjectPreDeleteSignal:
    def test_pre_delete_signal_blocks_public_datasets(self):
        from fairdm.core.dataset.models import Dataset
        from fairdm.core.project.models import PublicDatasetsProtect
        from fairdm.factories import ProjectFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        Dataset.objects.create(
            name="Public Dataset", project=project, visibility=Visibility.PUBLIC
        )

        with pytest.raises(PublicDatasetsProtect):
            project.delete()

    def test_pre_delete_signal_allows_private_only(self):
        from fairdm.core.dataset.models import Dataset
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        dataset = Dataset.objects.create(
            name="Private Dataset", project=project, visibility=Visibility.PRIVATE
        )
        pk = project.pk

        project.delete()

        assert not Project.objects.filter(pk=pk).exists()

    def test_pre_delete_signal_allows_no_datasets(self):
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        pk = project.pk

        project.delete()

        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectDescriptionModel:
    def test_description_type_choices_are_scoped_to_project(self):
        # Django does not validate choices on save, so this asserts the choices set on
        # the field, against literal member names rather than the vocabulary they were
        # copied from.
        codes = {code for code, _label in ProjectDescription.type.field.choices}
        assert codes == {
            "Abstract",
            "Introduction",
            "Background",
            "Objectives",
            "ExpectedOutput",
            "Conclusions",
            "Other",
        }
        assert "Methods" not in codes  # a dataset-only description type

    def test_duplicate_description_type_raises_validation_error(self):
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        ProjectDescription.objects.create(
            related=project, type="Abstract", value="First abstract"
        )

        desc2 = ProjectDescription(
            related=project, type="Abstract", value="Second abstract"
        )

        with pytest.raises(ValidationError) as exc_info:
            desc2.clean()

        assert "type" in exc_info.value.error_dict
        assert "Abstract" in str(exc_info.value)

    def test_duplicate_description_type_refused_at_database(self):
        project = ProjectFactory()
        ProjectDescription.objects.create(
            related=project, type="Abstract", value="First abstract"
        )

        with pytest.raises(IntegrityError):
            ProjectDescription.objects.create(
                related=project, type="Abstract", value="Second abstract"
            )


@pytest.mark.django_db
class TestProjectDateModel:
    def test_date_type_choices_are_scoped_to_project(self):
        # Asserted against literal member names, as for the description type.
        codes = {code for code, _label in ProjectDate.type.field.choices}
        assert codes == {"Start", "End"}

    def test_second_start_date_on_project_is_refused(self):
        from fairdm.factories.core import ProjectDateFactory

        project = ProjectFactory()
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")

        duplicate = ProjectDate(related=project, type="Start", value="2021-01-01")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_duplicate_date_type_refused_at_database(self):
        from fairdm.factories.core import ProjectDateFactory

        project = ProjectFactory()
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")

        with pytest.raises(IntegrityError):
            ProjectDateFactory(related=project, type="Start", value="2021-01-01")

    def test_end_date_before_start_date_raises_error(self):
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06-01")

        end = ProjectDate(related=project, type="End", value="2019-05-01")
        with pytest.raises(ValidationError) as exc_info:
            end.full_clean()

        message = str(exc_info.value)
        assert "2020-06-01" in message
        assert "2019-05-01" in message

    def test_changing_start_to_after_end_is_refused(self):
        project = ProjectFactory()
        start = ProjectDate.objects.create(
            related=project, type="Start", value="2020-01-01"
        )
        ProjectDate.objects.create(related=project, type="End", value="2020-12-31")

        start.value = "2021-01-01"
        with pytest.raises(ValidationError):
            start.full_clean()

    def test_end_date_with_no_start_date_is_accepted(self):
        project = ProjectFactory()
        end = ProjectDate(related=project, type="End", value="2024-06-15")

        end.full_clean()

    def test_year_only_end_in_same_year_as_month_precision_start_is_accepted(self):
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06")

        end = ProjectDate(related=project, type="End", value="2020")
        end.full_clean()

    def test_month_precision_end_before_month_precision_start_is_refused(self):
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06")

        end = ProjectDate(related=project, type="End", value="2020-03")
        with pytest.raises(ValidationError):
            end.full_clean()


@pytest.mark.django_db
class TestProjectFunding:
    def test_award_with_all_parts_round_trips(self):
        project = ProjectFactory()
        project.funding = [
            {
                "funderName": "Sample Agency",
                "funderIdentifier": "https://doi.org/10.13039/501100000923",
                "funderIdentifierType": "ROR",
                "awardNumber": "GRANT-2024-001",
                "awardTitle": "A study of things",
                "awardURI": "https://example.org/awards/GRANT-2024-001",
            }
        ]
        project.full_clean()
        project.save()

        project.refresh_from_db()
        reference = project.funding[0]
        assert reference["funderName"] == "Sample Agency"
        assert reference["funderIdentifier"] == "https://doi.org/10.13039/501100000923"
        assert reference["funderIdentifierType"] == "ROR"
        assert reference["awardNumber"] == "GRANT-2024-001"
        assert reference["awardTitle"] == "A study of things"
        assert reference["awardURI"] == "https://example.org/awards/GRANT-2024-001"

    def test_project_with_two_awards_retains_both(self):
        project = ProjectFactory()
        project.funding = [
            {"funderName": "First Agency"},
            {"funderName": "Second Agency", "awardNumber": "GRANT-002"},
        ]
        project.full_clean()
        project.save()

        project.refresh_from_db()
        assert len(project.funding) == 2
        assert project.funding[0]["funderName"] == "First Agency"
        assert project.funding[1]["funderName"] == "Second Agency"

    def test_award_naming_only_a_funder_is_accepted(self):
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency"}]

        project.full_clean()

    def test_identifier_scheme_outside_datacite_set_is_refused(self):
        project = ProjectFactory()
        project.funding = [
            {"funderName": "Sample Agency", "funderIdentifierType": "Wikidata"}
        ]

        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        message = str(exc_info.value)
        assert "ISNI" in message
        assert "GRID" in message
        assert "Crossref Funder ID" in message
        assert "ROR" in message
        assert "Other" in message

    def test_funding_that_is_not_a_list_is_refused(self):
        project = ProjectFactory()
        project.funding = {"funderName": "Sample Agency"}

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_list_of_scalars_is_refused_not_raised(self):
        project = ProjectFactory()
        project.funding = ["Sample Agency"]

        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert "funding" in exc_info.value.error_dict

    def test_unknown_key_is_refused_and_named(self):
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency", "amount": 50000}]

        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert "amount" in str(exc_info.value)

    def test_missing_funder_name_is_refused(self):
        project = ProjectFactory()
        project.funding = [{"awardNumber": "GRANT-2024-001"}]

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_funder_name_that_is_not_a_string_is_refused(self):
        # A truthiness check alone would accept a non-string.
        project = ProjectFactory()
        project.funding = [{"funderName": {"nested": "object"}}]

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_award_number_that_is_not_a_string_is_refused(self):
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency", "awardNumber": 42}]

        with pytest.raises(ValidationError):
            project.full_clean()


@pytest.mark.django_db
class TestProjectModelIntegration:
    def test_project_creation(self):
        project = ProjectFactory()

        assert project.pk is not None
        assert project.name is not None
        assert project.uuid is not None
        assert project.uuid.startswith("p")

    def test_project_visibility_default(self):
        project = ProjectFactory()
        assert project.visibility == Visibility.PRIVATE

    def test_project_queryset_get_visible(self):
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        visible = Project.objects.get_visible()

        assert public_project in visible
        assert private_project not in visible

    def test_project_queryset_with_contributors(self):
        project = ProjectFactory()

        queryset = Project.objects.with_contributors()
        project_with_prefetch = queryset.get(pk=project.pk)

        assert project_with_prefetch.contributors is not None

    def test_project_str_representation(self):
        project = ProjectFactory(name="Test Project")
        assert str(project) == "Test Project"

    def test_project_absolute_url(self):
        project = ProjectFactory()
        url = project.get_absolute_url()

        assert url == reverse("project:overview", kwargs={"uuid": project.uuid})

    def test_project_descriptions_relationship(self):
        project = ProjectFactory()
        descriptions = ProjectDescription.objects.filter(related=project)

        assert descriptions.count() >= 0
        assert all(desc.related == project for desc in descriptions)

    def test_project_dates_relationship(self):
        project = ProjectFactory()
        dates = ProjectDate.objects.filter(related=project)

        assert dates.count() >= 0
        assert all(date.related == project for date in dates)

    def test_add_contributor(self):
        project = ProjectFactory()
        user = PersonFactory()

        contribution = project.add_contributor(user, with_roles=["Creator"])

        assert contribution is not None
        assert contribution.contributor == user
        assert project.contributors.filter(pk=contribution.pk).exists()

        roles = list(contribution.roles.all())
        assert [role.name for role in roles] == ["Creator"]


@pytest.mark.django_db
class TestProjectRoleDataciteMapping:
    def test_every_project_role_has_a_datacite_contributor_type(self):
        from fairdm.core.choices import (
            PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES,
            DataciteContributorRoles,
        )

        project_role_names = set(Project.CONTRIBUTOR_ROLES.values)
        unmapped = project_role_names - set(PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES)
        assert not unmapped, f"no DataCite mapping recorded for: {unmapped}"

        datacite_names = set(DataciteContributorRoles().values)
        missing = {
            PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES[name] for name in project_role_names
        } - datacite_names
        assert not missing, f"mapped to a non-existent DataCite role: {missing}"


@pytest.mark.django_db
class TestProjectForm:
    def test_form_valid_data(self):
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }
        form = ProjectCreateForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        form_data = {}
        form = ProjectForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_saves_correctly(self):
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PRIVATE,
            "status": 1,
        }
        form = ProjectCreateForm(data=form_data)

        assert form.is_valid()
        project = form.save()

        assert project.name == "Test Project"
        assert project.visibility == Visibility.PRIVATE
        assert project.status == 1


@pytest.mark.django_db
class TestProjectViews:
    def test_project_list_view_accessible(self, client):
        response = client.get(reverse("project-list"))

        assert response.status_code == 200

    def test_project_list_view_shows_public_projects(self, client):
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        response = client.get(reverse("project-list"))

        assert public_project.name.encode() in response.content
        assert private_project.name.encode() not in response.content

    def test_project_create_view_requires_authentication(self, client):
        response = client.get(reverse("project-create"))

        assert response.status_code == 302

    def test_project_create_view_accessible_when_authenticated(
        self, authenticated_client
    ):
        response = authenticated_client.get(reverse("project-create"))

        assert response.status_code == 200

    def test_project_create_view_creates_project(self, authenticated_client):
        form_data = {
            "name": "New Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = authenticated_client.post(reverse("project-create"), data=form_data)

        assert response.status_code == 302

        project = Project.objects.filter(name="New Test Project").first()
        assert project is not None
        assert project.visibility == Visibility.PUBLIC

    def test_project_detail_view_accessible(self, client):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        assert response.status_code == 200
        assert project.name.encode() in response.content


@pytest.mark.django_db
class TestProjectPermissions:
    def test_anonymous_user_cannot_create_project(self, client):
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = client.post(reverse("project-create"), data=form_data)

        assert response.status_code == 302
        assert "login" in response["Location"]

    def test_project_creator_becomes_contributor(self, authenticated_client):
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        authenticated_client.post(reverse("project-create"), data=form_data)

        project = Project.objects.filter(name="Test Project").first()
        if project:
            assert project.contributors.count() > 0


@pytest.mark.django_db
class TestProjectDescriptions:
    def test_add_multiple_descriptions_to_project(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectDescription

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Research Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        ProjectDescription.objects.create(
            related=project,
            type="Abstract",
            value="This project studies the impact of X on Y using Z methodology.",
        )

        ProjectDescription.objects.create(
            related=project,
            type="Objectives",
            value="We aim to quantify the effect across ten sites using XRF.",
        )

        descriptions = project.descriptions.all()
        assert descriptions.count() == 2

        types = [d.type for d in descriptions]
        assert "Abstract" in types
        assert "Objectives" in types

        abstract_desc = project.descriptions.get(type="Abstract")
        assert "impact of X on Y" in abstract_desc.value

        objectives_desc = project.descriptions.get(type="Objectives")
        assert "XRF" in objectives_desc.value


@pytest.mark.django_db
class TestProjectKeywordsAndTags:
    def test_controlled_vocabulary_term_is_stored_as_a_reference(self):
        from research_vocabs.models import Concept

        project = ProjectFactory()
        # `Concept.preload()` runs once per session in tests/conftest.py.
        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        assert term is not None

        project.keywords.add(term)

        stored = project.keywords.get(pk=term.pk)
        assert isinstance(stored, Concept)
        assert stored.vocabulary.name == "fairdm-roles"
        assert stored.name == term.name

    def test_free_tags_are_distinguishable_from_controlled_keywords(self):
        from research_vocabs.models import Concept

        project = ProjectFactory()
        keyword = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        project.keywords.add(keyword)
        project.tags.add("erosion")

        assert "erosion" in project.tags.names()
        assert project.keywords.count() == 1
        assert all(isinstance(k, Concept) for k in project.keywords.all())
        assert not project.keywords.filter(name="erosion").exists()


@pytest.mark.django_db
class TestProjectDates:
    def test_add_date_range_to_project(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectDate

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Time-Bound Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        ProjectDate.objects.create(
            related=project,
            type="Start",
            value="2024-01-01",  # PartialDateField takes a string
        )

        ProjectDate.objects.create(
            related=project,
            type="End",
            value="2025-12-31",
        )

        dates = project.dates.all()
        assert dates.count() == 2

        types = [d.type for d in dates]
        assert "Start" in types
        assert "End" in types

        start = project.dates.get(type="Start")
        end = project.dates.get(type="End")
        assert start.value < end.value


@pytest.mark.django_db
class TestProjectIdentifiers:
    def test_add_identifiers_to_project(self):
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectIdentifier

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Funded Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        ProjectIdentifier.objects.create(
            related=project, type="ISNI", value="0000 0001 2283 4400"
        )

        ProjectIdentifier.objects.create(
            related=project,
            type="CROSSREF_FUNDER_ID",
            value="https://doi.org/10.13039/100000001",
        )

        identifiers = project.identifiers.all()
        assert identifiers.count() == 2

        types = [i.type for i in identifiers]
        assert "ISNI" in types
        assert "CROSSREF_FUNDER_ID" in types

        isni_identifier = project.identifiers.get(type="ISNI")
        assert isni_identifier.value == "0000 0001 2283 4400"

        funder_identifier = project.identifiers.get(type="CROSSREF_FUNDER_ID")
        assert funder_identifier.value == "https://doi.org/10.13039/100000001"

    def test_doi_attached_to_project_stored_under_doi_type(self):
        project = ProjectFactory()

        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/example")

        doi = project.identifiers.get(type="DOI")
        assert doi.value == "10.1234/example"

    def test_grant_number_stored_alongside_doi(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/example")

        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="GRANT-2024-001"
        )

        types = set(project.identifiers.values_list("type", flat=True))
        assert types == {"DOI", "GRANT_NUMBER"}

    def test_duplicate_identifier_value_across_projects_is_refused(self):
        project_a = ProjectFactory()
        project_b = ProjectFactory()
        ProjectIdentifierFactory(related=project_a, type="DOI", value="10.1234/shared")

        with pytest.raises(IntegrityError):
            ProjectIdentifierFactory(
                related=project_b, type="DOI", value="10.1234/shared"
            )

    def test_identifier_type_choices_are_scoped_to_project(self):
        codes = {code for code, _label in ProjectIdentifier.type.field.choices}

        assert "DOI" in codes
        assert "GRANT_NUMBER" in codes
        assert not codes & {
            "ORCID",
            "RESEARCHER_ID",
            "ROR",
            "WIKIDATA",
            "ISNI",
        }


@pytest.mark.django_db
class TestProjectObjectPermissions:
    def test_creator_gets_full_permissions(self, client):
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        user = UserFactory(email="creator@example.com")
        owner = Organization.objects.create(name="Test Organization")
        client.force_login(user)

        url = reverse("project-create")
        form_data = {
            "name": "Creator's Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }
        client.post(url, data=form_data)

        project = Project.objects.get(name="Creator's Project")

        expected_perms = [
            "view_project",
            "change_project",
            "delete_project",
            "change_project_metadata",
            "change_project_settings",
        ]

        for perm in expected_perms:
            assert user.has_perm(f"project.{perm}", project), (
                f"Creator missing '{perm}' permission"
            )

    def test_non_contributor_cannot_edit_private_project(self, client):
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        UserFactory(email="owner@example.com")
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Private Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner_org,
        )

        other_user = UserFactory(email="other@example.com")
        client.force_login(other_user)

        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # A 404, not a 403 or a sign-in redirect, which would confirm the project
        # exists.
        assert response.status_code == 404

    def test_user_with_change_permission_can_edit(self, client):
        from django.urls import reverse
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Shared Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PRIVATE,
            owner=owner_org,
        )

        editor = UserFactory(email="editor@example.com")
        assign_perm("change_project", editor, project)
        assign_perm("view_project", editor, project)

        client.force_login(editor)

        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        assert response.status_code == 200
        assert "form" in response.context


@pytest.mark.django_db
class TestProjectCreator:
    def test_created_by_field_is_not_editable(self):
        assert Project._meta.get_field("created_by").editable is False

    def test_project_survives_creators_account_removal(self):
        creator = UserFactory(email="creator@example.com")
        project = ProjectFactory(created_by=creator)

        creator.delete()
        project.refresh_from_db()

        assert project.pk is not None
        assert project.created_by is None

    def test_modifying_project_advances_modified_and_keeps_creator(self):
        creator = UserFactory(email="unchanged-creator@example.com")
        project = ProjectFactory(created_by=creator)
        original_modified = project.modified

        time.sleep(0.01)
        project.name = "Renamed Project"
        project.save()
        project.refresh_from_db()

        assert project.modified > original_modified
        assert project.created_by == creator


class TestProjectTranslationBinding:
    @pytest.mark.parametrize(
        "module_path",
        [
            "fairdm.core.project.models",
            "fairdm.core.project.admin",
            "fairdm.core.project.filters",
            "fairdm.core.project.validators",
            "fairdm.core.choices",
            "fairdm.core.vocabularies",
        ],
    )
    # Asserts the binding: a module using `gettext` at import time would still look
    # translated.
    def test_module_binds_gettext_lazy_not_eager(self, module_path):
        from importlib import import_module

        from django.utils.translation import gettext_lazy

        module = import_module(module_path)
        assert module._ is gettext_lazy, (
            f"{module_path} binds `_` to something other than gettext_lazy; "
            "a string assigned at import time with it would resolve "
            "eagerly rather than at request time."
        )


@pytest.mark.django_db
class TestProjectWithMetadataQueryCount:
    @staticmethod
    def _touch_all_related(projects):
        """Evaluate every relation `with_metadata()` prefetches, for each project."""
        for project in projects:
            list(project.descriptions.all())
            list(project.dates.all())
            list(project.identifiers.all())
            list(project.contributors.all())
            list(project.keywords.all())

    @staticmethod
    def _build_project_with_metadata(descriptions, dates, identifiers, keyword_terms):
        from fairdm.factories.core import ProjectDateFactory

        project = ProjectFactory()
        for type_ in descriptions:
            ProjectDescriptionFactory(related=project, type=type_)
        for type_, value in dates:
            ProjectDateFactory(related=project, type=type_, value=value)
        for type_, value in identifiers:
            ProjectIdentifierFactory(related=project, type=type_, value=value)
        project.add_contributor(PersonFactory(), with_roles=["Creator"])
        for term in keyword_terms:
            project.keywords.add(term)
        return project

    def test_query_count_does_not_grow_with_related_record_count(
        self, django_assert_num_queries
    ):
        from research_vocabs.models import Concept

        keyword_terms = list(
            Concept.objects.filter(vocabulary__name="fairdm-roles")[:2]
        )

        small = self._build_project_with_metadata(
            descriptions=["Abstract"],
            dates=[("Start", "2020-01-01")],
            identifiers=[("DOI", "10.1234/small")],
            keyword_terms=keyword_terms[:1],
        )

        with django_assert_num_queries(6):
            self._touch_all_related(Project.objects.with_metadata().filter(pk=small.pk))

        large = [
            self._build_project_with_metadata(
                descriptions=["Abstract", "Objectives"],
                dates=[("Start", "2020-01-01"), ("End", "2021-01-01")],
                identifiers=[
                    ("DOI", f"10.1234/large-{i}"),
                    ("GRANT_NUMBER", f"GRANT-{i}"),
                ],
                keyword_terms=keyword_terms,
            )
            for i in range(3)
        ]

        with django_assert_num_queries(6):
            self._touch_all_related(
                Project.objects.with_metadata().filter(
                    pk__in=[project.pk for project in large]
                )
            )


@pytest.mark.django_db
class TestProjectListDataAnnotation:
    # The count annotation bypasses `Dataset.objects`, so it excludes private datasets
    # itself (#330).
    def test_dataset_count_excludes_private_datasets(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)

        annotated = Project.objects.with_list_data().get(pk=project.pk)

        assert annotated.dataset_count == 2

    def test_dataset_count_is_zero_for_a_project_with_no_datasets(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        annotated = Project.objects.with_list_data().get(pk=project.pk)

        assert annotated.dataset_count == 0

    def test_dataset_count_is_zero_when_every_dataset_is_private(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)
        DatasetFactory(project=project, visibility=Visibility.PRIVATE)

        annotated = Project.objects.with_list_data().get(pk=project.pk)

        assert annotated.dataset_count == 0

    def test_dataset_count_is_not_multiplied_by_other_joined_rows(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        ProjectDescriptionFactory(related=project, type="Abstract")

        annotated = Project.objects.with_list_data().get(pk=project.pk)

        assert annotated.dataset_count == 1


@pytest.mark.django_db
class TestProjectAbstractSummary:
    def test_summary_is_empty_when_the_project_has_no_abstract(self):
        project = ProjectFactory()

        assert project.get_abstract_summary() == ""

    def test_summary_is_empty_when_the_only_description_is_another_type(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project, type="Objectives", value="Not the abstract."
        )

        assert project.get_abstract_summary() == ""

    def test_summary_strips_markdown_headings_and_emphasis(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="## Heading\n\nSome **bold** and _italic_ prose.",
        )

        summary = project.get_abstract_summary()

        assert "#" not in summary
        assert "*" not in summary
        assert "_" not in summary
        assert "Heading" in summary
        assert "bold" in summary
        assert "italic" in summary

    def test_a_heading_does_not_run_into_the_prose_below_it(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="## Background\n\nBorehole temperature logs were collected.",
        )

        summary = project.get_abstract_summary()

        assert "Background Borehole" not in summary
        assert summary == "Background — Borehole temperature logs were collected."

    def test_summary_carries_no_html_tags(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="A [link](https://example.org) and a list:\n\n- one\n- two",
        )

        summary = project.get_abstract_summary()

        assert "<" not in summary
        assert ">" not in summary
        assert "link" in summary
        assert "one" in summary

    def test_summary_resolves_html_entities_to_their_characters(self):
        # Markdown escapes `&`, and left as an entity the card would print `&amp;`.
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="Rock & roll geochemistry"
        )

        summary = project.get_abstract_summary()

        assert "&amp;" not in summary
        assert "Rock & roll geochemistry" in summary

    def test_summary_collapses_whitespace_left_by_block_markup(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="First paragraph.\n\nSecond paragraph.\n\n- item one\n- item two",
        )

        summary = project.get_abstract_summary()

        assert "\n" not in summary
        assert "  " not in summary
        assert summary.startswith("First paragraph.")

    def test_summary_is_capped_at_400_characters(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(related=project, type="Abstract", value="word " * 300)

        summary = project.get_abstract_summary()

        assert len(summary) <= 400

    def test_a_long_summary_ends_with_an_ellipsis(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(related=project, type="Abstract", value="word " * 300)

        assert project.get_abstract_summary().endswith("…")

    def test_a_short_summary_is_returned_whole_and_untruncated(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="A short abstract."
        )

        assert project.get_abstract_summary() == "A short abstract."

    def test_summary_does_not_execute_or_retain_embedded_script(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type="Abstract",
            value="Safe prose. <script>alert(1)</script>",
        )

        summary = project.get_abstract_summary()

        assert "alert(1)" not in summary
        assert "script" not in summary
        assert "Safe prose." in summary


@pytest.mark.django_db
class TestProjectStatusBadgeVariant:
    def test_every_status_in_the_vocabulary_has_a_variant(self):
        for status in ProjectStatus:
            project = ProjectFactory(status=status)
            assert project.status_badge_variant, f"{status.label} has no badge variant"


@pytest.mark.django_db
class TestProjectMetaDescription:
    # `get_meta_description()` once read an attribute `AbstractDescription` does not
    # declare (#331).
    def test_returns_the_abstracts_text_when_one_exists(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="A concise summary."
        )

        assert project.get_meta_description() == "A concise summary."

    def test_returns_none_when_there_is_no_abstract(self):
        project = ProjectFactory()

        assert project.get_meta_description() is None


@pytest.mark.django_db
class TestProjectIsActive:
    def test_a_project_in_progress_is_active(self):
        project = ProjectFactory(status=ProjectStatus.IN_PROGRESS)

        assert project.is_active is True

    @pytest.mark.parametrize(
        "status", [s for s in ProjectStatus if s != ProjectStatus.IN_PROGRESS]
    )
    def test_a_project_in_any_other_status_is_not_active(self, status):
        project = ProjectFactory(status=status)

        assert project.is_active is False

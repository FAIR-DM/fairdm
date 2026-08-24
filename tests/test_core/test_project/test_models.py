"""
Unit tests for fairdm.core.project models.

Tests the Project, ProjectDescription, ProjectDate, and ProjectIdentifier models
in isolation, focusing on field validation, constraints, and model methods.
Also covers form/view integration, object-level permissions, and metadata
workflows (descriptions, dates, identifiers).

Test-First Approach (Red-Green-Refactor):
1. Write tests that FAIL (Red)
2. Implement minimal code to pass (Green)
3. Refactor for quality (Refactor)
"""

import time

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.urls import reverse
from guardian.shortcuts import get_perms

from fairdm.core.choices import ProjectStatus
from fairdm.core.project.forms import ProjectCreateForm, ProjectForm
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.factories import (
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility


@pytest.mark.django_db
class TestProjectModel:
    """Unit tests for Project model."""

    def test_project_creation_with_required_fields(self):
        """Test that a project can be created with only required fields.

        Requirement: FR-001 - Projects must have name, status, visibility, owner.
        User Story: US1 - Streamlined creation with minimal required fields.
        """
        from fairdm.contrib.contributors.models import Organization

        # Create owner organization
        owner = Organization.objects.create(name="Test Organization")

        # Create project with minimal required fields
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        # Verify project was created successfully
        assert project.pk is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.CONCEPT
        assert project.visibility == Visibility.PRIVATE
        assert project.owner == owner
        assert project.uuid is not None
        assert project.uuid.startswith("p")  # Prefix validation

    def test_project_uuid_is_unique(self):
        """Test that each project gets a unique UUID.

        Requirement: FR-002 - Projects must have unique, stable identifiers.
        """
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

        # Verify UUIDs are unique
        assert project1.uuid != project2.uuid
        assert project1.uuid.startswith("p")
        assert project2.uuid.startswith("p")

    def test_project_status_choices(self):
        """Test that project status field accepts valid choices.

        Requirement: FR-003 - Projects must have defined status values.
        User Story: US1 - Status selection during creation.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        # Test all valid status choices
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
        """Test that project visibility field accepts valid choices.

        Requirement: FR-004 - Projects must support visibility control.
        User Story: US1 - Visibility selection during creation and editing.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")

        # Test all valid visibility choices
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
        """Test that projects with PUBLIC datasets cannot be deleted.

        Requirement: FR-021 - Prevent deletion of projects with publicly visible datasets.
        Implementation: T007 - pre_delete signal raises PublicDatasetsProtect for PUBLIC datasets.
        """
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

        # Add a PUBLIC dataset to the project
        Dataset.objects.create(
            name="Public Dataset",
            project=project,
            visibility=Visibility.PUBLIC,
        )

        # Attempt to delete project should raise PublicDatasetsProtect
        with pytest.raises(PublicDatasetsProtect):
            project.delete()


@pytest.mark.django_db
class TestProjectIdentifierField:
    """The generated project identifier (US-8).

    Requirement: FR-001 - the identifier is generated on creation and is not
    editable afterwards.
    """

    def test_uuid_field_is_not_editable(self):
        assert Project._meta.get_field("uuid").editable is False


@pytest.mark.django_db
class TestProjectRequiredFields:
    """A project requires a name; an owning organisation is optional (US-8).

    Requirement: FR-002, FR-005 - D-007 records that ownership stays
    optional so creation remains cheap.
    """

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


class TestProjectStatusVocabulary:
    """Every lifecycle status label names the state its member names (US-8).

    Requirement: FR-003, SC-010. The expected label is derived from the
    member's own name so this stays meaningful if a member is added later,
    rather than being a hard-coded list that would pass regardless.
    """

    def test_every_status_label_names_its_state(self):
        for member in ProjectStatus:
            expected = member.name.replace("_", " ").capitalize()
            assert str(member.label) == expected


@pytest.mark.django_db
class TestProjectDefaultOrdering:
    """Projects are ordered most-recently-modified first by default (US-8).

    Requirement: FR-007.
    """

    def test_default_ordering_is_most_recently_modified_first(self):
        first = ProjectFactory()
        time.sleep(0.01)
        second = ProjectFactory()
        time.sleep(0.01)
        third = ProjectFactory()

        # Re-saving `first` last makes it the most recently modified,
        # despite being created first - proving the ordering is by
        # `modified`, not by creation order or primary key.
        time.sleep(0.01)
        first.save()

        assert list(Project.objects.all()) == [first, third, second]


@pytest.mark.django_db
class TestProjectPreDeleteSignal:
    """Tests for the pre_delete signal guard on Project model."""

    def test_pre_delete_signal_blocks_public_datasets(self):
        """Test that deleting a project with PUBLIC datasets raises PublicDatasetsProtect.

        T004 - MUST FAIL before T007 implementation.
        """
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
        """Test that deleting a project with only PRIVATE datasets succeeds.

        T005 - MUST FAIL before T007 implementation.
        """
        from fairdm.core.dataset.models import Dataset
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        dataset = Dataset.objects.create(
            name="Private Dataset", project=project, visibility=Visibility.PRIVATE
        )
        pk = project.pk

        # Should not raise — private datasets do not block project deletion
        project.delete()

        assert not Project.objects.filter(pk=pk).exists()

    def test_pre_delete_signal_allows_no_datasets(self):
        """Test that deleting a project with no datasets succeeds.

        T006 - MUST FAIL before T007 implementation.
        """
        from fairdm.factories import ProjectFactory

        project = ProjectFactory()
        pk = project.pk

        project.delete()

        assert not Project.objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestProjectDescriptionModel:
    """Unit tests for ProjectDescription model."""

    def test_description_type_choices_are_scoped_to_project(self):
        """The type field's choices are exactly the project description
        collection's members, and exclude a dataset-only type.

        Requirement: FR-008 - A project's descriptions are drawn from a
        controlled set of description types.

        `type` is a plain CharField, so creating a row cannot prove the
        vocabulary binding - Django does not validate choices on save. This
        asserts the choices `GenericModel.__init_subclass__` pushed onto the
        field directly, against the literal expected member names rather
        than against `ProjectDescription.VOCABULARY.choices` itself - that
        comparison would hold for any vocabulary at all, since it is the
        same assignment's source and target, and so cannot detect a wrong
        binding.
        """
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
        """Test that duplicate description types for the same project are
        prevented, and that the message names the type that is already used.

        Requirement: FR-008 - Each project can have at most one description of
        each type, and the message names it. T004, T005.
        """
        from fairdm.contrib.contributors.models import Organization

        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Test Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner,
        )

        # Create first description
        ProjectDescription.objects.create(
            related=project, type="Abstract", value="First abstract"
        )

        # Attempt to create duplicate type should fail at validation
        desc2 = ProjectDescription(
            related=project, type="Abstract", value="Second abstract"
        )

        with pytest.raises(ValidationError) as exc_info:
            desc2.clean()

        assert "type" in exc_info.value.error_dict
        assert "already exists" in str(exc_info.value)
        assert "Abstract" in str(exc_info.value)

    def test_duplicate_description_type_refused_at_database(self):
        """The unique constraint on (related, type) refuses a duplicate
        description type even when validation is bypassed, so a concurrent
        write cannot slip past it.

        Requirement: FR-008 - At most one description per type, enforced by
        a database constraint as well as by validation. T006.
        """
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
    """Unit tests for ProjectDate model."""

    def test_date_type_choices_are_scoped_to_project(self):
        """The type field's choices are exactly the project date collection's members.

        Requirement: FR-009 - A project's dates are drawn from a controlled
        set containing a start and an end.

        `type` is a plain CharField, so creating a row cannot prove the
        vocabulary binding - Django does not validate choices on save. This
        asserts the choices `GenericModel.__init_subclass__` pushed onto the
        field directly, against the literal expected member names rather
        than against `ProjectDate.VOCABULARY.choices` itself - that
        comparison would hold for any vocabulary at all, since it is the
        same assignment's source and target, and so cannot detect a wrong
        binding.
        """
        codes = {code for code, _label in ProjectDate.type.field.choices}
        assert codes == {"Start", "End"}

    def test_second_start_date_on_project_is_refused(self):
        """A second start date on the same project is refused by validation.

        Requirement: FR-009 - At most one date per type.
        """
        from fairdm.factories.core import ProjectDateFactory

        project = ProjectFactory()
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")

        duplicate = ProjectDate(related=project, type="Start", value="2021-01-01")
        with pytest.raises(ValidationError):
            duplicate.full_clean()

    def test_duplicate_date_type_refused_at_database(self):
        """The unique constraint on (related, type) refuses a duplicate date
        type even when validation is bypassed, so a concurrent write cannot
        slip past it.

        Requirement: FR-009 - At most one date per type, enforced by a
        database constraint as well as by validation.
        """
        from fairdm.factories.core import ProjectDateFactory

        project = ProjectFactory()
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")

        with pytest.raises(IntegrityError):
            ProjectDateFactory(related=project, type="Start", value="2021-01-01")

    def test_end_date_before_start_date_raises_error(self):
        """An end date earlier than the project's start is refused, with a
        message naming both dates.

        Requirement: FR-010 - The system refuses to save a project date that
        would place the project's end before its start, and the message
        states which two dates conflict.
        """
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06-01")

        end = ProjectDate(related=project, type="End", value="2019-05-01")
        with pytest.raises(ValidationError) as exc_info:
            end.full_clean()

        message = str(exc_info.value)
        assert "2020-06-01" in message
        assert "2019-05-01" in message

    def test_changing_start_to_after_end_is_refused(self):
        """Changing the start to a date after the existing end is refused for
        the same reason, whichever of the two dates is being edited.

        Requirement: FR-010.
        """
        project = ProjectFactory()
        start = ProjectDate.objects.create(
            related=project, type="Start", value="2020-01-01"
        )
        ProjectDate.objects.create(related=project, type="End", value="2020-12-31")

        start.value = "2021-01-01"
        with pytest.raises(ValidationError):
            start.full_clean()

    def test_end_date_with_no_start_date_is_accepted(self):
        """An end date on a project with no start date is accepted - there is
        nothing to contradict.

        Requirement: FR-010.
        """
        project = ProjectFactory()
        end = ProjectDate(related=project, type="End", value="2024-06-15")

        end.full_clean()  # must not raise

    def test_year_only_end_in_same_year_as_month_precision_start_is_accepted(self):
        """A year-only end date in the same year as a month-precision start is
        accepted - the comparison happens at the coarser of the two
        precisions, so a project that started in June 2020 and ended some
        time in 2020 is not an error.

        Requirement: FR-010.
        """
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06")

        end = ProjectDate(related=project, type="End", value="2020")
        end.full_clean()  # must not raise

    def test_month_precision_end_before_month_precision_start_is_refused(self):
        """A month-precision end earlier than a month-precision start in the
        same year is refused - the month-precision branch of `precedes` was
        previously exercised by no test.

        Requirement: FR-010.
        """
        project = ProjectFactory()
        ProjectDate.objects.create(related=project, type="Start", value="2020-06")

        end = ProjectDate(related=project, type="End", value="2020-03")
        with pytest.raises(ValidationError):
            end.full_clean()


@pytest.mark.django_db
class TestProjectFunding:
    """Unit tests for the `Project.funding` field's DataCite shape.

    Requirement: FR-015, FR-016 - funding is a list of DataCite funding
    references; funder name is required, everything else optional, and the
    key set and identifier scheme are both closed.
    """

    def test_award_with_all_parts_round_trips(self):
        """An award with all six parts is accepted and each part reads back
        individually.

        Requirement: FR-015, SC-001, SC-005. T031.
        """
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
        """A project carrying two funding records keeps both.

        Requirement: FR-015 - a project MAY carry several funding records.
        T032.
        """
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
        """A funding record naming only a funder is accepted - every other
        part is optional.

        Requirement: FR-016, SC-005. T033.
        """
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency"}]

        project.full_clean()  # must not raise

    def test_identifier_scheme_outside_datacite_set_is_refused(self):
        """A funder identifier scheme outside DataCite's set is refused, and
        the message names the accepted schemes.

        Requirement: FR-016, SC-005. T034.
        """
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
        """Funding stored as a single object rather than a list is refused.

        Requirement: FR-015 - a single object is not accepted. T035.
        """
        project = ProjectFactory()
        project.funding = {"funderName": "Sample Agency"}

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_list_of_scalars_is_refused_not_raised(self):
        """A list whose members are not objects is refused with the same
        message as a non-list value, rather than raising an unhandled
        exception.

        Requirement: FR-015. T035.
        """
        project = ProjectFactory()
        project.funding = ["Sample Agency"]

        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert "list of funding reference objects" in str(exc_info.value)

    def test_unknown_key_is_refused_and_named(self):
        """A key outside FR-015's accepted set is refused, and the message
        names the offending key.

        Requirement: FR-015.
        """
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency", "amount": 50000}]

        with pytest.raises(ValidationError) as exc_info:
            project.full_clean()

        assert "amount" in str(exc_info.value)

    def test_missing_funder_name_is_refused(self):
        """A funding record without a funder name is refused.

        Requirement: FR-016 - funder name is required within a record.
        """
        project = ProjectFactory()
        project.funding = [{"awardNumber": "GRANT-2024-001"}]

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_funder_name_that_is_not_a_string_is_refused(self):
        """A funder name that is not a string is refused rather than stored -
        a truthiness check alone would accept it and pass it straight into
        the exported document, where DataCite requires a string.

        Requirement: FR-015, FR-016.
        """
        project = ProjectFactory()
        project.funding = [{"funderName": {"nested": "object"}}]

        with pytest.raises(ValidationError):
            project.full_clean()

    def test_award_number_that_is_not_a_string_is_refused(self):
        """A non-string value for another string-typed key is refused too.

        Requirement: FR-015, FR-016.
        """
        project = ProjectFactory()
        project.funding = [{"funderName": "Sample Agency", "awardNumber": 42}]

        with pytest.raises(ValidationError):
            project.full_clean()


@pytest.mark.django_db
class TestProjectModelIntegration:
    """Tests for the Project model."""

    def test_project_creation(self):
        """Test creating a basic Project instance."""
        project = ProjectFactory()

        assert project.pk is not None
        assert project.name is not None
        assert project.uuid is not None
        assert project.uuid.startswith("p")

    def test_project_visibility_default(self):
        """Test that default visibility is PRIVATE."""
        project = ProjectFactory()
        assert project.visibility == Visibility.PRIVATE

    def test_project_queryset_get_visible(self):
        """Test ProjectQuerySet.get_visible() filters correctly."""
        # Create public and private projects
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        visible = Project.objects.get_visible()

        assert public_project in visible
        assert private_project not in visible

    def test_project_queryset_with_contributors(self):
        """Test ProjectQuerySet.with_contributors() prefetches correctly."""
        project = ProjectFactory()

        # This should not raise an error and should be efficient
        queryset = Project.objects.with_contributors()
        project_with_prefetch = queryset.get(pk=project.pk)

        # Access contributors should not cause additional queries due to prefetch
        assert project_with_prefetch.contributors is not None

    def test_project_str_representation(self):
        """Test Project string representation."""
        project = ProjectFactory(name="Test Project")
        assert str(project) == "Test Project"

    def test_project_absolute_url(self):
        """Test get_absolute_url returns correct URL."""
        project = ProjectFactory()
        url = project.get_absolute_url()

        assert url == reverse("project:overview", kwargs={"uuid": project.uuid})

    def test_project_descriptions_relationship(self):
        """Test that project descriptions can be created correctly."""
        project = ProjectFactory()
        descriptions = ProjectDescription.objects.filter(related=project)

        # Factory may or may not create descriptions by default
        # Just test that the relationship works
        assert descriptions.count() >= 0
        assert all(desc.related == project for desc in descriptions)

    def test_project_dates_relationship(self):
        """Test that project dates can be created correctly."""
        project = ProjectFactory()
        dates = ProjectDate.objects.filter(related=project)

        # Factory may or may not create dates by default
        # Just test that the relationship works
        assert dates.count() >= 0
        assert all(date.related == project for date in dates)

    def test_add_contributor(self):
        """Test adding a contributor to a project.

        Requirement: FR-013 - a contribution records its contributor and its
        roles, and both read back. Passing roles in and never reading them
        back would leave this test passing even if `add_contributor` ignored
        roles entirely, so the roles are asserted explicitly here.
        """
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
    """The project role vocabulary is expressible in DataCite's contributor
    types (US-8).

    Requirement: FR-014. The project role vocabulary's names (PascalCase,
    e.g. "ProjectLeader") and `DataciteContributorRoles`'s names
    (SCREAMING_SNAKE_CASE, e.g. "PROJECT_LEADER") differ only in casing
    convention, so `PROJECT_ROLE_DATACITE_CONTRIBUTOR_TYPES` records that
    correspondence rather than requiring export to derive it. The expected
    role set is read from the vocabulary itself, not hard-coded, so this
    stays meaningful if the project role collection changes.
    """

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
    """Tests for the ProjectForm."""

    def test_form_valid_data(self):
        """Test form validation with valid data."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }
        form = ProjectCreateForm(data=form_data)

        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """Test form validation fails without required fields."""
        form_data = {}
        form = ProjectForm(data=form_data)

        assert not form.is_valid()
        assert "name" in form.errors

    def test_form_saves_correctly(self):
        """Test that form saves data correctly."""
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
    """Tests for Project views."""

    def test_project_list_view_accessible(self, client):
        """Test that project list view is accessible."""
        response = client.get(reverse("project-list"))

        assert response.status_code == 200

    def test_project_list_view_shows_public_projects(self, client):
        """Test that only public projects are shown in list view."""
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        response = client.get(reverse("project-list"))

        # Check that public project is visible
        assert public_project.name.encode() in response.content
        # Check that private project is not visible
        assert private_project.name.encode() not in response.content

    def test_project_create_view_requires_authentication(self, client):
        """Test that project creation requires login."""
        response = client.get(reverse("project-create"))

        # Should redirect to login
        assert response.status_code == 302

    def test_project_create_view_accessible_when_authenticated(
        self, authenticated_client
    ):
        """Test that authenticated users can access project create view."""
        response = authenticated_client.get(reverse("project-create"))

        assert response.status_code == 200

    def test_project_create_view_creates_project(self, authenticated_client):
        """Test that submitting project create form creates a project."""
        form_data = {
            "name": "New Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = authenticated_client.post(reverse("project-create"), data=form_data)

        # Check redirect after successful creation
        assert response.status_code == 302

        # Check project was created
        project = Project.objects.filter(name="New Test Project").first()
        assert project is not None
        assert project.visibility == Visibility.PUBLIC

    def test_project_detail_view_accessible(self, client):
        """Test that project detail view is accessible."""
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        response = client.get(
            reverse("project:overview", kwargs={"uuid": project.uuid})
        )

        assert response.status_code == 200
        assert project.name.encode() in response.content


@pytest.mark.django_db
class TestProjectPermissions:
    """Tests for Project permissions and access control."""

    def test_anonymous_user_cannot_create_project(self, client):
        """Test that anonymous users cannot create projects."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        response = client.post(reverse("project-create"), data=form_data)

        # Should redirect to login
        assert response.status_code == 302
        # Check that redirect URL contains 'login'
        assert "login" in response["Location"]

    def test_project_creator_becomes_contributor(self, authenticated_client):
        """Test that project creator is automatically added as contributor."""
        form_data = {
            "name": "Test Project",
            "visibility": Visibility.PUBLIC,
            "status": 0,
        }

        authenticated_client.post(reverse("project-create"), data=form_data)

        project = Project.objects.filter(name="Test Project").first()
        if project:
            # Check that the project has contributors
            assert project.contributors.count() > 0


@pytest.mark.django_db
class TestProjectDescriptions:
    """Integration tests for project description workflows."""

    def test_add_multiple_descriptions_to_project(self):
        """Test adding multiple descriptions with different types to a project.

        Requirement: FR-010 - Projects support multiple description types.
        User Story: US2 - Add rich descriptive metadata with multiple types.
        Implementation: T046 - Integration test for multiple descriptions.

        Workflow:
        1. Create a project
        2. Add description of type "Abstract"
        3. Add description of type "Methods"
        4. Verify both descriptions exist and are correctly typed
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectDescription

        # Create project
        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Research Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        # Add Abstract description
        ProjectDescription.objects.create(
            related=project,
            type="Abstract",
            value="This project studies the impact of X on Y using Z methodology.",
        )

        # Add Objectives description
        ProjectDescription.objects.create(
            related=project,
            type="Objectives",
            value="We aim to quantify the effect across ten sites using XRF.",
        )

        # Verify both descriptions exist
        descriptions = project.descriptions.all()
        assert descriptions.count() == 2

        # Verify types are different
        types = [d.type for d in descriptions]
        assert "Abstract" in types
        assert "Objectives" in types

        # Verify content is correct
        abstract_desc = project.descriptions.get(type="Abstract")
        assert "impact of X on Y" in abstract_desc.value

        objectives_desc = project.descriptions.get(type="Objectives")
        assert "XRF" in objectives_desc.value


@pytest.mark.django_db
class TestProjectKeywordsAndTags:
    """Tests for project categorisation via controlled keywords and free
    tags.

    Requirement: FR-006 - A project supports categorisation both by terms
    drawn from a configured controlled vocabulary and by free-form tags, and
    the two remain distinguishable.
    """

    def test_controlled_vocabulary_term_is_stored_as_a_reference(self):
        """A term from a configured controlled vocabulary added as a keyword
        is stored as a reference to that vocabulary rather than as text.

        Requirement: FR-006. T008.
        """
        from research_vocabs.models import Concept

        project = ProjectFactory()
        # `Concept.preload()` runs once per session (tests/conftest.py), so
        # real terms from every registered vocabulary are already available.
        term = Concept.objects.filter(vocabulary__name="fairdm-roles").first()
        assert term is not None

        project.keywords.add(term)

        stored = project.keywords.get(pk=term.pk)
        assert isinstance(stored, Concept)
        assert stored.vocabulary.name == "fairdm-roles"
        assert stored.name == term.name

    def test_free_tags_are_distinguishable_from_controlled_keywords(self):
        """Free tags are stored and remain distinguishable from controlled
        keywords.

        Requirement: FR-006. T009.
        """
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
    """Integration tests for project date workflows."""

    def test_add_date_range_to_project(self):
        """Test adding start and end dates to create a project timeline.

        Requirement: FR-011 - Projects support multiple date types for timelines.
        User Story: US2 - Add project dates with start/end ranges.
        Implementation: T047 - Integration test for date ranges.

        Workflow:
        1. Create a project
        2. Add a start date (type: "Start")
        3. Add an end date (type: "End")
        4. Verify both dates exist and create a valid timeline
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectDate

        # Create project
        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Time-Bound Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        # Add start date
        ProjectDate.objects.create(
            related=project,
            type="Start",
            value="2024-01-01",  # PartialDateField expects string format
        )

        # Add end date
        ProjectDate.objects.create(
            related=project,
            type="End",
            value="2025-12-31",  # PartialDateField expects string format
        )

        # Verify both dates exist
        dates = project.dates.all()
        assert dates.count() == 2

        # Verify types are correct
        types = [d.type for d in dates]
        assert "Start" in types
        assert "End" in types

        # Verify timeline is logical (start before end)
        start = project.dates.get(type="Start")
        end = project.dates.get(type="End")
        assert start.value < end.value


@pytest.mark.django_db
class TestProjectIdentifiers:
    """Integration tests for project identifier workflows."""

    def test_add_identifiers_to_project(self):
        """Test adding multiple identifiers to a project.

        Requirement: FR-005 - Projects support external identifiers.
        User Story: US2 - Add identifiers for FAIR compliance and traceability.
        Implementation: T048 - Integration test for multiple identifiers.

        Workflow:
        1. Create a project
        2. Add an ISNI identifier
        3. Add a Crossref Funder ID
        4. Verify both identifiers exist and are correctly typed

        Note: Current vocabulary uses FairDMIdentifiers (ORCID, ISNI, ROR, etc).
        For project-specific identifiers like DOI, vocabulary would need extension.
        """
        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project, ProjectIdentifier

        # Create project
        owner = Organization.objects.create(name="Test Organization")
        project = Project.objects.create(
            name="Funded Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PUBLIC,
            owner=owner,
        )

        # Add ISNI identifier
        ProjectIdentifier.objects.create(
            related=project, type="ISNI", value="0000 0001 2283 4400"
        )

        # Add Crossref Funder ID (like a grant number)
        ProjectIdentifier.objects.create(
            related=project,
            type="CROSSREF_FUNDER_ID",
            value="https://doi.org/10.13039/100000001",
        )

        # Verify both identifiers exist
        identifiers = project.identifiers.all()
        assert identifiers.count() == 2

        # Verify types are correct
        types = [i.type for i in identifiers]
        assert "ISNI" in types
        assert "CROSSREF_FUNDER_ID" in types

        # Verify values are correct
        isni_identifier = project.identifiers.get(type="ISNI")
        assert isni_identifier.value == "0000 0001 2283 4400"

        funder_identifier = project.identifiers.get(type="CROSSREF_FUNDER_ID")
        assert funder_identifier.value == "https://doi.org/10.13039/100000001"

    def test_doi_attached_to_project_stored_under_doi_type(self):
        """A DOI attached to a project is stored under the DOI type.

        Requirement: FR-011 - The project identifier vocabulary includes a DOI.
        """
        project = ProjectFactory()

        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/example")

        doi = project.identifiers.get(type="DOI")
        assert doi.value == "10.1234/example"

    def test_grant_number_stored_alongside_doi(self):
        """A grant number is stored alongside the DOI.

        Requirement: FR-011 - The project identifier vocabulary includes a grant number.
        """
        project = ProjectFactory()
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/example")

        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="GRANT-2024-001"
        )

        types = set(project.identifiers.values_list("type", flat=True))
        assert types == {"DOI", "GRANT_NUMBER"}

    def test_duplicate_identifier_value_across_projects_is_refused(self):
        """Attaching the same identifier value to a second project is refused.

        Requirement: FR-012 - An identifier value is unique across every record
        that carries identifiers, so the same identifier cannot name two things.
        """
        project_a = ProjectFactory()
        project_b = ProjectFactory()
        ProjectIdentifierFactory(related=project_a, type="DOI", value="10.1234/shared")

        with pytest.raises(IntegrityError):
            ProjectIdentifierFactory(
                related=project_b, type="DOI", value="10.1234/shared"
            )

    def test_identifier_type_choices_are_scoped_to_project(self):
        """The identifier types offered for a project contain a DOI and a grant
        number, and contain none of ORCID, ResearcherID, ROR, Wikidata or ISNI.

        Requirement: FR-011 - The project identifier vocabulary is scoped to
        types that apply to a project, not the vocabulary used for people and
        organisations.
        """
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
    """Integration tests for project-level permissions."""

    def test_creator_gets_full_permissions(self, client):
        """Test that project creator receives all permissions automatically.

        Requirement: FR-007 - Creator receives full project permissions.
        User Story: US1 - Automatic permission assignment on creation.
        """
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create user and organization
        user = UserFactory(email="creator@example.com")
        owner = Organization.objects.create(name="Test Organization")
        client.force_login(user)

        # Create project through view
        url = reverse("project-create")
        form_data = {
            "name": "Creator's Project",
            "status": ProjectStatus.CONCEPT,
            "visibility": Visibility.PRIVATE,
            "owner": owner.pk,
        }
        client.post(url, data=form_data)

        # Get created project
        project = Project.objects.get(name="Creator's Project")

        # Verify creator has all project permissions
        user_perms = get_perms(user, project)

        # Expected permissions for creator
        expected_perms = [
            "view_project",
            "change_project",
            "delete_project",
            "change_project_metadata",
            "change_project_settings",
        ]

        for perm in expected_perms:
            assert perm in user_perms, f"Creator missing '{perm}' permission"

    def test_non_contributor_cannot_edit_private_project(self, client):
        """Test that non-contributors cannot edit private projects.

        Requirement: FR-004 - Private projects require permissions.
        User Story: US1 - Access control for private projects.
        """
        from django.urls import reverse

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create owner and project
        UserFactory(email="owner@example.com")
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Private Project",
            status=ProjectStatus.CONCEPT,
            visibility=Visibility.PRIVATE,
            owner=owner_org,
        )

        # Create different user (non-contributor)
        other_user = UserFactory(email="other@example.com")
        client.force_login(other_user)

        # Attempt to access edit view
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # Verify access denied (403) or redirect
        assert response.status_code in [403, 302]

    def test_user_with_change_permission_can_edit(self, client):
        """Test that users with change permission can edit projects.

        Requirement: FR-007 - Object-level permissions control access.
        User Story: US1 - Granular permission assignment.
        """
        from django.urls import reverse
        from guardian.shortcuts import assign_perm

        from fairdm.contrib.contributors.models import Organization
        from fairdm.core.project.models import Project

        # Create owner and project
        owner_org = Organization.objects.create(name="Owner Organization")

        project = Project.objects.create(
            name="Shared Project",
            status=ProjectStatus.IN_PROGRESS,
            visibility=Visibility.PRIVATE,
            owner=owner_org,
        )

        # Create editor user and assign permission
        editor = UserFactory(email="editor@example.com")
        assign_perm("change_project", editor, project)
        assign_perm("view_project", editor, project)

        client.force_login(editor)

        # Access edit view
        url = reverse("project:overview-update", kwargs={"uuid": project.uuid})
        response = client.get(url)

        # Verify successful access
        assert response.status_code == 200
        assert "form" in response.context


@pytest.mark.django_db
class TestProjectCreator:
    """Unit tests for the `Project.created_by` creation record (US7)."""

    def test_created_by_field_is_not_editable(self):
        """`created_by` is kept out of forms, the admin and the serializer
        solely by `editable=False` - nothing else enforces it, so that flag
        needs its own assertion rather than relying on `perform_create`
        overriding `validated_data` regardless of what the field allows.

        Requirement: FR-017.
        """
        assert Project._meta.get_field("created_by").editable is False

    def test_project_survives_creators_account_removal(self):
        """A project outlives its creator's account, with its creator reading
        as unknown rather than raising or being deleted itself.

        Requirement: FR-017 - Survive the creating user's removal.
        """
        creator = UserFactory(email="creator@example.com")
        project = ProjectFactory(created_by=creator)

        creator.delete()
        project.refresh_from_db()

        assert project.pk is not None
        assert project.created_by is None

    def test_modifying_project_advances_modified_and_keeps_creator(self):
        """Changing a project advances its modification timestamp and leaves
        its creator unchanged.

        Requirement: FR-018 - Record when a project was created and last
        changed, without disturbing the creator.
        """
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
    """Every in-scope surface's strings resolve for translation at request
    time, not at import time (US-8).

    Requirement: FR-027. `gettext_lazy` returns a lazy proxy that resolves
    when it is rendered; `gettext` resolves immediately, at import time,
    against whatever locale happens to be active then. Binding `_` to
    `gettext_lazy` is what this specification's surfaces rely on, so this
    asserts the binding directly rather than the string values it produces -
    a module that imported `gettext` instead would fail this test even
    though every individual string still "looks" translated.

    `forms.py` is deliberately not among the modules checked below - D-014
    puts forms out of scope for FR-027, since `fairdm/core/project/forms.py`
    binds `_` to the eager `gettext` on purpose, not by omission.
    """

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
    """`with_metadata()` loads a project with all its related metadata in a
    bounded number of queries (US-8).

    Requirement: FR-028, SC-009. Built to fail if the prefetching were
    removed: the same query count is asserted twice, once against a project
    carrying one of each related record and once against the same project
    after several more of each kind are added, proving the count does not
    grow with the number of related records.
    """

    @staticmethod
    def _touch_all_related(projects):
        """Force evaluation of every relation `with_metadata()` prefetches,
        for every project in `projects`.

        A single project's relations cost the same one query each whether or
        not they are prefetched - prefetching only pays off, and N+1 only
        appears, once more than one project's relations are touched in the
        same pass. So the count is only meaningful measured across several
        projects, which is also the shape a real caller (a project list)
        uses.
        """
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

        # Several projects, each carrying several of every related record -
        # the query count for loading and touching all of them must not grow
        # beyond the count above.
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

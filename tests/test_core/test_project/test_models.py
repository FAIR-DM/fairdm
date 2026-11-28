"""Tests for the project models, their querysets, permissions and metadata records."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.core.choices import ProjectStatus
from fairdm.core.project.models import (
    Project,
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    CREATOR,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
    collection_members,
    notation,
)
from fairdm.factories import (
    ContributionFactory,
    DatasetFactory,
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.utils.location.coverage import Coverage


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


@pytest.mark.django_db
class TestProjectDescriptionModel:
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
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="First abstract",
        )

        desc2 = ProjectDescription(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Second abstract",
        )

        with pytest.raises(ValidationError) as exc_info:
            desc2.clean()

        assert "type" in exc_info.value.error_dict
        assert "Abstract" in str(exc_info.value)


@pytest.mark.django_db
class TestProjectDateModel:
    def test_an_end_before_the_start_is_refused_in_the_projects_words(self):
        project = ProjectFactory()
        ProjectDate.objects.create(
            related=project, type_id=f"{DATE_TYPES}/start", value="2020-06-01"
        )

        end = ProjectDate(
            related=project, type_id=f"{DATE_TYPES}/end", value="2019-05-01"
        )
        with pytest.raises(ValidationError) as exc_info:
            end.full_clean()

        message = str(exc_info.value)
        assert "project's end date (2019-05-01)" in message
        assert "its start date (2020-06-01)" in message


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
    def test_project_queryset_get_visible(self):
        public_project = ProjectFactory(visibility=Visibility.PUBLIC)
        private_project = ProjectFactory(visibility=Visibility.PRIVATE)

        visible = Project.objects.get_visible()

        assert public_project in visible
        assert private_project not in visible

    def test_project_absolute_url(self):
        project = ProjectFactory()
        url = project.get_absolute_url()

        assert url == reverse("project:overview", kwargs={"uuid": project.uuid})


@pytest.mark.django_db
class TestProjectRoleDataciteMapping:
    # The DataCite export writes a role's notation as its contributorType, so every project
    # role but the creator, which DataCite lists apart, must carry one DataCite accepts.
    DATACITE_CONTRIBUTOR_TYPES = {
        "ContactPerson",
        "DataCollector",
        "DataCurator",
        "DataManager",
        "Distributor",
        "Editor",
        "HostingInstitution",
        "Producer",
        "ProjectLeader",
        "ProjectManager",
        "ProjectMember",
        "RegistrationAgency",
        "RegistrationAuthority",
        "RelatedPerson",
        "Researcher",
        "ResearchGroup",
        "RightsHolder",
        "Sponsor",
        "Supervisor",
        "WorkPackageLeader",
        "Other",
    }

    def test_every_project_role_has_a_datacite_contributor_type(self):
        notations = {
            notation(role)
            for role in collection_members(Project.CONTRIBUTOR_ROLES)
            if role.uri != CREATOR
        }

        assert notations <= self.DATACITE_CONTRIBUTOR_TYPES


@pytest.mark.django_db
class TestProjectIdentifiers:
    def test_identifier_type_choices_are_scoped_to_project(self):
        codes = {concept.uri for concept in ProjectIdentifier.get_type_concepts()}

        assert f"{IDENTIFIER_TYPES}/doi" in codes
        assert f"{IDENTIFIER_TYPES}/grant-number" in codes
        assert not codes & {
            f"{IDENTIFIER_TYPES}/orcid",
            f"{IDENTIFIER_TYPES}/researcher-id",
            f"{IDENTIFIER_TYPES}/ror",
            f"{IDENTIFIER_TYPES}/wikidata",
            f"{IDENTIFIER_TYPES}/isni",
        }


@pytest.mark.django_db
class TestProjectCreator:
    def test_project_survives_creators_account_removal(self):
        creator = UserFactory(email="creator@example.com")
        project = ProjectFactory(created_by=creator)

        creator.delete()
        project.refresh_from_db()

        assert project.pk is not None
        assert project.created_by is None


class TestProjectTranslationBinding:
    @pytest.mark.parametrize(
        "module_path",
        [
            "fairdm.core.project.models",
            "fairdm.core.project.admin",
            "fairdm.core.project.filters",
            "fairdm.core.project.validators",
            "fairdm.core.choices",
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
            ProjectDescriptionFactory(related=project, type_id=type_)
        for type_, value in dates:
            ProjectDateFactory(related=project, type_id=type_, value=value)
        for type_, value in identifiers:
            ProjectIdentifierFactory(related=project, type_id=type_, value=value)
        project.add_contributor(
            PersonFactory(), with_roles=[f"{CONTRIBUTOR_ROLES}/creator"]
        )
        for term in keyword_terms:
            project.keywords.add(term)
        return project

    def test_query_count_does_not_grow_with_related_record_count(
        self, django_assert_num_queries
    ):
        from controlled_vocabularies.models import Record

        keyword_terms = list(
            Record.objects.filter(
                scheme__uri=CONTRIBUTOR_ROLES, type=Record.Type.CONCEPT
            ).order_by("pk")[:2]
        )

        small = self._build_project_with_metadata(
            descriptions=[f"{DESCRIPTION_TYPES}/abstract"],
            dates=[(f"{DATE_TYPES}/start", "2020-01-01")],
            identifiers=[(f"{IDENTIFIER_TYPES}/doi", "10.1234/small")],
            keyword_terms=keyword_terms[:1],
        )
        # A fresh queryset for each pass: a used one answers from its result cache.
        self._touch_all_related(Project.objects.with_metadata().filter(pk=small.pk))
        with CaptureQueriesContext(connection) as one_project:
            self._touch_all_related(Project.objects.with_metadata().filter(pk=small.pk))
        baseline = len(one_project.captured_queries)

        large = [
            self._build_project_with_metadata(
                descriptions=[
                    f"{DESCRIPTION_TYPES}/abstract",
                    f"{DESCRIPTION_TYPES}/objectives",
                ],
                dates=[
                    (f"{DATE_TYPES}/start", "2020-01-01"),
                    (f"{DATE_TYPES}/end", "2021-01-01"),
                ],
                identifiers=[
                    (f"{IDENTIFIER_TYPES}/doi", f"10.1234/large-{i}"),
                    (f"{IDENTIFIER_TYPES}/grant-number", f"GRANT-{i}"),
                ],
                keyword_terms=keyword_terms,
            )
            for i in range(3)
        ]
        large_pks = [project.pk for project in large]

        self._touch_all_related(
            Project.objects.with_metadata().filter(pk__in=large_pks)
        )
        with django_assert_num_queries(baseline):
            self._touch_all_related(
                Project.objects.with_metadata().filter(pk__in=large_pks)
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

    def test_dataset_count_is_not_multiplied_by_other_joined_rows(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        DatasetFactory(project=project, visibility=Visibility.PUBLIC)
        ProjectDescriptionFactory(
            related=project, type_id=f"{DESCRIPTION_TYPES}/abstract"
        )

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
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/objectives",
            value="Not the abstract.",
        )

        assert project.get_abstract_summary() == ""

    def test_summary_strips_markdown_headings_and_emphasis(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
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
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="## Background\n\nBorehole temperature logs were collected.",
        )

        summary = project.get_abstract_summary()

        assert "Background Borehole" not in summary
        assert summary == "Background — Borehole temperature logs were collected."

    def test_summary_carries_no_html_tags(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
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
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Rock & roll geochemistry",
        )

        summary = project.get_abstract_summary()

        assert "&amp;" not in summary
        assert "Rock & roll geochemistry" in summary

    def test_summary_collapses_whitespace_left_by_block_markup(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="First paragraph.\n\nSecond paragraph.\n\n- item one\n- item two",
        )

        summary = project.get_abstract_summary()

        assert "\n" not in summary
        assert "  " not in summary
        assert summary.startswith("First paragraph.")

    def test_a_long_summary_is_capped_at_400_characters_and_ends_with_an_ellipsis(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="word " * 300,
        )

        summary = project.get_abstract_summary()

        assert len(summary) <= 400
        assert summary.endswith("…")

    def test_a_short_summary_is_returned_whole_and_untruncated(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="A short abstract.",
        )

        assert project.get_abstract_summary() == "A short abstract."

    def test_summary_does_not_execute_or_retain_embedded_script(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="Safe prose. <script>alert(1)</script>",
        )

        summary = project.get_abstract_summary()

        assert "alert(1)" not in summary
        assert "script" not in summary
        assert "Safe prose." in summary


@pytest.mark.django_db
class TestProjectMetaDescription:
    # `get_meta_description()` once read an attribute `AbstractDescription` does not
    # declare (#331).
    def test_returns_the_abstracts_text_when_one_exists(self):
        project = ProjectFactory()
        ProjectDescriptionFactory(
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="A concise summary.",
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

    def test_a_project_in_any_other_status_is_not_active(self):
        project = ProjectFactory(status=ProjectStatus.COMPLETE)

        assert project.is_active is False


@pytest.mark.django_db
class TestProjectSpatialCoverage:
    """AS 2.11 and FR-023: the box holds the locations of the datasets the viewer may open."""

    @staticmethod
    def at(longitude, latitude):
        return Point(longitude, latitude, srid=4326)

    def test_it_holds_the_locations_of_every_dataset_in_the_project(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        first = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        second = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=first, location=self.at(10.0, 10.0))
        sample = RockSampleFactory(dataset=second, location=self.at(30.0, -5.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=second, location=self.at(-20.0, 40.0)
        )

        found = project.spatial_coverage()

        assert found == Coverage(west=-20.0, south=-5.0, east=30.0, north=40.0)

    def test_a_measurement_placed_by_a_sample_in_another_project_widens_the_box(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        elsewhere = DatasetFactory(
            project=ProjectFactory(visibility=Visibility.PUBLIC),
            visibility=Visibility.PUBLIC,
            published=True,
        )
        distant = RockSampleFactory(dataset=elsewhere, location=self.at(50.0, 40.0))
        ExampleMeasurementFactory(sample=distant, dataset=dataset)

        assert project.spatial_coverage() == Coverage(10.0, 10.0, 50.0, 40.0)

    def test_it_is_none_when_nothing_is_located(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=dataset)

        assert project.spatial_coverage() is None

    def test_another_projects_datasets_are_not_counted(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        RockSampleFactory(
            dataset=DatasetFactory(
                project=ProjectFactory(visibility=Visibility.PUBLIC),
                visibility=Visibility.PUBLIC,
                published=True,
            ),
            location=self.at(10.0, 10.0),
        )

        assert project.spatial_coverage() is None

    def test_a_dataset_the_viewer_may_not_open_is_not_counted(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        open_dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        private = DatasetFactory(
            project=project, visibility=Visibility.PRIVATE, published=True
        )
        RockSampleFactory(dataset=open_dataset, location=self.at(10.0, 10.0))
        RockSampleFactory(dataset=private, location=self.at(50.0, 50.0))
        stranger = PersonFactory(is_active=True)

        for viewer in (None, AnonymousUser(), stranger):
            assert project.spatial_coverage(viewer) == Coverage(10.0, 10.0, 10.0, 10.0)

    def test_a_private_project_counts_nothing_for_someone_with_no_level_on_it(self):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        dataset = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=dataset, location=self.at(10.0, 10.0))
        stranger = PersonFactory(is_active=True)

        for viewer in (None, AnonymousUser(), stranger):
            assert project.spatial_coverage(viewer) is None

    def test_a_member_of_a_private_dataset_counts_it(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        private = DatasetFactory(
            project=project, visibility=Visibility.PRIVATE, published=False
        )
        RockSampleFactory(dataset=private, location=self.at(50.0, 50.0))
        member = PersonFactory(is_active=True)
        ContributionFactory(
            content_object=private, contributor=member, level=ContributionLevel.VIEW
        )

        assert project.spatial_coverage(member) == Coverage(50.0, 50.0, 50.0, 50.0)
        assert project.spatial_coverage() is None

    def test_a_measurement_placed_only_by_a_hidden_sample_adds_nothing(self):
        project = ProjectFactory(visibility=Visibility.PUBLIC)
        hidden = DatasetFactory(
            project=project, visibility=Visibility.PRIVATE, published=False
        )
        released = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        sample = RockSampleFactory(dataset=hidden, location=self.at(10.0, 10.0))
        ExampleMeasurementFactory(sample=sample, dataset=released)

        assert project.spatial_coverage() is None

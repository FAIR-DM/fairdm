"""
Integration tests for project metadata workflows.

Tests the complete workflow of adding descriptions, dates, and identifiers
to projects, including database interactions and related model coordination.

Test-First Approach (Red-Green-Refactor):
1. Write tests that FAIL (Red)
2. Implement minimal code to pass (Green)
3. Refactor for quality (Refactor)
"""

import pytest

from fairdm.core.choices import ProjectStatus
from fairdm.utils.choices import Visibility


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
            name="Research Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
        )

        # Add Abstract description
        ProjectDescription.objects.create(
            related=project, type="Abstract", value="This project studies the impact of X on Y using Z methodology."
        )

        # Add Methods description
        ProjectDescription.objects.create(
            related=project, type="Methods", value="We collected samples from 10 sites and analyzed them using XRF."
        )

        # Verify both descriptions exist
        descriptions = project.descriptions.all()
        assert descriptions.count() == 2

        # Verify types are different
        types = [d.type for d in descriptions]
        assert "Abstract" in types
        assert "Methods" in types

        # Verify content is correct
        abstract_desc = project.descriptions.get(type="Abstract")
        assert "impact of X on Y" in abstract_desc.value

        methods_desc = project.descriptions.get(type="Methods")
        assert "XRF" in methods_desc.value


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
            name="Time-Bound Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
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
            name="Funded Project", status=ProjectStatus.IN_PROGRESS, visibility=Visibility.PUBLIC, owner=owner
        )

        # Add ISNI identifier
        ProjectIdentifier.objects.create(related=project, type="ISNI", value="0000 0001 2283 4400")

        # Add Crossref Funder ID (like a grant number)
        ProjectIdentifier.objects.create(
            related=project, type="CROSSREF_FUNDER_ID", value="https://doi.org/10.13039/100000001"
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

"""Integration tests for Project admin interface workflows."""

import json

import pytest
from django.urls import reverse

from fairdm.core.choices import ProjectStatus
from fairdm.core.project.models import (
    ProjectDate,
    ProjectDescription,
    ProjectIdentifier,
)
from fairdm.factories import (
    OrganizationFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)


@pytest.mark.django_db
class TestAdminSearchByName:
    """Test admin search functionality by project name."""

    def test_search_by_exact_name(self, admin_client):
        """Test searching for project by exact name match."""
        # Create test projects
        ProjectFactory(name="Climate Research Study")
        ProjectFactory(name="Ocean Temperature Analysis")
        ProjectFactory(name="Solar Energy Project")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Climate Research Study"})

        assert response.status_code == 200
        # Project should be in results
        content = response.content.decode()
        assert "Climate Research Study" in content
        assert "Ocean Temperature" not in content or "no results" in content.lower()

    def test_search_by_partial_name(self, admin_client):
        """Test searching for project by partial name match."""
        ProjectFactory(name="Climate Research Study")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Research"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Study" in content

    def test_search_by_uuid(self, admin_client):
        """Test searching for project by UUID."""
        project1 = ProjectFactory(name="Climate Research Study")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": project1.uuid})

        assert response.status_code == 200
        content = response.content.decode()
        assert project1.name in content

    def test_search_by_external_identifier(self, admin_client):
        """FR-019: an external identifier attached to a project finds it."""
        project = ProjectFactory(name="Climate Research Study")
        ProjectIdentifierFactory(
            related=project, type="DOI", value="10.1234/climate-example"
        )

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "10.1234/climate-example"})

        assert response.status_code == 200
        content = response.content.decode()
        assert project.name in content

    def test_search_by_owning_organisation(self, admin_client):
        """FR-019: a project's owning organisation name finds it."""
        owner = OrganizationFactory(name="Example Research Institute")
        project = ProjectFactory(name="Climate Research Study", owner=owner)

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Example Research Institute"})

        assert response.status_code == 200
        content = response.content.decode()
        assert project.name in content


@pytest.mark.django_db
class TestAdminFilterByStatus:
    """Test admin filtering by project status."""

    def test_filter_by_concept_status(self, admin_client):
        """Test filtering projects by concept status."""
        # Create projects with different statuses
        ProjectFactory(name="Concept Project", status=0)
        ProjectFactory(name="Active Project", status=1)
        ProjectFactory(name="Completed Project", status=2)

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"status__exact": "0"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Concept Project" in content
        # Other projects should not be in filtered results
        assert "Active Project" not in content or "no results" in content.lower()

    def test_filter_by_visibility(self, admin_client):
        """Test filtering projects by visibility."""
        from fairdm.utils.choices import Visibility

        ProjectFactory(name="Public Project", visibility=Visibility.PUBLIC)
        ProjectFactory(name="Private Project", visibility=Visibility.PRIVATE)

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(
            url, {"visibility__exact": str(Visibility.PUBLIC.value)}
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert "Public Project" in content

    def test_filter_by_added_date(self, admin_client):
        """Test filtering projects by date added."""
        concept_project = ProjectFactory(name="Concept Project", status=0)

        url = reverse("admin:project_project_changelist")

        # Filter by "today" (projects added today)
        from django.utils import timezone

        today = timezone.now().date()
        response = admin_client.get(
            url, {"added__year": str(today.year), "added__month": str(today.month)}
        )

        assert response.status_code == 200
        # All test projects were created today, should all be present
        content = response.content.decode()
        assert concept_project.name in content


@pytest.mark.django_db
class TestAdminInlineEditing:
    """Test admin inline editing of project descriptions."""

    def test_inline_description_shown_in_change_form(self, admin_client):
        """Test that description inline is displayed in project change form."""
        project = ProjectFactory(name="Test Project")
        url = reverse("admin:project_project_change", args=[project.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Look for inline formset elements
        assert (
            "projectdescription" in content.lower() or "description" in content.lower()
        )

    def test_can_add_description_via_inline(self, admin_client):
        """Test adding a description through inline form."""
        project = ProjectFactory(name="Test Project")
        url = reverse("admin:project_project_change", args=[project.pk])

        # Prepare inline form data
        form_data = {
            "name": project.name,
            "status": project.status,
            "visibility": project.visibility,
            # Inline formset management form (uses default_related_name from Meta)
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            # First inline form
            "descriptions-0-related": project.pk,
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
            # Date inline (empty - but management form required)
            "dates-TOTAL_FORMS": "0",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            # Identifier inline (empty - but management form required)
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        # Debug: Check for form errors
        if response.status_code == 200:
            # Form had validation errors - stayed on the same page
            content = response.content.decode()
            if "error" in content.lower():
                print("\n=== FORM ERRORS DETECTED (PROJECT TEST) ===")
                # Extract error messages for debugging
                import re

                errors = re.findall(
                    r'<ul class="errorlist[^>]*">.*?</ul>', content, re.DOTALL
                )
                for error in errors:
                    print(error)

        # Should redirect or show success
        assert response.status_code in [200, 302]

        # Check that description was created
        descriptions = ProjectDescription.objects.filter(related=project)
        assert descriptions.count() > 0, (
            f"Expected descriptions to be created, but found {descriptions.count()}"
        )

    def test_can_add_description_date_and_identifier_via_inline(self, admin_client):
        """FR-020: a description, a date and an identifier added inline all persist.

        Covers acceptance scenario US-6.3 in full - the earlier test only
        exercises the description inline.
        """
        project = ProjectFactory(name="Test Project")
        url = reverse("admin:project_project_change", args=[project.pk])

        form_data = {
            "name": project.name,
            "status": project.status,
            "visibility": project.visibility,
            "descriptions-TOTAL_FORMS": "1",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "descriptions-0-related": project.pk,
            "descriptions-0-type": "Abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
            "dates-TOTAL_FORMS": "1",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": project.pk,
            "dates-0-type": "Start",
            "dates-0-value": "2024-06-01",
            "identifiers-TOTAL_FORMS": "1",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "identifiers-0-related": project.pk,
            "identifiers-0-type": "DOI",
            "identifiers-0-value": "10.1234/inline-test",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code in [200, 302]

        assert ProjectDescription.objects.filter(
            related=project, type="Abstract"
        ).exists()
        assert ProjectDate.objects.filter(related=project, type="Start").exists()
        assert ProjectIdentifier.objects.filter(
            related=project, type="DOI", value="10.1234/inline-test"
        ).exists()


@pytest.mark.django_db
class TestAdminListDisplayColumns:
    """Test admin list columns showing abstract and start-date presence (FR-021)."""

    def test_columns_reflect_presence_and_absence_of_abstract_and_start_date(
        self, admin_client
    ):
        with_both = ProjectFactory(name="Fully Described Project")
        ProjectDate.objects.create(related=with_both, type="Start", value="2024-01-01")
        ProjectDescription.objects.create(
            related=with_both, type="Abstract", value="An abstract."
        )
        without_either = ProjectFactory(name="Bare Project")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200

        from django.contrib.admin.sites import AdminSite

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        admin_instance = ProjectAdmin(Project, AdminSite())
        assert admin_instance.has_abstract(with_both) is True
        assert admin_instance.has_start_date(with_both) is True
        assert admin_instance.has_abstract(without_either) is False
        assert admin_instance.has_start_date(without_either) is False


@pytest.mark.django_db
class TestAdminBulkStatusChange:
    """Test admin bulk status change operation."""

    def test_bulk_status_change_action_appears_in_ui(self, admin_client):
        """Test that bulk status change action appears in admin UI."""
        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        # Check for action dropdown or bulk action elements
        assert "action" in content.lower()

    @pytest.mark.parametrize(
        ("action", "expected_status"),
        [
            ("make_concept", ProjectStatus.CONCEPT),
            ("make_active", ProjectStatus.IN_PROGRESS),
            ("make_completed", ProjectStatus.COMPLETE),
        ],
    )
    def test_bulk_status_change_sets_the_status_its_label_names(
        self, admin_client, action, expected_status
    ):
        """FR-022/SC-008: every bulk status action leaves the selected projects
        in the status its label names.

        Rewritten from a test that only asserted a 200 response and never
        checked any project's status, which is why `make_active` and
        `make_completed` previously wrote the wrong status without failing.
        """
        # Start every project at PLANNING, which differs from all three
        # target statuses, so a no-op or a wrong-status write is caught.
        projects = ProjectFactory.create_batch(3, status=ProjectStatus.PLANNING)

        url = reverse("admin:project_project_changelist")

        form_data = {
            "action": action,
            "_selected_action": [str(p.pk) for p in projects],
            "index": "0",
        }

        response = admin_client.post(url, data=form_data, follow=True)

        assert response.status_code == 200
        for project in projects:
            project.refresh_from_db()
            assert project.status == expected_status


@pytest.mark.django_db
class TestAdminExportActions:
    """FR-026: export is available over a selection of several projects."""

    @pytest.mark.parametrize(
        ("action", "name_of"),
        [
            ("export_json", lambda record: record["name"]),
            ("export_datacite", lambda record: record["titles"][0]["title"]),
        ],
    )
    def test_export_over_a_selection_carries_every_selected_project(
        self, admin_client, action, name_of
    ):
        """T046: exporting several projects together produces output carrying
        all of them."""
        projects = ProjectFactory.create_batch(3, funding=None)

        url = reverse("admin:project_project_changelist")
        form_data = {
            "action": action,
            "_selected_action": [str(p.pk) for p in projects],
            "index": "0",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 200
        records = json.loads(response.content)
        assert len(records) == len(projects)
        exported_names = {name_of(record) for record in records}
        assert exported_names == {p.name for p in projects}

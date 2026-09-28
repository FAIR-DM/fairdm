"""Integration tests for the project admin."""

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
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)
from fairdm.factories.core import ProjectDateFactory


@pytest.mark.django_db
class TestAdminSearchByName:
    def test_search_by_exact_name(self, admin_client):
        ProjectFactory(name="Climate Research Study")
        ProjectFactory(name="Ocean Temperature Analysis")
        ProjectFactory(name="Solar Energy Project")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Climate Research Study"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Study" in content
        assert "Ocean Temperature" not in content or "no results" in content.lower()

    def test_search_by_partial_name(self, admin_client):
        ProjectFactory(name="Climate Research Study")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Research"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Climate Research Study" in content

    def test_search_by_uuid(self, admin_client):
        project1 = ProjectFactory(name="Climate Research Study")

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": project1.uuid})

        assert response.status_code == 200
        content = response.content.decode()
        assert project1.name in content

    def test_search_by_external_identifier(self, admin_client):
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
        owner = OrganizationFactory(name="Example Research Institute")
        project = ProjectFactory(name="Climate Research Study", owner=owner)

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"q": "Example Research Institute"})

        assert response.status_code == 200
        content = response.content.decode()
        assert project.name in content


@pytest.mark.django_db
class TestAdminFilterByStatus:
    def test_filter_by_concept_status(self, admin_client):
        ProjectFactory(name="Concept Project", status=0)
        ProjectFactory(name="Active Project", status=1)
        ProjectFactory(name="Completed Project", status=2)

        url = reverse("admin:project_project_changelist")
        response = admin_client.get(url, {"status__exact": "0"})

        assert response.status_code == 200
        content = response.content.decode()
        assert "Concept Project" in content
        assert "Active Project" not in content or "no results" in content.lower()

    def test_filter_by_visibility(self, admin_client):
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
        concept_project = ProjectFactory(name="Concept Project", status=0)

        url = reverse("admin:project_project_changelist")

        from django.utils import timezone

        today = timezone.now().date()
        response = admin_client.get(
            url, {"added__year": str(today.year), "added__month": str(today.month)}
        )

        assert response.status_code == 200
        content = response.content.decode()
        assert concept_project.name in content


@pytest.mark.django_db
class TestAdminInlineEditing:
    def test_inline_description_shown_in_change_form(self, admin_client):
        project = ProjectFactory(name="Test Project")
        url = reverse("admin:project_project_change", args=[project.pk])
        response = admin_client.get(url)

        assert response.status_code == 200
        content = response.content.decode()
        assert 'name="descriptions-TOTAL_FORMS"' in content

    def test_can_add_description_via_inline(self, admin_client):
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
            # Empty inline formsets still need their management forms.
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
        descriptions = ProjectDescription.objects.filter(related=project)
        assert descriptions.count() > 0, (
            f"Expected descriptions to be created, but found {descriptions.count()}"
        )

    def test_can_add_description_date_and_identifier_via_inline(self, admin_client):
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
class TestAdminDateInlineOrdering:
    # `ProjectDate.clean()` looks its sibling up in the database, so two new dates in
    # one submission never see each other unless the formset checks the pair itself.
    def test_posting_backwards_start_and_end_together_is_refused(self, admin_client):
        project = ProjectFactory(name="Backwards Timeline Project")
        url = reverse("admin:project_project_change", args=[project.pk])

        form_data = {
            "name": project.name,
            "status": project.status,
            "visibility": project.visibility,
            "descriptions-TOTAL_FORMS": "0",
            "descriptions-INITIAL_FORMS": "0",
            "descriptions-MIN_NUM_FORMS": "0",
            "descriptions-MAX_NUM_FORMS": "1000",
            "dates-TOTAL_FORMS": "2",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": project.pk,
            "dates-0-type": "Start",
            "dates-0-value": "2020-06-01",
            "dates-1-related": project.pk,
            "dates-1-type": "End",
            "dates-1-value": "2010-01-01",
            "identifiers-TOTAL_FORMS": "0",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 200
        assert not ProjectDate.objects.filter(related=project).exists()


@pytest.mark.django_db
class TestAdminListDisplayColumns:
    def test_columns_reflect_presence_and_absence_of_abstract_and_start_date(
        self, admin_client, rf
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
        queryset = admin_instance.get_queryset(rf.get(url))
        with_both = queryset.get(pk=with_both.pk)
        without_either = queryset.get(pk=without_either.pk)
        assert admin_instance.has_abstract(with_both) is True
        assert admin_instance.has_start_date(with_both) is True
        assert admin_instance.has_abstract(without_either) is False
        assert admin_instance.has_start_date(without_either) is False


@pytest.mark.django_db
class TestAdminListDisplayColumnsQueryCount:
    def test_flags_are_annotated_without_a_query_per_row(
        self, rf, django_assert_num_queries
    ):
        from django.contrib.admin.sites import AdminSite

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        for _ in range(5):
            project = ProjectFactory()
            ProjectDate.objects.create(
                related=project, type="Start", value="2024-01-01"
            )
            ProjectDescription.objects.create(
                related=project, type="Abstract", value="An abstract."
            )
        ProjectFactory()  # a row with neither, so both flags read False

        admin_instance = ProjectAdmin(Project, AdminSite())
        request = rf.get("/")
        queryset = admin_instance.get_queryset(request)

        with django_assert_num_queries(1):
            for obj in queryset:
                admin_instance.has_abstract(obj)
                admin_instance.has_start_date(obj)


@pytest.mark.django_db
class TestAdminBulkStatusChange:
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
        # PLANNING differs from every target status, so a no-op write is caught.
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


@pytest.mark.django_db
class TestAdminExportActionsQueryCount:
    # Counted by table: each contributor's own representation still queries per
    # contributor.
    @staticmethod
    def _build_project_with_full_metadata():
        project = ProjectFactory(
            funding=[{"funderName": "Sample Agency", "awardNumber": "GRANT-1"}]
        )
        ProjectDescriptionFactory(
            related=project, type="Abstract", value="An abstract."
        )
        ProjectDateFactory(related=project, type="Start", value="2020-01-01")
        ProjectIdentifierFactory(
            related=project, type="DOI", value=f"10.1234/{project.pk}"
        )
        project.add_contributor(PersonFactory(), with_roles=["Creator"])
        return project

    @pytest.mark.parametrize("action", ["export_json", "export_datacite"])
    def test_export_action_fetches_each_named_relation_once_for_the_selection(
        self, action
    ):
        from django.contrib.admin.sites import AdminSite
        from django.db import connection
        from django.test import RequestFactory
        from django.test.utils import CaptureQueriesContext

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        admin_instance = ProjectAdmin(Project, AdminSite())
        action_method = getattr(admin_instance, action)
        request = RequestFactory().post("/")

        projects = [self._build_project_with_full_metadata() for _ in range(3)]

        with CaptureQueriesContext(connection) as context:
            action_method(
                request, Project.objects.filter(pk__in=[p.pk for p in projects])
            )

        def query_count(table):
            return sum(1 for query in context.captured_queries if table in query["sql"])

        assert query_count("project_projectdescription") == 1
        assert query_count("project_projectdate") == 1
        assert query_count("project_projectidentifier") == 1
        assert query_count("contributors_contribution_roles") == 1

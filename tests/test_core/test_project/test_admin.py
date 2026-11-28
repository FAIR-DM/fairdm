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
from fairdm.core.vocabularies import (
    CONTRIBUTOR_ROLES,
    DATE_TYPES,
    DESCRIPTION_TYPES,
    IDENTIFIER_TYPES,
)
from fairdm.factories import (
    PersonFactory,
    ProjectDescriptionFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
)
from fairdm.factories.core import ProjectDateFactory


@pytest.mark.django_db
class TestAdminSearch:
    def test_the_search_matches_the_name_and_an_identifier_of_the_project(self, rf):
        from django.contrib.admin.sites import AdminSite

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        climate = ProjectFactory(name="Climate Research Study")
        ProjectIdentifierFactory(
            related=climate,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1234/climate-example",
        )
        ocean = ProjectFactory(name="Ocean Temperature Analysis")
        admin_instance = ProjectAdmin(Project, AdminSite())
        request = rf.get("/")

        def found(term):
            queryset, _ = admin_instance.get_search_results(
                request, Project.objects.all(), term
            )
            return set(queryset)

        assert found("Climate") == {climate}
        assert found("10.1234/climate-example") == {climate}
        assert found("Ocean") == {ocean}


@pytest.mark.django_db
class TestAdminInlineEditing:
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
            "descriptions-0-type": f"{DESCRIPTION_TYPES}/abstract",
            "descriptions-0-value": "This is a test description added via inline form.",
            "dates-TOTAL_FORMS": "1",
            "dates-INITIAL_FORMS": "0",
            "dates-MIN_NUM_FORMS": "0",
            "dates-MAX_NUM_FORMS": "1000",
            "dates-0-related": project.pk,
            "dates-0-type": f"{DATE_TYPES}/start",
            "dates-0-value": "2024-06-01",
            "identifiers-TOTAL_FORMS": "1",
            "identifiers-INITIAL_FORMS": "0",
            "identifiers-MIN_NUM_FORMS": "0",
            "identifiers-MAX_NUM_FORMS": "1000",
            "identifiers-0-related": project.pk,
            "identifiers-0-type": f"{IDENTIFIER_TYPES}/doi",
            "identifiers-0-value": "10.1234/inline-test",
            "_continue": "Save and continue editing",
        }

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302
        assert ProjectDescription.objects.filter(
            related=project, type_id=f"{DESCRIPTION_TYPES}/abstract"
        ).exists()
        assert ProjectDate.objects.filter(
            related=project, type_id=f"{DATE_TYPES}/start"
        ).exists()
        assert ProjectIdentifier.objects.filter(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value="10.1234/inline-test",
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
            "dates-0-type": f"{DATE_TYPES}/start",
            "dates-0-value": "2020-06-01",
            "dates-1-related": project.pk,
            "dates-1-type": f"{DATE_TYPES}/end",
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
    def test_columns_reflect_presence_and_absence_of_abstract_and_start_date(self, rf):
        with_both = ProjectFactory(name="Fully Described Project")
        ProjectDate.objects.create(
            related=with_both, type_id=f"{DATE_TYPES}/start", value="2024-01-01"
        )
        ProjectDescription.objects.create(
            related=with_both,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="An abstract.",
        )
        without_either = ProjectFactory(name="Bare Project")

        from django.contrib.admin.sites import AdminSite

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        admin_instance = ProjectAdmin(Project, AdminSite())
        queryset = admin_instance.get_queryset(rf.get("/"))
        with_both = queryset.get(pk=with_both.pk)
        without_either = queryset.get(pk=without_either.pk)
        assert admin_instance.has_abstract(with_both) is True
        assert admin_instance.has_start_date(with_both) is True
        assert admin_instance.has_abstract(without_either) is False
        assert admin_instance.has_start_date(without_either) is False


@pytest.mark.django_db
class TestAdminListDisplayColumnsQueryCount:
    def test_flags_are_annotated_without_a_query_per_row(self, rf):
        from django.contrib.admin.sites import AdminSite
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        from fairdm.core.project.admin import ProjectAdmin
        from fairdm.core.project.models import Project

        def add_project_with_abstract_and_start_date():
            project = ProjectFactory()
            ProjectDate.objects.create(
                related=project, type_id=f"{DATE_TYPES}/start", value="2024-01-01"
            )
            ProjectDescription.objects.create(
                related=project,
                type_id=f"{DESCRIPTION_TYPES}/abstract",
                value="An abstract.",
            )

        admin_instance = ProjectAdmin(Project, AdminSite())

        def queries_to_read_the_flags():
            queryset = admin_instance.get_queryset(rf.get("/"))
            with CaptureQueriesContext(connection) as context:
                for obj in queryset:
                    admin_instance.has_abstract(obj)
                    admin_instance.has_start_date(obj)
            return len(context.captured_queries)

        add_project_with_abstract_and_start_date()
        queries_to_read_the_flags()  # warm one-time caches
        one_row = queries_to_read_the_flags()

        add_project_with_abstract_and_start_date()
        ProjectFactory()  # a row with neither, so both flags read False
        three_rows = queries_to_read_the_flags()

        assert three_rows == one_row


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

        response = admin_client.post(url, data=form_data)

        assert response.status_code == 302
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
            related=project,
            type_id=f"{DESCRIPTION_TYPES}/abstract",
            value="An abstract.",
        )
        ProjectDateFactory(
            related=project, type_id=f"{DATE_TYPES}/start", value="2020-01-01"
        )
        ProjectIdentifierFactory(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/doi",
            value=f"10.1234/{project.pk}",
        )
        project.add_contributor(
            PersonFactory(), with_roles=[f"{CONTRIBUTOR_ROLES}/creator"]
        )
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

"""Integration tests for FairDM base view classes in ``fairdm/views/base.py``."""

import django_tables2 as tables
import pytest
from django.contrib.auth.models import AnonymousUser

from fairdm.core.models import Project
from fairdm.factories import ProjectFactory
from fairdm.views.base import (
    FairDMCreateView,
    FairDMDeleteView,
    FairDMDetailView,
    FairDMListView,
    FairDMTableView,
    FairDMTemplateView,
    FairDMUpdateView,
)


class ConcreteTemplateView(FairDMTemplateView):
    """Minimal TemplateView subclass for testing."""

    template_name = "page_view.html"


class ConcreteListView(FairDMListView):
    """Minimal ListView subclass using the Project model."""

    model = Project
    # Stop django_filters generating a filterset from every Project field, which includes
    # ThumbnailerImageField, an unsupported type.
    filterset_fields = []


class ConcreteDetailView(FairDMDetailView):
    """Minimal DetailView subclass using the Project model."""

    model = Project


class ConcreteCreateView(FairDMCreateView):
    """Minimal CreateView subclass using the Project model."""

    model = Project
    fields = ["name", "status", "visibility"]
    success_url = "/"


class ConcreteUpdateView(FairDMUpdateView):
    """Minimal UpdateView subclass using the Project model."""

    model = Project
    fields = ["name", "status", "visibility"]
    success_url = "/"


class ConcreteDeleteView(FairDMDeleteView):
    """Minimal DeleteView subclass using the Project model."""

    model = Project
    success_url = "/"


class _ProjectTable(tables.Table):
    """Minimal django-tables2 table for testing FairDMTableView."""

    class Meta:
        model = Project
        fields = ["name"]


class ConcreteTableView(FairDMTableView):
    """Minimal TableView subclass using the Project model."""

    model = Project
    table_class = _ProjectTable
    # See ConcreteListView for why this is needed.
    filterset_fields = []


@pytest.mark.django_db
class TestFairDMBaseViews:
    def test_every_base_view_renders_and_carries_the_page_meta(self, rf, user):
        project = ProjectFactory()
        views = {
            "template": (ConcreteTemplateView, {}, None),
            "list": (ConcreteListView, {}, None),
            "table": (ConcreteTableView, {}, None),
            "detail": (ConcreteDetailView, {"pk": project.pk}, None),
            "create": (ConcreteCreateView, {}, user),
            "update": (ConcreteUpdateView, {"pk": project.pk}, user),
            "delete": (ConcreteDeleteView, {"pk": project.pk}, user),
        }

        failed = []
        for name, (view, kwargs, person) in views.items():
            request = rf.get("/")
            request.user = person or AnonymousUser()
            response = view.as_view()(request, **kwargs)
            if response.status_code != 200:
                failed.append(f"{name}: status {response.status_code}")
            elif "meta" not in response.context_data:
                failed.append(f"{name}: no meta in the context")

        assert not failed, "\n".join(failed)


@pytest.mark.django_db
class TestFairDMListView:
    def test_grid_config_context_key_present(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteListView.as_view()(request)
        assert "grid_config" in response.context_data

    def test_a_core_record_list_leads_its_trail_with_the_types_icon(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        view = ConcreteListView()
        view.setup(request)
        assert view.get_breadcrumbs()[0]["icon"] == "project"


@pytest.mark.django_db
class TestFairDMTableViewPagination:
    def test_a_subclass_that_declares_no_page_size_pages_at_100(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()

        response = ConcreteTableView.as_view()(request)

        table = response.context_data["table"]
        assert table.paginator is not None
        assert table.paginator.per_page == 100

"""Integration tests for FairDM base view classes in ``fairdm/views/base.py``.

Each test class exercises one FairDM view by instantiating a minimal concrete
subclass via Django's ``RequestFactory``.  Tests verify:

- HTTP 200 responses (checked on the lazily-rendered ``TemplateResponse``
  before the template is actually rendered, so no template-engine dependencies
  are introduced here)
- ``meta`` context key injected by ``MetadataMixin``
- View-specific context keys documented in each class docstring
  (``grid_config``, ``form``, ``object``, ``table``, ``filter``)

Fixtures ``rf`` (RequestFactory) and ``user`` / ``authenticated_client`` come
from pytest-django and the project's root ``conftest.py`` respectively.
"""

import django_tables2 as tables
import pytest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add_messages(request):
    """Attach a message storage to *request* so SuccessMessageMixin works."""
    request.session = "session"
    storage = FallbackStorage(request)
    request._messages = storage


# ---------------------------------------------------------------------------
# Minimal concrete subclasses (defined once, shared across test classes)
# ---------------------------------------------------------------------------


class ConcreteTemplateView(FairDMTemplateView):
    """Minimal TemplateView subclass for testing."""

    template_name = "page_view.html"


class ConcreteListView(FairDMListView):
    """Minimal ListView subclass using the Project model."""

    model = Project
    # Prevent django_filters from auto-generating a filterset from all Project
    # fields (which includes ThumbnailerImageField, an unsupported type).
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


# ---------------------------------------------------------------------------
# TestFairDMTemplateView (T018)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMTemplateView:
    """Tests for FairDMTemplateView."""

    def test_get_returns_200(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteTemplateView.as_view()(request)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteTemplateView.as_view()(request)
        assert "meta" in response.context_data


# ---------------------------------------------------------------------------
# TestFairDMListView (T019)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMListView:
    """Tests for FairDMListView."""

    def test_get_returns_200(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteListView.as_view()(request)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteListView.as_view()(request)
        assert "meta" in response.context_data

    def test_grid_config_context_key_present(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteListView.as_view()(request)
        assert "grid_config" in response.context_data


# ---------------------------------------------------------------------------
# TestFairDMDetailView (T020)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMDetailView:
    """Tests for FairDMDetailView."""

    def test_get_returns_200(self, rf):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteDetailView.as_view()(request, pk=project.pk)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteDetailView.as_view()(request, pk=project.pk)
        assert "meta" in response.context_data

    def test_object_in_context(self, rf):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteDetailView.as_view()(request, pk=project.pk)
        assert response.context_data["object"] == project


# ---------------------------------------------------------------------------
# TestFairDMCreateView (T021)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMCreateView:
    """Tests for FairDMCreateView."""

    def test_get_returns_200(self, rf, user):
        request = rf.get("/")
        request.user = user
        response = ConcreteCreateView.as_view()(request)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf, user):
        request = rf.get("/")
        request.user = user
        response = ConcreteCreateView.as_view()(request)
        assert "meta" in response.context_data

    def test_form_in_context(self, rf, user):
        request = rf.get("/")
        request.user = user
        response = ConcreteCreateView.as_view()(request)
        assert "form" in response.context_data

    def test_post_creates_object_and_redirects(self, rf, user):
        data = {"name": "Integration Test Project", "status": 1, "visibility": 0}
        request = rf.post("/", data)
        request.user = user
        _add_messages(request)
        initial_count = Project.objects.count()
        response = ConcreteCreateView.as_view()(request)
        assert response.status_code == 302
        assert Project.objects.count() == initial_count + 1


# ---------------------------------------------------------------------------
# TestFairDMUpdateView (T022)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMUpdateView:
    """Tests for FairDMUpdateView."""

    def test_get_returns_200(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteUpdateView.as_view()(request, pk=project.pk)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteUpdateView.as_view()(request, pk=project.pk)
        assert "meta" in response.context_data

    def test_form_in_context(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteUpdateView.as_view()(request, pk=project.pk)
        assert "form" in response.context_data

    def test_object_in_context(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteUpdateView.as_view()(request, pk=project.pk)
        assert response.context_data["object"] == project


# ---------------------------------------------------------------------------
# TestFairDMDeleteView (T023)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMDeleteView:
    """Tests for FairDMDeleteView."""

    def test_get_returns_200(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteDeleteView.as_view()(request, pk=project.pk)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteDeleteView.as_view()(request, pk=project.pk)
        assert "meta" in response.context_data

    def test_object_in_context(self, rf, user):
        project = ProjectFactory()
        request = rf.get("/")
        request.user = user
        response = ConcreteDeleteView.as_view()(request, pk=project.pk)
        assert response.context_data["object"] == project


# ---------------------------------------------------------------------------
# TestFairDMTableView (T024)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestFairDMTableView:
    """Tests for FairDMTableView."""

    def test_get_returns_200(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteTableView.as_view()(request)
        assert response.status_code == 200

    def test_meta_context_key_present(self, rf):
        request = rf.get("/")
        request.user = AnonymousUser()
        response = ConcreteTableView.as_view()(request)
        assert "meta" in response.context_data

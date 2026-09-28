"""Tests for the shared refusal-shape mixins."""

import pytest
from django.http import Http404, HttpResponse

from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility


class _StubPermissionRequiredMixin:
    """Stand in for ``PermissionRequiredMixin``."""

    handle_no_permission_called = False

    def handle_no_permission(self):
        self.handle_no_permission_called = True
        return HttpResponse(status=403)


class _StubFairDMDeleteView:
    """Stand in for ``FairDMDeleteView``."""

    def get_back_url_fallback(self) -> str:
        return "/list/"


class _PageWithNoPermissionMixin(
    PrivateRecordNotFoundMixin, _StubPermissionRequiredMixin
):
    registered_model = None

    def __init__(self, base_object):
        self.base_object = base_object


class _PageWithBackFallbackMixin(RecordOwnPageBackFallbackMixin, _StubFairDMDeleteView):
    def __init__(self, base_object):
        self.base_object = base_object


@pytest.mark.django_db
class TestPrivateRecordNotFoundMixin:
    def test_wins_over_permission_required_mixin_in_the_mro(self):
        private = DatasetFactory()
        page = _PageWithNoPermissionMixin(private)

        with pytest.raises(Http404):
            page.handle_no_permission()

        assert page.handle_no_permission_called is False

    def test_a_public_record_falls_through_to_the_stock_behaviour(self):
        public = DatasetFactory(visibility=Visibility.PUBLIC)
        page = _PageWithNoPermissionMixin(public)

        response = page.handle_no_permission()

        assert response.status_code == 403
        assert page.handle_no_permission_called is True

    def test_a_missing_record_falls_through_to_the_stock_behaviour(self):
        page = _PageWithNoPermissionMixin(None)

        response = page.handle_no_permission()

        assert response.status_code == 403
        assert page.handle_no_permission_called is True

    def test_the_404_message_names_the_registered_models_own_kind(self):
        from fairdm.core.project.models import Project

        private = DatasetFactory()
        page = _PageWithNoPermissionMixin(private)
        page.registered_model = Project

        with pytest.raises(Http404, match="No project matches the given query."):
            page.handle_no_permission()

    def test_the_404_message_names_the_dataset_kind_for_a_dataset_page(self):
        from fairdm.core.dataset.models import Dataset

        private = DatasetFactory()
        page = _PageWithNoPermissionMixin(private)
        page.registered_model = Dataset

        with pytest.raises(Http404, match="No dataset matches the given query."):
            page.handle_no_permission()


class TestRecordOwnPageBackFallbackMixin:
    def test_wins_over_fairdm_delete_views_own_fallback_in_the_mro(self):
        class _Record:
            def get_absolute_url(self):
                return "/records/1/"

        page = _PageWithBackFallbackMixin(_Record())

        assert page.get_back_url_fallback() == "/records/1/"

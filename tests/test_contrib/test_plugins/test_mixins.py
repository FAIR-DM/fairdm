"""Tests for the shared refusal-shape mixins (T089).

Source: ``fairdm/contrib/plugins/mixins.py``

Exercised directly against minimal stand-in classes rather than through the dataset
or project pages that consume them: a component built from one consumer's own shape
proves nothing about the other, and the wiring itself is proven by the dataset and
project test suites continuing to pass unchanged (`tests/test_core/test_dataset`,
`tests/test_core/test_project`).
"""

import pytest
from django.http import Http404, HttpResponse

from fairdm.contrib.plugins.mixins import (
    PrivateRecordNotFoundMixin,
    RecordOwnPageBackFallbackMixin,
)
from fairdm.factories import DatasetFactory
from fairdm.utils.choices import Visibility


class _StubPermissionRequiredMixin:
    """Stands in for ``django.contrib.auth.mixins.PermissionRequiredMixin``: any
    class the real mixin sits ahead of in the MRO, so a test can prove the real
    mixin's ``handle_no_permission`` wins without a full view/request cycle."""

    handle_no_permission_called = False

    def handle_no_permission(self):
        self.handle_no_permission_called = True
        return HttpResponse(status=403)


class _StubFairDMDeleteView:
    """Stands in for ``fairdm.views.FairDMDeleteView``, the other class that
    defines ``get_back_url_fallback`` in a real consumer's MRO."""

    def get_back_url_fallback(self) -> str:
        return "/list/"


class _PageWithNoPermissionMixin(PrivateRecordNotFoundMixin, _StubPermissionRequiredMixin):
    registered_model = None

    def __init__(self, base_object):
        self.base_object = base_object


class _PageWithBackFallbackMixin(RecordOwnPageBackFallbackMixin, _StubFairDMDeleteView):
    def __init__(self, base_object):
        self.base_object = base_object


@pytest.mark.django_db
class TestPrivateRecordNotFoundMixin:
    def test_wins_over_permission_required_mixin_in_the_mro(self):
        """The mixin must be listed ahead of the class supplying the stock
        ``handle_no_permission`` for its override to take effect at all - proven here
        rather than trusted, per the story's own instruction."""
        private = DatasetFactory()  # private, per the model default
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
        """``base_object`` is ``None`` when the plugin's own lookup already raised - not
        this mixin's concern, so it defers rather than raising a second 404 of its own."""
        page = _PageWithNoPermissionMixin(None)

        response = page.handle_no_permission()

        assert response.status_code == 403
        assert page.handle_no_permission_called is True

    def test_the_404_message_names_the_registered_models_own_kind(self):
        """T090's requirement in miniature: a project's page must not say 'dataset', and
        vice versa - proven generically here by parameterising the stand-in's own
        ``registered_model`` rather than by any one consumer's wiring."""
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

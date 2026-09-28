"""Access control on the sample record's editing surfaces."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from fairdm.contrib.plugins.access import can_open
from fairdm.core.sample.plugins import Descriptions, Edit, KeyDates, Keywords, Overview
from fairdm.core.utils import assign_perm

EDITING_PLUGINS = [Edit, Descriptions, Keywords, KeyDates]


def _request_for(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestSampleWritePluginsAreGated:
    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_anonymous_request_is_refused(self, plugin_class, rock_sample):
        request = _request_for(AnonymousUser())
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_signed_in_user_with_no_rights_is_refused(
        self, plugin_class, rock_sample, user
    ):
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_user_holding_dataset_change_rights_is_admitted(
        self, plugin_class, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is True

    def test_the_reading_surface_stays_open_for_a_user_with_no_rights(
        self, rock_sample, user
    ):
        request = _request_for(user)
        assert can_open(Overview, request, rock_sample) is True

    def test_the_reading_surface_stays_open_for_an_anonymous_request(self, rock_sample):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, rock_sample) is True


@pytest.mark.django_db
class TestPermissionStillGatesEvenWithAnAlwaysTruePredicate:
    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    # A truthy-but-not-callable `check` is treated by can_open as no gate at all, so
    # permission alone must still refuse an anonymous request.
    def test_an_always_true_predicate_does_not_reopen_the_surface(
        self, plugin_class, rock_sample
    ):
        always_open = type(
            f"AlwaysOpen{plugin_class.__name__}",
            (plugin_class,),
            {"check": staticmethod(lambda request, obj: True)},
        )
        request = _request_for(AnonymousUser())

        assert can_open(always_open, request, rock_sample) is False


@pytest.mark.django_db
class TestDescriptionsAndKeyDatesRenderTheirOwnForm:
    # Both pages return 200 even when InlineFormSetView silently falls back to the
    # sample's detail template, so status alone never caught it (#280).
    def test_descriptions_page_renders_the_descriptions_form_not_the_detail_page(
        self, client, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        client.force_login(user)

        response = client.get(
            reverse("sample:basic-information", kwargs={"uuid": rock_sample.uuid})
        )

        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/descriptions.html" in template_names
        assert "sample/sample_detail.html" not in template_names
        assert 'id="descriptions-form"' in response.content.decode()

    def test_key_dates_page_renders_the_key_dates_form_not_the_detail_page(
        self, client, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        client.force_login(user)

        response = client.get(
            reverse("sample:key-dates", kwargs={"uuid": rock_sample.uuid})
        )

        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/key-dates.html" in template_names
        assert "sample/sample_detail.html" not in template_names
        content = response.content.decode()
        assert "key-dates-form" in content

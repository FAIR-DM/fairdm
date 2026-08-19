"""Access control on the sample record's editing surfaces.

FR-033a: a plugin declaring no required right is opened for every request, anonymous included.
The four management plugins on ``Sample`` used to carry an unconditional ``check`` predicate that
masked this; this file proves the closed state and guards against the predicate's return.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from fairdm.contrib.plugins.access import can_open, resolve_check
from fairdm.core.sample.plugins import Descriptions, Edit, KeyDates, Keywords, Overview
from fairdm.core.utils import assign_perm

EDITING_PLUGINS = [Edit, Descriptions, Keywords, KeyDates]


def _request_for(user):
    request = RequestFactory().get("/")
    request.user = user
    return request


@pytest.mark.django_db
class TestSampleWritePluginsAreGated:
    """Every editing surface registered against a specimen refuses an anonymous request and a
    signed-in user with no rights, and admits a user holding change rights on the parent
    dataset. The reading surface stays open."""

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_anonymous_request_is_refused(self, plugin_class, rock_sample):
        request = _request_for(AnonymousUser())
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_signed_in_user_with_no_rights_is_refused(self, plugin_class, rock_sample, user):
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is False

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_user_holding_dataset_change_rights_is_admitted(
        self, plugin_class, rock_sample, user
    ):
        assign_perm("change_dataset", user, rock_sample.dataset)
        request = _request_for(user)
        assert can_open(plugin_class, request, rock_sample) is True

    def test_the_reading_surface_stays_open_for_a_user_with_no_rights(self, rock_sample, user):
        request = _request_for(user)
        assert can_open(Overview, request, rock_sample) is True

    def test_the_reading_surface_stays_open_for_an_anonymous_request(self, rock_sample):
        request = _request_for(AnonymousUser())
        assert can_open(Overview, request, rock_sample) is True


class TestNoUnconditionalPredicate:
    """No plugin carries an access predicate that returns true for every request.

    The regression this guards: a module-level ``check_has_edit_permission`` that always
    returned ``True`` was assigned as every management plugin's ``check``, so the gate on
    :class:`TestSampleWritePluginsAreGated` never ran. Every editing plugin now relies solely on
    its declared ``permission`` - none of them declares a callable ``check`` at all.
    """

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
    def test_no_editing_plugin_declares_a_callable_check(self, plugin_class):
        assert not callable(resolve_check(plugin_class))

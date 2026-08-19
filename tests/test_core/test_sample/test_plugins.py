"""Access control on the sample record's editing surfaces.

FR-033a: a plugin declaring no required right is opened for every request, anonymous included.
The four management plugins on ``Sample`` used to carry an unconditional ``check`` predicate that
masked this; this file proves the closed state and guards against the predicate's return.
"""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

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


@pytest.mark.django_db
class TestPermissionStillGatesEvenWithAnAlwaysTruePredicate:
    """F12 - the deleted assertion (``not callable(resolve_check(plugin_class))``) also passes
    for ``check = True``, which reopens exactly the surface it was meant to guard: a plugin
    whose ``check`` is truthy-but-not-callable is treated by ``can_open`` as "no gate", the same
    as one with no ``check`` at all. This reinstates the original regression - a predicate that
    always returns ``True`` - on a copy of each editing plugin, and proves ``can_open`` still
    refuses an anonymous request on ``permission`` alone."""

    @pytest.mark.parametrize("plugin_class", EDITING_PLUGINS)
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

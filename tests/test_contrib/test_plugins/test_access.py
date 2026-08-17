"""One access decision, reached identically by navigation and by dispatch."""

import pytest
from django.views.generic import TemplateView

from fairdm.contrib.plugins import Plugin
from fairdm.contrib.plugins.access import (
    can_open,
    check_is_valid,
    has_perm,
    is_instance_of,
    menu_check,
    resolve_check,
)
from fairdm.core.sample.models import Sample


class TestResolveCheck:
    """The predicate must read the same whichever caller asks for it."""

    def test_plain_function(self):
        def predicate(request, obj):
            return True

        class P(Plugin, TemplateView):
            check = predicate

        assert resolve_check(P) is predicate

    def test_staticmethod(self):
        def predicate(request, obj):
            return True

        class P(Plugin, TemplateView):
            check = staticmethod(predicate)

        assert resolve_check(P)("request", "obj") is True

    def test_lambda(self):
        class P(Plugin, TemplateView):
            check = lambda request, obj: False

        assert resolve_check(P)("request", "obj") is False

    def test_inherited_attribute(self):
        def predicate(request, obj):
            return True

        class Parent(Plugin, TemplateView):
            check = predicate

        class Child(Parent):
            pass

        assert resolve_check(Child) is predicate

    def test_default_is_true(self):
        class P(Plugin, TemplateView):
            pass

        assert resolve_check(P) is True


class TestCheckIsValid:
    """A classmethod predicate is the trap: not callable, but truthy."""

    def test_plain_function_is_valid(self):
        assert check_is_valid(lambda request, obj: True) is True

    def test_bool_is_valid(self):
        assert check_is_valid(True) is True
        assert check_is_valid(False) is True

    def test_classmethod_is_refused(self):
        class P:
            @classmethod
            def check(cls, request, obj):
                return False

        static = resolve_check(P)
        # This is precisely why it needs refusing: a callable() guard falls through, and
        # bool(classmethod_object) is True, so the page would be published.
        assert not callable(static)
        assert bool(static) is True
        assert check_is_valid(static) is False


@pytest.mark.django_db
class TestPermissionResolution:
    """Model-level OR object-level. ModelBackend contributes nothing once an object is passed."""

    def test_model_level_permission_alone_passes(self, as_user, model_perm_user, sample):
        request = as_user(model_perm_user)
        assert has_perm(request, "sample.change_sample", sample) is True

    def test_object_level_permission_alone_passes(self, as_user, object_perm_user, sample):
        request = as_user(object_perm_user)
        assert has_perm(request, "sample.change_sample", sample) is True

    def test_neither_is_refused(self, as_user, plain_user, sample):
        request = as_user(plain_user)
        assert has_perm(request, "sample.change_sample", sample) is False

    def test_result_is_memoised_on_the_request(self, as_user, plain_user, sample):
        request = as_user(plain_user)
        has_perm(request, "sample.change_sample", sample)
        cache = request._fairdm_plugin_perm_cache
        assert (
            "sample.change_sample",
            sample._meta.label,
            sample.pk,
        ) in cache

    def test_memo_key_survives_a_new_instance_of_the_same_record(
        self, as_user, plain_user, sample
    ):
        """Keyed on identity, not id() — the decision runs inside template loops."""
        request = as_user(plain_user)
        has_perm(request, "sample.change_sample", sample)
        reloaded = Sample.objects.get(pk=sample.pk)
        assert reloaded is not sample
        assert len(request._fairdm_plugin_perm_cache) == 1
        has_perm(request, "sample.change_sample", reloaded)
        assert len(request._fairdm_plugin_perm_cache) == 1


@pytest.mark.django_db
class TestCanOpen:
    def test_no_predicate_and_no_permission_opens(self, as_user, plain_user, sample):
        class P(Plugin, TemplateView):
            pass

        request = as_user(plain_user)
        assert can_open(P, request, sample) is True

    def test_false_predicate_refuses(self, as_user, plain_user, sample):
        class P(Plugin, TemplateView):
            check = staticmethod(lambda request, obj: False)

        request = as_user(plain_user)
        assert can_open(P, request, sample) is False

    def test_predicate_receives_the_record(self, as_user, plain_user, sample):
        seen = {}

        def predicate(request, obj):
            seen["obj"] = obj
            return True

        class P(Plugin, TemplateView):
            check = staticmethod(predicate)

        request = as_user(plain_user)
        can_open(P, request, sample)
        assert seen["obj"] is sample

    def test_is_instance_of_narrows_by_subtype(self, as_user, plain_user, sample):
        class P(Plugin, TemplateView):
            check = staticmethod(is_instance_of(Sample))

        class Other:
            pass

        request = as_user(plain_user)
        assert can_open(P, request, sample) is True
        assert can_open(P, request, Other()) is False

    def test_missing_permission_refuses(self, as_user, plain_user, sample):
        class P(Plugin, TemplateView):
            permission = "sample.delete_sample"

        request = as_user(plain_user)
        assert can_open(P, request, sample) is False

    def test_extra_view_inherits_the_owning_plugin_predicate(
        self, as_user, plain_user, sample
    ):
        """The finding this whole feature exists to prevent.

        An extra view is an ordinary Plugin subclass and inherits the permissive default, so a
        decision read off the view alone would serve the child of a restricted plugin to a user
        who is refused the parent and shown no entry for it.
        """

        class Curation(Plugin, TemplateView):
            check = staticmethod(lambda request, obj: False)

        class CurationEdit(Plugin, TemplateView):
            plugin_class = Curation

        request = as_user(plain_user)
        assert can_open(Curation, request, sample) is False
        assert can_open(CurationEdit, request, sample) is False

    def test_extra_view_keeps_its_own_permission(self, as_user, plain_user, sample):
        class Parent(Plugin, TemplateView):
            pass

        class Child(Plugin, TemplateView):
            plugin_class = Parent
            permission = "sample.delete_sample"

        request = as_user(plain_user)
        assert can_open(Parent, request, sample) is True
        assert can_open(Child, request, sample) is False


@pytest.mark.django_db
class TestMenuCheck:
    """The adapter is what the navigation package holds, never the author's function."""

    def test_matches_the_navigation_package_signature(
        self, as_user, plain_user, sample
    ):
        class P(Plugin, TemplateView):
            pass

        request = as_user(plain_user)
        # flex_menu calls check(request, **kwargs); it never passes the record positionally.
        assert menu_check(P)(request, object=sample, uuid=sample.uuid) is True

    def test_a_raising_predicate_hides_rather_than_500s(
        self, as_user, plain_user, sample
    ):
        def explodes(request, obj):
            raise RuntimeError("author error")

        class P(Plugin, TemplateView):
            check = staticmethod(explodes)

        request = as_user(plain_user)
        assert menu_check(P)(request, object=sample, uuid=sample.uuid) is False

    def test_anonymous_user_is_handled(self, as_user, anonymous_user, sample):
        class P(Plugin, TemplateView):
            permission = "sample.change_sample"

        request = as_user(anonymous_user)
        assert menu_check(P)(request, object=sample, uuid=sample.uuid) is False

    def test_navigation_and_dispatch_reach_the_same_decision(
        self, as_user, plain_user, sample
    ):
        """FR-020 structurally: if these ever diverge, a page is hidden but reachable."""
        calls = []

        class P(Plugin, TemplateView):
            template_name = "base.html"
            check = staticmethod(lambda request, obj: calls.append("check") is None)

        request = as_user(plain_user)
        menu_check(P)(request, object=sample, uuid=sample.uuid)
        from_menu = len(calls)

        view = P()
        view.request = request
        view.kwargs = {"uuid": sample.uuid}
        view.registered_model = Sample
        view.has_permission()
        assert len(calls) == from_menu + 1

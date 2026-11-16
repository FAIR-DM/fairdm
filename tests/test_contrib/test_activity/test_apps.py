"""Tests that recorded activity is reachable through no feed of its own."""

import pytest
from actstream import views as actstream_views
from actstream.models import Action
from django.urls import URLPattern, URLResolver, get_resolver
from mvp_community.integrations.activity import views as community_views

from fairdm.contrib.activity.receivers import EDITED
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory

pytestmark = pytest.mark.django_db

FEED_MODULES = {actstream_views.__name__, community_views.__name__}
"""The views of the two packages that list actions, whatever their rule."""


def view_modules(patterns):
    """Return the module of every view the URL patterns reach, however deeply nested."""
    modules = set()
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            modules |= view_modules(pattern.url_patterns)
        elif isinstance(pattern, URLPattern):
            view = getattr(pattern.callback, "view_class", pattern.callback)
            modules.add(view.__module__)
    return modules


class TestNoOtherFeed:
    def test_no_address_reaches_a_view_of_either_package(self):
        reached = view_modules(get_resolver().url_patterns)

        assert not reached & FEED_MODULES

    def test_neither_package_has_a_url_namespace(self):
        namespaces = get_resolver().namespace_dict

        assert "mvp_community_activity" not in namespaces
        assert "actstream" not in namespaces

    def test_every_recorded_action_is_not_public(self):
        project = ProjectFactory()
        dataset = DatasetFactory(project=project, published=True)
        project.name = "Edited"
        project.save()
        Crediting(dataset).add(PersonFactory())

        assert Action.objects.filter(verb=EDITED).exists()
        assert Action.objects.exists()
        assert not Action.objects.filter(public=True).exists()

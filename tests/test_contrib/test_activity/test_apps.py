"""Tests that recorded activity is reachable through no feed of its own."""

import pytest
from actstream.models import Action
from django.urls import NoReverseMatch, get_resolver, reverse

from fairdm.contrib.activity.receivers import EDITED
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory

pytestmark = pytest.mark.django_db

FEED_NAMES = [
    "mvp_community_activity:list",
    "mvp_community_activity:feed",
    "actstream_follow",
    "actstream_unfollow",
    "actstream_followers",
    "actstream_actor",
    "actstream_model",
    "actstream_stream",
]


class TestNoOtherFeed:
    @pytest.mark.parametrize("name", FEED_NAMES)
    def test_no_feed_address_resolves(self, name):
        with pytest.raises(NoReverseMatch):
            reverse(name)

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

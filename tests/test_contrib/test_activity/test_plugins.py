"""Tests for fairdm/contrib/activity/plugins.py."""

from datetime import timedelta

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone

from fairdm.contrib.activity.lines import ActivityLines
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteSampleFactory

pytestmark = pytest.mark.django_db

PAGE_SIZE = 25


def make_record(kind, visibility=Visibility.PUBLIC):
    """Return a project or a dataset, with the visibility."""
    if kind == "project":
        return ProjectFactory(visibility=visibility)
    return DatasetFactory(visibility=visibility, published=True)


def address(record):
    """Return the address of the record's full list of activity."""
    return reverse(f"{record._meta.model_name}:activity", kwargs={"uuid": record.uuid})


def rows_of(response):
    """Return the lines of the page, counted from the rendered list."""
    page = BeautifulSoup(response.content, "html.parser")
    return page.select(".ov-activity__events li")


@pytest.fixture(params=["project", "dataset"])
def kind(request):
    """The two kinds of record that have a page of activity."""
    return request.param


class TestActivityPage:
    def test_a_public_record_answers(self, client, kind):
        record = make_record(kind)

        response = client.get(address(record))

        assert response.status_code == 200

    def test_a_private_record_answers_a_visitor_with_not_found(self, client, kind):
        record = make_record(kind, Visibility.PRIVATE)

        response = client.get(address(record))

        assert response.status_code == 404

    def test_a_private_record_answers_a_stranger_with_not_found(self, client, kind):
        record = make_record(kind, Visibility.PRIVATE)
        client.force_login(PersonFactory())

        response = client.get(address(record))

        assert response.status_code == 404

    def test_a_private_record_answers_its_team(self, client, kind):
        record = make_record(kind, Visibility.PRIVATE)
        member = PersonFactory()
        Crediting(record).add(member)
        client.force_login(member)

        response = client.get(address(record))

        assert response.status_code == 200

    def test_thirty_lines_fall_on_a_page_of_twenty_five_and_one_of_five(self, client):
        dataset = make_record("dataset")
        today = timezone.now()
        for days_ago in range(30 - len(ActivityLines(dataset, None))):
            sample = ConcreteSampleFactory(dataset=dataset)
            Sample.objects.filter(pk=sample.pk).update(
                added=today - timedelta(days=days_ago + 1)
            )
        assert len(ActivityLines(dataset, None)) == 30

        first = client.get(address(dataset))
        second = client.get(address(dataset), {"page": 2})

        assert len(rows_of(first)) == PAGE_SIZE
        assert len(rows_of(second)) == 5

    def test_a_page_beyond_the_last_is_not_found(self, client):
        dataset = make_record("dataset")

        response = client.get(address(dataset), {"page": 9})

        assert response.status_code == 404

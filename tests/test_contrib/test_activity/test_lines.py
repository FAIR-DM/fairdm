"""Tests for fairdm/contrib/activity/lines.py."""

from collections import Counter
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from actstream.models import Action
from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from fairdm.contrib.activity.lines import (
    ActivityLines,
    Day,
    Line,
    group_days,
    recent_activity,
)

from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
from fairdm.utils.choices import Visibility
from tests.factories import ConcreteMeasurementFactory, ConcreteSampleFactory

pytestmark = pytest.mark.django_db

CREATED = Counter(project=1, dataset=1)
"""The lines a project with one dataset always carries: both were created."""


def make_project():
    """Return a public project."""
    return ProjectFactory(visibility=Visibility.PUBLIC)


def make_dataset(project, published=True, visibility=Visibility.PUBLIC):
    """Return a dataset of the project, public and published unless told otherwise."""
    return DatasetFactory(project=project, visibility=visibility, published=published)


def team_member(record):
    """Return a person credited on the record, who may therefore see it."""
    person = PersonFactory()
    Crediting(record).add(person)
    return person


def lines_of(record, user=None):
    """Return every line the user sees on the record's page, newest first."""
    return list(ActivityLines(record, user)[:])


def kinds(lines):
    """Count the lines of each kind."""
    return Counter(line.kind for line in lines)


def set_added(record, when):
    """Set when a record was added, which ``auto_now_add`` otherwise decides."""
    model = type(record)
    model._base_manager.filter(pk=record.pk).update(added=when)


def add_samples(dataset, count=1, when=None):
    """Add samples to the dataset, all added at ``when`` if it is given."""
    samples = [ConcreteSampleFactory(dataset=dataset) for _ in range(count)]
    if when is not None:
        Sample.objects.filter(pk__in=[s.pk for s in samples]).update(added=when)
    return samples


def add_measurements(dataset, sample, count=1, when=None):
    """Add measurements of the sample, filed on the dataset, all added at ``when``."""
    measurements = [
        ConcreteMeasurementFactory(dataset=dataset, sample=sample) for _ in range(count)
    ]
    if when is not None:
        Measurement.objects.filter(pk__in=[m.pk for m in measurements]).update(
            added=when
        )
    return measurements


def edit(record):
    """Change the record's name, which records an edit."""
    record.name = f"{record.name} again"
    record.save()


def at(year, month, day, hour=12, minute=0):
    """Return a moment in UTC."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


class TestActivityLines:
    def test_a_line_for_each_source(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project, published=False)
        person = PersonFactory()
        clean_slate()
        samples = add_samples(dataset, 2)
        add_measurements(dataset, samples[0])
        edit(dataset)
        Crediting(dataset).add(person)
        dataset.published = True
        dataset.save()

        lines = lines_of(project)

        assert kinds(lines) == CREATED + Counter(sample=1, measurement=1, dataset=3)
        assert all(isinstance(line, Line) for line in lines)
        assert any(dataset.get_absolute_url() in line.html for line in lines)
        assert any(person.get_absolute_url() in line.html for line in lines)

    def test_the_project_creation_belongs_to_its_own_page_only(self):
        project = make_project()
        dataset = make_dataset(project)

        assert kinds(lines_of(project))["project"] == 1
        assert kinds(lines_of(dataset))["project"] == 0

    def test_a_dataset_page_gives_the_dataset_alone(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        other = make_dataset(project)
        clean_slate()
        add_samples(dataset)
        add_samples(other)
        edit(other)

        assert kinds(lines_of(dataset)) == Counter(dataset=1, sample=1)

    def test_samples_on_two_days_give_two_lines(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        add_samples(dataset, 2, when=at(2026, 7, 1, 9))
        add_samples(dataset, 1, when=at(2026, 7, 1, 15))
        add_samples(dataset, 1, when=at(2026, 7, 2, 9))

        sample_lines = [line for line in lines_of(project) if line.kind == "sample"]

        assert sorted(line.day for line in sample_lines) == [
            date(2026, 7, 1),
            date(2026, 7, 2),
        ]

    def test_samples_on_two_datasets_one_day_give_two_lines(self, clean_slate):
        project = make_project()
        first = make_dataset(project)
        second = make_dataset(project)
        clean_slate()
        add_samples(first, 1, when=at(2026, 7, 1))
        add_samples(second, 1, when=at(2026, 7, 1))

        lines = [line for line in lines_of(project) if line.kind == "sample"]

        assert len(lines) == 2
        for dataset in (first, second):
            assert sum(dataset.get_absolute_url() in line.html for line in lines) == 1

    def test_measurements_are_a_line_apart_from_samples(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        (sample,) = add_samples(dataset, 1, when=at(2026, 7, 1))
        add_measurements(dataset, sample, 1, when=at(2026, 7, 1))

        assert kinds(lines_of(project)) == CREATED + Counter(sample=1, measurement=1)

    def test_a_measurement_counts_in_its_own_dataset_and_not_its_samples(
        self, clean_slate
    ):
        project = make_project()
        home = make_dataset(project)
        away = make_dataset(project)
        (sample,) = add_samples(home, 1)
        clean_slate()
        add_measurements(away, sample, 1)

        on_home = lines_of(home)
        on_away = lines_of(away)

        assert kinds(on_home)["measurement"] == 0
        assert kinds(on_away)["measurement"] == 1

    def test_sample_edits_and_a_contributor_on_a_sample_give_no_line(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        (sample,) = add_samples(dataset)
        clean_slate()
        before = kinds(lines_of(project))

        sample.name = "Renamed"
        sample.save()
        Crediting(sample).add(PersonFactory())

        assert kinds(lines_of(project)) == before

    def test_lines_are_newest_first(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        add_samples(dataset, 1, when=at(2026, 7, 3))
        add_samples(dataset, 1, when=at(2026, 7, 1))
        edit(dataset)
        Action.objects.update(timestamp=at(2026, 7, 2))
        set_added(dataset, at(2026, 6, 1))
        set_added(project, at(2026, 5, 1))

        lines = lines_of(project)

        assert [line.timestamp for line in lines] == sorted(
            (line.timestamp for line in lines), reverse=True
        )
        assert [line.kind for line in lines] == [
            "sample",
            "dataset",
            "sample",
            "dataset",
            "project",
        ]

    def test_a_day_is_the_portal_day(self, settings, clean_slate):
        settings.TIME_ZONE = "Pacific/Auckland"
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        local = datetime(2026, 7, 11, 0, 30, tzinfo=ZoneInfo("Pacific/Auckland"))
        add_samples(dataset, 1, when=local)

        (line,) = [line for line in lines_of(project) if line.kind == "sample"]

        assert local.astimezone(UTC).date() == date(2026, 7, 10)
        assert line.day == date(2026, 7, 11)

    def test_a_slice_reads_only_as_far_as_it_is_asked(self):
        project = make_project()
        dataset = make_dataset(project)
        for day in range(1, 6):
            add_samples(dataset, 1, when=at(2026, 7, day))
        lines = ActivityLines(project, None)

        assert len(lines[:3]) == 3
        assert len(lines[2:4]) == 2

    def test_a_plain_index_is_refused(self):
        lines = ActivityLines(make_project(), None)

        with pytest.raises(TypeError):
            lines[0]

    def test_its_length_is_the_number_of_lines_a_full_slice_returns(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        (sample,) = add_samples(dataset, 1, when=at(2026, 7, 1))
        add_samples(dataset, 1, when=at(2026, 7, 2))
        add_measurements(dataset, sample, 1, when=at(2026, 7, 2))
        edit(dataset)
        edit(project)
        team_member(dataset)
        lines = ActivityLines(project, None)

        assert len(lines) == len(lines[:])
        assert len(lines) == 8

    def test_a_sample_count_of_a_portal_defined_type(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        ConcreteSampleFactory(dataset=dataset)

        assert kinds(lines_of(dataset))["sample"] == 1

    def test_names_are_escaped(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project)
        dataset.name = "<b>x</b>"
        dataset.save()
        person = PersonFactory(name="<b>x</b>")
        clean_slate()
        add_samples(dataset)
        Crediting(dataset).add(person)

        lines = lines_of(project)

        assert any(dataset.get_absolute_url() in line.html for line in lines)
        assert any(person.get_absolute_url() in line.html for line in lines)
        for line in lines:
            assert "<b>" not in line.html
        assert sum("&lt;b&gt;" in line.html for line in lines) >= 2


@pytest.fixture
def request_of_a_visitor():
    """Return a request made by a visitor."""
    request = RequestFactory().get("/")
    request.user = AnonymousUser()
    return request


@pytest.fixture
def full_list_address(monkeypatch):
    """Make the full list's address resolve, as it does once its page exists."""
    monkeypatch.setattr(
        "fairdm.contrib.activity.lines.safe_reverse", lambda name, **kwargs: "/all/"
    )


class TestRecentActivity:
    def test_nine_lines_give_eight_and_a_link_to_the_rest(
        self, request_of_a_visitor, full_list_address
    ):
        project = make_project()
        dataset = make_dataset(project)
        add_samples(dataset, 1, when=at(2026, 7, 1))
        for day in range(2, 8):
            add_samples(dataset, 1, when=at(2026, 7, day))
        edit(project)

        panel = recent_activity(project, request_of_a_visitor)

        total = sum(len(day.lines) for day in panel["days"])
        assert total == 8
        assert panel["more_url"]

    def test_eight_lines_give_no_link(self, request_of_a_visitor, full_list_address):
        project = make_project()
        dataset = make_dataset(project)
        for day in range(1, 7):
            add_samples(dataset, 1, when=at(2026, 7, day))

        panel = recent_activity(project, request_of_a_visitor)

        assert sum(len(day.lines) for day in panel["days"]) == 8
        assert not panel["more_url"]

    def test_days_follow_the_lines(self):
        first = Line(at(2026, 7, 2), date(2026, 7, 2), "sample", "a")
        second = Line(at(2026, 7, 2, 8), date(2026, 7, 2), "dataset", "b")
        third = Line(at(2026, 7, 1), date(2026, 7, 1), "project", "c")

        days = group_days([first, second, third])

        assert days == [
            Day(date(2026, 7, 2), (first, second)),
            Day(date(2026, 7, 1), (third,)),
        ]


class TestActivityLinesAccess:
    def test_a_private_dataset_is_absent_for_a_visitor_and_a_stranger(
        self, clean_slate
    ):
        project = make_project()
        dataset = make_dataset(project, published=False, visibility=Visibility.PRIVATE)
        add_samples(dataset)
        edit(dataset)
        stranger = PersonFactory()

        assert kinds(lines_of(project, None)) == Counter(project=1)
        assert kinds(lines_of(project, stranger)) == Counter(project=1)

    def test_a_private_dataset_is_present_for_its_team(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project, published=False, visibility=Visibility.PRIVATE)
        member = team_member(dataset)
        clean_slate()
        add_samples(dataset)
        edit(dataset)

        lines = lines_of(project, member)

        assert kinds(lines) == CREATED + Counter(sample=1, dataset=1)

    def test_made_public_its_earlier_lines_appear_and_made_private_they_go(
        self, clean_slate
    ):
        project = make_project()
        dataset = make_dataset(project, published=False, visibility=Visibility.PRIVATE)
        add_samples(dataset)
        edit(dataset)
        assert kinds(lines_of(project)) == Counter(project=1)

        dataset.visibility = Visibility.PUBLIC
        dataset.published = True
        dataset.save()
        shown = kinds(lines_of(project))

        dataset.visibility = Visibility.PRIVATE
        dataset.save()

        assert shown["sample"] == 1
        assert shown["dataset"] >= 2
        assert kinds(lines_of(project)) == Counter(project=1)

    def test_a_public_unpublished_dataset_shows_no_counts_to_a_visitor(
        self, clean_slate
    ):
        project = make_project()
        dataset = make_dataset(project, published=False)
        (sample,) = add_samples(dataset)
        add_measurements(dataset, sample)
        edit(dataset)

        visitor = kinds(lines_of(project))
        member = kinds(lines_of(project, team_member(dataset)))

        assert visitor["sample"] == visitor["measurement"] == 0
        assert visitor["dataset"] >= 2
        assert member["sample"] == member["measurement"] == 1


class TestActivityLinesRemoval:
    def test_a_deleted_sample_leaves_the_count_and_all_deleted_leave_no_line(
        self, clean_slate
    ):
        project = make_project()
        dataset = make_dataset(project)
        clean_slate()
        first, second = add_samples(dataset, 2, when=at(2026, 7, 1))

        first.delete()
        assert kinds(lines_of(project))["sample"] == 1
        second.delete()

        assert kinds(lines_of(project))["sample"] == 0

    def test_a_deleted_dataset_takes_its_lines(self, clean_slate):
        project = make_project()
        dataset = make_dataset(project, published=False)
        add_samples(dataset)
        edit(dataset)
        Crediting(dataset).add(PersonFactory())
        dataset.published = True
        dataset.save()

        dataset.delete()

        assert kinds(lines_of(project)) == Counter(project=1)

    def test_records_made_with_recording_off_still_give_their_additions(
        self, clean_slate
    ):
        project = make_project()
        dataset = make_dataset(project)
        add_samples(dataset)
        clean_slate()

        assert Action.objects.count() == 0
        assert kinds(lines_of(project)) == CREATED + Counter(sample=1)

    def test_a_moved_dataset_shows_on_its_new_project_only(self, clean_slate):
        old = make_project()
        new = make_project()
        dataset = make_dataset(old)
        add_samples(dataset)
        edit(dataset)

        dataset.project = new
        dataset.save()

        assert kinds(lines_of(old)) == Counter(project=1)
        assert kinds(lines_of(new))["sample"] == 1
        assert kinds(lines_of(new))["dataset"] >= 2


class TestActivityLinesScale:
    def seed(self, datasets):
        """Return a project of that many datasets, each with samples, measurements, actions."""
        project = make_project()
        for _ in range(datasets):
            dataset = make_dataset(project)
            samples = add_samples(dataset, 3)
            add_measurements(dataset, samples[0], 2)
            edit(dataset)
            Crediting(dataset).add(PersonFactory())
        return project

    def test_the_queries_do_not_grow_with_the_datasets(self, django_assert_num_queries):
        small = self.seed(1)
        large = self.seed(5)
        lines_of_small = ActivityLines(small, None)
        lines_of_large = ActivityLines(large, None)
        list(lines_of_small[:9])
        with CaptureQueriesContext(connection) as captured:
            list(lines_of_small[:9])

        with django_assert_num_queries(len(captured)):
            list(lines_of_large[:9])

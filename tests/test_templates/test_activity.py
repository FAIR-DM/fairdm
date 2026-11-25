"""Tests for the recent activity panel and the community package's overridden row."""

from datetime import UTC, date, datetime

import pytest
from django.urls import reverse
from django.utils.safestring import mark_safe

from fairdm.contrib.activity.lines import Day, Line
from fairdm.factories import DatasetFactory, PersonFactory, ProjectFactory
from fairdm.utils.choices import Visibility

MOMENT = datetime(2026, 3, 4, 12, 0, tzinfo=UTC)


def make_line(kind, day, text="a line"):
    """Return a line of the kind, falling on the day."""
    return Line(MOMENT, day, kind, mark_safe(f"<b>{text}</b>"))


@pytest.fixture
def two_days():
    """Two days of lines: a dataset and a sample on one, a project on the other."""
    return [
        Day(
            date(2026, 3, 4),
            (
                make_line("dataset", date(2026, 3, 4)),
                make_line("sample", date(2026, 3, 4)),
            ),
        ),
        Day(date(2026, 3, 2), (make_line("project", date(2026, 3, 2)),)),
    ]


@pytest.mark.django_db
class TestActivityPanel:
    def test_each_day_is_a_row_holding_its_lines(self, render_overview, soup, two_days):
        html = render_overview("activity", days=two_days, more_url="")

        rows = soup(html).select(".ov-activity__row")
        assert len(rows) == 2
        assert [len(row.select(".ov-activity__events li")) for row in rows] == [2, 1]

    def test_each_line_carries_the_colour_of_its_kind(
        self, render_overview, soup, two_days
    ):
        html = render_overview("activity", days=two_days, more_url="")

        lines = soup(html).select(".ov-activity__events li")
        assert [line["class"] for line in lines] == [
            ["record-dataset"],
            ["record-sample"],
            ["record-project"],
        ]

    def test_a_line_is_drawn_as_the_html_it_carries(
        self, render_overview, soup, two_days
    ):
        html = render_overview("activity", days=two_days, more_url="")

        assert len(soup(html).select(".ov-activity__events li b")) == 3

    def test_no_days_draws_the_empty_state_and_no_row(self, render_overview, soup):
        html = render_overview("activity", days=[], more_url="")

        page = soup(html)
        assert page.select_one('[data-card="activity"]') is not None
        assert page.select(".ov-activity__row") == []
        assert page.select_one(".mvp-list-empty") is not None

    def test_a_more_url_draws_a_link_to_it(self, render_overview, soup, two_days):
        html = render_overview("activity", days=two_days, more_url="/all/")

        link = soup(html).select_one('a.more-link[href="/all/"]')
        assert link is not None

    def test_no_more_url_draws_no_link(self, render_overview, soup, two_days):
        html = render_overview("activity", days=two_days, more_url="")

        assert soup(html).select_one("a.more-link") is None


@pytest.mark.django_db
class TestOverrides:
    def test_the_community_list_draws_fairdms_row(
        self, child_template, render_template, soup, two_days
    ):
        name = child_template('<c-mvp_community.activity.feed :actions="days" only />')

        html = render_template(name, {"days": two_days})

        page = soup(html)
        assert len(page.select("li.ov-activity__row")) == 2
        assert page.select("img, .avatar") == []

    def test_the_account_center_keeps_the_accounts_package_page(self, client):
        client.force_login(PersonFactory())

        response = client.get(reverse("account-center"))

        assert response.status_code == 200
        assert reverse("account_email").encode() in response.content


@pytest.mark.django_db
class TestPagesDrawThePanel:
    def test_the_project_page_has_the_panel(self, client, soup):
        project = ProjectFactory(visibility=Visibility.PUBLIC)

        response = client.get(project.get_absolute_url())

        assert soup(response.content).select_one('[data-card="activity"]') is not None

    def test_the_dataset_page_has_the_panel(self, client, soup):
        dataset = DatasetFactory(visibility=Visibility.PUBLIC)

        response = client.get(dataset.get_absolute_url())

        assert soup(response.content).select_one('[data-card="activity"]') is not None

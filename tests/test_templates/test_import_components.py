"""Tests for the ``c-import`` components the import pages are built from.

Each component is rendered with the data its states need and the tests read its
structure: the elements, their roles and the attributes a script or HTMX reads.
Wording and look are never asserted.
"""

import pytest
from django_cotton import render_component

from fairdm.contrib.import_export.forms import ImportOptionsForm
from fairdm.contrib.import_export.models import ImportJob, ImportRow
from tests.factories import ImportJobFactory

pytestmark = pytest.mark.django_db

STEPS = [("file", "File"), ("columns", "Columns"), ("check", "Check"), ("import", "Go")]


@pytest.fixture
def render(request_):
    """Return a function rendering one ``c-import`` component from attributes."""

    def build(name, **attributes):
        """Render the component.

        Args:
            name: The component's name under ``import``.
            **attributes: The component's attributes.

        Returns:
            The HTML.
        """
        return render_component(request_, f"import.{name}", **attributes)

    return build


@pytest.fixture
def render_markup(child_template, render_template):
    """Return a function rendering a template string, for components with a slot."""

    def build(source, **context):
        """Render the source.

        Args:
            source: The template's text.
            **context: The template's context.

        Returns:
            The HTML.
        """
        return render_template(child_template(source), context)

    return build


class TestSteps:
    """The step bar marks the current step once."""

    @pytest.mark.parametrize("current", [0, 1, 3])
    def test_one_step_is_current(self, render, soup, current):
        page = soup(render("steps", steps=STEPS, current=current))
        items = page.select("ol > li")
        assert len(items) == len(STEPS)
        marked = [i for i, item in enumerate(items) if item.get("aria-current")]
        assert marked == [current]

    def test_a_current_of_minus_one_marks_none(self, render, soup):
        page = soup(render("steps", steps=STEPS, current=-1))
        assert not page.select("[aria-current]")

    def test_the_steps_before_the_current_one_are_marked_done(self, render, soup):
        page = soup(render("steps", steps=STEPS, current=2))
        done = [
            item for item in page.select("ol > li") if "ie-step--done" in item["class"]
        ]
        assert len(done) == 2


class TestProgress:
    """The progress component asks for itself every second."""

    def test_it_polls_its_address(self, render, soup):
        page = soup(render("progress", percent=25, done=50, total=200, url="/s/"))
        root = page.select_one("[data-ie-progress]")
        assert root["hx-get"] == "/s/"
        assert root["hx-trigger"] == "every 1s"
        assert root["hx-swap"] == "outerHTML"

    def test_the_bar_reads_the_figures(self, render, soup):
        page = soup(render("progress", percent=25, done=50, total=200, url="/s/"))
        bar = page.select_one("[role=progressbar]")
        assert bar["aria-valuenow"] == "50"
        assert bar["aria-valuemax"] == "200"
        assert bar["aria-valuemin"] == "0"
        assert "25%" in bar.select_one("span")["style"]

    def test_a_bar_for_an_import_is_labelled_apart_from_a_check(self, render, soup):
        check = soup(render("progress", percent=0, done=0, total=1, url="/s/"))
        import_ = soup(
            render("progress", percent=0, done=0, total=1, url="/s/", importing=True)
        )
        assert (
            check.select_one("[role=progressbar]")["aria-label"]
            != import_.select_one("[role=progressbar]")["aria-label"]
        )

    def test_a_bar_for_an_undo_is_labelled_apart_from_a_check_and_an_import(
        self, render, soup
    ):
        def label(**kwargs):
            page = soup(
                render("progress", percent=0, done=0, total=1, url="/s/", **kwargs)
            )
            return page.select_one("[role=progressbar]")["aria-label"]

        assert label(undoing=True) not in {label(), label(importing=True)}


class TestOutcomeBadge:
    """A badge for each outcome of a row."""

    def test_each_outcome_is_named_by_a_badge_of_its_own(self, render, soup):
        names = {
            outcome.value: soup(
                render("outcome-badge", outcome=outcome.value)
            ).get_text(strip=True)
            for outcome in ImportRow.Outcome
        }

        assert all(names.values())
        assert len(set(names.values())) == len(names)

    @pytest.mark.parametrize("outcome", ["new", "update"])
    def test_a_row_already_written_is_named_in_the_past(self, render, soup, outcome):
        planned = soup(render("outcome-badge", outcome=outcome)).get_text(strip=True)
        written = soup(render("outcome-badge", outcome=outcome, done=True)).get_text(
            strip=True
        )
        assert planned != written


class TestPanel:
    """A panel with a heading and whatever is put in it."""

    def test_it_holds_its_content_under_a_heading(self, render_markup, soup):
        page = soup(
            render_markup(
                '<c-import.panel title="T"><p id="inside">x</p></c-import.panel>'
            )
        )
        section = page.select_one("section.ie-panel")
        assert section.select_one("h2").get_text(strip=True) == "T"
        assert section.select_one("#inside")

    def test_the_heading_labels_the_section_when_it_has_an_id(
        self, render_markup, soup
    ):
        page = soup(
            render_markup(
                '<c-import.panel title="T" heading_id="h1">x</c-import.panel>'
            )
        )
        assert page.select_one("section")["aria-labelledby"] == "h1"
        assert page.select_one("h2")["id"] == "h1"

    def test_a_count_is_shown_beside_the_title(self, render_markup, soup):
        page = soup(
            render_markup('<c-import.panel title="T" count="7">x</c-import.panel>')
        )
        assert page.select_one(".ie-count").get_text(strip=True) == "7"

    def test_without_a_count_none_is_drawn(self, render_markup, soup):
        page = soup(render_markup('<c-import.panel title="T">x</c-import.panel>'))
        assert not page.select(".ie-count")

    def test_a_bare_title_has_no_header_row(self, render_markup, soup):
        page = soup(render_markup('<c-import.panel title="T">x</c-import.panel>'))
        assert not page.select("section > header")
        assert page.select_one("section > h2")

    def test_a_count_moves_the_title_into_a_header_row(self, render_markup, soup):
        page = soup(
            render_markup('<c-import.panel title="T" count="7">x</c-import.panel>')
        )
        assert page.select_one("section > header > h2")

    def test_the_action_slot_is_drawn_in_the_header_row(self, render_markup, soup):
        page = soup(
            render_markup(
                '<c-import.panel title="T"><c-slot name="action">'
                '<a id="more" href="/m/">More</a></c-slot>x</c-import.panel>'
            )
        )
        assert page.select_one("section > header #more")

    def test_a_flush_panel_keeps_its_heading_in_the_header(self, render_markup, soup):
        page = soup(
            render_markup('<c-import.panel title="T" size="flush">x</c-import.panel>')
        )
        header = page.select_one("section.ie-panel--flush > header.ie-panel__head")
        assert header is not None
        assert header.select_one("h2.ie-panel__title") is not None


class TestAlert:
    """An alert that is announced when it is an error."""

    def test_an_error_has_the_alert_role(self, render_markup, soup):
        page = soup(render_markup('<c-import.alert kind="error">Bad</c-import.alert>'))
        assert page.select_one("[role=alert]").get_text(strip=True) == "Bad"

    def test_a_warning_is_not_announced(self, render_markup, soup):
        page = soup(render_markup('<c-import.alert kind="warning">Hm</c-import.alert>'))
        assert page.select_one(".ie-alert--warning")
        assert not page.select("[role=alert]")


class TestChoice:
    """A fieldset around one field of the options form."""

    def test_it_draws_the_field_inside_a_fieldset_with_a_legend(self, render, soup):
        form = ImportOptionsForm()
        page = soup(render("choice", field=form["mode"]))
        assert page.select_one("fieldset legend")
        assert len(page.select("fieldset input[name=mode]")) == len(
            ImportJob.Mode.choices
        )

    def test_a_hidden_legend_stays_for_screen_readers(self, render, soup):
        page = soup(
            render("choice", field=ImportOptionsForm()["mode"], hide_legend=True)
        )
        assert "sr-only" in page.select_one("legend")["class"]


class TestDownloads:
    """A list of files to download."""

    def test_each_link_is_a_download(self, render, soup):
        links = [
            {"label": "A", "url": "/a.xlsx", "icon": "file-earmark-excel"},
            {"label": "B", "url": "/b.csv", "icon": "file-earmark-text"},
        ]
        page = soup(render("downloads", links=links))
        anchors = page.select("ul li a[download]")
        assert [a["href"] for a in anchors] == ["/a.xlsx", "/b.csv"]


class TestJobList:
    """The list of imports, one link to each."""

    def test_each_job_links_to_its_page(self, render, soup):
        jobs = [ImportJobFactory() for _ in range(3)]
        page = soup(render("job-list", jobs=jobs))
        links = [a["href"] for a in page.select("[data-ie-job] a")]
        assert links == [job.get_absolute_url() for job in jobs]

    def test_the_status_is_in_a_class_of_its_own(self, render, soup):
        job = ImportJobFactory(status=ImportJob.Status.PROBLEMS)
        page = soup(render("job-list", jobs=[job]))
        assert page.select_one(".ie-state--problems")

    def test_an_imported_job_counts_what_it_added_and_changed(self, render, soup):
        job = ImportJobFactory(
            status=ImportJob.Status.IMPORTED, summary={"new": 4, "update": 2}
        )
        page = soup(render("job-list", jobs=[job]))
        assert page.select_one(".ie-delta--new")
        assert page.select_one(".ie-delta--update")

    def test_a_job_that_wrote_nothing_counts_nothing(self, render, soup):
        job = ImportJobFactory(status=ImportJob.Status.CHECKED, summary={"new": 4})
        page = soup(render("job-list", jobs=[job]))
        assert not page.select(".ie-delta--new")

    def test_the_type_is_named_only_when_asked_for(self, render, soup):
        job = ImportJobFactory()
        with_type = soup(render("job-list", jobs=[job], show_type=True))
        without = soup(render("job-list", jobs=[job]))
        assert len(with_type.get_text()) > len(without.get_text())

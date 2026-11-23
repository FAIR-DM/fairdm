"""Tests for the ``c-import.guide`` component, the column guide of a type's file.

The component is rendered for a table schema and the tests read its structure: the tables,
their headers and roles, which columns carry which tag, and how a long list is cut. Wording and
look are never asserted.
"""

from dataclasses import replace

import pytest
from django_cotton import render_component

from fairdm.registry import registry

LONG_LIST = 50
SHOWN = 40


@pytest.fixture
def render_guide(request_, soup):
    """Return a function rendering the guide for a schema and parsing the HTML."""

    def render(schema):
        """Render the guide.

        Args:
            schema: The table schema to lay out.

        Returns:
            The parsed HTML.
        """
        return soup(render_component(request_, "import.guide", schema=schema))

    return render


@pytest.fixture
def schema(rock_config):
    """The table schema of the registered rock sample type."""
    return rock_config.get_table_schema()


@pytest.fixture
def rock_config():
    """The registered rock sample configuration."""
    from demo.models import RockSample

    return registry.get_for_model(RockSample)


@pytest.fixture
def long_list_schema(schema):
    """The rock sample schema with a column of fifty allowed values, and that column's name."""
    index = next(i for i, column in enumerate(schema.columns) if column.group == "own")
    values = [(f"value-{n}", f"meaning {n}") for n in range(LONG_LIST)]
    schema.columns[index] = replace(schema.columns[index], allowed=values)
    return schema, schema.columns[index].name


@pytest.mark.django_db
class TestGuideComponent:
    def test_each_group_is_one_table_with_a_caption_and_column_headers(
        self, render_guide, schema
    ):
        page = render_guide(schema)

        tables = page.select("section table")
        assert len(tables) == len(schema.groups())
        for table in tables:
            assert table["role"] == "table"
            assert table.find("caption")
            headers = table.select("thead th")
            assert headers
            assert {th["scope"] for th in headers} == {"col"}
            assert {th["role"] for th in headers} == {"columnheader"}

    def test_the_parts_of_each_table_carry_their_roles(self, render_guide, schema):
        page = render_guide(schema)

        for table in page.select("table"):
            assert {part["role"] for part in table.select("thead, tbody")} == {
                "rowgroup"
            }
            assert {row["role"] for row in table.select("tr")} == {"row"}
            assert {td["role"] for td in table.select("tbody td")} == {"cell"}

    def test_each_row_is_headed_by_its_column(self, render_guide, schema):
        page = render_guide(schema)

        for _, _, columns in schema.groups():
            rows = page.select(", ".join(f"tr#col-{column.name}" for column in columns))
            assert [row["id"] for row in rows] == [f"col-{c.name}" for c in columns]
        for column in schema.columns:
            heading = page.select_one(f"tr#col-{column.name} th")
            assert heading["scope"] == "row"
            assert heading["role"] == "rowheader"
            assert heading.find("code").get_text(strip=True) == column.name

    def test_only_the_required_columns_are_tagged_required(self, render_guide, schema):
        page = render_guide(schema)

        tagged = {
            row["id"] for row in page.select("tr") if row.select("[data-tag=required]")
        }
        assert tagged == {f"col-{c.name}" for c in schema.columns if c.required}
        assert tagged

    def test_only_the_identifying_columns_are_tagged_as_finding_the_record(
        self, render_guide, schema
    ):
        page = render_guide(schema)

        tagged = {
            row["id"] for row in page.select("tr") if row.select("[data-tag=key]")
        }
        assert tagged == {
            f"col-{c.name}"
            for c in schema.columns
            if c.role in {"key", "match"} and not c.required
        }
        assert tagged

    def test_a_column_written_on_export_only_is_tagged_so(self, render_guide, schema):
        page = render_guide(schema)

        tagged = {
            row["id"] for row in page.select("tr") if row.select("[data-tag=export]")
        }
        assert tagged == {f"col-{c.name}" for c in schema.columns if c.role == "export"}

    def test_a_long_list_shows_the_first_forty_and_the_total(
        self, render_guide, long_list_schema
    ):
        schema, name = long_list_schema

        page = render_guide(schema)

        details = page.select_one(f"tr#col-{name}").find("details")
        assert [
            li.find("code").get_text(strip=True) for li in details.select("li")
        ] == [f"value-{n}" for n in range(SHOWN)]
        assert str(LONG_LIST) in details.find("summary").get_text()
        assert len(schema.get(name).allowed) == LONG_LIST

    def test_a_short_list_is_shown_whole(self, render_guide, schema):
        column = next(c for c in schema.columns if 0 < len(c.allowed) <= SHOWN)

        page = render_guide(schema)

        details = page.select_one(f"tr#col-{column.name}").find("details")
        assert len(details.select("li")) == len(column.allowed)

    def test_an_example_is_shown_in_the_last_cell(self, render_guide, schema):
        page = render_guide(schema)

        for column in schema.columns:
            cell = page.select_one(f"tr#col-{column.name}").select("td")[-1]
            assert cell.get_text(strip=True) == column.example


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model", [*registry.samples, *registry.measurements], ids=lambda m: m.__name__
)
class TestGuideForEveryType:
    def test_the_guide_renders_for_a_registered_type(self, render_guide, model):
        schema = registry.get_for_model(model).get_table_schema()

        page = render_guide(schema)

        assert len(page.select("table")) == len(schema.groups())
        assert len(page.select("tbody tr")) == len(schema.columns)

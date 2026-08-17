"""
Tests for the ``show_config`` management command (FR-019, FR-020).
"""

from io import StringIO

from django.core.management import call_command


class TestShowConfigCommand:
    """``manage.py show_config`` lists every layer in application order,
    marked found or absent (FR-019)."""

    def test_lists_every_layer_in_order_marked_found_or_absent(self, provenance_record):
        provenance_record.reset()
        provenance_record.add_layer(
            "baseline", "/fake/settings", True, ["INSTALLED_APPS"]
        )
        provenance_record.add_layer(
            "fairdm override", "/fake/development.py", True, ["DEBUG"]
        )
        provenance_record.add_layer("addons", None, False, [])
        provenance_record.add_layer(
            "portal override", "/fake/portal/development.py", False, []
        )

        out = StringIO()
        call_command("show_config", stdout=out)
        output = out.getvalue()

        lines = [line for line in output.splitlines() if line.strip()]
        assert len(lines) == 4

        assert (
            output.index("baseline")
            < output.index("fairdm override")
            < output.index("addons")
            < output.index("portal override")
        )
        assert output.count(": found") == 2
        assert output.count(": absent") == 2


class TestShowConfigNamedSetting:
    """``manage.py show_config SETTING_NAME`` (FR-020)."""

    def test_reports_resolved_value_and_producing_layer(
        self, provenance_record, settings
    ):
        provenance_record.reset()
        provenance_record.add_layer(
            "baseline", "/fake/settings", True, ["SOME_OTHER_SETTING"]
        )
        provenance_record.add_layer(
            "portal override",
            "/fake/portal/development.py",
            True,
            ["MARKER_SETTING"],
        )
        settings.MARKER_SETTING = "resolved-value"

        out = StringIO()
        call_command("show_config", "MARKER_SETTING", stdout=out)
        output = out.getvalue()

        assert "resolved-value" in output
        assert "portal override" in output

    def test_cleanses_a_known_secret_so_it_never_reaches_stdout(
        self, provenance_record, settings
    ):
        provenance_record.reset()
        provenance_record.add_layer("baseline", "/fake/settings", True, ["SECRET_KEY"])

        secret_value = "sekr3t-marker-" + "z" * 40
        settings.SECRET_KEY = secret_value

        out = StringIO()
        call_command("show_config", "SECRET_KEY", stdout=out)
        output = out.getvalue()

        assert secret_value not in output
        assert "baseline" in output

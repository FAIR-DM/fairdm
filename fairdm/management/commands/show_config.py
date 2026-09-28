"""Interrogate the running portal about where a setting came from.

With no arguments, reports every layer ``fairdm.setup()`` considered, in
application order, each marked found or absent. Given a setting name,
reports that setting's resolved value and the layer that produced it — the
value passed through ``SafeExceptionReporterFilter().cleanse_setting()``
first, so a secret never reaches stdout.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.views.debug import SafeExceptionReporterFilter

from fairdm.conf import record


class Command(BaseCommand):
    """Report the configuration layers, or where one setting came from."""

    help = (
        "Report the configuration layers fairdm.setup() composed, or a "
        "named setting's resolved value and the layer that produced it."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """Add the optional setting name argument."""
        parser.add_argument(
            "setting",
            nargs="?",
            default=None,
            help="Report this setting's resolved value and producing layer.",
        )

    def handle(self, *args, **options) -> None:
        """Report one setting when a name is given, otherwise every layer."""
        setting_name = options["setting"]
        if setting_name:
            self._report_setting(setting_name)
        else:
            self._report_layers()

    def _report_layers(self) -> None:
        """Print each layer in application order, marked found or absent."""
        for layer in record.layers():
            status = "found" if layer.found else "absent"
            self.stdout.write(f"{layer.name}: {status}")

    def _report_setting(self, name: str) -> None:
        """Print a setting's cleansed value and the layer that produced it.

        Args:
            name: The setting name to report.
        """
        value = getattr(settings, name, None)
        cleansed = SafeExceptionReporterFilter().cleanse_setting(name, value)
        layer = record.producer(name)
        layer_name = layer.name if layer is not None else "unattributed"
        self.stdout.write(f"{name} = {cleansed} ({layer_name})")

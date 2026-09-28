"""FairDM configuration package: settings baseline, environment layers and addons.

Provides a production-ready Django configuration baseline, layered with
environment overrides selected by the DJANGO_ENV variable, and addon
integration.

Also holds ``record``, the provenance of the layers ``setup()`` composes.
``setup()`` snapshots the caller's scope before and after each layer's
``include()`` call and records the delta: the uppercase setting names that layer
wrote. Never a value, because the scope holds ``SECRET_KEY`` and the database and
email passwords. The record lives here rather than in settings so it never
appears in a settings dump. ``show_config`` reads it after ``django.setup()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Layer:
    """One layer ``setup()`` considered, in application order.

    Attributes:
        name: The layer's name, such as ``production`` or an addon's name.
        path: The file the layer was loaded from, or ``None`` when it has none.
        found: Whether the layer's file existed.
        settings: The uppercase setting names the layer wrote.
    """

    name: str
    path: str | None
    found: bool
    settings: tuple[str, ...] = field(default_factory=tuple)


class Provenance:
    """The ordered record of layers the most recent ``setup()`` call composed."""

    def __init__(self) -> None:
        self._layers: list[Layer] = []

    def reset(self) -> None:
        """Clear the record so a second ``setup()`` call replaces it rather than appends."""
        self._layers = []

    def add_layer(self, name: str, path: str | None, found: bool, settings) -> None:
        """Append one layer's outcome, in the order ``setup()`` applied it.

        Args:
            name: The layer's name.
            path: The file the layer was loaded from, or ``None``.
            found: Whether the layer's file existed.
            settings: The setting names the layer wrote.
        """
        self._layers.append(
            Layer(name=name, path=path, found=found, settings=tuple(settings))
        )

    def layers(self) -> list[Layer]:
        """Return every layer considered, in application order.

        Returns:
            A copy of the recorded layers.
        """
        return list(self._layers)

    def producer(self, setting: str) -> Layer | None:
        """Return the layer that produced ``setting``'s final resolved value, if any.

        Later layers override earlier ones, so the producer is the *last* layer whose
        settings include this name. A layer is credited when it changed the value, not
        merely when it assigned one.

        Args:
            setting: The setting name to look up.

        Returns:
            The producing layer, or ``None`` when no layer wrote the setting.
        """
        for layer in reversed(self._layers):
            if setting in layer.settings:
                return layer
        return None

    def replace(self, layers) -> None:
        """Restore a previously captured layer list, discarding the current one.

        Args:
            layers: The layers to restore, in application order.
        """
        self._layers = list(layers)


#: One instance per process. A settings module executes once, so ``setup()``
#: mutates this in place.
record = Provenance()

from .setup import setup

__all__ = ["setup"]

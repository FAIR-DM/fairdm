"""
FairDM Configuration Package.

Provides a production-ready Django configuration baseline, layered with
environment overrides selected by the DJANGO_ENV variable, and addon
integration.

Also holds ``record``, the provenance of the layers ``setup()`` composes
(FR-019, FR-020, research R2). ``setup()`` snapshots the caller's scope
before and after each layer's ``include()`` call and records the delta —
the uppercase setting names that layer wrote. Never a value: the scope
holds ``SECRET_KEY``, the database password and the email password, so a
value here would leak into whatever reads this record.

The record lives here rather than in settings so it never appears in a
settings dump or serialisation. ``show_config``, the interrogation
command, reads it after ``django.setup()`` has populated the app registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Layer:
    """One layer ``setup()`` considered, in application order."""

    name: str
    path: str | None
    found: bool
    settings: tuple[str, ...] = field(default_factory=tuple)


class Provenance:
    """The ordered record of layers the most recent ``setup()`` call composed."""

    def __init__(self) -> None:
        self._layers: list[Layer] = []

    def reset(self) -> None:
        """Clear the record. ``setup()`` calls this before composing layers,
        so a second call in the same process replaces the record rather than
        appending to it."""
        self._layers = []

    def add_layer(self, name: str, path: str | None, found: bool, settings) -> None:
        """Append one layer's outcome, in the order ``setup()`` applied it."""
        self._layers.append(
            Layer(name=name, path=path, found=found, settings=tuple(settings))
        )

    def layers(self) -> list[Layer]:
        """Every layer considered, in application order."""
        return list(self._layers)

    def producer(self, setting: str) -> Layer | None:
        """The layer that produced ``setting``'s final resolved value, if any.

        The layer list is in application order, later layers overriding
        earlier ones (FR-008), so the producer is the *last* layer whose
        settings include this name.
        """
        for layer in reversed(self._layers):
            if setting in layer.settings:
                return layer
        return None

    def replace(self, layers) -> None:
        """Restore a previously captured layer list, discarding the current one."""
        self._layers = list(layers)


#: One instance for the process. A Django settings module executes once per
#: process, so ``setup()`` mutates this in place rather than each caller
#: holding its own.
record = Provenance()

from .setup import setup

__all__ = ["setup"]

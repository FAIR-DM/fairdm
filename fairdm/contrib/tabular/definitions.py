"""The one place the import pages, the export menu and the import record find what a file holds.

An import definition names a kind of file and says everything the workflow needs about it: the
record type it fills, its columns, the resource that reads it, the formats it is offered in and
the rows an export writes. Every page asks for a definition by name through ``get_definition``
and never works these out itself.

FairDM builds one definition for every registered sample and measurement type, named after the
type (``soilsample``), so each type keeps the import it has always had. A project can add its
own with ``register``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fairdm.core.measurement.models import Measurement
from fairdm.registry import registry

from .exports import FORMATS
from .resources import build_resource
from .schema import TableSchema, schema_for


@dataclass(frozen=True)
class ImportDefinition:
    """What one kind of file holds and how it goes in and out.

    Attributes:
        name: The name pages, addresses and import records know it by.
        model: The record type its rows fill.
        formats: The file formats it is offered and read in, keys of ``exports.FORMATS``.
    """

    name: str
    model: type
    formats: tuple[str, ...] = field(default=tuple(FORMATS))

    @property
    def kind(self) -> str:
        return "measurement" if issubclass(self.model, Measurement) else "sample"

    def columns(self) -> TableSchema:
        """The columns of the file, with their guide."""
        return schema_for(self.model)

    def resource(self, dataset, columns=None, schema=None):
        """The resource class that reads the file into ``dataset``."""
        return build_resource(schema or self.columns(), dataset, columns=columns)

    def export_rows(self, queryset):
        """The rows an export of ``queryset`` writes, in a stable order."""
        return queryset.order_by("pk")


_added: dict[str, ImportDefinition] = {}


def register(definition: ImportDefinition) -> ImportDefinition:
    """Add a project's own definition. Its name must not be one already known."""
    if definition.name in {d.name for d in definitions()}:
        raise ValueError(f"An import definition named {definition.name!r} already exists.")
    _added[definition.name] = definition
    return definition


def built_in() -> list[ImportDefinition]:
    """One definition per registered type: every sample type, then every measurement type."""
    return [
        ImportDefinition(name=model._meta.model_name, model=model)
        for model in [*registry.samples, *registry.measurements]
    ]


def definitions(kind: str | None = None) -> list[ImportDefinition]:
    """Every definition, or only those whose rows are ``sample`` or ``measurement`` records."""
    found = [*built_in(), *_added.values()]
    if kind:
        found = [d for d in found if d.kind == kind]
    return found


def get_definition(name) -> ImportDefinition | None:
    """The definition called ``name``, or None."""
    return next((d for d in definitions() if d.name == name), None)


def definition_for_model(model) -> ImportDefinition | None:
    """The definition FairDM built for a registered type, or None."""
    return get_definition(model._meta.model_name)

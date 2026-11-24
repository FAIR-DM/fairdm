"""The import definitions: what each kind of file holds and where it is found.

A definition names a kind of file, the record type its rows fill and the formats it is
offered in. FairDM builds one for every registered sample and measurement type, named
after the type (``rocksample``). A project adds its own with ``register``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings

from fairdm.contrib.import_export.resources import RecordResource, build_resource
from fairdm.core.measurement.models import Measurement
from fairdm.registry import registry

if TYPE_CHECKING:
    from fairdm.contrib.import_export.schema import TableSchema


@dataclass(frozen=True)
class ImportDefinition:
    """What one kind of file holds and the formats it is offered in.

    Attributes:
        name: The name pages and addresses know the definition by.
        model: The registered sample or measurement model its rows fill.
        formats: The names of the file formats it is offered in.
    """

    name: str
    model: type
    formats: tuple[str, ...]

    @property
    def kind(self) -> str:
        """Whether the rows are ``sample`` or ``measurement`` records.

        Returns:
            The word for the model's kind.
        """
        return "measurement" if issubclass(self.model, Measurement) else "sample"

    def table_schema(self) -> TableSchema:
        """Build the columns of the file from the model's configuration.

        Returns:
            The table schema of the registered model.
        """
        return registry.get_for_model(self.model).get_table_schema()

    def resource(self, dataset, **options) -> RecordResource:
        """Build the resource that imports a file of this type into a dataset.

        Args:
            dataset: The dataset the rows are added to and changed in.
            **options: ``mode``, ``empty``, ``user`` and ``columns``, as
                ``build_resource`` takes them.

        Returns:
            The resource, ready to import one file.
        """
        return build_resource(self.table_schema(), dataset, **options)


class ImportDefinitions:
    """The import definitions of a portal: the built-in ones and those it adds.

    Attributes:
        added: The definitions a project registered, by name.
    """

    def __init__(self) -> None:
        """Start with no definition added."""
        self.added: dict[str, ImportDefinition] = {}

    @staticmethod
    def format_names() -> tuple[str, ...]:
        """Name the formats the portal reads, from ``settings.IMPORT_FORMATS``.

        Returns:
            The lower-case title of each format that can be imported.
        """
        return tuple(
            format_class().get_title().lower()
            for format_class in settings.IMPORT_FORMATS
            if format_class().can_import()
        )

    def built_in(self) -> list[ImportDefinition]:
        """Build one definition per registered type, samples first.

        Returns:
            The definitions, named by each model's lower-case name.
        """
        formats = self.format_names()
        return [
            ImportDefinition(name=model._meta.model_name, model=model, formats=formats)
            for model in [*registry.samples, *registry.measurements]
        ]

    def register(self, definition: ImportDefinition) -> ImportDefinition:
        """Add a project's own definition.

        Args:
            definition: The definition to add.

        Returns:
            The definition, once added.

        Raises:
            ValueError: The name is already known, or the model is not registered.
        """
        if self.get(definition.name) is not None:
            raise ValueError(f"An import definition named {definition.name!r} exists.")
        if not registry.is_registered(definition.model):
            raise ValueError(f"{definition.model.__name__} is not registered.")
        self.added[definition.name] = definition
        return definition

    def all(self, kind: str | None = None) -> list[ImportDefinition]:
        """List the definitions, built in first.

        Args:
            kind: ``sample`` or ``measurement`` to keep only that kind. Defaults to all.

        Returns:
            The matching definitions.
        """
        found = [*self.built_in(), *self.added.values()]
        if kind:
            found = [definition for definition in found if definition.kind == kind]
        return found

    def get(self, name: str) -> ImportDefinition | None:
        """Find a definition by name.

        Args:
            name: The definition's name.

        Returns:
            The definition, or None when no definition has the name.
        """
        return next((d for d in self.all() if d.name == name), None)


import_definitions = ImportDefinitions()
register = import_definitions.register
get_definition = import_definitions.get

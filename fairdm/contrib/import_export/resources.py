"""The import of one type of record into one dataset.

``build_resource`` turns a type's table schema into a ``RecordResource`` bound to a
dataset. The resource does the reading, the checking and the saving of a file's rows.
What it adds to django-import-export:

- rows are matched to stored records by portal ID, then by Local ID within the dataset,
- the chosen mode leaves out the rows the person did not ask for, with the reason kept,
- an empty cell keeps the stored value unless the person asked for it to be cleared,
- every cell a row changes is kept as old and new, which the review screen shows.
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from import_export import fields, resources

from fairdm.core.measurement.models import Measurement
from fairdm.core.sample.models import Sample
from fairdm.utils.location.resources import (
    LOCATION_COLUMNS,
    LocatedResourceMixin,
    location_fields,
)

from .widgets import CellWidget, render_cell


class RowProblem(Exception):
    """A row that cannot be imported, with the column its problem belongs to.

    Attributes:
        column: The heading of the column the problem is in.
        message: What is wrong, in words the person can act on.
    """

    def __init__(self, column: str, message: str) -> None:
        """Keep the column and the message.

        Args:
            column: The heading of the column the problem is in.
            message: What is wrong.
        """
        super().__init__(message)
        self.column = column
        self.message = message


class RecordResource(LocatedResourceMixin, resources.ModelResource):
    """The import of one type into one dataset, built for a file by ``build_resource``.

    Row numbers count from 1 in the order of the file.

    Attributes:
        schema: The columns of the type.
        dataset: The dataset the rows are added to and changed in.
        mode: ``both``, ``add`` or ``update``.
        empty: ``keep`` to leave a stored value where the cell is empty, ``clear`` to
            empty it.
        notes: Why a row was left out, by row number.
        changes: The cells an updated row changes, by row number, as listed by
            ``changed_cells``.
        record_pks: The primary key of the stored record each row matched, by row
            number. A row that adds a record has none here: its record's key is on the
            row's result once it is saved.
        on_row: A function called with the number of rows done after each row, or None.
        row_number: The row being imported.
        rows_done: How many rows have been imported so far.
        located: The record the current row's portal ID names, or None.
    """

    schema = None

    def __init__(self, dataset, mode: str = "both", empty: str = "keep") -> None:
        """Keep the dataset and the options of the import.

        Args:
            dataset: The dataset the rows are added to and changed in.
            mode: ``both``, ``add`` or ``update``.
            empty: ``keep`` or ``clear``.
        """
        super().__init__()
        self.dataset = dataset
        self.mode = mode
        self.empty = empty
        self.notes: dict[int, str] = {}
        self.changes: dict[int, list[dict]] = {}
        self.record_pks: dict[int, int] = {}
        self.on_row = None
        self.row_number = 0
        self.rows_done = 0
        self.located = None

    @property
    def base_model(self) -> type:
        """The model a portal ID is looked up in, whatever the record's type.

        Returns:
            ``Sample`` or ``Measurement``.
        """
        return Sample if issubclass(self._meta.model, Sample) else Measurement

    def import_row(self, row, instance_loader, **kwargs):
        """Import one row, or leave it out when its portal ID names another dataset.

        Args:
            row: The row, as a dict of heading to cell.
            instance_loader: The loader django-import-export passes on.
            **kwargs: What django-import-export passes on, including ``row_number``.

        Returns:
            The row's result.
        """
        self.row_number = kwargs["row_number"]
        portal_id = CellWidget.text_of(row.get("portal_id"))
        self.located = (
            self.base_model.objects.filter(uuid=portal_id).first()
            if portal_id
            else None
        )
        if self.located is not None and self.located.dataset_id != self.dataset.pk:
            result = self.leave_out_other_dataset()
        else:
            result = super().import_row(row, instance_loader, **kwargs)
        self.rows_done += 1
        if self.on_row:
            self.on_row(self.rows_done)
        return result

    def leave_out_other_dataset(self):
        """Skip the current row and say why.

        An import adds and changes only this dataset's records. Only a measurement has a
        way to use another dataset's record, by naming one of its samples.

        Returns:
            A skipped row result.
        """
        if issubclass(self._meta.model, Sample):
            note = _(
                "Belongs to another dataset. An import adds and changes only this "
                "dataset's records."
            )
        else:
            note = _(
                "Belongs to another dataset. An import adds and changes only this "
                "dataset's records. A measurement made here can name a sample from "
                "another dataset in the sample column."
            )
        self.notes[self.row_number] = note
        result = self.get_row_result_class()()
        result.import_type = result.IMPORT_TYPE_SKIP
        return result

    def get_instance(self, instance_loader, row):
        """Find the stored record a row is about.

        Args:
            instance_loader: The loader django-import-export passes on.
            row: The row.

        Returns:
            The record the portal ID names, else the one with the Local ID in the
            dataset, else None.

        Raises:
            RowProblem: The portal ID names no record or a record of another type, or
                the Local ID is held by several records.
        """
        model = self._meta.model
        portal_id = CellWidget.text_of(row.get("portal_id"))
        if portal_id:
            if self.located is None:
                raise RowProblem(
                    "portal_id",
                    _("No record has this portal ID."),
                )
            if not isinstance(self.located, model):
                raise RowProblem(
                    "portal_id",
                    _("This portal ID belongs to a %(other)s, not a %(this)s.")
                    % {
                        "other": self.located._meta.verbose_name,
                        "this": model._meta.verbose_name,
                    },
                )
            self.record_pks[self.row_number] = self.located.pk
            return self.located
        local_id = CellWidget.text_of(row.get("local_id"))
        if not local_id:
            return None
        matches = list(
            model.objects.filter(dataset=self.dataset, local_id=local_id)[:2]
        )
        if len(matches) > 1:
            raise RowProblem(
                "local_id",
                _(
                    "Several records in this dataset have this Local ID. Add the "
                    "portal ID to say which."
                ),
            )
        if matches:
            self.record_pks[self.row_number] = matches[0].pk
            return matches[0]
        return None

    def init_instance(self, row=None):
        """Start a new record in the dataset.

        Args:
            row: The row.

        Returns:
            An unsaved record of the type.
        """
        return self._meta.model(dataset=self.dataset)

    def import_instance(self, instance, row, **kwargs):
        """Settle the row's empty cells, then read the rest into the record.

        Args:
            instance: The new or stored record.
            row: The row.
            **kwargs: What django-import-export passes on.

        Raises:
            ValidationError: The empty required cells and the cells that cannot be
                read, each under its column.
        """
        errors = self.settle_empty_cells(instance, row)
        try:
            super().import_instance(instance, row, **kwargs)
        except ValidationError as error:
            errors = error.update_error_dict(errors)
        if errors:
            raise ValidationError(errors)

    def settle_empty_cells(self, instance, row) -> dict:
        """Drop the empty cells that change nothing and refuse those that would.

        A new record has nothing to clear, so its empty cells are left to the model's
        defaults. A stored record keeps its value where the cell is empty unless the
        person asked for empty cells to clear it.

        Args:
            instance: The new or stored record.
            row: The row, which loses the empty cells that are left out.

        Returns:
            The problems, by column: an empty cell in a column a record needs, on a new
            record or on one whose empty cells are to be cleared. Empty when none.
        """
        errors = {}
        is_new = instance.pk is None
        clearing = not is_new and self.empty == "clear"
        for column in self.schema.importable:
            if column.role == "key" or column.name not in row:
                continue
            if not CellWidget.is_empty(row[column.name]):
                continue
            if column.required and (is_new or clearing):
                message = (
                    _("A %(label)s is needed here, and this cell is empty.")
                    if is_new
                    else _("The %(label)s cannot be emptied, as the record needs one.")
                )
                errors[column.name] = [
                    ValidationError(message % {"label": column.label}, code="required")
                ]
            if not clearing:
                del row[column.name]
        return errors

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """Leave out a row the mode does not ask for, or one that changes nothing.

        Args:
            instance: The record with the row's cells read into it.
            original: The record as it was stored, or an unsaved copy for a new one.
            row: The row.
            import_validation_errors: The problems found reading the row's cells.

        Returns:
            Whether the row is left out.
        """
        is_new = original is None or original.pk is None
        if self.mode == "add" and not is_new:
            self.notes[self.row_number] = _(
                "Matches a record, and this import only adds new records."
            )
            return True
        if self.mode == "update" and is_new:
            self.notes[self.row_number] = _(
                "Matches no record in the dataset, and this import only updates."
            )
            return True
        if is_new or import_validation_errors:
            return False
        changes = changed_cells(self.schema, original, instance, row)
        self.changes[self.row_number] = changes
        return not changes


def changed_cells(schema, original, instance, row) -> list[dict]:
    """List the cells a row changes in a stored record.

    Only the columns the row has are compared, as the cells an export would write.

    Args:
        schema: The type's table schema.
        original: The record as it was stored.
        instance: The record with the row's cells read into it.
        row: The row.

    Returns:
        One dict of ``column``, ``label``, ``old`` and ``new`` for each changed cell, in
        the order of the columns.
    """
    changes = []
    for column in schema.importable:
        if column.role == "key" or column.name not in row:
            continue
        old = render_cell(column, original)
        new = render_cell(column, instance)
        if old == new:
            continue
        changes.append(
            {"column": column.name, "label": str(column.label), "old": old, "new": new}
        )
    return changes


def build_resource(
    schema, dataset, mode="both", empty="keep", user=None, columns=None
) -> RecordResource:
    """Build the resource that imports a file of a type into a dataset.

    Args:
        schema: The type's table schema.
        dataset: The dataset the rows are added to and changed in.
        mode: ``both``, ``add`` or ``update``.
        empty: ``keep`` or ``clear``.
        user: The person importing, whose view of the samples a measurement may name.
        columns: The headings the file has. Defaults to every importable column.

    Returns:
        A resource that reads those columns. It holds one widget per column, so a
        sample cell is looked up once for the whole file.
    """
    wanted = None if columns is None else set(columns)
    declared = {}
    for column in schema.importable:
        if column.role == "key" or (wanted is not None and column.name not in wanted):
            continue
        if column.name in LOCATION_COLUMNS:
            declared[column.name] = location_fields()[column.name]
        else:
            declared[column.name] = fields.Field(
                attribute=column.attribute,
                column_name=column.name,
                widget=column.widget(dataset=dataset, user=user),
            )
    options = type(
        "Meta",
        (),
        {
            "model": schema.model,
            "fields": tuple(declared),
            "skip_unchanged": False,
            "report_skipped": True,
            "clean_model_instances": False,
            "use_transactions": True,
        },
    )
    resource_class = type(
        f"{schema.model.__name__}Import",
        (RecordResource,),
        {**declared, "Meta": options, "schema": schema},
    )
    return resource_class(dataset, mode=mode, empty=empty)

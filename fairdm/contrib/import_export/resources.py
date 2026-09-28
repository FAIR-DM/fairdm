"""django-import-export resources for samples and measurements."""

from import_export import fields
from import_export.resources import ModelResource
from import_export.widgets import ForeignKeyWidget

from fairdm.core.models import Sample


class BaseFairDMResource(ModelResource):
    """Shared base class for Sample and Measurement resources.

    Args:
        dataset: The dataset that imported rows are attributed to.
        *args: Passed to ``ModelResource``.
        **kwargs: Passed to ``ModelResource``.
    """

    def __init__(self, dataset, *args, **kwargs):
        self.dataset = dataset
        super().__init__(*args, **kwargs)

    def for_delete(self, row, instance):
        """Delete the row's record when its ``delete`` column is ``1``."""
        return row.get("delete") == "1"

    def before_import_row(self, row, **kwargs):
        """Attribute the row to the resource's dataset."""
        row["dataset"] = self.dataset.uuid
        return super().before_import_row(row, **kwargs)

    def get_import_order(self):
        """Append the dataset and sample columns to the import order."""
        return [*super().get_import_order(), "dataset", "sample"]

    def get_export_order(self):
        """Leave the dataset column out of exports but keep it for import."""
        fields = list(super().get_export_order())
        if "dataset" in fields:
            fields.remove("dataset")
        return fields

    def _get_ordered_field_names(self, order_field):
        """Put the id and dataset columns first."""
        fields = list(super()._get_ordered_field_names(order_field))
        if "id" not in fields:
            fields = ["id", *fields]
        if "dataset" not in fields:
            fields = ["dataset", *fields]

        return fields


class SampleResource(BaseFairDMResource):
    """Resource for importing and exporting samples."""

    class Meta:
        fields = (
            "dataset",
            "id",
            "local_id",
            "name",
            "char_field",
        )

    def get_instance(self, instance_loader, row):
        """Find the existing sample by id, or by local id within the dataset."""
        dataset_id = row.get("dataset")
        obj_id = row.get("id")
        local_id = row.get("local_id")

        if obj_id:
            return self.model.objects.filter(id=obj_id).first()
        elif local_id and dataset_id:
            return self.model.objects.filter(
                local_id=local_id, dataset_id=dataset_id
            ).first()

        return None


class SampleWidget(ForeignKeyWidget):
    """Resolve a sample from a UUID or from its name within the row's dataset.

    Args:
        model: The sample model. Defaults to ``Sample``.
        **kwargs: Passed to ``ForeignKeyWidget``.
    """

    def __init__(self, model=None, **kwargs):
        super().__init__(model=model or Sample, **kwargs)

    def clean(self, value, row=None, *args, **kwargs):
        """Look the sample up by UUID (a 23-character value starting with ``s``), else by name."""
        if value and value.startswith("s") and len(value) == 23:
            return self.model.objects.filter(uuid=value).first()

        elif value:
            return self.model.objects.filter(name=value, dataset=row["dataset"]).first()
        return None


class MeasurementResource(BaseFairDMResource):
    """Resource for importing and exporting measurements."""

    sample = fields.Field(
        attribute="sample", column_name="sample", widget=SampleWidget()
    )

    def get_instance(self, instance_loader, row):
        """Find the existing measurement by id, or by name within the dataset."""
        dataset = row.get("dataset")
        obj_id = row.get("id")
        name = row.get("name")
        row.get("sample")

        if obj_id:
            return self._meta.model.objects.filter(id=obj_id).first()

        elif name and dataset:
            # Raises if several measurements in the dataset share the name.
            obj = self._meta.model.objects.get(name=name, dataset=dataset)
            if obj:
                # A blank id would otherwise create a new record instead of updating this one.
                del row["id"]
                return obj
        return None

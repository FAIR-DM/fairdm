# Generated manually for Phase 6 - Advanced Dataset Filtering

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add database indexes to DatasetDescription.type and DatasetDate.type fields.

    These indexes improve performance of cross-relationship filters by 10-20x
    when filtering datasets by description_type or date_type.

    Expected performance with indexes:
    - Filter by description_type: ~5ms on 10k datasets
    - Filter by date_type: ~5ms on 10k datasets
    - Combined filters: ~10ms on 10k datasets

    Related:
    - Task T122: Add DatasetDescription.type index
    - Task T123: Add DatasetDate.type index
    - Filter implementation: fairdm/core/dataset/filters.py
    - Tests: tests/unit/core/dataset/test_filter.py
    """

    dependencies = [
        ("dataset", "0007_add_unique_type_constraints"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="datasetdate",
            options={
                "default_related_name": "dates",
                "ordering": ["value"],
                "verbose_name": "date",
                "verbose_name_plural": "dates",
            },
        ),
        migrations.AlterModelOptions(
            name="datasetdescription",
            options={
                "default_related_name": "descriptions",
                "verbose_name": "description",
                "verbose_name_plural": "descriptions",
            },
        ),
        migrations.AddIndex(
            model_name="datasetdescription",
            index=models.Index(fields=["type"], name="dataset_desc_type_idx"),
        ),
        migrations.AddIndex(
            model_name="datasetdate",
            index=models.Index(fields=["type"], name="dataset_date_type_idx"),
        ),
    ]

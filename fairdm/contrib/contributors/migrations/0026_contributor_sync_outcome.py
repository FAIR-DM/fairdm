from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0025_convert_partial_dates"),
    ]

    operations = [
        migrations.AddField(
            model_name="contributor",
            name="sync_status",
            field=models.CharField(
                blank=True,
                choices=[("succeeded", "Succeeded"), ("failed", "Failed")],
                default="",
                editable=False,
                help_text=(
                    "Whether the last fetch from the external provider succeeded. "
                    "Blank until one is tried."
                ),
                max_length=16,
                verbose_name="sync status",
            ),
        ),
        migrations.AddField(
            model_name="contributor",
            name="sync_error",
            field=models.TextField(
                blank=True,
                default="",
                editable=False,
                help_text="Why the last fetch from the external provider failed.",
                verbose_name="sync error",
            ),
        ),
        migrations.AlterField(
            model_name="contributor",
            name="last_synced",
            field=models.DateField(
                blank=True,
                default=None,
                editable=False,
                help_text=(
                    "The last time a record was fetched from the external provider "
                    "(e.g. ORCID, ROR)."
                ),
                null=True,
                verbose_name="last synced",
            ),
        ),
    ]

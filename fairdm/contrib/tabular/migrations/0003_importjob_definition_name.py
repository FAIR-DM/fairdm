"""Store the name of the import definition a file was read with, instead of its model."""

from django.db import migrations, models


def copy_names(apps, schema_editor):
    ImportJob = apps.get_model("tabular", "ImportJob")
    for job in ImportJob.objects.select_related("content_type"):
        job.definition_name = job.content_type.model
        job.save(update_fields=["definition_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("tabular", "0002_alter_importjob_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="importjob",
            name="definition_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.RunPython(copy_names, migrations.RunPython.noop),
        migrations.RemoveField(model_name="importjob", name="content_type"),
    ]

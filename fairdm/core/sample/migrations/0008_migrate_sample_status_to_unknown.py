# The status vocabulary changed to custody states, and no previous term maps to one, so every row
# becomes unknown (FS-005). It uses `update()` because a `ConceptField` raises `ValueError` when a
# stored value is outside the current vocabulary. No reverse: the previous values are discarded.

from django.db import migrations


def migrate_status_to_unknown(apps, schema_editor):
    Sample = apps.get_model("sample", "Sample")
    Sample.objects.using(schema_editor.connection.alias).update(status="unknown")


class Migration(migrations.Migration):

    dependencies = [
        ("sample", "0007_alter_sample_status_alter_sample_uuid_and_more"),
    ]

    operations = [
        migrations.RunPython(migrate_status_to_unknown, migrations.RunPython.noop),
    ]

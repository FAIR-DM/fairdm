from django.db import migrations


def move_content_type(apps, schema_editor):
    """Give the tagged item's content type, and with it its permissions, to this app."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    if ContentType.objects.filter(app_label="fairdm", model="taggeditem").exists():
        return
    ContentType.objects.filter(app_label="generic", model="taggeditem").update(
        app_label="fairdm"
    )


def restore_content_type(apps, schema_editor):
    """Hand the tagged item's content type back to the old app label."""
    ContentType = apps.get_model("contenttypes", "ContentType")
    ContentType.objects.filter(app_label="fairdm", model="taggeditem").update(
        app_label="generic"
    )


class Migration(migrations.Migration):
    """Rename the tagged item table to this app's name.

    Kept apart from ``0001``, which an upgraded database never runs.
    """

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("fairdm", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(name="taggeditem", table=None),
        migrations.RunPython(move_content_type, restore_content_type),
    ]

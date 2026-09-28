from django.db import migrations


def set_is_claimed_values(apps, schema_editor):
    Person = apps.get_model("contributors", "Person")
    db_alias = schema_editor.connection.alias

    Person.objects.using(db_alias).filter(email__isnull=False).update(is_claimed=True)

    Person.objects.using(db_alias).filter(email__isnull=True).update(is_claimed=False)


def reverse_set_is_claimed(apps, schema_editor):
    Person = apps.get_model("contributors", "Person")
    Person.objects.using(schema_editor.connection.alias).update(is_claimed=None)


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0014_add_is_claimed_field"),
    ]

    operations = [
        migrations.RunPython(set_is_claimed_values, reverse_set_is_claimed),
    ]

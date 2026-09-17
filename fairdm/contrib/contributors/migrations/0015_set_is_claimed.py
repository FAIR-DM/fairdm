# Generated data migration for is_claimed BooleanField (Step 2 of 3)

from django.db import migrations


def set_is_claimed_values(apps, schema_editor):
    """
    Set is_claimed=True for existing users with email NOT NULL.
    Set is_claimed=False for users created via create_unclaimed() (email=NULL).
    
    This implements the Ghost→Invited→Claimed→Banned state machine:
    - Users with email are considered claimed
    - Users without email are ghosts (unclaimed attribution records)
    """
    Person = apps.get_model("contributors", "Person")
    db_alias = schema_editor.connection.alias

    # Set is_claimed=True for users with email (claimed accounts)
    Person.objects.using(db_alias).filter(email__isnull=False).update(is_claimed=True)

    # Set is_claimed=False for users without email (ghost profiles)
    Person.objects.using(db_alias).filter(email__isnull=True).update(is_claimed=False)


def reverse_set_is_claimed(apps, schema_editor):
    """Reverse migration: set all is_claimed to None."""
    Person = apps.get_model("contributors", "Person")
    Person.objects.using(schema_editor.connection.alias).update(is_claimed=None)


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0014_add_is_claimed_field"),
    ]

    operations = [
        migrations.RunPython(set_is_claimed_values, reverse_set_is_claimed),
    ]

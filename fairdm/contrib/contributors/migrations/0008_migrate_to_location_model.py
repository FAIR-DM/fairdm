from django.db import migrations, models
import django.db.models.deletion
import auto_prefetch


def migrate_coordinates_to_location(apps, schema_editor):
    Organization = apps.get_model('contributors', 'Organization')
    Point = apps.get_model('fairdm_location', 'Point')
    db_alias = schema_editor.connection.alias

    for org in Organization.objects.using(db_alias).exclude(lat__isnull=True, lon__isnull=True):
        if org.lat is not None and org.lon is not None:
            point, created = Point.objects.using(db_alias).get_or_create(
                x=org.lon,
                y=org.lat,
            )
            org.location = point
            org.save(using=db_alias, update_fields=['location'])


def reverse_migration(apps, schema_editor):
    Organization = apps.get_model('contributors', 'Organization')
    db_alias = schema_editor.connection.alias

    for org in Organization.objects.using(db_alias).exclude(location__isnull=True):
        if org.location:
            org.lat = org.location.y
            org.lon = org.location.x
            org.save(using=db_alias, update_fields=['lat', 'lon'])


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0007_add_unique_type_constraints'),
        ('fairdm_location', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name="contributor",
            name="location",
            field=auto_prefetch.ForeignKey(
                blank=True,
                help_text="The geographic location of the contributor.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="contributors",
                to="fairdm_location.point",
                verbose_name="location",
            ),
        ),
        
        migrations.RunPython(
            migrate_coordinates_to_location,
            reverse_migration,
        ),
        
        migrations.RemoveField(
            model_name='organization',
            name='lat',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='lon',
        ),
    ]

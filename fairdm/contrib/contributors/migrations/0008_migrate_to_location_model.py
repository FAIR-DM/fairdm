# Generated migration to move Organization lat/lon to Location model

from django.db import migrations, models
import django.db.models.deletion
import auto_prefetch


def migrate_coordinates_to_location(apps, schema_editor):
    """
    Migrate existing lat/lon coordinates from Organization to Point objects.
    
    For each organization with lat/lon coordinates:
    1. Get or create a Point object with those coordinates
    2. Link the organization to that Point
    """
    Organization = apps.get_model('contributors', 'Organization')
    Point = apps.get_model('fairdm_location', 'Point')
    
    for org in Organization.objects.exclude(lat__isnull=True, lon__isnull=True):
        if org.lat is not None and org.lon is not None:
            # Point model uses x=longitude, y=latitude
            point, created = Point.objects.get_or_create(
                x=org.lon,
                y=org.lat,
            )
            org.location = point
            org.save(update_fields=['location'])


def reverse_migration(apps, schema_editor):
    """
    Reverse the migration by copying location data back to lat/lon fields.
    
    Note: This will be called if the migration is rolled back.
    """
    Organization = apps.get_model('contributors', 'Organization')
    
    for org in Organization.objects.exclude(location__isnull=True):
        if org.location:
            org.lat = org.location.y
            org.lon = org.location.x
            org.save(update_fields=['lat', 'lon'])


class Migration(migrations.Migration):

    dependencies = [
        ('contributors', '0007_add_unique_type_constraints'),
        ('fairdm_location', '0001_initial'),
    ]

    operations = [
        # Step 1: Add the new location field (nullable)
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
        
        # Step 2: Migrate data from lat/lon to location
        migrations.RunPython(
            migrate_coordinates_to_location,
            reverse_migration,
        ),
        
        # Step 3: Remove old lat/lon fields
        migrations.RemoveField(
            model_name='organization',
            name='lat',
        ),
        migrations.RemoveField(
            model_name='organization',
            name='lon',
        ),
    ]

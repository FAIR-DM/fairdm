from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("fairdm_location", "0001_initial"),
        ("contributors", "0024_organization_location"),
        ("sample", "0012_located_samples"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Point",
        ),
    ]

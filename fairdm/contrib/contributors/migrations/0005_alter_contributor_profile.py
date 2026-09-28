from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0004_delete_contributorrole_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contributor",
            name="profile",
            field=models.TextField(blank=True, null=True, verbose_name="profile"),
        ),
    ]

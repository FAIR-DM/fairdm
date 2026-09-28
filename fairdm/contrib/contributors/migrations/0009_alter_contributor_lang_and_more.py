from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0008_migrate_to_location_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contributor",
            name="lang",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="ISO 639-1 language codes (e.g., 'en', 'es', 'fr').",
                null=True,
                verbose_name="language",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="organizationmember",
            unique_together={("person", "organization")},
        ),
    ]

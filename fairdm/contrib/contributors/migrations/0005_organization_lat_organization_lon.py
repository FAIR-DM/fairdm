# Generated by Django 5.1.6 on 2025-05-16 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0004_remove_person_added_remove_person_modified_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="lat",
            field=models.DecimalField(
                blank=True,
                decimal_places=5,
                help_text="The latitude of the organization.",
                max_digits=7,
                null=True,
                verbose_name="latitude",
            ),
        ),
        migrations.AddField(
            model_name="organization",
            name="lon",
            field=models.DecimalField(
                blank=True,
                decimal_places=5,
                help_text="The longitude of the organization.",
                max_digits=8,
                null=True,
                verbose_name="longitude",
            ),
        ),
    ]

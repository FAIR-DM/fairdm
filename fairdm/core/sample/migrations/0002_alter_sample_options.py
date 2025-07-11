# Generated by Django 5.1.6 on 2025-06-27 07:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("sample", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sample",
            options={
                "default_related_name": "samples",
                "ordering": ["added"],
                "permissions": [
                    ("add_contributor", "Can add contributors"),
                    ("modify_contributor", "Can modify contributors"),
                    ("modify_metadata", "Can modify metadata"),
                ],
                "verbose_name": "sample",
                "verbose_name_plural": "samples",
            },
        ),
    ]

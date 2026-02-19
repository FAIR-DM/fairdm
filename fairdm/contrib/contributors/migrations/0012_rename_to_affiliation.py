"""Rename OrganizationMember model to Affiliation."""

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0011_add_partial_dates_and_privacy"),
    ]

    operations = [
        # Rename the model (auto-updates FK references and table name)
        migrations.RenameModel(
            old_name="OrganizationMember",
            new_name="Affiliation",
        ),
    ]

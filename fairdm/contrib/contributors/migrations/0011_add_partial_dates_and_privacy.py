"""Add start_date/end_date PartialDateFields to OrganizationMember, privacy_settings to Contributor, remove is_current."""

import fairdm.db.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0010_alter_contributoridentifier_managers"),
    ]

    operations = [
        # Add privacy_settings to Contributor
        migrations.AddField(
            model_name="contributor",
            name="privacy_settings",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Per-field privacy controls. Keys: field names. Values: 'public' or 'private'.",
                verbose_name="privacy settings",
            ),
        ),
        # Add start_date to OrganizationMember
        migrations.AddField(
            model_name="organizationmember",
            name="start_date",
            field=fairdm.db.fields.PartialDateField(
                blank=True,
                null=True,
                help_text="When the affiliation began. Supports year, year-month, or full date precision.",
                verbose_name="start date",
            ),
        ),
        # Add end_date to OrganizationMember
        migrations.AddField(
            model_name="organizationmember",
            name="end_date",
            field=fairdm.db.fields.PartialDateField(
                blank=True,
                null=True,
                help_text="When the affiliation ended. Leave blank for active affiliations.",
                verbose_name="end date",
            ),
        ),
        # Remove is_current (replaced by end_date logic)
        migrations.RemoveField(
            model_name="organizationmember",
            name="is_current",
        ),
        # Update type field help_text
        migrations.AlterField(
            model_name="organizationmember",
            name="type",
            field=models.IntegerField(
                choices=[
                    (0, "Pending"),
                    (1, "Member"),
                    (2, "Admin"),
                    (3, "Owner"),
                ],
                default=1,
                help_text="The verification state / role of the person within the organization.",
                verbose_name="type",
            ),
        ),
    ]

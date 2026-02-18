"""Update related_names and Organization meta options."""

import auto_prefetch
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0012_rename_to_affiliation"),
    ]

    operations = [
        # Update person FK related_name from "organization_memberships" to "affiliations"
        migrations.AlterField(
            model_name="affiliation",
            name="person",
            field=auto_prefetch.ForeignKey(
                help_text="The person that is a member of the organization.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="affiliations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="person",
            ),
        ),
        # Update Organization.members M2M to use Affiliation through model
        migrations.AlterField(
            model_name="organization",
            name="members",
            field=models.ManyToManyField(
                help_text="A list of personal contributors that are members of the organization.",
                related_name="+",
                through="contributors.Affiliation",
                to=settings.AUTH_USER_MODEL,
                verbose_name="members",
            ),
        ),
        # Add manage_organization permission to Organization
        migrations.AlterModelOptions(
            name="organization",
            options={
                "permissions": [("manage_organization", "Can manage organization")],
                "verbose_name": "organization",
                "verbose_name_plural": "organizations",
            },
        ),
    ]

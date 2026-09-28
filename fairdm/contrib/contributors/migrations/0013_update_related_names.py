import auto_prefetch
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0012_rename_to_affiliation"),
    ]

    operations = [
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
        migrations.AlterModelOptions(
            name="organization",
            options={
                "permissions": [("manage_organization", "Can manage organization")],
                "verbose_name": "organization",
                "verbose_name_plural": "organizations",
            },
        ),
    ]

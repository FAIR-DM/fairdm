# Generated migration for is_claimed BooleanField (Step 1 of 3)

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0013_update_related_names"),
    ]

    operations = [
        migrations.AddField(
            model_name="person",
            name="is_claimed",
            field=models.BooleanField(
                null=True,
                blank=True,
                help_text="True if this person has claimed their account. False for ghost/invited profiles.",
            ),
        ),
    ]

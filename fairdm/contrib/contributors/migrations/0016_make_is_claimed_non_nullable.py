# Generated migration for is_claimed BooleanField (Step 3 of 3)

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contributors", "0015_set_is_claimed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="is_claimed",
            field=models.BooleanField(
                default=False,
                help_text="True if this person has claimed their account. False for ghost/invited profiles.",
            ),
        ),
    ]

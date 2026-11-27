from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0027_person_preferences"),
    ]

    operations = [
        migrations.AddField(
            model_name="contribution",
            name="in_citation",
            field=models.BooleanField(
                db_default=True,
                default=True,
                help_text=(
                    "Whether the person is named in the record's citation and in the creator "
                    "lists of its metadata. When off, they are still credited and listed on "
                    "the record. An organization is always named."
                ),
                verbose_name="in the citation",
            ),
        ),
    ]

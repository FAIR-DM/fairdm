from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="Member",
        ),
        migrations.RemoveField(
            model_name="person",
            name="is_member",
        ),
        migrations.RemoveField(
            model_name="person",
            name="member_since",
        ),
    ]

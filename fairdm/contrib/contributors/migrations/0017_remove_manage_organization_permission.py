import auto_prefetch
import django.db.models.deletion
from django.db import migrations, models


def cleanup_guardian_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias

    try:
        org_ct = ContentType.objects.using(db_alias).get(
            app_label="contributors", model="organization"
        )
    except ContentType.DoesNotExist:
        return

    Permission.objects.using(db_alias).filter(
        content_type=org_ct,
        codename="manage_organization"
    ).delete()

    try:
        UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
        UserObjectPermission.objects.using(db_alias).filter(
            permission__content_type=org_ct,
            permission__codename="manage_organization"
        ).delete()
    except LookupError:
        pass

    try:
        GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")
        GroupObjectPermission.objects.using(db_alias).filter(
            permission__content_type=org_ct,
            permission__codename="manage_organization"
        ).delete()
    except LookupError:
        pass


def reverse_cleanup(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0016_make_is_claimed_non_nullable"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="organization",
            options={
                "verbose_name": "organization",
                "verbose_name_plural": "organizations",
            },
        ),
        migrations.RunPython(cleanup_guardian_permissions, reverse_cleanup),
        migrations.AlterField(
            model_name="affiliation",
            name="organization",
            field=auto_prefetch.ForeignKey(
                help_text="The organization that the person is a member of.",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="affiliations",
                to="contributors.organization",
                verbose_name="organization",
            ),
        ),
        migrations.AlterField(
            model_name="person",
            name="is_claimed",
            field=models.BooleanField(
                default=False,
                help_text="True if this person has claimed their account. False for ghost/invited profiles.",
                verbose_name="is claimed",
            ),
        ),
    ]

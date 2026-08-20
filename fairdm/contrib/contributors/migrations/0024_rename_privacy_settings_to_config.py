# Replace Contributor.privacy_settings with the general-purpose config store (D9, R3).
#
# A rename preserves the column and its contents; a new field plus a drop would not.
# The column's only possible content is the "email": "public"/"private" key that
# Person.save() used to seed, which described a policy this specification removes. It is
# cleared by the data migration below rather than left as a stale instruction for whatever
# eventually reads the store.

from django.db import migrations, models
import django.utils.translation


def clear_config(apps, schema_editor):
    Contributor = apps.get_model("contributors", "Contributor")
    Contributor.objects.update(config={})


def reverse_clear_config(apps, schema_editor):
    # Nothing to restore: the cleared contents were a stale privacy policy this
    # specification removes, not data worth recovering.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("contributors", "0023_alter_contributor_modified"),
    ]

    operations = [
        migrations.RenameField(
            model_name="contributor",
            old_name="privacy_settings",
            new_name="config",
        ),
        migrations.AlterField(
            model_name="contributor",
            name="config",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=django.utils.translation.gettext_lazy(
                    "General-purpose configuration data for this contributor. This "
                    "specification does not define its contents."
                ),
                verbose_name=django.utils.translation.gettext_lazy("configuration"),
            ),
        ),
        migrations.RunPython(clear_config, reverse_clear_config),
    ]

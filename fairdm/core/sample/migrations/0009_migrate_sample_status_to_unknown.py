# FS-005 US-5 / D-002: the sample status vocabulary changed from the previous ODM2 terms
# (complete, ongoing, planned, unknown) to a local vocabulary of custody states (available,
# in_use, stored, destroyed, unknown). None of the previous terms describes a custody state, so
# there is no mapping from old to new - every existing row is rewritten to unknown instead
# (FR-025).
#
# Rewrites through `QuerySet.update()`, never by iterating instances or reading `status` back:
# a `ConceptField` raises `ValueError` from `from_db_value` when a stored value is absent from
# the field's current vocabulary, and every previous status term now is. `update()` builds its
# `UPDATE` statement from the value passed in, not from a value read off any row, so it never
# triggers that conversion.
#
# No reverse: the previous values are discarded here and cannot be reconstructed.

from django.db import migrations


def migrate_status_to_unknown(apps, schema_editor):
    Sample = apps.get_model("sample", "Sample")
    Sample.objects.update(status="unknown")


class Migration(migrations.Migration):

    dependencies = [
        ("sample", "0008_alter_sample_status"),
    ]

    operations = [
        migrations.RunPython(migrate_status_to_unknown, migrations.RunPython.noop),
    ]

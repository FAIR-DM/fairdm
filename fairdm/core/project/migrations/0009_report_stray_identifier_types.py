# Generated for FS-003 - 0007 narrowed ProjectIdentifier.type's choices to
# DOI, GRANT_NUMBER and PROPOSAL_ID. Choices are not enforced at the
# database level, so a pre-existing row holding a type outside that set
# (e.g. ORCID, ISNI, ROR - valid under the vocabulary used for people and
# organisations) survives untouched and only fails validation the next time
# an editor happens to save it through a form.
#
# This reports any such rows rather than reassigning or deleting them -
# reassignment would change what the identifier means, which is not this
# migration's call to make. No-op in reverse: there is nothing to undo.

from django.db import migrations

#: The type set 0007 narrowed ProjectIdentifier.type's choices to.
NARROWED_IDENTIFIER_TYPES = frozenset({"DOI", "GRANT_NUMBER", "PROPOSAL_ID"})


def report_identifiers_outside_narrowed_choices(apps, schema_editor):
    ProjectIdentifier = apps.get_model("project", "ProjectIdentifier")

    stray = ProjectIdentifier.objects.exclude(type__in=NARROWED_IDENTIFIER_TYPES)
    count = stray.count()

    if count == 0:
        print("No ProjectIdentifier rows outside the narrowed type set - database is clean!")
        return

    types = sorted(stray.values_list("type", flat=True).distinct())
    print(
        f"{count} ProjectIdentifier row(s) carry a type outside the set "
        f"narrowed in 0007: {', '.join(types)}. These rows are left "
        "untouched - reassigning or deleting them would change what they mean."
    )


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0008_convert_funding_to_datacite_shape"),
    ]

    operations = [
        migrations.RunPython(
            report_identifiers_outside_narrowed_choices, migrations.RunPython.noop
        ),
    ]

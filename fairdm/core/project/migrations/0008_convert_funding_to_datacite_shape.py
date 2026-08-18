# Generated for FS-003 US-4 - convert stored funding from the retired flat
# shape ({"agency", "grant_number", "amount"}) to DataCite's funding
# reference shape (a list of {"funderName", "awardNumber", ...} objects).
#
# Rows already in the new shape (a list) and rows that match neither shape
# are left untouched. `amount` has no destination in DataCite's schema and
# is dropped (see D-013 in specs/003-core-projects/decisions.md), so this
# migration is irreversible: a reverse built from `funderName` and
# `awardNumber` alone would drop `funderIdentifier`, `funderIdentifierType`,
# `awardTitle` and `awardURI` from any record that carries them, and it
# cannot distinguish a record this migration produced from a project
# created directly in the new shape afterwards - either way it would
# rewrite data it has no business touching. No reverse is declared, so
# rolling back this migration fails loudly instead.

from django.db import migrations


def convert_flat_funding_to_datacite_shape(apps, schema_editor):
    Project = apps.get_model("project", "Project")

    for project in Project.objects.exclude(funding__isnull=True).iterator():
        funding = project.funding

        if isinstance(funding, list):
            continue  # already in the new shape

        if not isinstance(funding, dict):
            continue  # matches neither shape - leave it alone

        agency = funding.get("agency")
        if not agency:
            continue  # matches neither shape - leave it alone

        reference = {"funderName": agency}
        grant_number = funding.get("grant_number")
        if grant_number:
            reference["awardNumber"] = grant_number

        project.funding = [reference]
        project.save(update_fields=["funding"])


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0007_project_created_by_alter_project_funding_and_more"),
    ]

    operations = [
        migrations.RunPython(
            convert_flat_funding_to_datacite_shape,
            # No reverse: see the module docstring above.
        ),
    ]

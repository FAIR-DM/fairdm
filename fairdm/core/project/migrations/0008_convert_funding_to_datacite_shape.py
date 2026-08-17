# Generated for FS-003 US-4 - convert stored funding from the retired flat
# shape ({"agency", "grant_number", "amount"}) to DataCite's funding
# reference shape (a list of {"funderName", "awardNumber", ...} objects).
#
# Rows already in the new shape (a list) and rows that match neither shape
# are left untouched. `amount` has no destination in DataCite's schema and
# is dropped.

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


def revert_datacite_shape_to_flat_funding(apps, schema_editor):
    Project = apps.get_model("project", "Project")

    for project in Project.objects.exclude(funding__isnull=True).iterator():
        funding = project.funding

        if not isinstance(funding, list) or len(funding) != 1:
            continue  # not something this migration produced - leave it alone

        reference = funding[0]
        if not isinstance(reference, dict) or not reference.get("funderName"):
            continue

        flat = {"agency": reference["funderName"]}
        award_number = reference.get("awardNumber")
        if award_number:
            flat["grant_number"] = award_number

        project.funding = flat
        project.save(update_fields=["funding"])


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0007_project_created_by_alter_project_funding_and_more"),
    ]

    operations = [
        migrations.RunPython(
            convert_flat_funding_to_datacite_shape,
            revert_datacite_shape_to_flat_funding,
        ),
    ]

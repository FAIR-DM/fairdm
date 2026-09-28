# Converts stored funding from the retired flat shape ({"agency", "grant_number", "amount"}) to
# DataCite's list of funding references (FS-003). Rows in neither shape are left untouched.
# Irreversible: `amount` has no DataCite destination, and a reverse cannot tell rows apart.

from django.db import migrations


def convert_flat_funding_to_datacite_shape(apps, schema_editor):
    Project = apps.get_model("project", "Project")
    db_alias = schema_editor.connection.alias

    for project in Project.objects.using(db_alias).exclude(funding__isnull=True).iterator():
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
        project.save(using=db_alias, update_fields=["funding"])


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0007_project_created_by_alter_project_funding_and_more"),
    ]

    operations = [
        migrations.RunPython(
            convert_flat_funding_to_datacite_shape,
            # No reverse is declared, so rolling back fails loudly.
        ),
    ]

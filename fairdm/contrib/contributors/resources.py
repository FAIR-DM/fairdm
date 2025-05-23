import time

from import_export import fields, resources

from .models import Organization, OrganizationMember, Person
from .utils import update_or_create_from_orcid, update_or_create_from_ror


class PersonResource(resources.ModelResource):
    orcid = fields.Field(column_name="orcid")
    ror_id = fields.Field(column_name="ror_id")
    affiliation = fields.Field(column_name="affiliation")

    class Meta:
        model = Person
        import_id_fields = ["name"]  # or use another unique field
        skip_unchanged = True
        use_transactions = False
        skip_admin_log = True
        fields = ("name", "first_name", "last_name", "orcid", "ror_id", "affiliation")

    # def after_import_row(self, row, row_result, **kwargs):
    #     print(row["name"])

    def after_save_instance(self, instance, row, **kwargs):
        org = None
        if ror_id := row.get("ror_id"):
            org, created = update_or_create_from_ror(ror_id, name=row.get("affiliation"))

        elif row.get("affiliation") and not ror_id:
            # If no ROR ID is provided, we can still create a new organization based on the name provided in the affiliation column
            org, created = Organization.objects.get_or_create(name=row["affiliation"])

        if org:
            # Link person to organization
            OrganizationMember.objects.get_or_create(
                person=instance,
                organization=org,
                defaults={"type": OrganizationMember.MembershipType.MEMBER},
            )
        time.sleep(1.5)  # Rate limit to avoid hitting API limits

    def get_instance(self, instance_loader, row):
        # Allows reuse of instance created during before_import_row
        if orcid := row.get("orcid"):
            person, created = update_or_create_from_orcid(orcid, id=row.get("id"))
            return person
        return super().get_instance(instance_loader, row)

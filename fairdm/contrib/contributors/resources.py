"""django-import-export resource for importing people from a spreadsheet."""

import time

from django.core.exceptions import ValidationError
from import_export import fields, resources

from .models import Affiliation, ContributorIdentifier, Organization, Person
from .utils import update_or_create_from_orcid, update_or_create_from_ror


class PersonResource(resources.ModelResource):
    """Import people, their ORCID iD and their affiliation from a spreadsheet.

    Attributes:
        orcid: The person's ORCID iD.
        ror_id: The ROR id of the person's affiliation.
        affiliation: The name of the person's affiliation.
        uuid: The row's identifier, used to find the person but never written.
    """

    orcid = fields.Field(column_name="orcid")
    ror_id = fields.Field(column_name="ror_id")
    affiliation = fields.Field(column_name="affiliation")
    # Read-only so a blank or colliding cell cannot overwrite the public identifier profile URLs use.
    uuid = fields.Field(attribute="uuid", column_name="uuid", readonly=True)

    class Meta:
        model = Person
        # Names can collide by coincidence, so `uuid` alone identifies a row without an ORCID iD.
        import_id_fields = ["uuid"]
        skip_unchanged = True
        # A per-row savepoint: with ATOMIC_REQUESTS a failing row would otherwise break the
        # request's transaction and fail every later row with TransactionManagementError.
        use_transactions = True
        skip_admin_log = True
        fields = (
            "uuid",
            "name",
            "first_name",
            "last_name",
            "orcid",
            "ror_id",
            "affiliation",
        )

    def after_save_instance(self, instance, row, **kwargs):
        """Link the person to their affiliation's organisation, creating it if needed."""
        org = None
        if ror_id := row.get("ror_id"):
            org, _ = update_or_create_from_ror(ror_id, name=row.get("affiliation"))

        elif row.get("affiliation") and not ror_id:
            org, _created = Organization.objects.get_or_create(name=row["affiliation"])

        if org:
            Affiliation.objects.get_or_create(
                person=instance,
                organization=org,
                defaults={"type": Affiliation.MembershipType.MEMBER},
            )
        time.sleep(1.5)  # Stay under the external API rate limits.

    def get_instance(self, instance_loader, row):
        """Resolve the row to an existing person, or None so a new one is created.

        Args:
            instance_loader: The import-export instance loader.
            row: The spreadsheet row.

        Returns:
            The matching or newly created person, or None for a new row.

        Raises:
            ValidationError: The row matches an already-claimed person, which an import must not overwrite.
        """
        if orcid := row.get("orcid"):
            existing = ContributorIdentifier.objects.filter(
                value=orcid, type="ORCID"
            ).first()
            if (
                existing
                and isinstance(existing.related, Person)
                and existing.related.is_claimed
            ):
                raise ValidationError(
                    f"Row {row.get('name')!r}: ORCID {orcid} belongs to an "
                    "already-claimed person and cannot be modified by import."
                )
            person, created = update_or_create_from_orcid(orcid, id=row.get("id"))
            if created:
                # Same result as `UserManager.create_unclaimed`: unclaimed but active, so an invitation can still reach them.
                person.email = None
                person.is_claimed = False
                person.is_active = True
                person.set_unusable_password()
                person.save(
                    update_fields=["email", "is_claimed", "is_active", "password"]
                )
            return person

        instance = super().get_instance(instance_loader, row)
        if instance is not None and instance.is_claimed:
            raise ValidationError(
                f"Row {row.get('name')!r}: matches an already-claimed person and "
                "cannot be modified by import."
            )
        return instance

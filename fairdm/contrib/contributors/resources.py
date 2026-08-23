import time

from django.core.exceptions import ValidationError
from import_export import fields, resources

from .models import Affiliation, ContributorIdentifier, Organization, Person
from .utils import update_or_create_from_orcid, update_or_create_from_ror


class PersonResource(resources.ModelResource):
    orcid = fields.Field(column_name="orcid")
    ror_id = fields.Field(column_name="ror_id")
    affiliation = fields.Field(column_name="affiliation")
    # `uuid` identifies a row - it is never written by one. Declared
    # `readonly` (import_export.fields.Field's own supported way to exclude a
    # field from `import_field()`/`Field.save()`, read in
    # import_export==4.4.1's fields.py) so `import_instance()` skips writing
    # it, while `import_id_fields` below still uses it - unaffected, since
    # instance lookup goes through `Field.clean()`/`get_value()`, not
    # `save()` - to find the row's matching Person. Without this, the
    # auto-generated field for a model attribute of the same name defaults to
    # writable, and a row whose `uuid` cell is blank or collides with another
    # Person's real uuid could overwrite the public identifier every
    # profile URL is built from, or raise an IntegrityError (see
    # `use_transactions` below for why that must not take the rest of the
    # batch with it).
    uuid = fields.Field(attribute="uuid", column_name="uuid", readonly=True)

    class Meta:
        model = Person
        # A display name is not an identity check — a spreadsheet row and an
        # existing Person can share one by coincidence. `uuid` is the public
        # identifier every Person carries, and is the only field this resource
        # uses to decide "this row is that record" for a row that also
        # supplies no ORCID (see get_instance).
        import_id_fields = ["uuid"]
        skip_unchanged = True
        # Each row's `import_row()` is wrapped in its own atomic()/savepoint
        # (import_export==4.4.1 resources.py `import_data_inner`, the `with
        # atomic_if_using_transaction(...)` around the per-row loop) only
        # when this is True. Without it, a row whose `instance.save()` raises
        # (an IntegrityError, say) has nothing to roll back to: the project
        # runs PostgreSQL with `ATOMIC_REQUESTS=True`
        # (fairdm/conf/settings/database.py), so the admin-import request's
        # own ambient transaction is left broken and every later row fails
        # with TransactionManagementError instead of reporting its own real
        # outcome, however unrelated it was to the row that actually failed.
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

    # def after_import_row(self, row, row_result, **kwargs):
    #     print(row["name"])

    def after_save_instance(self, instance, row, **kwargs):
        org = None
        if ror_id := row.get("ror_id"):
            org, _ = update_or_create_from_ror(ror_id, name=row.get("affiliation"))

        elif row.get("affiliation") and not ror_id:
            # If no ROR ID is provided, we can still create a new organization based on the name provided in the affiliation column
            org, _created = Organization.objects.get_or_create(name=row["affiliation"])

        if org:
            # Link person to organization
            Affiliation.objects.get_or_create(
                person=instance,
                organization=org,
                defaults={"type": Affiliation.MembershipType.MEMBER},
            )
        time.sleep(1.5)  # Rate limit to avoid hitting API limits

    def get_instance(self, instance_loader, row):
        """Resolve the row to an existing Person, or ``None`` so a new one is created.

        An uploaded spreadsheet is untrusted input, so a row is never allowed to
        resolve to — and thereby overwrite — an already-claimed Person, whether
        the match comes from the row's ORCID identifier or its uuid (the only
        `import_id_fields` this resource trusts; see ``Meta``). Either match is
        refused with a `ValidationError` naming the row rather than silently
        skipped, so the import report shows it.
        """
        # Allows reuse of instance created during before_import_row
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
                # Match `UserManager.create_unclaimed`'s Ghost-state result exactly
                # (decisions.md D8): a person created purely to attribute an import
                # is unclaimed but not banned, so a later invitation can still
                # reach them. `is_active=False` means banned, not "not yet real".
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

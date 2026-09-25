"""Create the five development accounts FairDM ships (FR-022 to FR-029, D7).

Nothing in the framework otherwise creates a *named* account: there is the one
superuser a portal's environment variables produce, and a fake-data command for
records. This command creates one account per shipped portal role and one
holding none, through the ORM rather than a fixture - ``Person`` subclasses a
polymorphic ``Contributor``, so a fixture row would need a content-type primary
key that differs between databases, and a fixture cannot refuse to load at all
(D7).

The accounts share a published password (``password``, also written down in
``docs/portal-development/development_accounts.md``), so the refusal below -
not secrecy - is their whole safety outside development. ``fairdm.E501``
(``fairdm/conf/checks.py``) is the second line of defence: it reports any of
these five addresses found on a portal this command never ran against, such as
one restored from a production database copy (D16).
"""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fairdm.portal_roles import PortalRoles

#: The password every development account shares (FR-025). Published
#: deliberately - see the module docstring - so this is not a secret to guard.
DEV_ACCOUNT_PASSWORD = "password"  # noqa: S105 - published development password, not a secret

#: The five accounts the specification's *Key entities* table names, in table
#: order: one per shipped role, and one holding none (FR-023, FR-024).
DEV_ACCOUNTS = (
    {
        "first_name": "Portal",
        "last_name": "Administrator",
        "email": "portal.administrator@fairdm.org",
        "role": PortalRoles.PORTAL_ADMINISTRATOR.name,
    },
    {
        "first_name": "Data",
        "last_name": "Curator",
        "email": "data.curator@fairdm.org",
        "role": PortalRoles.DATA_CURATOR.name,
    },
    {
        "first_name": "Community",
        "last_name": "Manager",
        "email": "community.manager@fairdm.org",
        "role": PortalRoles.COMMUNITY_MANAGER.name,
    },
    {
        "first_name": "Portal",
        "last_name": "Developer",
        "email": "portal.developer@fairdm.org",
        "role": PortalRoles.DEVELOPER.name,
    },
    {
        "first_name": "Regular",
        "last_name": "User",
        "email": "regular.user@fairdm.org",
        "role": None,
    },
)

#: The five addresses alone, for ``fairdm.E501`` to look for on a portal this
#: command never ran against (D16).
DEV_ACCOUNT_EMAILS = frozenset(account["email"] for account in DEV_ACCOUNTS)

#: The sign-in accounts the demo's development data uses: ``(email, first, last, is_staff,
#: is_superuser)``, all with the password ``password``. They share that written-down password as
#: the five above do, so ``fairdm.E501`` looks for them too.
EXAMPLE_ACCOUNTS = (
    ("regular.user@example.com", "Regular", "User", False, False),
    ("staff.user@example.com", "Staff", "User", True, False),
    ("super.user@example.com", "Super", "User", True, True),
)
EXAMPLE_ACCOUNT_EMAILS = frozenset(account[0] for account in EXAMPLE_ACCOUNTS)


class Command(BaseCommand):
    help = (
        "Create the five development accounts (one per portal role, one "
        "holding none) so anyone building a portal on FairDM can sign in as "
        "each role. Refuses on any environment FairDM does not ship a "
        "non-production override for."
    )

    def handle(self, *args, **options):
        environment = apps.get_app_config("fairdm").resolved_environment()

        # Deferred: fairdm.apps imports fairdm.conf.checks at module level,
        # which is the pattern this check module follows too - a top-level
        # import here would be circular the moment checks.py imports this
        # command back for DEV_ACCOUNT_EMAILS.
        from fairdm.apps import NON_PRODUCTION_ENVIRONMENTS

        if environment not in NON_PRODUCTION_ENVIRONMENTS:
            raise CommandError(
                f"Refusing to create the development accounts: the resolved "
                f"environment {environment!r} is not one FairDM ships a "
                "non-production override for. These accounts share a "
                "password written down in the documentation, so this "
                "refusal is their only safety outside development."
            )

        with transaction.atomic():
            for account in DEV_ACCOUNTS:
                self._create_or_reuse(account)

    def _create_or_reuse(self, account: dict) -> None:
        from allauth.account.models import EmailAddress

        Person = get_user_model()
        email = account["email"]

        person = Person.objects.filter(email__iexact=email).first()
        if person is None:
            person = Person(
                email=email,
                first_name=account["first_name"],
                last_name=account["last_name"],
                is_active=True,
                is_claimed=True,
            )
            person.set_password(DEV_ACCOUNT_PASSWORD)
            person.save()
            self.stdout.write(self.style.SUCCESS(f"Created {email}."))
        elif (person.first_name, person.last_name) != (
            account["first_name"],
            account["last_name"],
        ):
            raise CommandError(
                f"{email} already belongs to somebody else; refusing to adopt it."
            )
        else:
            self.stdout.write(f"{email} already exists; left unchanged.")

        # Marks the address confirmed so allauth's mandatory verification
        # lets the account straight in (FR-026) - idempotent, and re-affirmed
        # on every run regardless of how the account got here.
        EmailAddress.objects.update_or_create(
            user=person,
            email=email,
            defaults={"verified": True, "primary": True},
        )

        if account["role"]:
            person.groups.add(Group.objects.get(name=account["role"]))

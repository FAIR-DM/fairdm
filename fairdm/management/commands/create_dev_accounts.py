"""Create the five development accounts FairDM ships.

Nothing in the framework otherwise creates a *named* account: there is the one
superuser a portal's environment variables produce, and a fake-data command for
records. This command creates one account per shipped portal role and one
holding none, through the ORM rather than a fixture. ``Person`` subclasses a
polymorphic ``Contributor``, so a fixture row would need a content-type primary
key that differs between databases, and a fixture cannot refuse to load at all.

The accounts share a published password (``password``, also written down in
``docs/portal-development/development_accounts.md``), so the refusal below, not
secrecy, is their whole safety outside development. ``fairdm.E501``
(``fairdm/conf/checks.py``) is the second line of defence: it reports any of
these five addresses found on a portal this command never ran against, such as
one restored from a production database copy.
"""

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from fairdm.portal_roles import PortalRoles

#: The password every development account shares. Published deliberately, so not a secret.
DEV_ACCOUNT_PASSWORD = "password"  # noqa: S105 - published development password, not a secret

#: One account per shipped role, and one holding none.
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

#: The five addresses alone, for ``fairdm.E501`` to look for.
DEV_ACCOUNT_EMAILS = frozenset(account["email"] for account in DEV_ACCOUNTS)

#: The sign-in accounts the demo's development data uses: ``(email, first, last, is_staff,
#: is_superuser)``, all with the password ``password``. They share that written-down password as
#: the five above do, so ``fairdm.E501`` looks for them too.
EXAMPLE_ACCOUNTS = (
    ("regular.user@example.com", "Regular", "User", False, False),
    ("staff.user@example.com", "Staff", "User", True, False),
    ("super.user@example.com", "Super", "User", True, True),
)

#: The accounts ``seed_profiles`` adds around the organization ``regular.user`` owns, and the
#: two that hold a portal role, in the same shape as ``EXAMPLE_ACCOUNTS`` and with the same
#: password.
PROFILE_ACCOUNTS = (
    ("admin.user@example.com", "Admin", "User", False, False),
    ("member.user@example.com", "Member", "User", False, False),
    ("former-admin.user@example.com", "Former Admin", "User", False, False),
    ("community-manager.user@example.com", "Community Manager", "User", False, False),
    ("data-curator.user@example.com", "Data Curator", "User", False, False),
)
EXAMPLE_ACCOUNT_EMAILS = frozenset(
    account[0] for account in (*EXAMPLE_ACCOUNTS, *PROFILE_ACCOUNTS)
)


class Command(BaseCommand):
    """Create the development accounts, one per portal role and one holding none."""

    help = (
        "Create the five development accounts (one per portal role, one "
        "holding none) so anyone building a portal on FairDM can sign in as "
        "each role. Refuses on any environment FairDM does not ship a "
        "non-production override for."
    )

    def handle(self, *args, **options):
        """Create the accounts, refusing outside an environment FairDM ships a non-production override for."""
        environment = apps.get_app_config("fairdm").resolved_environment()

        # Deferred: `fairdm.apps` imports `fairdm.conf.checks`, which imports this module
        # back for DEV_ACCOUNT_EMAILS, so a top-level import would be circular.
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
        """Create the account, or reuse the one already holding its address, and give it its role.

        Args:
            account: One entry of ``DEV_ACCOUNTS``.

        Raises:
            CommandError: The address already belongs to a person with a different name.
        """
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

        # Confirmed on every run so allauth's mandatory verification admits the account.
        EmailAddress.objects.update_or_create(
            user=person,
            email=email,
            defaults={"verified": True, "primary": True},
        )

        if account["role"]:
            person.groups.add(Group.objects.get(name=account["role"]))

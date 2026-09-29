"""What the development-data seeds share: the example accounts and the clean-up of earlier runs."""

from allauth.account.models import EmailAddress

from fairdm.contrib.contributors.models import Person
from fairdm.core.dataset.models import Dataset
from fairdm.core.project.models import Project
from fairdm.management.commands.create_dev_accounts import (
    DEV_ACCOUNT_PASSWORD,
    EXAMPLE_ACCOUNTS,
)


def example_accounts() -> dict[str, Person]:
    """Return the three example accounts by name, creating the ones that are missing.

    An account that already exists is returned as it is: its password, names and rights stay
    whatever they were.

    Returns:
        ``regular.user``, ``staff.user`` and ``super.user``, keyed by the part before the ``@``.
    """
    users = {}
    for email, first, last, staff, superuser in EXAMPLE_ACCOUNTS:
        user = Person.objects.filter(email=email).first()
        if user is None:
            user = Person.objects.create_user(
                email=email,
                password=DEV_ACCOUNT_PASSWORD,
                first_name=first,
                last_name=last,
            )
            user.name = f"{first} {last}"
            user.is_staff, user.is_superuser = staff, superuser
            user.save()
            # Confirmed, so allauth's mandatory verification admits the account.
            EmailAddress.objects.update_or_create(
                user=user, email=email, defaults={"verified": True, "primary": True}
            )
        users[email.split("@")[0]] = user
    return users


def remove_own_projects(names: list[str], users: dict[str, Person]) -> None:
    """Delete the projects an earlier run created, and their datasets.

    A project counts as this command's own when it has one of ``names`` and ``super.user`` created
    it, which every seeded project records. A project somebody else made under the same name is
    left alone.

    Args:
        names: The names of the projects the calling seed creates.
        users: The example accounts, from :func:`example_accounts`.
    """
    projects = Project.objects.filter(name__in=names, created_by=users["super.user"])
    # Datasets first: a project with public datasets refuses to be deleted.
    Dataset.all_objects.filter(project__in=projects).delete()
    projects.delete()

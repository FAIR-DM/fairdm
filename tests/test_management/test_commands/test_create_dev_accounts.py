"""
Tests for the ``create_dev_accounts`` management command (FR-022 to FR-029, T026).

The suite's own environment is ``development`` (``pytest-env`` sets ``DJANGO_ENV``
in ``pyproject.toml``), so every scenario except the production refusal runs the
command in-process. The production refusal needs a real process boot under a
different resolved environment - ``tests/test_apps.py`` and
``TestBundledPortalBoots`` in ``tests/test_conf/test_setup.py`` already establish
that pattern, and the brief's own environment note names it as the one to follow.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.urls import reverse

from fairdm.management.commands.create_dev_accounts import (
    DEV_ACCOUNT_PASSWORD,
    DEV_ACCOUNTS,
)

Person = get_user_model()

REPO_ROOT = Path(__file__).resolve().parents[3]

DEV_ACCOUNT_EMAILS = [account["email"] for account in DEV_ACCOUNTS]


@pytest.mark.django_db
class TestCreateDevAccountsCreatesTheFive:
    """T026: exactly the five accounts of the specification's table, each in
    its stated role and the last in none (FR-023, FR-024)."""

    def test_creates_exactly_five_accounts(self):
        call_command("create_dev_accounts", verbosity=0)

        assert Person.objects.filter(email__in=DEV_ACCOUNT_EMAILS).count() == 5

    def test_each_account_holds_its_stated_role_and_the_last_holds_none(self):
        call_command("create_dev_accounts", verbosity=0)

        for account in DEV_ACCOUNTS:
            person = Person.objects.get(email=account["email"])
            held_roles = set(person.groups.values_list("name", flat=True))
            if account["role"] is None:
                assert held_roles == set(), account["email"]
            else:
                assert held_roles == {account["role"]}, account["email"]


@pytest.mark.django_db
class TestCreateDevAccountsSignIn:
    """FR-025, FR-026: every account uses the shared password and needs no
    confirmation step to sign in through the portal."""

    def test_each_account_signs_in_with_no_confirmation_step(self, client):
        call_command("create_dev_accounts", verbosity=0)

        for account in DEV_ACCOUNTS:
            client.logout()
            client.post(
                reverse("account_login"),
                {"login": account["email"], "password": DEV_ACCOUNT_PASSWORD},
            )
            assert "_auth_user_id" in client.session, (
                f"{account['email']} did not sign in with no further step"
            )

    def test_each_address_is_already_confirmed(self):
        call_command("create_dev_accounts", verbosity=0)

        for account in DEV_ACCOUNTS:
            person = Person.objects.get(email=account["email"])
            assert EmailAddress.objects.filter(
                user=person,
                email=account["email"],
                verified=True,
                primary=True,
            ).exists(), account["email"]


@pytest.mark.django_db
class TestCreateDevAccountsIsIdempotent:
    """FR-028: running the command twice creates no duplicate account."""

    def test_running_twice_creates_no_duplicate(self):
        call_command("create_dev_accounts", verbosity=0)
        call_command("create_dev_accounts", verbosity=0)

        assert Person.objects.filter(email__in=DEV_ACCOUNT_EMAILS).count() == 5


@pytest.mark.django_db
class TestCreateDevAccountsRefusesToAdopt:
    """FR-029: when one of the addresses already belongs to somebody, the
    command fails rather than adopting that account."""

    def test_refuses_when_an_address_already_belongs_to_somebody_else(self):
        claimed_email = DEV_ACCOUNTS[0]["email"]
        Person.objects.create_user(
            email=claimed_email,
            password="a-real-persons-password",
            first_name="Somebody",
            last_name="Else",
        )

        with pytest.raises(CommandError):
            call_command("create_dev_accounts", verbosity=0)

        # The refusal aborts the whole run - none of the other four accounts
        # are created either.
        other_emails = DEV_ACCOUNT_EMAILS[1:]
        assert Person.objects.filter(email__in=other_emails).count() == 0

        # And the pre-existing account is left exactly as it was.
        untouched = Person.objects.get(email=claimed_email)
        assert untouched.first_name == "Somebody"
        assert untouched.last_name == "Else"


class TestCreateDevAccountsRefusesOutsideDevelopment:
    """FR-027: on the production baseline the command fails, says why, and
    creates nothing.

    A real process boot under a fully valid production configuration -
    mirroring ``TestBundledPortalBoots`` - so Django itself starts cleanly and
    the command's own environment gate is what refuses, not an unrelated
    missing setting. ``override_settings`` cannot stand in here: the point is
    that the refusal fires before a single query is issued, which only a
    real, otherwise-successful boot under a non-development environment can
    demonstrate (prohibitions: never weaken this to make the test easier).
    """

    def test_refuses_on_the_production_baseline_and_touches_no_database(self):
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(
                (
                    "DJANGO_",
                    "DATABASE_",
                    "REDIS_",
                    "POSTGRES_",
                    "EMAIL_",
                    "S3_",
                    "SENTRY_",
                )
            )
        }
        env |= {
            "DJANGO_ENV": "production",
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_SECRET_KEY": "b" * 60,
            "DJANGO_SITE_DOMAIN": "example.com",
            "DJANGO_ALLOWED_HOSTS": "example.com",
            "DATABASE_URL": "postgresql://portal:portal@localhost:5432/portal",
            "REDIS_URL": "redis://localhost:6379/0",
        }

        result = subprocess.run(
            [sys.executable, "manage.py", "create_dev_accounts"],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        assert result.returncode != 0, (
            f"create_dev_accounts exited 0 on the production baseline:\n"
            f"stdout: {result.stdout[-2000:]}\nstderr: {result.stderr[-2000:]}"
        )
        assert "production" in result.stderr, result.stderr[-2000:]
        # No database traceback: the refusal fires ahead of any query the
        # command itself would issue (a bug here would surface as an
        # OperationalError instead of the command's own message).
        assert "OperationalError" not in result.stderr

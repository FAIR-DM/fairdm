"""allauth adapters that gate signup and link ORCID sign-in to contributor profiles."""

import waffle
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_signed_up
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.internal.flows.signup import redirect_to_signup
from django.conf import settings
from django.http import HttpRequest

from fairdm.contrib.contributors.models import ContributorIdentifier
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform


def is_provider(name, sociallogin):
    """Check whether a social login came from the named provider.

    Args:
        name: The provider name, such as ``"orcid"``.
        sociallogin: The social login being processed.

    Returns:
        True when the login's provider is ``name``.
    """
    return sociallogin.account.provider == name


class AccountAdapter(DefaultAccountAdapter):
    """Account adapter that opens signup by switch, invitation and verified email."""

    def is_open_for_signup(self, request: HttpRequest):
        """Allow signup when the ``allow_signup`` switch is on and either the email is verified or signup is not invitation-only."""
        if not waffle.switch_is_active("allow_signup"):
            return False
        if hasattr(request, "session") and request.session.get(
            "account_verified_email",
        ):
            return True
        return not settings.FAIRDM_INVITATION_ONLY_SIGNUP

    def get_user_signed_up_signal(self):
        """Return allauth's ``user_signed_up`` signal."""
        return user_signed_up


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Social account adapter that claims or links a profile on ORCID sign-in."""

    def is_open_for_signup(self, request, socialogin):
        """Also require the ``allow_signup`` switch to be on."""
        return waffle.switch_is_active("allow_signup") and super().is_open_for_signup(
            request, socialogin
        )

    def get_signup_form_initial_data(self, sociallogin):
        """Prefill the signup form's name from the social login."""
        initial = super().get_signup_form_initial_data(sociallogin)
        return {
            **initial,
            "name": getattr(sociallogin.user, "name", ""),
        }

    def get_db_user_by_orcid(self, orcid_id):
        """Find the profile that holds an ORCID iD.

        Args:
            orcid_id: The ORCID iD.

        Returns:
            The profile, or None when no identifier row matches.
        """
        existing = ContributorIdentifier.objects.filter(
            value=orcid_id, type="ORCID"
        ).first()
        if existing:
            return existing.related

    def pre_social_login(self, request, sociallogin):
        """Claim an unclaimed profile that already holds the signing-in ORCID iD."""
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            existing_user = self.get_db_user_by_orcid(orcid_id)
            # An identifier row can be written by an administrator or an import, so it does not prove
            # identity: a claimed account is left to allauth's normal flow.
            if existing_user and not existing_user.is_claimed:
                from fairdm.contrib.contributors.exceptions import ClaimingError
                from fairdm.contrib.contributors.services.claiming import (
                    claim_via_orcid,
                )

                sociallogin.user = existing_user
                try:
                    claim_via_orcid(existing_user, sociallogin)
                except ClaimingError as exc:
                    raise ImmediateHttpResponse(
                        redirect_to_signup(request, sociallogin)
                    ) from exc
                raise ImmediateHttpResponse(redirect_to_signup(request, sociallogin))

    def save_user(self, request, sociallogin, form=None):
        """Adopt an unclaimed profile holding the ORCID iD, or create a new user and attach the iD."""
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            existing_user = self.get_db_user_by_orcid(orcid_id)
            # As in pre_social_login, only an unclaimed profile is adopted. A claimed one is left alone
            # and signup proceeds as a new account.
            adopted_user = (
                existing_user
                if existing_user and not existing_user.is_claimed
                else None
            )
            if adopted_user:
                sociallogin.user = adopted_user

            user = super().save_user(request, sociallogin, form=form)
            # The identifier value is unique, so writing it when a claimed profile already holds it
            # would raise an IntegrityError and crash the signup.
            if not adopted_user and existing_user is None:
                user.identifiers.create(
                    value=orcid_id,
                    type="ORCID",
                )
            return user

        return super().save_user(request, sociallogin, form=form)

    def populate_user(self, request, sociallogin, data):
        """Fill the user from the ORCID record's extra data."""
        user = super().populate_user(request, sociallogin, data)
        if is_provider("orcid", sociallogin):
            user = ORCIDTransform().import_data(
                sociallogin.account.extra_data, instance=user, save=False
            )
        return user

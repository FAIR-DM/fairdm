import waffle
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_signed_up
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.internal.flows.signup import redirect_to_signup
from django.conf import settings
from django.http import HttpRequest

# from allauth.socialaccount.models import SocialLogin
from fairdm.contrib.contributors.models import ContributorIdentifier
from fairdm.contrib.contributors.utils.transforms import ORCIDTransform


def is_provider(name, sociallogin):
    """
    Check if the sociallogin provider matches the given name.
    """
    return sociallogin.account.provider == name


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest):
        if not waffle.switch_is_active("allow_signup"):
            # Site is NOT open for signup
            return False
        if hasattr(request, "session") and request.session.get(
            "account_verified_email",
        ):
            return True
        # Site is open to signup if not invitation only
        return not settings.FAIRDM_INVITATION_ONLY_SIGNUP

    def get_user_signed_up_signal(self):
        return user_signed_up


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, socialogin):
        return waffle.switch_is_active("allow_signup") and super().is_open_for_signup(
            request, socialogin
        )

    def get_signup_form_initial_data(self, sociallogin):
        initial = super().get_signup_form_initial_data(sociallogin)
        return {
            **initial,
            "name": getattr(sociallogin.user, "name", ""),
        }

    def get_db_user_by_orcid(self, orcid_id):
        """
        Retrieve a user from the database by their ORCID ID.
        """
        existing = ContributorIdentifier.objects.filter(
            value=orcid_id, type="ORCID"
        ).first()
        if existing:
            return existing.related

    def pre_social_login(self, request, sociallogin):
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            existing_user = self.get_db_user_by_orcid(orcid_id)
            # A ContributorIdentifier row is not proof of identity — it can be
            # written by an administrator or a bulk import, not just by the
            # person it names. A claimed account already belongs to someone,
            # so it is never signed into on the strength of that row alone;
            # allauth's ordinary flow (email verification) is the correct
            # outcome there. Only an unclaimed profile — which nobody
            # controls yet, and which the import exists to make claimable —
            # is claimed automatically here.
            if existing_user and not existing_user.is_claimed:
                # Unclaimed Person with a matching ORCID identifier — claim it automatically.
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
                # Complete the login — the Person is now claimed and active.
                raise ImmediateHttpResponse(redirect_to_signup(request, sociallogin))

            # message = (
            #     f"User with ORCID {orcid_id} already exists. "
            #     "Logging in with existing user."
            # )
            # 1a)

    def save_user(self, request, sociallogin, form=None):
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            existing_user = self.get_db_user_by_orcid(orcid_id)
            # As in pre_social_login: the identifier row is not proof of identity,
            # so only an unclaimed Person is adopted here. A claimed Person is left
            # alone entirely — signup proceeds as a genuinely new account. Adopting
            # no longer reactivates the target (a deactivated account is banned;
            # un-banning it because an ORCID row points at it is the same hole).
            adopted_user = (
                existing_user
                if existing_user and not existing_user.is_claimed
                else None
            )
            if adopted_user:
                # swap out existing data for incoming data from confirmation form (it exists on the sociallogin.user)
                # we don't need to save as the remaining flow will do that for us
                sociallogin.user = adopted_user

            user = super().save_user(request, sociallogin, form=form)
            # An ORCID identifies at most one person - `ContributorIdentifier.value`
            # carries a database-level uniqueness constraint (fairdm/core/abstract.py)
            # that already refuses two rows for the same value, so writing this one
            # unconditionally when `existing_user` is a claimed Person who already
            # holds it does not silently duplicate the value: it raises an uncaught
            # IntegrityError and crashes the signup instead. Skipping the write here
            # is the same choice `pre_social_login`/the block above already made for
            # `existing_user` itself - a claimed match is left alone entirely, so the
            # new account it's attached to is not entitled to that identifier either.
            # The account itself still gets created; it just doesn't carry an ORCID
            # identifier this signup can't legitimately claim.
            if not adopted_user and existing_user is None:
                # The following must be done after the user is saved to ensure the user instance has a pk
                # create the new ContributorIdentifier relation
                user.identifiers.create(
                    value=orcid_id,
                    type="ORCID",
                )
            return user

        return super().save_user(request, sociallogin, form=form)

    def populate_user(self, request, sociallogin, data):
        # This method will help populate the user with data from the social login.
        user = super().populate_user(request, sociallogin, data)
        if is_provider("orcid", sociallogin):
            user = ORCIDTransform().import_data(
                sociallogin.account.extra_data, instance=user, save=False
            )
        return user

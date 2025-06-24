import waffle
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_signed_up
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpRequest

from fairdm.contrib.contributors.models import ContributorIdentifier

from .utils import contributor_from_orcid_data


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
        return not settings.INVITATIONS_INVITATION_ONLY

    def get_user_signed_up_signal(self):
        return user_signed_up


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, socialogin):
        return waffle.switch_is_active("allow_signup") and super().is_open_for_signup(request, socialogin)

    def get_signup_form_initial_data(self, sociallogin):
        initial = super().get_signup_form_initial_data(sociallogin)
        return {
            **initial,
            "name": getattr(sociallogin.user, "name", ""),
        }

    def pre_social_login(self, request, sociallogin):
        pass

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if is_provider("orcid", sociallogin):
            user = contributor_from_orcid_data(sociallogin.account.extra_data, user, save=False)
        user.is_member = True  # Ensure user is marked as a member
        return user

    def save_user(self, request, sociallogin, form=None):
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid

            # If the ORCID ID already exists in the database, we associate the incoming user with that ID.
            orcid_exists = ContributorIdentifier.objects.filter(value=orcid_id, type="orcid").first()
            if orcid_exists:
                sociallogin.user = orcid_exists.related

            user = super().save_user(request, sociallogin, form=form)

            # The following must be done after the user is saved to ensure the user instance has a pk
            if not orcid_exists:
                # create the new ContributorIdentifier relation
                user.identifiers.create(
                    value=orcid_id,
                    type="orcid",
                )

        return user

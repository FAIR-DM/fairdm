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
from fairdm.contrib.contributors.utils import contributor_from_orcid_data


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

    def get_db_user_by_orcid(self, orcid_id):
        """
        Retrieve a user from the database by their ORCID ID.
        """
        existing = ContributorIdentifier.objects.filter(value=orcid_id, type="ORCID").first()
        if existing:
            return existing.related

    def pre_social_login(self, request, sociallogin):
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            if existing_user := self.get_db_user_by_orcid(orcid_id):
                if existing_user.is_active:
                    # If the existing user is already active, we simply connect the orcid account and log them in.
                    # Note: It's unclear in what scenario an active user can have an ORCID id in their identifiers
                    # without having signed up with it, but this is a safeguard.
                    # Normal flow for active users
                    sociallogin.user = existing_user
                    sociallogin.connect(request, existing_user)
                # link the existing user to the social login
                # This prevents Allauth send a "Account Already Exists" email
                else:
                    raise ImmediateHttpResponse(redirect_to_signup(request, sociallogin))

                # message = (
                #     f"User with ORCID {orcid_id} already exists. "
                #     "Logging in with existing user."
                # )
                # 1a)

    def save_user(self, request, sociallogin, form=None):
        if is_provider("orcid", sociallogin):
            orcid_id = sociallogin.account.uid
            if existing_user := self.get_db_user_by_orcid(orcid_id):
                existing_user.is_active = True  # Mark the existing user as active
                # swap out existing data for incoming data from confirmation form (it exists on the sociallogin.user)
                # we don't need to save as the remaining flow will do that for us
                sociallogin.user = existing_user

            user = super().save_user(request, sociallogin, form=form)
            if not existing_user:
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
            user = contributor_from_orcid_data(sociallogin.account.extra_data, user, save=False)
        return user

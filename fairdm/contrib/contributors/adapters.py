import waffle
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.signals import user_signed_up
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.providers.orcid.provider import extract_from_dict
from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest

from fairdm.contrib.contributors.models import ContributorIdentifier

from .choices import PersonalIdentifiers


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
        user = sociallogin.user
        initial = super().get_signup_form_initial_data(sociallogin)
        return {
            **initial,
            "name": user.name,
        }

    def pre_social_login(self, request, sociallogin):
        """
        Override pre_social_login to process ORCID data before account creation.

        sociallogin: allauth.socialaccount.models.SocialLogin instance
        """
        if sociallogin.account.provider == "orcid":
            orcid_id = sociallogin.account.uid

            # Check if the orcid_id is already in the database. If it is, link the social account to the existing user
            if existing := ContributorIdentifier.objects.filter(value=orcid_id).first():
                sociallogin.user = existing.content_object

                # Set the user as active and save. Otherwise django-allauth will prevent login.
                # Users can exists in the database as inactive if they were added as a contributor to a project, dataset, etc.
                # without actually having an account.
                sociallogin.user.is_active = True
                sociallogin.user.save()
                messages.success(
                    request,
                    "We were able to match your ORCID account against existing information in our system and have updated your profile.",
                )

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        if sociallogin.account.provider == "orcid":
            # Ensures the ORCID identifier is saved as a ContributorIdentifier for new users
            user.identifiers.get_or_create(value=sociallogin.account.uid, type=PersonalIdentifiers.ORCID)
        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        if sociallogin.account.provider != "orcid":
            return user
        orcid_data = sociallogin.account.extra_data
        user.name = extract_from_dict(orcid_data, ["person", "name", "credit-name", "value"])

        user.profile = extract_from_dict(orcid_data, ["person", "biography", "content"])

        other_names = extract_from_dict(orcid_data, ["person", "other-names", "other-name"])
        if other_names:
            user.alternative_names = [name["content"] for name in other_names]

        links = extract_from_dict(orcid_data, ["person", "researcher-urls", "researcher-url"])
        if links:
            user.links = [{"display": link["url-name"], "url": link["url"]["value"]} for link in links]
        return user

"""The ORCID sign-in addresses, which answer 404 until an application is configured."""

from functools import wraps

from allauth.socialaccount.models import SocialApp
from allauth.socialaccount.providers.orcid.views import oauth2_callback, oauth2_login
from django.http import Http404


def not_found_without_application(view):
    """Answer 404 instead of a server error when the social application is missing.

    Args:
        view: The allauth view.

    Returns:
        The wrapped view.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        try:
            return view(request, *args, **kwargs)
        except SocialApp.DoesNotExist as exc:
            raise Http404 from exc

    return wrapper


orcid_login = not_found_without_application(oauth2_login)
orcid_callback = not_found_without_application(oauth2_callback)

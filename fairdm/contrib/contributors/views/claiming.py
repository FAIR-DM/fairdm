"""Views for the token-based profile claiming flow."""

from __future__ import annotations

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from fairdm.contrib.contributors.exceptions import ClaimingError

logger = logging.getLogger(__name__)

_CLAIM_TOKEN_SESSION_KEY = "claim_token"  # noqa: S105


class ClaimProfileView(TemplateView):
    """Show the unclaimed profile a claim token names, for the user to confirm.

    Nothing is claimed on GET. An anonymous visitor is sent to sign in with the token kept
    in the session, and an invalid token or a deactivated profile renders an error.

    Attributes:
        template_name: The confirmation template.
    """

    template_name = "contributors/claim_profile.html"

    def _resolve_token(self, token: str) -> tuple:
        """Resolve a token to a person or an error message.

        Args:
            token: The signed claim token.

        Returns:
            A ``(person, None)`` or ``(None, error message)`` pair.
        """
        from fairdm.contrib.contributors.utils.tokens import validate_claim_token

        try:
            person = validate_claim_token(token)
        except ClaimingError as exc:
            return None, str(exc)
        return person, None

    def get(self, request, *args, **kwargs):
        """Render the confirmation page, or an error, or send an anonymous visitor to sign in."""
        token = kwargs["token"]

        if not request.user.is_authenticated:
            request.session[_CLAIM_TOKEN_SESSION_KEY] = token
            from django.conf import settings

            login_url = getattr(settings, "LOGIN_URL", "/accounts/login/")
            return redirect(login_url)

        person, error = self._resolve_token(token)
        context = self.get_context_data(**kwargs)

        if error or person is None:
            context["error_message"] = error or _("Invalid or expired claim token.")
            context["error"] = True
            context["token"] = token
            return self.render_to_response(context)

        if not person.is_active:
            context["error_message"] = _(
                "This profile is banned and cannot be claimed."
            )
            context["error"] = True
            context["token"] = token
            return self.render_to_response(context)

        context["unclaimed_person"] = person
        context["token"] = token
        return self.render_to_response(context)


class ClaimProfileConfirmView(LoginRequiredMixin, TemplateView):
    """Claim the profile a token names, for the signed-in user.

    Attributes:
        template_name: The template rendered when the claim fails.
    """

    template_name = "contributors/claim_profile.html"

    def post(self, request, *args, **kwargs):
        """Claim the profile and redirect to the user's page, or re-render with the error."""
        token = kwargs["token"]
        user = request.user

        from fairdm.contrib.contributors.services.claiming import claim_via_token

        try:
            claim_via_token(token, user)
        except ClaimingError as exc:
            context = self.get_context_data(**kwargs)
            context["error_message"] = str(exc)
            context["error"] = True
            return self.render_to_response(context)

        from django.contrib import messages

        messages.success(request, _("Profile successfully claimed."))
        try:
            return redirect(user.get_absolute_url())
        except Exception:
            return redirect("/")

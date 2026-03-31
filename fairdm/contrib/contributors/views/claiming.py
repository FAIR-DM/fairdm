"""Views for the token-based profile claiming flow (US3).

GET  /claim/<token>/         — Show confirmation page (or error/merge page)
POST /claim/<token>/confirm/ — Execute the claim (requires auth + CSRF)
"""

from __future__ import annotations

import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from fairdm.contrib.contributors.exceptions import ClaimingError

logger = logging.getLogger(__name__)

_CLAIM_TOKEN_SESSION_KEY = "claim_token"


class ClaimProfileView(TemplateView):
    """Claim Profile landing page.

    GET: Always renders a read-only confirmation page showing the unclaimed profile.
         No claim or merge is ever executed on GET.

         Four user states:
           (a) Unauthenticated       → save token in session, redirect to login
           (b) Authenticated, simple → show standard claim confirmation
           (c) Authenticated, merge  → show merge confirmation (Phase 6)
           (d) Banned target         → render error page
           Invalid/expired token    → render error page

    POST: Executes the claim.  Requires authentication + CSRF.
          Routes to claim_via_token() for state (b), merge_persons() for state (c).
    """

    template_name = "contributors/claim_profile.html"

    def _resolve_token(self, token: str) -> tuple:
        """Resolve a token to a Person and an optional error message.

        Returns:
            (person_or_None, error_message_or_None)
        """
        from fairdm.contrib.contributors.utils.tokens import validate_claim_token

        try:
            person = validate_claim_token(token)
        except ClaimingError as exc:
            return None, str(exc)
        return person, None

    def get(self, request, *args, **kwargs):
        token = kwargs["token"]

        # (a) Unauthenticated — redirect to login, preserving token in session
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

        # (d) Banned target
        if not person.is_active:
            context["error_message"] = _("This profile is banned and cannot be claimed.")
            context["error"] = True
            context["token"] = token
            return self.render_to_response(context)

        context["unclaimed_person"] = person
        context["token"] = token
        return self.render_to_response(context)


class ClaimProfileConfirmView(LoginRequiredMixin, TemplateView):
    """Execute the profile claim via POST.

    Requires authentication and CSRF protection.
    """

    template_name = "contributors/claim_profile.html"

    def post(self, request, *args, **kwargs):
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

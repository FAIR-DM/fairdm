"""Signal handlers for the contributors app."""

from __future__ import annotations

import logging

from django.conf import settings

from fairdm.contrib.contributors.models import Person
from fairdm.contrib.contributors.services.claiming import claim_via_email

logger = logging.getLogger(__name__)


def handle_email_confirmed(sender, request=None, email_address=None, **kwargs):
    """Claim the unclaimed person whose email was just confirmed.

    Does nothing unless ``ACCOUNT_EMAIL_VERIFICATION`` is ``mandatory`` and an unclaimed
    person has that email. A claiming failure is logged, not raised.

    Args:
        sender: The signal sender.
        request: The current request.
        email_address: The confirmed email address.
        **kwargs: Other signal arguments.

    Returns:
        None.
    """
    if getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") != "mandatory":
        return

    if email_address is None:
        return

    email = getattr(email_address, "email", None)
    if not email:
        return

    try:
        person = Person.objects.get(email=email, is_claimed=False)
    except Person.DoesNotExist:
        return

    try:
        claim_via_email(person)
    except Exception:
        logger.exception("claim_via_email failed for email %s", email)

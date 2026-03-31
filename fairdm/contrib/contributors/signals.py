"""Signal handlers for the contributors app.

Currently handles:
  - email_confirmed: triggers claim_via_email() for unclaimed Persons
    whose email address matches the confirmed email.
"""

from __future__ import annotations

import logging

from django.conf import settings

from fairdm.contrib.contributors.models import Person
from fairdm.contrib.contributors.services.claiming import claim_via_email

logger = logging.getLogger(__name__)


def handle_email_confirmed(sender, request=None, email_address=None, **kwargs):
    """Handle allauth email_confirmed signal.

    Looks up any unclaimed Person whose email matches the confirmed address
    and calls claim_via_email() if found.  Silent no-op when:
      - ACCOUNT_EMAIL_VERIFICATION != 'mandatory'
      - No unclaimed Person with that email exists
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

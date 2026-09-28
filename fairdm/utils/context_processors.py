"""Context processor that exposes FairDM configuration to templates."""

import json

from django.conf import settings

from fairdm.contrib.identity.models import Authority, Identity
from fairdm.registry import registry


def fairdm(request):
    """Return the FairDM template context.

    The page config is the ``PAGE_CONFIG`` setting with the portal's uploaded brand assets and
    name layered over it.

    Args:
        request: The current request.

    Returns:
        A dict with ``config``, ``identity``, ``theme_options``, ``registry``, ``page_config``
        and ``json_config`` entries.
    """
    identity = Identity.get_solo()
    authority = Authority.get_solo()

    page_config = dict(settings.PAGE_CONFIG)

    brand = page_config.get("brand", {})
    if identity.logo_light:
        brand["image_light"] = identity.logo_light.url
    if identity.logo_dark:
        brand["image_dark"] = identity.logo_dark.url
    if identity.icon_light:
        brand["icon_light"] = identity.icon_light.url
    if identity.icon_dark:
        brand["icon_dark"] = identity.icon_dark.url

    portal_name = identity.safe_translation_getter("name")
    if portal_name:
        brand["text"] = portal_name

    page_config["brand"] = brand

    context = {
        "config": {
            "site_name": settings.SITE_NAME,
            "site_domain": settings.SITE_DOMAIN,
            "allow_registration": settings.ACCOUNT_ALLOW_REGISTRATION,
            "portal_description": getattr(settings, "PORTAL_DESCRIPTION", None),
        },
        "identity": {
            # Templates still read the identity under the `dataset` key.
            "dataset": identity,
            "authority": authority,
        },
        "theme_options": settings.FAIRDM_CONFIG,
        "registry": registry,
        "page_config": page_config,
    }
    context["json_config"] = json.dumps(context["config"])
    return context

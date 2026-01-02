import json

from django.conf import settings

from fairdm.contrib.identity.models import Authority, Identity
from fairdm.registry import registry


def fairdm(request):
    """A context processor that adds the following variables to the context:"""
    # Get singleton instances
    identity = Identity.get_solo()
    authority = Authority.get_solo()

    # Build hybrid page_config by merging database brand assets with settings

    page_config = dict(settings.PAGE_CONFIG)  # Copy settings config

    # Override brand configuration with uploaded assets if available
    brand = page_config.get("brand", {})
    if identity.logo_light:
        brand["image_light"] = identity.logo_light.url
    if identity.logo_dark:
        brand["image_dark"] = identity.logo_dark.url
    if identity.icon_light:
        brand["icon_light"] = identity.icon_light.url
    if identity.icon_dark:
        brand["icon_dark"] = identity.icon_dark.url

    # Use portal name from database if available
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
            "dataset": identity,  # Keep 'dataset' key for template compatibility
            "authority": authority,
        },
        "theme_options": settings.FAIRDM_CONFIG,
        "registry": registry,
        "page_config": page_config,  # Add page_config to context
    }
    context["json_config"] = json.dumps(context["config"])
    return context

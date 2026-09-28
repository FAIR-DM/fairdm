"""Production settings overrides for the demo portal.

See docs/portal-development/configuration.md. This module runs inside the
``fairdm.setup()`` call in ``settings.py`` and must not call it again.
"""

from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]

# django-parler validates PARLER_LANGUAGES against LANGUAGES on import, so narrowing
# LANGUAGES means narrowing this too. Leaving the baseline is refused as fairdm.E400.
PARLER_LANGUAGES = {
    1: (
        {"code": "en"},
        {"code": "de"},
    ),
    "default": {
        "fallback": "en",
        "hide_untranslated": False,
    },
}

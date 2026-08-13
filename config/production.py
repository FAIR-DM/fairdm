"""Portal override module for the production environment (see docs/portal-development/configuration.md).

Applied by fairdm.setup() as layer 4 — after the baseline, FairDM's own
environment override, and addon settings, and before assignments made in
settings.py after the setup() call. It must not call fairdm.setup() itself:
it runs inside the caller's already-in-progress setup() call, sharing scope.
"""

from django.utils.translation import gettext_lazy as _

LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]

# django-parler validates every code in PARLER_LANGUAGES against LANGUAGES when
# it is imported, so a portal that narrows LANGUAGES has to narrow this to match.
# Leaving it at the FairDM baseline (en, fr, de) is refused at startup as
# fairdm.E400, which names both settings (T107).
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

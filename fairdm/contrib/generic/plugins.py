"""Plugin for editing keywords."""

from django.utils.translation import gettext_lazy as _

from fairdm.contrib.generic.forms import KeywordForm
from fairdm.plugins import Plugin
from fairdm.views import FairDMUpdateView


class KeywordsPlugin(Plugin, FairDMUpdateView):
    """Plugin for managing keywords on an object."""

    name = "keywords"
    title = _("Manage Keywords")
    form_class = KeywordForm
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

"""Plugins for editing keywords and key dates."""

from crispy_forms.helper import FormHelper
from django.utils.translation import gettext_lazy as _
from extra_views import InlineFormSetView

from fairdm.contrib.generic.forms import (
    CoreInlineFormset,
    DateForm,
    KeywordForm,
)
from fairdm.plugins import Plugin
from fairdm.views import FairDMUpdateView


class KeywordsPlugin(Plugin, FairDMUpdateView):
    """Plugin for managing keywords on an object."""

    name = "keywords"
    title = _("Manage Keywords")
    form_class = KeywordForm
    slug_url_kwarg = "uuid"
    slug_field = "uuid"


class KeyDatesPlugin(Plugin, InlineFormSetView):
    """Plugin for managing key dates on an object with an inline formset."""

    name = "key-dates"
    title = _("Key Dates")
    template_name = "plugins/key-dates.html"
    form_class = DateForm
    formset_class = CoreInlineFormset
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        """Expose the formset as ``form`` with a crispy helper."""
        context = super().get_context_data(**kwargs)
        formset = context.get("formset")
        if formset:
            formset.helper = FormHelper()
            formset.helper.form_id = "key-dates-form"
            context["form"] = formset
        return context

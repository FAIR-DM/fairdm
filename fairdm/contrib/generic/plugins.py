"""Plugins for editing keywords, descriptions and key dates."""

from crispy_forms.helper import FormHelper
from django.utils.translation import gettext_lazy as _
from extra_views import InlineFormSetView
from mvp.views.base import PageMixin

from fairdm.contrib.generic.forms import (
    CoreInlineFormset,
    DateForm,
    DescriptionForm,
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


class DescriptionsPlugin(Plugin, PageMixin, InlineFormSetView):
    """Plugin for managing descriptions on an object with an inline formset."""

    # Without it InlineFormSetView's "_detail" suffix resolves to the record's own detail template (#280).
    template_name = "plugins/descriptions.html"
    form_class = DescriptionForm
    formset_class = CoreInlineFormset
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    page_title = _("Descriptions")
    page_subtitle = _("Manage the descriptive metadata for this object")
    show_page_info_button = True
    page_info_modal_target = "#descriptionsInfoModal"

    def get_context_data(self, **kwargs):
        """Expose the formset as ``form`` with a crispy helper, and add the page-info button settings."""
        context = super().get_context_data(**kwargs)
        formset = context.get("formset")
        if formset:
            formset.helper = FormHelper()
            formset.helper.form_id = "descriptions-form"
            context["form"] = formset

        context["show_page_info_button"] = self.show_page_info_button
        context["page_info_modal_target"] = self.page_info_modal_target

        return context


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

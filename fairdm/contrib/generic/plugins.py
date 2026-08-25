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
    """Base plugin class for managing keywords on FairDM objects."""

    name = "keywords"
    title = _("Manage Keywords")
    form_class = KeywordForm
    slug_url_kwarg = "uuid"
    slug_field = "uuid"


class DescriptionsPlugin(Plugin, PageMixin, InlineFormSetView):
    """Base plugin class for managing descriptions on FairDM objects using inline formsets."""

    # Neither this class nor KeyDatesPlugin below declared a template, so
    # InlineFormSetView's inherited "_detail" suffix resolved to the record's own detail
    # template and the formset was never drawn (issue #280).
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
        context = super().get_context_data(**kwargs)
        formset = context.get("formset")
        if formset:
            formset.helper = FormHelper()
            formset.helper.form_id = "descriptions-form"
            context["form"] = formset

        # Add page header configuration
        context["show_page_info_button"] = self.show_page_info_button
        context["page_info_modal_target"] = self.page_info_modal_target

        return context


class KeyDatesPlugin(Plugin, InlineFormSetView):
    """Base plugin class for managing key dates on FairDM objects using inline formsets."""

    name = "key-dates"
    title = _("Key Dates")
    template_name = "plugins/key-dates.html"
    form_class = DateForm
    formset_class = CoreInlineFormset
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        formset = context.get("formset")
        if formset:
            formset.helper = FormHelper()
            formset.helper.form_id = "key-dates-form"
            context["form"] = formset
        return context

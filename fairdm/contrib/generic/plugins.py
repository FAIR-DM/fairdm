from crispy_forms.helper import FormHelper
from django.utils.translation import gettext_lazy as _
from extra_views import InlineFormSetView

from fairdm import plugins
from fairdm.contrib.generic.forms import CoreInlineFormset, DateForm, DescriptionForm, KeywordForm
from fairdm.utils.view_mixins import FairDMModelFormMixin
from fairdm.views import FairDMUpdateView


class KeywordsPlugin(plugins.Management, FairDMUpdateView):
    name = "keywords"
    title = _("Manage Keywords")
    menu_item = {
        "name": _("Keywords"),
        "icon": "keywords",
    }
    heading_config = {
        "title": _("Keywords"),
    }
    form_class = KeywordForm


class DescriptionsPlugin(plugins.Management, FairDMModelFormMixin, InlineFormSetView):
    name = "descriptions"
    title = _("Edit Descriptions")
    menu_item = {
        "name": _("Descriptions"),
        "icon": "description",
    }
    heading_config = {
        "title": _("Descriptions"),
    }
    form_class = DescriptionForm
    formset_class = CoreInlineFormset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("formset", None)
        form.helper = FormHelper()
        form.helper.form_id = "descriptions-form"
        context["form"] = form
        return context


class KeyDatesPlugin(plugins.Management, FairDMModelFormMixin, InlineFormSetView):
    name = "key-dates"
    title = _("Key Dates")
    menu_item = {
        "name": _("Key Dates"),
        "icon": "calendar",
    }
    heading_config = {
        "title": _("Key dates"),
    }
    form_class = DateForm
    formset_class = CoreInlineFormset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get("formset", None)
        form.helper = FormHelper()
        form.helper.form_id = "key-dates-form"
        context["form"] = form
        return context

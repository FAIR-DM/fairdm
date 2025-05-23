from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import UpdateView
from extra_views import InlineFormSetView

from fairdm.contrib.generic.forms import CoreInlineFormset, DateForm, DescriptionForm, KeywordForm
from fairdm.plugins import ModelFormPlugin


class KeywordsPlugin(ModelFormPlugin, UpdateView):
    name = _("Keywords")
    title = _("Manage Keywords")
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/keywords.html"
    icon = "gear"
    form_class = KeywordForm


class DescriptionsPlugin(ModelFormPlugin, InlineFormSetView):
    title = _("Edit Descriptions")
    name = "Descriptions"
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/descriptions.html"
    form_class = DescriptionForm
    formset_class = CoreInlineFormset
    template_name = "cotton/layouts/plugin/form.html"


class KeyDatesPlugin(ModelFormPlugin, InlineFormSetView):
    title = _("Key Dates")
    name = "Key Dates"
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/dates.html"
    form_class = DateForm
    formset_class = CoreInlineFormset
    template_name = "cotton/layouts/plugin/form.html"

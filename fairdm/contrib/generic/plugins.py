from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import UpdateView
from extra_views import InlineFormSetView

from fairdm import plugins
from fairdm.contrib.generic.forms import CoreInlineFormset, DateForm, DescriptionForm, KeywordForm


class KeywordsPlugin(plugins.Management, UpdateView):
    title = _("Manage Keywords")
    menu_item = {
        "name": _("Keywords"),
        "icon": "keywords",
    }
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/keywords.html"
    form_class = KeywordForm


class DescriptionsPlugin(plugins.Management, InlineFormSetView):
    title = _("Edit Descriptions")
    menu_item = {
        "name": _("Descriptions"),
        "icon": "description",
    }
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/descriptions.html"
    form_class = DescriptionForm
    formset_class = CoreInlineFormset
    template_name = "cotton/layouts/plugin/form.html"


class KeyDatesPlugin(plugins.Management, InlineFormSetView):
    title = _("Key Dates")
    menu_item = {
        "name": _("Key Dates"),
        "icon": "calendar",
    }
    learn_more = "https://fairdm.readthedocs.io/en/latest/user-guide/dates.html"
    form_class = DateForm
    formset_class = CoreInlineFormset
    template_name = "cotton/layouts/plugin/form.html"

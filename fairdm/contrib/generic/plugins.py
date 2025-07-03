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
    form_class = KeywordForm


class DescriptionsPlugin(plugins.Management, InlineFormSetView):
    title = _("Edit Descriptions")
    menu_item = {
        "name": _("Descriptions"),
        "icon": "description",
    }
    form_class = DescriptionForm
    formset_class = CoreInlineFormset


class KeyDatesPlugin(plugins.Management, InlineFormSetView):
    title = _("Key Dates")
    menu_item = {
        "name": _("Key Dates"),
        "icon": "calendar",
    }
    form_class = DateForm
    formset_class = CoreInlineFormset

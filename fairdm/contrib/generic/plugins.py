from crispy_forms.helper import FormHelper
from django.utils.translation import gettext_lazy as _
from extra_views import InlineFormSetView

from fairdm.contrib.generic.forms import (
    CoreInlineFormset,
    DateForm,
    DescriptionForm,
    KeywordForm,
)
from fairdm.plugins import FairDMPlugin
from fairdm.views import FairDMModelFormMixin, FairDMUpdateView


class KeywordsPlugin(FairDMPlugin, FairDMUpdateView):
    """Base plugin class for managing keywords on FairDM objects."""

    name = "keywords"
    title = _("Manage Keywords")
    menu_item = None  # Subclasses should define this with a category
    form_class = KeywordForm
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_template_names(self):
        """
        Return a list of template names for form-based plugin views.

        Template resolution order:
        1. {model_name}/plugins/keywords.html
        2. fairdm/plugins/keywords.html
        3. fairdm/plugins/form.html (generic form template)
        4. fairdm/plugin.html (fallback)
        """
        if self.template_name is not None:
            return [self.template_name]

        templates = []

        # Check if we have a base_model
        if self.base_model:
            # Model-specific plugin template (e.g., project/plugins/keywords.html)
            templates.append(f"{self.base_model._meta.model_name}/plugins/keywords.html")

        # Framework-specific plugin template
        templates.append("fairdm/plugins/keywords.html")

        # Generic form template - covers 90% of form-based plugin use cases
        templates.append("fairdm/plugins/form.html")

        # Fallback: default plugin template
        templates.append("fairdm/plugin.html")

        return templates


class DescriptionsPlugin(FairDMPlugin, FairDMModelFormMixin, InlineFormSetView):
    """Base plugin class for managing descriptions on FairDM objects using inline formsets."""

    name = "descriptions"
    title = _("Descriptions")
    menu_item = None  # Subclasses should define this with a category
    form_class = DescriptionForm
    formset_class = CoreInlineFormset
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    # Page configuration
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
        context["page_subtitle"] = self.page_subtitle
        context["show_page_info_button"] = self.show_page_info_button
        context["page_info_modal_target"] = self.page_info_modal_target

        return context


class KeyDatesPlugin(FairDMPlugin, FairDMModelFormMixin, InlineFormSetView):
    """Base plugin class for managing key dates on FairDM objects using inline formsets."""

    name = "key-dates"
    title = _("Key Dates")
    menu_item = None  # Subclasses should define this with a category
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

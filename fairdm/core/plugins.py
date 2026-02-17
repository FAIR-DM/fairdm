from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from extra_views import InlineFormSetView

from fairdm.contrib.activity_stream.utils import get_object_activities
from fairdm.contrib.plugins import Plugin
from fairdm.forms import Form
from fairdm.views import FairDMDeleteView, FairDMModelFormMixin, FairDMUpdateView


class DeleteForm(Form):
    confirm = forms.BooleanField(
        label=_("I confirm that I want to delete this dataset"),
        required=True,
        help_text=_("This action cannot be undone."),
    )

    def clean_confirm(self):
        if not self.cleaned_data.get("confirm"):
            raise forms.ValidationError(_("You must confirm the deletion."))
        return self.cleaned_data["confirm"]

    class Meta:
        fields = ["confirm"]


class OverviewPlugin(Plugin, TemplateView):
    """Legacy base class for overview plugins.

    NOTE: This class is deprecated and maintained only for backward compatibility.
    New plugins should inherit from BaseOverviewPlugin instead.

    A plugin for displaying an overview of a project or dataset.

    This plugin is used to provide a detailed overview of a project or dataset, including
    its associated contributors and other relevant information.

    Behavior:
    - Render a generic DetailView using self.object as the primary object.

    Note: this probably needs to be optimized to select related objects.
    """

    def get_context_data(self, **kwargs):
        """Add recent activities to the context."""

        context = super().get_context_data(**kwargs)

        # Get the 5 most recent activities for this object
        recent_activities = get_object_activities(self.object, limit=5)

        context["recent_activities"] = recent_activities
        return context

    def get_page_title(self):
        """Return the string representation of the object as the page title."""
        return str(self.object)

    def get_breadcrumbs(self) -> list[dict[str, str]]:
        breadcrumbs = super().get_breadcrumbs()  # type: ignore[misc]
        breadcrumbs = breadcrumbs[:-1]  # Remove last breadcrumb (current page)
        breadcrumbs[-1].pop("href", None)  # Remove href from last breadcrumb
        return breadcrumbs


class EditPlugin(Plugin, FairDMUpdateView):
    """Legacy base class for edit plugins.

    NOTE: This class is deprecated and maintained only for backward compatibility.
    New plugins should inherit from BaseEditPlugin instead.
    """

    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_template_names(self):
        """Return a list of template names

        for form-based plugin views.

               Template resolution order:
               1. {model_name}/plugins/{plugin_class_name}.html (e.g., contributor/plugins/edit.html)
               2. fairdm/plugins/{plugin_class_name}.html (e.g., fairdm/plugins/edit.html)
               3. fairdm/plugins/form.html (generic form template - covers 90% of use cases)
               4. fairdm/plugin.html (fallback)
        """
        from fairdm.plugins import slugify

        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = slugify(self.__class__.__name__)

        # Check if we have a base_model
        if hasattr(self, "model") and self.model:
            # Model-specific plugin template (e.g., contributor/plugins/edit.html)
            templates.append(f"{self.model._meta.model_name}/plugins/{plugin_class_name}.html")

        # Framework-specific plugin template (e.g., fairdm/plugins/edit.html)
        templates.append(f"fairdm/plugins/{plugin_class_name}.html")

        # Generic form template - covers 90% of form-based plugin use cases
        templates.append("fairdm/plugins/form.html")

        # Fallback: default plugin template
        templates.append("fairdm/plugin.html")

        return templates


class InlineFormSetPlugin(Plugin, FairDMModelFormMixin, InlineFormSetView):
    """Legacy base class for inline formset plugins.

    NOTE: This class is deprecated and maintained only for backward compatibility.

    Base plugin class for managing inline formsets.

    This plugin provides a standardized way to edit related objects using Django's
    InlineFormSetView from django-extra-views. It handles formset rendering,
    validation, and saving.

    Attributes:
        title: Display title for the plugin
        slug_url_kwarg: URL kwarg for object lookup (default: "uuid")
        slug_field: Model field for object lookup (default: "uuid")
        inline_model: The related model for the inline formset (required)
        formset_class: The formset class to use (default: BaseInlineFormSet)
        factory_kwargs: Additional kwargs for inlineformset_factory
        display_as_table: Whether to render formset as a table (default: False)

    Template Resolution Order:
        1. {model_name}/plugins/{plugin_class_name}.html
        2. fairdm/plugins/{plugin_class_name}.html
        3. fairdm/plugins/formset.html (generic formset template - covers 90% of use cases)
        4. fairdm/plugin.html (fallback)
    """

    title = _("Edit Related Objects")
    slug_url_kwarg = "uuid"
    slug_field = "uuid"
    factory_kwargs = {
        "extra": 1,
        "max_num": None,
        "can_order": False,
        "can_delete": True,
    }
    display_as_table = False

    def get_template_names(self):
        """
        Return a list of template names for formset-based plugin views.

        Template resolution order:
        1. {model_name}/plugins/{plugin_class_name}.html (e.g., contributor/plugins/identifiers.html)
        2. fairdm/plugins/{plugin_class_name}.html (e.g., fairdm/plugins/identifiers.html)
        3. fairdm/plugins/formset.html (generic formset template - covers 90% of use cases)
        4. fairdm/plugin.html (fallback)
        """
        from fairdm.plugins import slugify

        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = slugify(self.__class__.__name__)

        # Check if we have a model
        if hasattr(self, "model") and self.model:
            # Model-specific plugin template (e.g., contributor/plugins/identifiers.html)
            templates.append(f"{self.model._meta.model_name}/plugins/{plugin_class_name}.html")

        # Framework-specific plugin template (e.g., fairdm/plugins/identifiers.html)
        templates.append(f"fairdm/plugins/{plugin_class_name}.html")

        # Generic formset template - covers 90% of formset-based plugin use cases
        templates.append("fairdm/plugins/formset.html")

        # Fallback: default plugin template
        templates.append("fairdm/plugin.html")

        return templates

    def get_context_data(self, **kwargs):
        """Add formset helper configuration to context."""
        context = super().get_context_data(**kwargs)
        formset = context.get("formset")
        if formset and not hasattr(formset, "helper"):
            formset.helper = FormHelper()
            formset.helper.form_id = f"{self.name}-form" if hasattr(self, "name") else "formset-form"
            # Only use table template if display_as_table is True
            if self.display_as_table:
                formset.helper.template = "bootstrap5/table_inline_formset.html"
            context["form"] = formset
        return context


# =============================================================================
# New Plugin API - Reusable Base Classes
# =============================================================================
# These classes use the new Plugin API and are designed to be inherited
# and customized by portal developers. They provide common patterns for
# overview, editing, and deletion functionality.
# =============================================================================


class BaseOverviewPlugin(Plugin, TemplateView):
    """Reusable overview plugin for displaying object details.

    This base class provides a standard overview/detail view for any model.
    Portal developers can inherit from this and customize:
    - menu: Configure tab label, icon, and order
    - template_name: Override the template (or use hierarchical resolution)
    - get_context_data(): Add custom context variables
    - permission: Set required permission for access

    Example:
        ```python
        from fairdm import plugins
        from fairdm.core.plugins import BaseOverviewPlugin


        @plugins.register(Sample)
        class SampleOverview(BaseOverviewPlugin):
            menu = {"label": "Overview", "icon": "eye", "order": 0}
            template_name = "samples/plugins/overview.html"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["measurements"] = self.object.measurements.all()
                return context
        ```
    """

    menu = {"label": _("Overview"), "icon": "eye", "order": 0}

    def get_context_data(self, **kwargs):
        """Add recent activities to the context if activity stream is enabled."""
        context = super().get_context_data(**kwargs)

        # Add activities if available (optional contrib app)
        try:
            context["activities"] = get_object_activities(self.object, limit=10)
        except (ImportError, AttributeError):
            pass

        return context


class BaseEditPlugin(Plugin, FairDMUpdateView):
    """Reusable edit plugin for model forms.

    This base class provides a standard edit view with form handling.
    Portal developers can inherit from this and customize:
    - form_class: Set the form class for editing
    - menu: Configure tab label, icon, and order
    - template_name: Override the template (or use hierarchical resolution)
    - permission: Set required permission (defaults to change permission)

    Example:
        ```python
        from fairdm import plugins
        from fairdm.core.plugins import BaseEditPlugin
        from .forms import SampleForm


        @plugins.register(Sample)
        class SampleEdit(BaseEditPlugin):
            form_class = SampleForm
            menu = {"label": "Edit", "icon": "pencil", "order": 10}
            permission = "samples.change_sample"
        ```
    """

    menu = {"label": _("Edit"), "icon": "pencil", "order": 100}

    def get_success_url(self):
        """Return to the base object's detail page after successful save."""
        return self.object.get_absolute_url()


class BaseDeletePlugin(Plugin, FairDMDeleteView):
    """Reusable delete plugin with confirmation.

    This base class provides a standard delete view with confirmation form.
    Portal developers can inherit from this and customize:
    - menu: Configure tab label, icon, and order
    - template_name: Override the template (or use hierarchical resolution)
    - get_success_url(): Customize redirect after deletion
    - permission: Set required permission (defaults to delete permission)

    The default behavior requires users to check a confirmation box before
    deletion can proceed.

    Example:
        ```python
        from fairdm import plugins
        from fairdm.core.plugins import BaseDeletePlugin


        @plugins.register(Sample)
        class SampleDelete(BaseDeletePlugin):
            menu = {"label": "Delete", "icon": "trash", "order": 1000}
            permission = "samples.delete_sample"

            def get_success_url(self):
                # Redirect to the project after deleting a sample
                return self.object.project.get_absolute_url()
        ```
    """

    menu = {"label": _("Delete"), "icon": "trash", "order": 1000}
    form_class = DeleteForm
    template_name = "plugins/delete.html"

    def get_success_url(self):
        """Redirect to model's list view after successful deletion."""
        # Try to get parent object's URL first
        if hasattr(self.object, "project"):
            return self.object.project.get_absolute_url()
        if hasattr(self.object, "dataset"):
            return self.object.dataset.get_absolute_url()

        # Fall back to model's list view
        app_label = self.object._meta.app_label
        model_name = self.object._meta.model_name
        try:
            return reverse(f"{app_label}:{model_name}-list")
        except Exception:
            return reverse("home")

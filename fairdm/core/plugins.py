from crispy_forms.helper import FormHelper
from django import forms
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from extra_views import InlineFormSetView

from fairdm.contrib.activity_stream.utils import get_object_activities
from fairdm.forms import Form
from fairdm.plugins import EXPLORE, MANAGEMENT, FairDMPlugin, PluginMenuItem
from fairdm.views import FairDMDeleteView, FairDMModelFormMixin, FairDMUpdateView

from .dataset.views import DatasetListView
from .project.views import ProjectListView


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


class OverviewPlugin(FairDMPlugin, TemplateView):
    """
    A plugin for displaying an overview of a project or dataset.

    This plugin is used to provide a detailed overview of a project or dataset, including
    its associated contributors and other relevant information.

    Behavior:
    - Render a generic DetailView using self.base_object as the primary object.

    Note: this probably needs to be optimized to select related objects.
    """

    title = _("Overview")
    menu_item = PluginMenuItem(name=_("Overview"), category=EXPLORE, icon="view")

    def get_context_data(self, **kwargs):
        """Add recent activities to the context."""

        context = super().get_context_data(**kwargs)

        # Make base_object available as 'object' for template compatibility
        context["object"] = self.base_object

        # Get the 5 most recent activities for this object
        recent_activities = get_object_activities(self.base_object, limit=5)

        context["recent_activities"] = recent_activities
        return context

    def get_page_title(self):
        """Return the string representation of the base object as the page title."""
        return str(self.base_object)

    def get_breadcrumbs(self) -> list[dict[str, str]]:
        breadcrumbs = super().get_breadcrumbs()
        breadcrumbs = breadcrumbs[:-1]  # Remove last breadcrumb (current page)
        breadcrumbs[-1].pop("href", None)  # Remove href from last breadcrumb
        return breadcrumbs


class EditPlugin(FairDMPlugin, FairDMUpdateView):
    title = _("Basic Information")
    slug_url_kwarg = "uuid"
    slug_field = "uuid"

    def get_template_names(self):
        """
        Return a list of template names for form-based plugin views.

        Template resolution order:
        1. {model_name}/plugins/{plugin_class_name}.html (e.g., contributor/plugins/edit.html)
        2. fairdm/plugins/{plugin_class_name}.html (e.g., fairdm/plugins/edit.html)
        3. fairdm/plugins/form.html (generic form template - covers 90% of use cases)
        4. fairdm/plugin.html (fallback)
        """
        from fairdm.plugins import class_to_slug

        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = class_to_slug(self.__class__.__name__)

        # Check if we have a base_model
        if self.base_model:
            # Model-specific plugin template (e.g., contributor/plugins/edit.html)
            templates.append(f"{self.base_model._meta.model_name}/plugins/{plugin_class_name}.html")

        # Framework-specific plugin template (e.g., fairdm/plugins/edit.html)
        templates.append(f"fairdm/plugins/{plugin_class_name}.html")

        # Generic form template - covers 90% of form-based plugin use cases
        templates.append("fairdm/plugins/form.html")

        # Fallback: default plugin template
        templates.append("fairdm/plugin.html")

        return templates


class InlineFormSetPlugin(FairDMPlugin, FairDMModelFormMixin, InlineFormSetView):
    """
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
    factory_kwargs = {"extra": 1, "max_num": None, "can_order": False, "can_delete": True}
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
        from fairdm.plugins import class_to_slug

        if self.template_name is not None:
            return [self.template_name]

        templates = []
        plugin_class_name = class_to_slug(self.__class__.__name__)

        # Check if we have a base_model
        if self.base_model:
            # Model-specific plugin template (e.g., contributor/plugins/identifiers.html)
            templates.append(f"{self.base_model._meta.model_name}/plugins/{plugin_class_name}.html")

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


class DeleteObjectPlugin(FairDMPlugin, FairDMDeleteView):
    name = "delete"
    title = _("Delete")
    menu_item = PluginMenuItem(name=_("Delete"), category=MANAGEMENT, icon="delete")
    form_config = {
        "submit_button": {
            "text": _("Delete"),
            "class": "btn-danger btn-lg",
        },
    }
    form_class = DeleteForm

    def get_success_url(self):
        self.messages.info(
            _("Successfully deleted {object}.").format(object=self.base_object),
        )
        return self.request.user.get_absolute_url()


class ProjectPlugin(FairDMPlugin, ProjectListView):
    """
    A plugin for displaying and filtering a list of projects related to a contributor.

    Inherits from `FairDMListView` to add filtering functionality to the list of projects.
    This plugin handles the display and filtering of projects associated with the current
    contributor.

    Behavior:
    - Registers itself to the "contributor" detail view.
    - Retrieves the list of projects associated with the contributor.
    - Supports filtering and pagination for the project list via `FairDMListView`.

    Note: This plugin requires a model method `projects` to retrieve the a Project queryset from the related object.
    """

    title = _("Projects")
    menu_item = PluginMenuItem(name=_("Projects"), category=EXPLORE, icon="project")
    template_name = "plugins/list_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_url"] = reverse("project-create")
        return context

    def get_queryset(self, *args, **kwargs):
        return self.base_object.projects.all()

    def get_heading_config(self):
        """
        Returns the heading configuration for the project list view.
        """
        return {
            "description": _(f"The following projects are associated with {self.base_object}."),
            "title_actions": ["project.create-button"],
        }


class DatasetPlugin(FairDMPlugin, DatasetListView):
    """
    A plugin for displaying and filtering a list of datasets related to a parent object.

    Inherits from `FairDMListView` to add filtering functionality to the list of datasets.
    This plugin handles the display and filtering of datasets associated with the current
    parent object.

    Behavior:
    - Registers itself to detail views that have related datasets.
    - Retrieves the list of datasets associated with the parent object.
    - Supports filtering and pagination for the dataset list via `FairDMListView`.

    Note: This plugin requires a model method `datasets` to retrieve the Dataset queryset from the related object.
    """

    title = _("Datasets")
    menu_item = PluginMenuItem(name=_("Datasets"), category=EXPLORE, icon="dataset")
    template_name = "plugins/list_view.html"

    def get_queryset(self, *args, **kwargs):
        return self.base_object.datasets.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["create_url"] = (
            self.get_create_url()
            + f"?{self.base_object.__class__.__name__.lower()}={self.base_object.id}&next={self.request.path}"
        )
        return context

    def get_create_url(self):
        """
        Returns the URL for creating a new dataset.
        """
        return reverse("dataset-create")

    def get_heading_config(self):
        """
        Returns the heading configuration for the project list view.
        """
        return {
            "description": _(f"The following datasets are associated with {self.base_object}."),
            "title_actions": ["dataset.create-button"],
        }

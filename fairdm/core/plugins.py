from django import forms
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView

from fairdm.forms import Form
from fairdm.plugins import EXPLORE, FairDMPlugin, PluginMenuItem
from fairdm.registry import registry
from fairdm.views import FairDMDeleteView, FairDMUpdateView

from .dataset.views import DatasetListView
from .project.views import ProjectListView
from .views import DataTableView


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


class ActivityPlugin(TemplateView):
    title = _("Recent Activity")
    menu_item = PluginMenuItem(name=_("Activity"), icon="activity")
    title_config = {
        "text": _("Recent Activity"),
    }
    grid_config = {"card": "activity.action_compact"}
    template_name = "plugins/activity_stream.html"


class OverviewPlugin(FairDMPlugin, TemplateView):
    """
    A plugin for displaying an overview of a project or dataset.

    This plugin is used to provide a detailed overview of a project or dataset, including
    its associated contributors and other relevant information.

    Behavior:
    - Render a generic DetailView using self.base_object as the primary object.

    Note: this probably needs to be optimized to select related objects.
    """

    category = EXPLORE
    title = _("Overview")
    menu_item = PluginMenuItem(name=_("Overview"), icon="eye")


class ManageBaseObjectPlugin(FairDMUpdateView):
    name = "basic-information"
    title = _("Basic Information")
    menu_item = PluginMenuItem(name=_("Basic Information"), icon="gear")
    heading_config = {
        "title": _("Basic Information"),
    }


class DeleteObjectPlugin(FairDMDeleteView):
    name = "delete"
    title = _("Delete")
    menu_item = PluginMenuItem(name=_("Delete"), icon="trash")
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


class ProjectPlugin(ProjectListView):
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

    menu_item = PluginMenuItem(name=_("Projects"), icon="project")

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


class DatasetPlugin(DatasetListView):
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

    menu_item = PluginMenuItem(name=_("Datasets"), icon="dataset")
    # actions = ["dataset.create-button"]

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


class DataTablePlugin(DataTableView):
    title = _("Data")
    sections = {"header": "datatable.header"}
    menu_item = PluginMenuItem(name=_("Data"), icon="table")

    def get_queryset(self, *args, **kwargs):
        # return self.base_object.samples.instance_of(self.model)
        if hasattr(self.model, "sample_ptr"):
            return self.model.objects.filter(dataset=self.base_object)
        elif hasattr(self.model, "measurement_ptr"):
            return self.model.objects.filter(sample__dataset=self.base_object)

        return super().get_queryset(*args, **kwargs)

        # return self.model.objects.filter(dataset=self.base_object)

    @classmethod
    def get_urls(cls, **kwargs):
        """
        Return the URLs for the table view.
        """
        if not registry.samples or not registry.measurements:
            # In case there are no samples or measurements registered, return an empty list.
            return [], None
        urls = []
        for item in [*registry.samples, *registry.measurements]:
            urls.append(
                path(
                    f"{item['type']}s/{item['slug']}/",
                    cls.as_view(model=item["class"], **kwargs),
                    name=f"{item['slug']}-collection",
                )
            )
        first = registry.samples[0]

        return urls, f"{first['slug']}-collection"

from django.utils.translation import gettext as _
from django.views.generic import DetailView, UpdateView
from django.views.generic.base import TemplateView
from render_fields.views import FieldsetsMixin

from fairdm import plugins
from fairdm.core.filters import DatasetFilter, ProjectFilter
from fairdm.utils.utils import feature_is_enabled
from fairdm.views import FairDMListView

from .models import Dataset, Project
from .views import DataTableView


class DiscussionPlugin(plugins.Explore, TemplateView):
    title = name = _("Discussion")
    menu_item = {
        "name": _("Discussion"),
        "icon": "comments",
    }
    menu_check = feature_is_enabled("ALLOW_DISCUSSIONS")
    icon = "comments"
    template_name = "plugins/discussion.html"


class ActivityPlugin(plugins.Explore, TemplateView):
    title = _("Recent Activity")
    menu_item = {
        "name": _("Activity"),
        "icon": "activity",
    }
    template_name = "plugins/activity_stream.html"


class Images(plugins.Explore, TemplateView):
    menu_item = {
        "name": _("Images"),
        "icon": "images",
    }
    template_name = "plugins/images.html"


class OverviewPlugin(plugins.Explore, FieldsetsMixin, DetailView):
    """
    A plugin for displaying an overview of a project or dataset.

    This plugin is used to provide a detailed overview of a project or dataset, including
    its associated contributors and other relevant information.

    Behavior:
    - Render a generic DetailView using self.base_object as the primary object.

    Note: this probably needs to be optimized to select related objects.
    """

    title = _("Overview")
    menu_item = {
        "name": _("Overview"),
        "icon": "overview",
    }
    slug = ""

    @property
    def model(self):
        return self.base_object.__class__

    def get_object(self, queryset=None):
        return self.base_object

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]
        opts = self.model._meta
        if self.model is not None and self.template_name_suffix is not None:
            templates = [
                f"{opts.app_label}/{opts.object_name.lower()}{self.template_name_suffix}.html",
                # "fairdm_core/sample_detail.html",
                f"fairdm/object{self.template_name_suffix}.html",
            ]
            print(templates)
            return templates
        return super().get_template_names()


class ManageBaseObjectPlugin(plugins.Management, UpdateView):
    title = _("Configure")
    menu_item = {
        "name": _("Configure"),
        "icon": "gear",
    }

    @staticmethod
    def check(request, instance, **kwargs):
        return request.user.is_superuser

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context["menu"] = flex_menu.root[self.related_class.__name__]["Manage"]
    #     return context


class ProjectPlugin(plugins.Explore, FairDMListView):
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
    model = Project
    filterset_class = ProjectFilter
    menu_item = {
        "name": _("Projects"),
        "icon": "project",
    }
    card = "project.card"

    def get_queryset(self, *args, **kwargs):
        return self.base_object.projects.all()


class DatasetPlugin(plugins.Explore, FairDMListView):
    """
    A plugin for displaying and filtering datasets related to another entry in the database.
    """

    title = _("Datasets")
    model = Dataset
    filterset_class = DatasetFilter
    menu_item = {
        "name": _("Datasets"),
        "icon": "dataset",
    }
    card = "dataset.card"

    def get_queryset(self, *args, **kwargs):
        return self.base_object.datasets.all()


class DataTablePlugin(plugins.Explore, DataTableView):
    title = _("Data")
    menu_item = {
        "name": _("Data"),
        "icon": "data",
    }
    template_name = "plugins/data_table.html"
    menu_check = feature_is_enabled("SHOW_DATA_TABLES")
    icon = "sample"
    extra_context = {
        # DANGER: REMOVE ME
        "can_add": True,
    }

    def get_queryset(self, *args, **kwargs):
        # return self.base_object.samples.instance_of(self.model)
        if hasattr(self.model, "sample_ptr"):
            return self.model.objects.filter(dataset=self.base_object)
        elif hasattr(self.model, "measurement_ptr"):
            return self.model.objects.filter(sample__dataset=self.base_object)

        return super().get_queryset(*args, **kwargs)

        # return self.model.objects.filter(dataset=self.base_object)

import waffle
from django import forms
from django.http import Http404
from django.urls import path, reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView
from render_fields.views import FieldsetsMixin

from fairdm import plugins
from fairdm.forms import Form
from fairdm.registry import registry
from fairdm.views import FairDMDeleteView

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


class DiscussionPlugin(plugins.Explore, TemplateView):
    name = "discussion"
    title = _("Discussion")
    menu_item = {
        "name": _("Discussion"),
        "icon": "comments",
    }
    icon = "comments"
    template_name = "plugins/discussion.html"

    sidebar_secondary_config = {"visible": True}  # Hide the secondary sidebar by default

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to check if the discussion plugin is enabled.
        """
        if not self.check(request, self.base_object, **kwargs):
            raise Http404(_("This plugin has not been enabled."))
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def check(request, instance, **kwargs):
        """
        Check if the user has permission to view the discussion plugin.
        This can be overridden in subclasses to implement custom logic.
        """
        return waffle.switch_is_active("allow_discussions")


class ActivityPlugin(plugins.Explore, TemplateView):
    title = _("Recent Activity")
    menu_item = {
        "name": _("Activity"),
        "icon": "activity",
    }
    title_config = {
        "text": _("Recent Activity"),
    }
    grid_config = {"card": "activity.action_compact"}
    template_name = "plugins/activity_stream.html"


class Images(plugins.Explore, TemplateView):
    menu_item = {
        "name": _("Images"),
        "icon": "images",
    }
    template_name = "plugins/images.html"


class OverviewPlugin(plugins.Explore, FieldsetsMixin, TemplateView):
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
    sections = {"heading": False}
    path = ""

    @property
    def model(self):
        return self.base_object.__class__

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.base_object
        return context

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]
        opts = self.model._meta
        templates = [f"{opts.app_label}/{opts.object_name.lower()}{self.template_name_suffix}.html"]
        if hasattr(self.model, "type_of"):
            poly_opts = self.model.type_of._meta
            templates += [f"{poly_opts.app_label}/{poly_opts.object_name.lower()}{self.template_name_suffix}.html"]

        templates += [
            f"fairdm/object{self.template_name_suffix}.html",
        ]
        return templates
        # return super().get_template_names()


class ManageBaseObjectPlugin(plugins.Management, UpdateView):
    name = "configure"
    title = _("Configure")
    menu_item = {
        "name": _("Configure"),
        "icon": "gear",
    }


class DeleteObjectPlugin(plugins.Management, FairDMDeleteView):
    name = "delete"
    title = _("Delete")
    menu_item = {
        "name": _("Delete"),
        "icon": "trash",
    }
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


class ProjectPlugin(plugins.Explore, ProjectListView):
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

    menu_item = {
        "name": _("Projects"),
        "icon": "project",
    }

    def get_queryset(self, *args, **kwargs):
        return self.base_object.projects.all()


class DatasetPlugin(plugins.Explore, DatasetListView):
    """
    A plugin for displaying and filtering datasets related to another entry in the database.
    """

    menu_item = {
        "name": _("Datasets"),
        "icon": "dataset",
    }
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


class DataTablePlugin(plugins.Explore, DataTableView):
    title = _("Data")
    sections = {"header": "datatable.header"}
    menu_item = {
        "name": _("Data"),
        "icon": "table",
    }

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

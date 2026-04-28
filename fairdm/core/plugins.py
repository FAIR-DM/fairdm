from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.plugins import Plugin
from fairdm.views import FairDMDeleteView, FairDMTemplateView, FairDMUpdateView


class OverviewPlugin(Plugin, FairDMTemplateView):
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
        from fairdm.core.plugins import OverviewPlugin


        @plugins.register(Sample)
        class SampleOverview(OverviewPlugin):
            menu = {"label": "Overview", "icon": "eye", "order": 0}
            template_name = "samples/plugins/overview.html"

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context["measurements"] = self.object.measurements.all()
                return context
        ```
    """

    page_subtitle = _("Overview")
    page_icon = "overview"
    menu = {"label": _("Overview"), "icon": "overview", "order": 0}

    def get_page_title(self):
        """Default page title is the object's string representation."""
        return str(self.object)

    # def get_page_title(self):
    #     """Default page title is the object's string representation."""
    #     return str(self.get_object())


class UpdatePlugin(Plugin, FairDMUpdateView):
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
        from fairdm.core.plugins import UpdatePlugin
        from .forms import SampleForm


        @plugins.register(Sample)
        class SampleEdit(UpdatePlugin):
            form_class = SampleForm
            menu = {"label": "Edit", "icon": "pencil", "order": 10}
            permission = "samples.change_sample"
        ```
    """

    page_title = _("Update")
    page_icon = "edit"

    def get_success_url(self):
        """Return to the base object's detail page after successful save."""
        return self.object.get_absolute_url()


class DeletePlugin(Plugin, FairDMDeleteView):
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
        from fairdm.core.plugins import DeletePlugin


        @plugins.register(Sample)
        class SampleDelete(DeletePlugin):
            menu = {"label": "Delete", "icon": "trash", "order": 1000}
            permission = "samples.delete_sample"

            def get_success_url(self):
                # Redirect to the project after deleting a sample
                return self.object.project.get_absolute_url()
        ```
    """

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

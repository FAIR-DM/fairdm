from typing import Any

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
                context["measurements"] = self.base_object.measurements.all()
                return context
        ```
    """

    page_subtitle = _("Overview")
    page_icon = "overview"
    menu = {"label": _("Overview"), "icon": "overview", "order": 0}

    def get_page_title(self):
        """Default page title is the object's string representation."""
        return str(self.base_object)


class TypedOverviewPlugin(OverviewPlugin):
    """The overview of a record portals subclass: a sample or a measurement.

    Two things differ from a project or dataset overview.

    **The template follows the record's type.** For each concrete class from the record's own
    type up to ``base_model``, it looks for ``<app_label>/<model_name>_overview.html``, then falls
    back to ``fallback_template``. A type gets its own page by providing that template, extending
    its record's template and filling the ``overview.*`` blocks it wants. A subtype inherits its
    parent type's page until it provides its own.

    **The record follows its dataset.** It opens for everyone once its own dataset is public and
    published, and otherwise only for that dataset's team (``visible_to``). Anyone else gets a
    404, so the address never confirms the record exists. ``PrivateRecordNotFoundMixin`` can't be
    reused here: it reads ``obj.visibility``, which samples and measurements don't have.
    """

    base_model = None
    fallback_template = None

    @staticmethod
    def check(request, obj):
        # A staticmethod, not a classmethod: registration refuses a classmethod `check`
        # (fairdm.contrib.plugins.access.check_is_valid).
        if obj is None:
            return True
        return type(obj).objects.visible_to(request.user).filter(pk=obj.pk).exists()

    def handle_no_permission(self):
        from django.http import Http404

        raise Http404(_("Nothing matches the given query."))

    def get_template_names(self):
        names = []
        for cls in type(self.base_object).__mro__:
            if cls is self.base_model:
                break
            if isinstance(cls, type) and issubclass(cls, self.base_model) and not cls._meta.abstract:
                names.append(f"{cls._meta.app_label}/{cls._meta.model_name}_overview.html")
        return [*names, self.fallback_template]


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

    page_subtitle = _("Update")
    page_icon = "edit"

    def get_success_url(self):
        """Return to the base object's detail page after successful save."""
        return self.base_object.get_absolute_url()

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        return super().get_context_data(**kwargs)


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
                return self.base_object.project.get_absolute_url()
        ```
    """

    template_name = "plugins/delete.html"

    def get_success_url(self):
        """Redirect to model's list view after successful deletion."""
        # Try to get parent object's URL first
        if hasattr(self.base_object, "project"):
            return self.base_object.project.get_absolute_url()
        if hasattr(self.base_object, "dataset"):
            return self.base_object.dataset.get_absolute_url()

        # Fall back to model's list view
        app_label = self.base_object._meta.app_label
        model_name = self.base_object._meta.model_name
        try:
            return reverse(f"{app_label}:{model_name}-list")
        except Exception:
            return reverse("home")

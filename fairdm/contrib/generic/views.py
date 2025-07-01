from actstream import action
from django.db.models.base import Model as Model
from django.utils.translation import gettext as _
from extra_views import ModelFormSetView, UpdateWithInlinesView

from fairdm import plugins
from fairdm.utils.utils import get_core_object_or_404

from .forms import CoreFormset, DateForm, DescriptionInline


class BaseFormsetView(ModelFormSetView):
    """
    A base view for handling model formsets with dynamic vocabulary integration.

    Behavior:
        - The formset is associated with a specific object determined via `get_object()`.
        - Vocabulary choices are dynamically injected into the context and formset.
        - On successful submission, the view redirects to the same page.
    """

    form_class = None
    formset_class = None
    template_name = None

    @property
    def model(self):
        return self.get_object().dates.model

    def get_object(self):
        return get_core_object_or_404(self.kwargs.get("uuid"))

    def get_success_url(self):
        return self.request.path


class UpdateDatesView(BaseFormsetView):
    """
    A view for updating date-related milestones using a formset.

    Behavior:
        - Retrieves the related date records for the object.
        - Provides vocabulary choices based on the object's `DATE_TYPES`.
        - Logs an action when the formset is successfully submitted.
    """

    form_class = DateForm
    formset_class = CoreFormset
    template_name = "generic/milestone.html"

    def construct_formset(self):
        formset = super().construct_formset()
        formset.helper.form_id = "date-form-collection"
        return formset

    def get_formset_kwargs(self):
        kwargs = super().get_formset_kwargs()
        kwargs.update({"queryset": self.get_queryset()})
        return kwargs

    def get_queryset(self):
        return self.get_object().dates.all()

    def formset_valid(self, formset):
        response = super().formset_valid(formset)
        action.send(
            self.request.user,
            verb=_("updated"),
            target=self.get_object(),
            description=_("Updated milestones."),
        )

        return response


class UpdateCoreObjectBasicInfo(plugins.Management, UpdateWithInlinesView):
    """Presents a form to update the name and descriptions of a Project, Dataset, Sample or Measurment."""

    menu_item = {
        "name": _("Basic Information"),
        "icon": "info",
    }
    sections = {
        "form": "components.form.form-with-inlines",
    }
    inlines = [DescriptionInline]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu_name"] = "DatasetMenu"
        context["object"] = self.get_object()
        return context

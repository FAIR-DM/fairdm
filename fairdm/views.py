from actstream import action
from crispy_forms.helper import FormHelper
from django.contrib.auth.decorators import login_required
from django.db.models.base import Model as Model
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_filters.views import FilterView
from neapolitan.views import CRUDView

from fairdm.contrib.contributors.utils import current_user_has_role
from fairdm.contrib.identity.models import Database
from fairdm.utils.permissions import assign_all_model_perms
from fairdm.utils.view_mixins import CRUDView as CRUDViewMixin
from fairdm.utils.view_mixins import FairDMBaseMixin, FairDMModelFormMixin, HTMXMixin


@method_decorator(login_required, name="show_form")
class BaseCRUDView(FairDMBaseMixin, HTMXMixin, CRUDView):
    menu = None
    path_converter = "str"
    paginate_by = 20
    modals = [
        "modals.social",
        "modals.milestones",
        "modals.keywords",
    ]

    def get_template_names(self):
        if self.template_name is not None:
            return [self.template_name]

        if self.model is not None and self.template_name_suffix is not None:
            return [
                f"{self.model._meta.app_label}/{self.model._meta.object_name.lower()}{self.template_name_suffix}.html",
                f"fairdm/object{self.template_name_suffix}.html",
            ]
        return super().get_template_names()

    def get_detail_context_data(self, context):
        context["user_can_edit"] = self.user_can_edit()
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu"] = self.menu
        func_name = f"get_{self.role.value}_context_data"
        if hasattr(self, func_name):
            context = getattr(self, func_name)(context)
        return context

    def get_meta_title(self, context):
        value = context["object_verbose_name_plural"].capitalize()
        if self.role.value == "create":
            value = _(f"Create {self.model._meta.verbose_name}")
        if self.object:
            value = self.object
        if self.role.value == "edit":
            value = _(f"Edit {self.model._meta.verbose_name}")
        context["title"] = value
        return f"{value} · {Database.get_solo().safe_translation_getter('name')}"


class FairDMTemplateView(FairDMBaseMixin, TemplateView):
    pass


# @method_decorator(cache_page(60 * 5), name="dispatch")
class FairDMListView(FairDMBaseMixin, FilterView):
    """
    The base class for displaying a list of objects within the FairDM framework.
    """

    template_name = "fairdm/list_view.html"
    template_name_suffix = "_list"
    paginate_by = 20
    layout = {
        "container_class": "container",
    }
    sections = {
        "sidebar_primary": "sections.sidebar.form",
        "sidebar_secondary": False,  # hide the secondary sidebar
        "header": False,
        "grid": "sections.object-list",
        "title": "text.title",
    }
    # title_config = {
    #     "actions": [
    #         "list-view-order-action",
    #     ],
    # }
    sidebar_primary_config = {
        "breakpoint": "md",
        "header": {
            "title": _("Filter"),
        },
    }
    grid_config = {
        "cols": 1,
        "gap": 2,
        "card": "project.card",
        "empty_message": _("No results found."),
    }

    def get(self, request, *args, **kwargs):
        """Override the get method of the FilterView to allow views to not specify a filterset_class."""
        filterset_class = self.get_filterset_class()
        if filterset_class is None:
            self.filterset = None
            self.object_list = self.get_queryset()
        else:
            self.filterset = self.get_filterset(filterset_class)
            if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
                self.object_list = self.filterset.qs
            else:
                self.object_list = self.filterset.queryset.none()

        context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
        return self.render_to_response(context)

    def get_model(self):
        return self.model or self.queryset.model

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["object_list"] is not None:
            context["filtered_object_count"] = context["object_list"].count()
        context["is_filtered"] = hasattr(context["filter"].form, "cleaned_data")
        context["object_verbose_name_plural"] = self.get_model()._meta.verbose_name_plural

        # Required for sections.sidebar.form to work without modification
        # Ensure the form method is set to GET
        form = context["filter"].form
        if not hasattr(form, "helper"):
            form.helper = FormHelper()
        form.helper.form_method = "get"
        form.helper.form_id = "filter-form"
        # form.helper.render_unmentioned_fields = False
        # form.helper.layout = Layout(Field("o", type="hidden", form="filter-form"))
        form.helper.render_unmentioned_fields = False
        context["form"] = form
        return context

    def get_filterset_class(self):
        if self.filterset_class is not None:
            # If a filterset class is explicitly set, use it.
            return self.filterset_class
        elif hasattr(self.model, "config"):
            return self.model.config.get_filterset_class()

    def get_meta_image(self, context=None):
        context["image"] = self.image
        return super().get_meta_image(context)


class FairDMDetailView(FairDMBaseMixin, DetailView):
    model = None
    menu = None
    edit_roles = ["Creator", "Reviewer", "ProjectMember"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["menu"] = self.menu
        return context

    def user_can_edit(self):
        if current_user_has_role(self.request, self.object, self.edit_roles):
            return True
        return super().user_can_edit()

    def get_meta_title(self, context):
        value = context["object"]
        context["title"] = value
        title = super().get_meta_title(context)
        return f"{value} · {title}"


class FairDMCreateView(FairDMModelFormMixin, CreateView):
    """
    The base class for creating objects within the FairDM framework.
    """

    def get_template_names(self):
        templates = super().get_template_names()
        return templates

    def form_valid(self, form):
        response = super().form_valid(form)
        assign_all_model_perms(self.request.user, self.object)
        action.send(
            self.request.user,
            verb="created",
            target=self.object,
            description=_("Created a new {}: {}").format(self.object._meta.verbose_name, str(self.object)),
        )
        return response


class FairDMUpdateView(FairDMModelFormMixin, UpdateView):
    """
    The base class for creating objects within the FairDM framework.
    """


class FairDMDeleteView(FairDMModelFormMixin, DeleteView):
    """
    The base class for deleting objects within the FairDM framework.
    """


class FairDMTemplateView(FairDMBaseMixin, TemplateView):
    """
    The base class for template views within the FairDM framework.
    """

    template_name = "fairdm/template_view.html"
    sections = {
        "sidebar_primary": False,
        "sidebar_secondary": False,
        "footer": False,
        "header": False,
    }
    layout = {
        "container_class": "container-lg",
    }


class FairDMCRUDView(CRUDViewMixin):
    view_classes = {
        "list": FairDMListView,
        "create": FairDMCreateView,
        "detail": FairDMDetailView,
        "update": FairDMUpdateView,
        "delete": FairDMDeleteView,
    }

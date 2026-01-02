from __future__ import annotations

from functools import cached_property

from braces.views import MessageMixin
from crispy_forms.helper import FormHelper
from django.contrib.auth.decorators import login_required
from django.db.models import Model
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django_addanother.views import CreatePopupMixin
from django_filters.views import FilterView
from meta.views import MetadataMixin
from mvp.views import SearchOrderMixin

from fairdm.contrib.contributors.utils import current_user_has_role
from fairdm.contrib.identity.models import Identity
from fairdm.core.utils import get_non_polymorphic_instance
from fairdm.forms import Form
from fairdm.utils import assign_all_model_perms, get_model_class

# =============================================================================
# VIEW MIXINS
# =============================================================================


class FairDMBaseMixin(MessageMixin, MetadataMixin):
    """
    A mixin class providing common context and sidebar configuration for views.

    Methods:
        get_context_data(**kwargs):
            Extends the context data with user edit permissions and sidebar configurations.
        user_can_edit():
            Determines if the current user has edit permissions. Returns False by default.
        get_meta_title(context):
            Sets the page title in the context and returns a formatted meta title string.
    """

    about = None
    # Optional about text for the page

    actions = []
    # List of template components to be displayed inline with the page title

    learn_more = None
    # Optional link to a user guide or documentation (use fairdm.utils.utils.user_guide to generate the link)

    page_title = None
    # Title of the page, used in the page title

    @staticmethod
    def check(request, *args, **kwargs):
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_can_edit"] = self.user_can_edit()
        context["about"] = self.get_about()
        context["learn_more"] = self.get_learn_more()
        context["actions"] = self.get_actions()
        context["title"] = self.get_page_title()
        return context

    def get_about(self):
        if isinstance(self.about, list):
            return self.about
        return [self.about]

    def get_actions(self):
        return self.actions

    def get_learn_more(self):
        return self.learn_more

    def user_can_edit(self):
        return False

    def get_meta_title(self, context):
        title = self.get_title() if hasattr(self, "get_title") else self.title
        return f"{title} - {Identity.get_solo().safe_translation_getter('name')}"

    def get_page_title(self):
        """Return the page title for the view."""
        return self.page_title or self.title


class FairDMFormViewMixin:
    """Mixin for form views that provides common form handling functionality."""

    def get_success_url(self):
        if self.request.GET.get("next"):
            return self.request.GET["next"]
        return super().get_success_url()


@method_decorator(login_required, name="post")
class FairDMModelFormMixin(
    FairDMFormViewMixin,
    FairDMBaseMixin,
    CreatePopupMixin,
):
    """
    A mixin class to provide dynamic form class generation for Django model forms.

    Attributes:
        model (Model): The Django model associated with the form.
        form_class (Form): The base form class to use for form generation.
        fields (list or tuple): The fields to include in the generated form.

    Methods:
        get_form_class():
            Returns a form class for the associated model. If both `fields` and `form_class` are set,
            it uses `forms.modelform_factory` to create a form class with the specified fields and base form.
            If the `base_object` has a `config` attribute with a `get_form_class` method (e.g. registered samples/measurements), it delegates form class
            retrieval to that method. Otherwise, it falls back to the superclass implementation.
    """

    model = None
    form_class = None
    fields = None

    def post(self, request, *args, **kwargs):
        """This is here so the method_decorator works correctly."""
        return super().post(request, *args, **kwargs)

    # def get_template(self, template_name=None):
    #     """Return the template to be used for rendering the view."""
    #     if template_name is None:
    #         template_name = self.template_name
    #     return super().get_template(template_name)

    def get_context_data(self, **kwargs):
        """Add the form class to the context if it is set."""
        context = super().get_context_data(**kwargs)
        context["form_visible"] = self.request.user.is_authenticated
        return context

    def get_form_class(self):
        if self.form_class is None and getattr(self.base_object, "config", None):
            self.form_class = self.base_object.config.get_form_class()

        if self.fields:
            return modelform_factory(
                self.model,
                form=self.form_class,
                fields=self.fields,
            )
        return super().get_form_class()


class RelatedObjectMixin:
    """Mixin to fetch and add a related object to the context for views behind the detail view of core models.

    This mixin is primarily used in plugins but can be applied to other views where a related object needs to be
    fetched based on a URL parameter. The related object is retrieved using the URL parameter specified by
    `base_object_url_kwarg` (defaults to `base_uuid`). The related object is then added to the context with additional
    useful information about the related model.

    Example:
        class SampleListView(RelatedObjectMixin, ListView):
            def get_queryset(self):
                return self.base_object.samples.all()
    """

    base_model: Model | None = None
    base_object_url_kwarg = "uuid"

    def get_related_model(self):
        """Retrieve the related model class.

        Uses the URL parameter specified by `base_object_url_kwarg` to fetch the related model class.

        Returns:
            model: The model class corresponding to the related object.
        """
        return get_model_class(self.kwargs.get(self.base_object_url_kwarg))

    @cached_property
    def base_object(self):
        """Fetch the related object based on the primary key in the URL.

        If the related model is polymorphic, the method fetches a non-polymorphic version of the object.
        """
        uuid = self.kwargs.get(self.base_object_url_kwarg)
        obj = get_object_or_404(self.base_model, uuid=uuid)
        if hasattr(obj, "polymorphic_model_marker"):
            # If the object is polymorphic, get the non-polymorphic instance
            self.non_polymorphic = get_non_polymorphic_instance(obj)
        return obj

    def get_context_data(self, **kwargs):
        """Add the related object and related model information to the context.

        Adds the `base_object` (related object), related model class, and model metadata to the context dictionary.
        """
        context = super().get_context_data(**kwargs)
        context["base_object"] = self.base_object
        context["base_model"] = self.base_model
        context["base_model_name"] = self.base_model._meta.model_name
        context["non_polymorphic_object"] = get_non_polymorphic_instance(self.base_object)
        context[self.base_model._meta.model_name] = self.base_object
        return context


# =============================================================================
# CONCRETE VIEW CLASSES
# =============================================================================


class FairDMTemplateView(FairDMBaseMixin, TemplateView):
    pass


# @method_decorator(cache_page(60 * 5), name="dispatch")
class FairDMListView(FairDMBaseMixin, SearchOrderMixin, FilterView):
    """
    The base class for displaying a list of objects within the FairDM framework.
    """

    template_name = "layouts/list_view.html"
    template_name_suffix = "_list"
    paginate_by = 20
    grid_config = {
        "cols": 1,
        "gap": 2,
        "card": "project.card",
        "empty_message": _("No results found."),
    }
    page = {}

    # def get_filterset_kwargs(self, filterset_class):
    #     """Override to apply search and ordering to the base queryset before filtering."""
    #     kwargs = super().get_filterset_kwargs(filterset_class)

    #     # Get the base queryset
    #     queryset = kwargs.get("queryset")

    #     # Apply search from SearchMixin
    #     search_term = self.request.GET.get("q", "").strip()
    #     if search_term and self.get_search_fields():
    #         queryset = self._apply_search(queryset, search_term)

    #     # Apply ordering from OrderMixin
    #     ordering = self.request.GET.get("o", "")
    #     if ordering and self.get_order_by_choices():
    #         queryset = self._apply_ordering(queryset, ordering)

    #     kwargs["queryset"] = queryset
    #     return kwargs

    def get(self, request, *args, **kwargs):
        """Override the get method of the FilterView to allow views to not specify a filterset_class."""
        filterset_class = self.get_filterset_class()
        if filterset_class is None:
            self.filterset = None
            # When no filterset, use the mixin's get_queryset which applies search/ordering
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

    def get_template_names(self):
        """Override template if there's no filter - use plugin template instead."""
        if self.filterset is None:
            # Use the simpler plugin list view template when there's no filter
            return ["plugins/list_view.html"]
        return super().get_template_names()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context["object_list"] is not None:
            context["filtered_object_count"] = context["object_list"].count()

        # Handle case where no filter is present
        if context.get("filter") is not None and hasattr(context["filter"], "form"):
            context["is_filtered"] = hasattr(context["filter"].form, "cleaned_data")

            # Required for sections.sidebar.form to work without modification
            # Ensure the form method is set to GET
            form = context["filter"].form
            if not hasattr(form, "helper"):
                form.helper = FormHelper()
            form.helper.form_method = "get"
            form.helper.form_id = "filter-form"
            form.helper.render_unmentioned_fields = False
            context["form"] = form
        else:
            context["is_filtered"] = False
            context["form"] = None

        context["object_verbose_name_plural"] = self.get_model()._meta.verbose_name_plural
        context["page"] = self.page

        # Add card template if specified
        if hasattr(self, "card_template") and self.card_template:
            context["card_template"] = self.card_template

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

    form_config = {
        "submit_button": {
            "text": _("Create & enter"),
            "icon": "arrow_right",
            "icon_position": "end",
        },
    }

    def get_template_names(self):
        templates = super().get_template_names()
        return templates

    def form_valid(self, form):
        response = super().form_valid(form)
        self.assign_permissions()

        return response

    def assign_permissions(self):
        """
        Assign permissions to the user after creating the object.
        This method can be overridden in subclasses to customize permission assignment.
        """
        assign_all_model_perms(self.request.user, self.object)


class FairDMUpdateView(FairDMModelFormMixin, UpdateView):
    """
    The base class for creating objects within the FairDM framework.
    """


class FairDMDeleteView(FairDMModelFormMixin, DeleteView):
    """
    The base class for deleting objects within the FairDM framework.
    """

    template_name = "layouts/form_view.html"
    form_class = Form
    form_config = {
        "submit_button": {
            "text": _("Confirm delete"),
            "icon": "delete",
            "class": "btn-danger",
        },
        # "cancel_button": {
        #     "text": _("Cancel"),
        #     "css_class": "btn-secondary",
        # },
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.form_class()
        # context["form"] = modelform_factory(self.model, fields=[])()
        # context["form"].helper = FormHelper()
        # context["form"].helper.form_id = "delete-form"
        return context

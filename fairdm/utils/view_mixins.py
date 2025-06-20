from functools import cached_property

from braces.views import MessageMixin
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import get_object_or_404
from django.urls import path
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView, View
from django_addanother.views import CreatePopupMixin
from meta.views import MetadataMixin

from fairdm.contrib.identity.models import Database
from fairdm.core.utils import get_non_polymorphic_instance
from fairdm.utils.utils import get_model_class

from ..layouts import BaseLayout, FormLayout


class FairDMBaseMixin(BaseLayout, MessageMixin, MetadataMixin):
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

    # def get_object(self):
    # return super().get_object() if hasattr(super(), "get_object") else None

    # def dispatch(self, request, *args, **kwargs):
    #     self.object = self.get_object()
    #     if (isinstance(self.check, bool) and not self.check) or (
    #         callable(self.check) and self.check(request, self.object)
    #     ):
    #         raise PermissionDenied(_("You do not have permission to view this page."))
    #     return super().dispatch(request, *args, **kwargs)

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
        return f"{self.title} - {Database.get_solo().safe_translation_getter('name')}"

    def get_page_title(self):
        """Return the page title for the view."""
        return self.page_title or self.title


class FairDMFormViewMixin(FormLayout):
    def get_success_url(self):
        if self.request.GET.get("next"):
            return self.request.GET["next"]
        return super().get_success_url()


class FairDMModelFormMixin(
    FairDMFormViewMixin,
    LoginRequiredMixin,
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
    help_text = None
    form_component = "components.form.default"
    template_name = "fairdm/form_view.html"

    def get_context_data(self, **kwargs):
        """Add the form class to the context if it is set."""
        context = super().get_context_data(**kwargs)
        context["help_text"] = self.get_help_text()
        context["form_component"] = self.get_form_component()
        return context

    def get_form_component(self):
        """Return the form component to be used in the template."""
        return self.form_component

    def get_help_text(self):
        return self.help_text

    def get_form_class(self):
        if self.form_class is None and getattr(self.base_object, "config", None):
            self.form_class = self.base_object.config.get_form_class()

        if self.fields:
            return forms.modelform_factory(
                self.model,
                form=self.form_class,
                fields=self.fields,
            )
        # elif getattr(self.base_object, "config", None):
        # return self.base_object.config.get_form_class()
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

    base_model: models.Model | None = None
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
        return get_object_or_404(self.base_model, uuid=uuid)

    def get_context_data(self, **kwargs):
        """Add the related object and related model information to the context.

        Adds the `base_object` (related object), related model class, and model metadata to the context dictionary.
        """
        context = super().get_context_data(**kwargs)
        context["base_object"] = self.base_object
        context["base_model"] = self.base_model
        context["non_polymorphic_object"] = get_non_polymorphic_instance(self.base_object)
        context[self.base_model._meta.model_name] = self.base_object
        return context


class HTMXMixin:
    """
    Modifies template selection to support HTMX requests by appending a fragment identifier.

    This mixin depends on `django-template-partials` and requires the correct fragment to be
    specified in the template for it to function properly.

    If the request is an HTMX request, the mixin retrieves the `fragment` parameter from the
    request's GET data (defaulting to `"plugin"`) and appends `#fragment` to each template name.
    This enables rendering specific template sections instead of full templates.

    When the request is not from HTMX, the mixin falls back to the standard template selection process.
    """

    htmx_fragment = "plugin"

    def get_template_names(self, template_names=None):
        if template_names is None:
            template_names = super().get_template_names()
        if self.request.htmx:
            fragment = self.request.GET.get("fragment", self.htmx_fragment)
            template_names = [f"{t}#{fragment}" for t in template_names]
        return template_names


class CRUDView(View):
    """Experimental class for generating CRUD views dynamically based on a model."""

    model = None
    base_url = None
    action = None  # Set dynamically in generated views
    view_classes = {
        "list": ListView,
        "create": CreateView,
        "detail": DetailView,
        "update": UpdateView,
        "delete": DeleteView,
    }

    @classmethod
    def get_view_classes(cls):
        merged = {}
        for base in reversed(cls.__mro__):
            if hasattr(base, "view_classes"):
                merged.update(base.view_classes)
        return merged

    @classmethod
    def get_urls(cls):
        if cls.model is None:
            raise ValueError(f"{cls.__name__} requires a `model` attribute.")

        model_name = cls.model._meta.model_name
        base = cls.base_url or model_name
        views = cls.get_view_classes()
        urls = []

        action_paths = {
            "list": (f"{base}/", f"{model_name}_changelist"),
            "create": (f"{base}/add/", f"{model_name}_add"),
            "detail": (f"{base}/<int:pk>/", f"{model_name}_detail"),
            "update": (f"{base}/<int:pk>/change/", f"{model_name}_change"),
            "delete": (f"{base}/<int:pk>/delete/", f"{model_name}_delete"),
        }

        for action, (route, name) in action_paths.items():
            view_class = views.get(action)
            if view_class is False:
                continue
            urls.append(path(route, cls.make_view(action, views), name=name))

        return urls

    @classmethod
    def make_view(cls, action, view_classes):
        base_view = view_classes[action]

        view = type(f"{cls.model.__name__}{base_view.__name__}", (cls, base_view), {"action": action})
        return view.as_view()

    def has_permission(self):
        attr_name = f"has_{self.action}_permission"
        if hasattr(self, attr_name):
            attr = getattr(self, attr_name)
            return attr() if callable(attr) else bool(attr)
        return True

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission():
            raise PermissionError("Permission denied.")
        return super().dispatch(request, *args, **kwargs)

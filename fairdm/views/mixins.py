from __future__ import annotations

from functools import cached_property

from braces.views import MessageMixin
from django.db.models import Model
from django.shortcuts import get_object_or_404
from meta.views import MetadataMixin

from fairdm.core.utils import get_non_polymorphic_instance
from fairdm.utils import get_model_class

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

    @staticmethod
    def check(request, *args, **kwargs):
        return True


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

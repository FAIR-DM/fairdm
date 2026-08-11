"""Plugin mixin base class for extending model detail views."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.forms.widgets import Media
from django.http import HttpRequest, HttpResponse
from django.urls import URLPattern, include, path
from django.views.generic.base import View

if TYPE_CHECKING:
    from collections.abc import Callable


class Plugin(View):
    """Mixin class that adds plugin behavior to Django class-based views.

    Attributes:
        name: Unique identifier per model (auto-derived from class name if not set)
        url_path: URL path segment (auto-derived from name if not set)
        model: Set by registry during registration (base model only)
        menu: Tab configuration dict with keys:
            - label (str, required): Display text
            - icon (str, optional): Icon identifier
            - order (int, optional, default 0): Sort position
            If None/falsey, no tab is created.

    """

    # The model against which a plugin is registered. Set by the registry during registration.
    registered_model: ClassVar[type[Model] | None] = None

    # Plugin name (slugified class name if not set)
    name: ClassVar[str | None] = None
    url_path: ClassVar[str | None] = ""
    # Note: url_path="" (default) → use slugified class name
    #       url_path=None (explicit) → no base path for plugin or subviews
    #       url_path="foo" → use "foo" as base path
    permission: ClassVar[str | None] = None
    check: ClassVar[Callable[[HttpRequest, Model | None], bool] | None] = True
    model: ClassVar[type[Model] | None] = None
    menu: ClassVar[dict[str, Any] | None] = None
    # tab = None
    subviews: ClassVar[list[type[View]] | None] = []
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    @classmethod
    def get_name(cls) -> str:
        """Get the plugin name (slugified class name if not set).

        Returns:
            Plugin name used for URL naming and identification
        """
        if cls.name:
            return cls.name
        from .utils import slugify

        return slugify(cls.__name__)

    @classmethod
    def get_url_path(cls) -> str | None:
        """Get the URL path segment.

        Returns:
            URL path segment (e.g., "analysis" or "download"),
            or None if url_path is explicitly set to None (no base path)
        """
        if cls.url_path is None:
            return None
        if cls.url_path:
            return cls.url_path
        return cls.get_name()

    @classmethod
    def get_urls(cls, menu_class) -> list[URLPattern]:
        """Generate URL pattern(s) for this plugin.

        Returns:
            List containing one URLPattern for simple plugins.
            Subclasses may override to return multiple patterns.
        """
        base_name = cls.get_name()
        base_path = cls.get_url_path()
        urls = []
        for subview in cls.subviews:
            urls.append(
                path(
                    f"{subview.get_url_path()}/",
                    subview.as_view(menu=menu_class),
                    name=subview.get_name(),
                )
            )

        base_path = f"{base_path}/" if base_path is not None else ""
        return [
            path(base_path, cls.as_view(menu=menu_class), name=base_name),
            path(base_path, include((urls, base_name), namespace=base_name)),
        ]

    def get_base_object(self) -> Model:
        """Fetch model instance from URL kwargs.

        Returns:
            Model instance based on URL kwargs (typically 'pk' or 'uuid')

        Raises:
            Model.DoesNotExist: If instance not found
        """
        if not self.registered_model:
            msg = f"Plugin {self.__class__.__name__} has no associated model"
            raise ValueError(msg)

        # Try pk first (integer primary key)
        if pk := self.kwargs.get("pk"):
            return self.registered_model.objects.get(pk=pk)

        # Try uuid (UUID field)
        if uuid := self.kwargs.get("uuid"):
            return self.registered_model.objects.get(uuid=uuid)

        msg = "Plugin URL must include 'pk' or 'uuid' kwarg"
        raise ValueError(msg)

    def has_permission(self, request: HttpRequest, obj: Model | None = None) -> bool:
        """Two-tier permission check.

        Checks both model-level and object-level permissions.

        Args:
            request: HTTP request
            obj: Model instance (optional, for object-level checks)

        Returns:
            True if user has permission
        """
        # No permission requirement
        if not self.permission:
            return True

        # Model-level permission check
        if not request.user.has_perm(self.permission):
            return False

        # Object-level permission check (if guardian is available)
        if obj:
            try:
                from guardian.shortcuts import get_objects_for_user

                # Check if user has object-level permission
                queryset = get_objects_for_user(
                    request.user, self.permission, klass=obj.__class__
                )
                return queryset.filter(pk=obj.pk).exists()
            except ImportError:
                # Guardian not available, rely on model-level check
                pass

        return True

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Permission-gated dispatch.

        Checks permissions before allowing access to the view.

        Args:
            request: HTTP request
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            HTTP response

        Raises:
            PermissionDenied: If user lacks required permissions
        """
        if callable(self.check):
            if not self.check(request):
                raise PermissionDenied
        elif not self.check:
            raise PermissionDenied

        # Get object for permission checking
        try:
            obj = self.get_base_object()
        except (ValueError, self.registered_model.DoesNotExist):  # type: ignore[union-attr]
            obj = None

        # Check permissions
        if not self.has_permission(request, obj):
            raise PermissionDenied

        # Store object for use in view methods
        if obj:
            self.object = obj  # type: ignore[attr-defined]

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add plugin-specific context data.

        Adds:
        - object: Model instance
        - tabs: List of Tab objects for this model
        - breadcrumbs: Breadcrumb navigation chain
        - plugin_media: Static assets for this plugin

        Args:
            **kwargs: Additional context

        Returns:
            Context dictionary
        """
        context = super().get_context_data(**kwargs)  # type: ignore[misc]

        # Add object if not already present
        if not context.get("object"):
            # Check if object was set in dispatch() first
            if hasattr(self, "object") and self.object is not None:
                context["object"] = self.object
            else:
                try:
                    context["object"] = self.get_base_object()
                except (ValueError, Exception):
                    context["object"] = None

        # Add breadcrumbs
        context["breadcrumbs"] = self.get_breadcrumbs()

        # Note: The presence of `plugin_menu` in the context is used by the base template to render the local tab navigation against an instance of the registered model.
        context["plugin_menu"] = self.menu
        # Add plugin media
        if hasattr(self, "Media"):
            context["plugin_media"] = Media(self.Media)
        else:
            context["plugin_media"] = None

        return context

    def get_breadcrumbs(self) -> list[dict[str, Any]]:
        """Auto-generate breadcrumb navigation chain.

        Returns:
            List of breadcrumb dicts with 'text' and optionally 'href' keys
        """
        breadcrumbs = []

        # Add model list view breadcrumb
        if self.registered_model:
            model_name = self.registered_model._meta.verbose_name_plural
            # TODO: Reverse model list URL
            breadcrumbs.append({"text": model_name, "href": "/"})

        # Add object breadcrumb
        try:
            obj = self.get_base_object()
            obj_str = str(obj)
            # Truncate long object names
            if len(obj_str) > 50:
                obj_str = obj_str[:47] + "..."
            # TODO: Reverse object detail URL
            breadcrumbs.append({"text": obj_str, "href": "#"})
        except (ValueError, Exception):  # noqa: S110
            pass

        # Add current page breadcrumb
        if self.menu:
            breadcrumbs.append({"text": self.page_title})

        return breadcrumbs

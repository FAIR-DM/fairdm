"""Plugin mixin base class for extending model detail views."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Model
from django.forms.widgets import Media
from django.urls import URLPattern, include, path
from django.views.generic.base import View

from .access import can_open

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest


class Plugin(PermissionRequiredMixin, View):
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

    # The model this mount serves. Bound per mount by as_view(), never assigned onto the class —
    # a plugin registered against two models must serve each independently.
    registered_model: ClassVar[type[Model] | None] = None

    # The plugin that owns this view. For a plugin itself this is None and it owns itself; for an
    # additional view it is the declaring plugin, whose predicate governs the whole group.
    plugin_class: ClassVar[type[Plugin] | None] = None

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

    @cached_property
    def base_object(self) -> Model | None:
        """The core record this plugin hangs from.

        Distinct from ``self.object``, which stays whatever the view class decides it is — the two
        are different things and sharing one attribute name is what broke any view managing its own.
        Named to match ``RelatedObjectMixin`` so a plugin and an ordinary related view read alike.
        """
        try:
            return self.get_base_object()
        except Exception:
            return None

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

    def has_permission(self) -> bool:
        """Whether this request may open this view.

        Overrides ``PermissionRequiredMixin.has_permission``, which supplies the surrounding
        ``dispatch`` and the ``handle_no_permission`` behaviour — an authenticated user gets 403, an
        anonymous one is sent to log in.

        The decision itself is :func:`~fairdm.contrib.plugins.access.can_open`, which the navigation
        entry also calls. That is the whole mechanism behind the guarantee that what a user can see
        and what a user can reach are the same set.
        """
        return can_open(self.__class__, self.request, self.base_object)

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

        # The core record, always. `object` is left to the view class.
        context["base_object"] = self.base_object

        # Kept for templates that predate `base_object`; it resolves to the view's own object when
        # the view has one, and to the core record otherwise.
        if not context.get("object"):
            context["object"] = getattr(self, "object", None) or self.base_object

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
        obj = self.base_object
        if obj is not None:
            obj_str = str(obj)
            # Truncate long object names
            if len(obj_str) > 50:
                obj_str = obj_str[:47] + "..."
            # TODO: Reverse object detail URL
            breadcrumbs.append({"text": obj_str, "href": "#"})

        # Add current page breadcrumb
        if self.menu:
            breadcrumbs.append({"text": self.page_title})

        return breadcrumbs

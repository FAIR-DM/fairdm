"""Plugin mixin base class for extending model detail views."""

from __future__ import annotations

import contextlib
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Model
from django.forms.widgets import Media
from django.urls import URLPattern, path
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
    #: Additional view classes belonging to this plugin. Read only through get_extra_views().
    extra_views: ClassVar[list[type[Plugin]]] = []

    #: Shown as the last entry in the navigation trail. Declared here because get_breadcrumbs()
    #: reads it directly, and a plugin that set none used to raise AttributeError (issue #112).
    page_title: ClassVar[str] = ""
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
    def get_extra_views(cls) -> list[type[Plugin]]:
        """The additional view classes belonging to this plugin.

        The single reader of ``extra_views``. Declaration is a class attribute and resolution is one
        method, which is the pattern this project settled for the model registry and the one Django
        admin uses for inlines.
        """
        return list(cls.extra_views or [])

    @classmethod
    def get_urls(cls, menu_class=None, model=None) -> list[URLPattern]:
        """Flat URL patterns for this plugin and every view it owns.

        One ``path()`` per view, named ``<plugin>`` and ``<plugin>-<child>``. No nested namespace:
        the earlier shape emitted an ``include()`` for every plugin whether or not it had children,
        installing an empty resolver whose namespace equalled the plugin's own pattern name — the
        plugin was simultaneously a route and a container. Django admin, DRF routers and neapolitan
        all flatten instead.

        The model is bound per mount rather than assigned onto the class, so one plugin registered
        against two records serves each independently.
        """
        base_name = cls.get_name()
        base_path = cls.get_url_path()
        prefix = f"{base_path}/" if base_path is not None else ""

        def mount(view_class, owner=None):
            return view_class.as_view(
                menu=menu_class,
                registered_model=model,
                plugin_class=owner,
            )

        patterns = [path(prefix, mount(cls), name=base_name)]
        for extra in cls.get_extra_views():
            segment = extra.get_url_path()
            segment = f"{segment}/" if segment else ""
            patterns.append(
                path(
                    f"{prefix}{segment}",
                    mount(extra, owner=cls),
                    name=f"{base_name}-{extra.get_name()}",
                )
            )
        return patterns

    @cached_property
    def base_object(self) -> Model | None:
        """The core record this plugin hangs from.

        Distinct from ``self.object``, which stays whatever the view class decides it is — the two
        are different things and sharing one attribute name is what broke any view managing its own.
        Named to match ``RelatedObjectMixin`` so a plugin and an ordinary related view read alike.
        """
        from django.http import Http404

        try:
            return self.get_base_object()
        except Http404:
            # A record that does not exist is a 404, not an absent record. Swallowing it here is
            # what turned a missing sample into a 500 further along.
            raise
        except Exception:
            return None

    def get_base_object(self) -> Model:
        """Fetch the core record named by the address.

        The lookup comes from the model's declared addressing rather than a hardcoded ``uuid``, so
        a record identified some other way — the location record is keyed on a coordinate pair and
        has no ``uuid`` field — can be served by the same machinery.

        Raises:
            Http404: if no such record exists
            ValueError: if the mount is missing, which is a wiring mistake rather than a bad request
        """
        from django.shortcuts import get_object_or_404

        from .registration import registry

        if not self.registered_model:
            msg = f"Plugin {self.__class__.__name__} has no associated model"
            raise ValueError(msg)

        lookup = registry.lookup_for(self.registered_model)
        filters = {
            field: self.kwargs[kwarg]
            for kwarg, field in lookup.items()
            if kwarg in self.kwargs
        }
        if not filters:
            # Kept for plugins mounted by a URL configuration that predates declared addressing.
            if pk := self.kwargs.get("pk"):
                filters = {"pk": pk}
            else:
                msg = (
                    f"Plugin {self.__class__.__name__} is mounted without any of the lookup "
                    f"kwargs {sorted(lookup)} its model declares"
                )
                raise ValueError(msg)

        return get_object_or_404(self.registered_model, **filters)

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
        from django.urls import NoReverseMatch
        from django.urls import reverse as django_reverse

        breadcrumbs: list[dict[str, Any]] = []

        if self.registered_model:
            meta = self.registered_model._meta
            entry: dict[str, Any] = {"text": meta.verbose_name_plural}
            # A record type may have no list page; a trail entry that does not navigate is worse
            # than one that is plain text, so the link is added only when it resolves.
            for candidate in (f"{meta.model_name}-list", f"{meta.model_name}s"):
                try:
                    entry["href"] = django_reverse(candidate)
                except NoReverseMatch:
                    continue
                break
            breadcrumbs.append(entry)

        obj = self.base_object
        if obj is not None:
            obj_str = str(obj)
            if len(obj_str) > 50:
                obj_str = obj_str[:47] + "..."
            entry = {"text": obj_str}
            get_absolute_url = getattr(obj, "get_absolute_url", None)
            if callable(get_absolute_url):
                with contextlib.suppress(Exception):
                    entry["href"] = get_absolute_url()
            breadcrumbs.append(entry)

        if self.page_title:
            breadcrumbs.append({"text": self.page_title})

        return breadcrumbs

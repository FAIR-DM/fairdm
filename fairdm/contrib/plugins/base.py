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
    """Mixin that turns a Django class-based view into a page attached to a core record.

    Attributes:
        registered_model: The model this mount serves. Bound per mount by ``as_view``, so
            a plugin registered against two models serves each independently.
        plugin_class: The plugin that owns this view. None for a plugin itself. For an
            additional view, the declaring plugin, whose predicate governs the whole group.
        name: Unique identifier per model. Defaults to the slugified class name.
        url_path: URL path segment. ``""`` uses the name, ``None`` mounts without a base
            path, and any other string is used as given.
        permission: Permission or permissions required to open the page.
        check: Predicate ``(request, obj)`` or bool deciding whether the page opens.
        model: The base model, set by the registry during registration.
        menu: The navigation menu bound per mount by ``as_view``.
        extra_views: Additional view classes belonging to this plugin. Read through
            ``get_extra_views``.
        page_title: Last entry of the breadcrumb trail (#112).
        slug_field: Model field used to find the record.
        slug_url_kwarg: URL keyword argument holding the record's slug.
    """

    registered_model: ClassVar[type[Model] | None] = None

    plugin_class: ClassVar[type[Plugin] | None] = None

    name: ClassVar[str | None] = None
    url_path: ClassVar[str | None] = ""
    permission: ClassVar[str | None] = None
    check: ClassVar[Callable[[HttpRequest, Model | None], bool] | None] = True
    model: ClassVar[type[Model] | None] = None
    menu: ClassVar[dict[str, Any] | None] = None
    extra_views: ClassVar[list[type[Plugin]]] = []

    page_title: ClassVar[str] = ""
    slug_field = "uuid"
    slug_url_kwarg = "uuid"

    @classmethod
    def get_name(cls) -> str:
        """Return the plugin name, the slugified class name unless ``name`` is set.

        Returns:
            The name used for URL naming and identification.
        """
        if cls.name:
            return cls.name
        from .utils import slugify

        return slugify(cls.__name__)

    @classmethod
    def get_url_path(cls) -> str | None:
        """Return the URL path segment.

        Returns:
            The segment, such as ``"analysis"``, or None when ``url_path`` is None
            (no base path).
        """
        if cls.url_path is None:
            return None
        if cls.url_path:
            return cls.url_path
        return cls.get_name()

    @classmethod
    def get_extra_views(cls) -> list[type[Plugin]]:
        """Return the additional view classes belonging to this plugin.

        Returns:
            A new list copied from ``extra_views``.
        """
        return list(cls.extra_views or [])

    @classmethod
    def get_urls(cls, menu_class=None, model=None) -> list[URLPattern]:
        """Build one flat URL pattern for the plugin and one for each view it owns.

        Patterns are named ``<plugin>`` and ``<plugin>-<child>``, with no nested namespace.

        Args:
            menu_class: The menu bound to each mount.
            model: The model bound to each mount, so one plugin registered against two
                records serves each independently.

        Returns:
            The URL patterns.
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
        """The core record this plugin hangs from, or None when it cannot be resolved.

        Distinct from ``self.object``, which the view class manages for itself.
        """
        from django.http import Http404

        try:
            return self.get_base_object()
        except Http404:
            raise
        except Exception:
            return None

    def get_base_object(self) -> Model:
        """Fetch the core record named by the address, using the model's declared addressing.

        Returns:
            The record.

        Raises:
            ValueError: The mount has no model, or none of the model's lookup kwargs are in the URL.
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

        # `all_objects` skips the privacy-first default manager, which would 404 a private record before
        # `can_open` runs. A plugin on restricted records must declare `check` or `permission`.
        manager = getattr(self.registered_model, "all_objects", self.registered_model)
        return get_object_or_404(manager, **filters)

    def get_queryset(self):
        """Read through the served model's ``all_objects`` manager, as ``get_base_object`` does."""
        if getattr(self, "queryset", None) is not None:
            return super().get_queryset()  # type: ignore[misc]
        model = self.registered_model or self.model
        manager = getattr(model, "all_objects", None) if model is not None else None
        if manager is not None:
            return manager.all()
        return super().get_queryset()  # type: ignore[misc]

    def has_permission(self) -> bool:
        """Decide with :func:`~fairdm.contrib.plugins.access.can_open`, as the navigation entry does."""
        return can_open(self.__class__, self.request, self.base_object)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the core record, breadcrumbs, the plugin menu and the plugin's media."""
        context = super().get_context_data(**kwargs)  # type: ignore[misc]

        context["base_object"] = self.base_object

        # Templates that predate `base_object` read `object`.
        if not context.get("object"):
            context["object"] = getattr(self, "object", None) or self.base_object

        context["breadcrumbs"] = self.get_breadcrumbs()

        # The base template renders the local tab navigation when `plugin_menu` is present.
        context["plugin_menu"] = self.menu
        if hasattr(self, "Media"):
            context["plugin_media"] = Media(self.Media)
        else:
            context["plugin_media"] = None

        return context

    def get_breadcrumbs(self) -> list[dict[str, Any]]:
        """Build the breadcrumb trail from the model, the record and the page title.

        Returns:
            Breadcrumb dicts with a ``text`` key and, where a link resolves, an ``href``.
        """
        from django.urls import NoReverseMatch
        from django.urls import reverse as django_reverse

        breadcrumbs: list[dict[str, Any]] = []

        if self.registered_model:
            meta = self.registered_model._meta
            entry: dict[str, Any] = {"text": meta.verbose_name_plural}
            # A record type may have no list page, so the link is added only when it resolves.
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

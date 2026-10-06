"""A plugin drawn as a card inside a record's overview."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from django.forms.widgets import Media
from django.template.loader import render_to_string

from .access import can_open
from .base import Plugin

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest
    from django.urls import URLPattern
    from django.utils.safestring import SafeString


class Card(Plugin):
    """A plugin that is drawn inside a record's overview and has no page of its own.

    Register it with ``place="card"``. The overview asks it to draw itself with the record being
    viewed and the current request, so a card never runs the permission handling of a page. Its
    ``check`` and ``permission`` decide whether it is drawn, and a card that owns further views
    is served at ``<name>/<segment>/`` to the same viewers only.

    Attributes:
        template_name: The template the card draws. A card that overrides
            :meth:`render_card` needs none.
    """

    template_name: ClassVar[str | None] = None

    @classmethod
    def get_urls(
        cls, menu_class=None, model=None, name=None, url_path=""
    ) -> list[URLPattern]:
        """Build the patterns of the card's further views.

        Args:
            menu_class: The menu bound to each mount.
            model: The model bound to each mount.
            name: The name to serve under, the card's own when not given.
            url_path: The segment to serve at, the card's own when empty.

        Returns:
            One pattern per further view, none at the card's own name.
        """
        patterns = super().get_urls(
            menu_class=menu_class, model=model, name=name, url_path=url_path
        )
        # The first pattern is the plugin's own address, which a card does not have.
        return patterns[1:]

    @classmethod
    def admits(cls, request: HttpRequest, record: Model, model: type[Model]) -> bool:
        """Decide whether this card would be drawn for this viewer on this record.

        The record type's overview must open for the viewer, and then the card's own predicate
        and permission must pass. A further view of the card is served only when this holds.

        Args:
            request: The current request.
            record: The record the card belongs to.
            model: The record type the card is mounted on.

        Returns:
            True when the card would be drawn.
        """
        from .places import OverviewPlaces
        from .registration import registry

        overview = next(
            (
                mount
                for mount in registry.resolve(model)
                if issubclass(mount.plugin_class, OverviewPlaces)
            ),
            None,
        )
        if overview is None or not can_open(overview.plugin_class, request, record):
            return False
        return can_open(cls, request, record)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Give the template the record as ``record`` and ``base_object``, and the request.

        Args:
            **kwargs: Extra context.

        Returns:
            The context the template is drawn with.
        """
        return {
            "record": self.base_object,
            "base_object": self.base_object,
            "request": self.request,
            **kwargs,
        }

    def get_media(self) -> Media:
        """Collect the stylesheets and scripts the card declares in its ``Media`` class.

        Returns:
            The card's media, empty when it declares none.
        """
        return Media(self.Media) if hasattr(self, "Media") else Media()

    def render_card(self, request: HttpRequest, record: Model) -> SafeString:
        """Draw the card for one record.

        Args:
            request: The current request.
            record: The record being viewed.

        Returns:
            The card's HTML.
        """
        self.request = request
        self.base_object = record
        return render_to_string(
            self.template_name, self.get_context_data(), request=request
        )

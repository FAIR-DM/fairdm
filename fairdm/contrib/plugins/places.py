"""The places a registration can put a plugin on a record's page, and the overview that draws them."""

from __future__ import annotations

import logging
from typing import Any

from django.db import models
from django.forms.widgets import Media
from django.utils.translation import gettext_lazy as _

from .access import can_open
from .utils import reverse

logger = logging.getLogger(__name__)


class Place(models.TextChoices):
    """Where a registration puts its plugin on a record's page.

    A registration that names no place gets ``NAVIGATION``.

    Attributes:
        NAVIGATION: An entry in the record's local navigation.
        ACTION: An entry in the dropdown of page actions on the record's overview.
        CARD: A card drawn inside the record's overview.
    """

    NAVIGATION = "navigation", _("Navigation")
    ACTION = "action", _("Page action")
    CARD = "card", _("Overview card")


class Column(models.TextChoices):
    """Which column of the overview a card is drawn in.

    A card that names no column gets ``SIDE``.

    Attributes:
        SIDE: The narrow column of facts beside the content.
        WIDE: The wide column of content.
    """

    SIDE = "side", _("Side column")
    WIDE = "wide", _("Wide column")


class OverviewPlaces:
    """Mixin for the overview plugin of a record type, which draws the places a plugin can ask for.

    Mix it in ahead of ``Plugin`` so the context it adds reaches the overview template. A record
    type offers page actions and cards when one of its registered plugins is built on this class.
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the page actions the visitor may open and the cards drawn for them.

        The assets of every card that was drawn are added to the overview's own.
        """
        context = super().get_context_data(**kwargs)
        context["page_actions"] = self.get_page_actions()
        cards, media = self.get_overview_cards()
        context["overview_cards"] = cards
        if media is not None:
            own = context.get("plugin_media")
            context["plugin_media"] = media if own is None else own + media
        return context

    def get_page_actions(self) -> list[dict[str, Any]]:
        """List the page actions of this record the current visitor may open.

        An action whose access decision raises is left out and the failure is logged, so one
        broken predicate never fails the page.

        Returns:
            One dict per action, in order, with its ``label``, ``icon`` and ``url``.
        """
        from .registration import registry

        record = self.base_object
        actions = []
        for mount in registry.get_page_actions(self.registered_model):
            try:
                allowed = can_open(mount.plugin_class, self.request, record)
            except Exception:
                logger.exception(
                    "Access check failed for page action %s; hiding it",
                    mount.plugin_class.__name__,
                )
                continue
            if allowed:
                actions.append(
                    {
                        "label": mount.label,
                        "icon": mount.icon,
                        "url": reverse(record, mount.name),
                    }
                )
        return actions

    def get_overview_cards(self) -> tuple[dict[str, list[str]], Media | None]:
        """Draw the cards of this record that the current visitor may see.

        A card whose access decision is false is skipped. A card whose decision or drawing raises
        is skipped and the failure is logged, so one broken card never fails the page.

        Returns:
            The drawn HTML of each column, keyed by ``"wide"`` and ``"side"``, in order, and the
            combined assets of the cards that were drawn, or None when none were.
        """
        from .registration import registry

        record = self.base_object
        cards: dict[str, list[str]] = {Column.WIDE.value: [], Column.SIDE.value: []}
        media = None
        for mount in registry.get_cards(self.registered_model):
            name = mount.plugin_class.__name__
            try:
                if not can_open(mount.plugin_class, self.request, record):
                    continue
            except Exception:
                logger.exception("Access check failed for card %s; hiding it", name)
                continue
            try:
                card = mount.plugin_class(registered_model=self.registered_model)
                html = card.render_card(self.request, record)
                card_media = card.get_media()
            except Exception:
                logger.exception(
                    "Card %s failed to draw for %s %s; leaving it out",
                    name,
                    record._meta.label,
                    record.pk,
                )
                continue
            cards[mount.column.value].append(html)
            media = card_media if media is None else media + card_media
        return cards, media

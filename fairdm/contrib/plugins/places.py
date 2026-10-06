"""The places a registration can put a plugin on a record's page, and the overview that draws them."""

from __future__ import annotations

import logging
from typing import Any

from django.db import models
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
    """

    NAVIGATION = "navigation", _("Navigation")
    ACTION = "action", _("Page action")


class OverviewPlaces:
    """Mixin for the overview plugin of a record type, which draws the places a plugin can ask for.

    Mix it in ahead of ``Plugin`` so the context it adds reaches the overview template. A record
    type offers page actions when one of its registered plugins is built on this class.
    """

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the page actions the visitor may open."""
        context = super().get_context_data(**kwargs)
        context["page_actions"] = self.get_page_actions()
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

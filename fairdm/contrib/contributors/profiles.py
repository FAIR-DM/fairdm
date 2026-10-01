"""Pure helpers behind the person and organization overview pages.

Nothing here touches the database or a request, so each function can be tested with plain values.
"""

from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any
from urllib.parse import urlparse

from django.conf.locale import LANG_INFO
from django.utils.translation import gettext


def link_host(url: str) -> str:
    """Name a link by the site it points at.

    Args:
        url: The link.

    Returns:
        The host without a leading ``www.``, or the link as written when it has no host.
    """
    host = urlparse(url).netloc.removeprefix("www.")
    return host or url


def language_names(codes: Iterable[str] | None) -> list[str]:
    """Name each ISO 639-1 code in the active language.

    Args:
        codes: The language codes.

    Returns:
        One name per code, in the order given. A code Django does not know is kept as written.
    """
    names = []
    for code in codes or []:
        info = LANG_INFO.get(code)
        names.append(gettext(info["name"]) if info and "name" in info else code)
    return names


def ranked_shares(counts: Mapping[str, int]) -> list[dict[str, Any]]:
    """Rank counts, largest first, each with its share of the largest.

    Args:
        counts: A count for each label.

    Returns:
        One ``{"label", "count", "percent"}`` entry per label, where the largest count is 100.
    """
    if not counts:
        return []
    largest = max(counts.values())
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [
        {"label": label, "count": count, "percent": round(100 * count / largest)}
        for label, count in ranked
    ]


def fill_slots(
    items: Sequence[Any], slots: int, reserve: bool = False
) -> dict[str, Any]:
    """Fit a list into a fixed number of slots.

    Args:
        items: Everything there is to show, in order.
        slots: How many slots there are.
        reserve: Keep the last slot for a "+n more" entry when the items do not all fit, so the
            list never takes more than ``slots`` places.

    Returns:
        ``shown`` (the items that fit), ``more`` (how many do not) and ``total``.
    """
    shown = items
    if len(items) > slots:
        shown = items[: slots - 1] if reserve else items[:slots]
    return {"shown": list(shown), "more": len(items) - len(shown), "total": len(items)}


def active_then_recent(
    items: Iterable[Any],
    modified: Callable[[Any], Any],
    active: Callable[[Any], bool] | None = None,
) -> list[Any]:
    """Order items with the active ones first, each group most recently updated first.

    Args:
        items: The items to order.
        modified: Returns when an item was last updated.
        active: Says whether an item is active, or None when the items have no such state.

    Returns:
        The items in order.
    """
    ordered = sorted(items, key=modified, reverse=True)
    if active is not None:
        ordered.sort(key=lambda item: not active(item))
    return ordered


def checklist(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Sum up a checklist.

    Args:
        items: The checklist's items, each with a ``done`` flag.

    Returns:
        The ``items``, how many are ``done``, the ``total``, and whether all of them are
        (``ready``).
    """
    done = sum(1 for item in items if item["done"])
    return {
        "items": list(items),
        "done": done,
        "total": len(items),
        "ready": done == len(items),
    }

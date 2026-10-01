"""Tests for the pure helpers behind the contributor overview pages."""

from datetime import datetime
from types import SimpleNamespace

from django.utils import translation

from fairdm.contrib.contributors.profiles import (
    active_then_recent,
    checklist,
    fill_slots,
    language_names,
    link_host,
    ranked_shares,
)


class TestLinkHost:
    def test_a_link_is_named_by_its_host(self):
        assert link_host("https://github.com/someone") == "github.com"

    def test_a_leading_www_is_dropped(self):
        assert link_host("https://www.example.org/page") == "example.org"

    def test_a_link_with_no_host_is_kept_as_written(self):
        assert link_host("not a link") == "not a link"


class TestLanguageNames:
    def test_a_known_code_is_named_in_the_active_language(self):
        with translation.override("en"):
            assert language_names(["de"]) == ["German"]

    def test_the_name_follows_the_active_language(self):
        with translation.override("de"):
            assert language_names(["de"]) == ["Deutsch"]

    def test_an_unknown_code_is_kept_as_written(self):
        assert language_names(["zz-unknown"]) == ["zz-unknown"]

    def test_the_order_given_is_kept(self):
        with translation.override("en"):
            assert language_names(["fr", "de"]) == ["French", "German"]

    def test_nothing_gives_an_empty_list(self):
        assert language_names(None) == []
        assert language_names([]) == []


class TestRankedShares:
    def test_the_largest_count_comes_first_and_is_one_hundred_percent(self):
        ranked = ranked_shares({"Author": 2, "Editor": 4})

        assert [entry["label"] for entry in ranked] == ["Editor", "Author"]
        assert [entry["percent"] for entry in ranked] == [100, 50]

    def test_each_entry_carries_its_count(self):
        ranked = ranked_shares({"Author": 3})

        assert ranked == [{"label": "Author", "count": 3, "percent": 100}]

    def test_nothing_gives_an_empty_list(self):
        assert ranked_shares({}) == []


class TestFillSlots:
    def test_a_list_that_fits_is_shown_whole(self):
        assert fill_slots([1, 2, 3], 5) == {"shown": [1, 2, 3], "more": 0, "total": 3}

    def test_a_list_that_overflows_is_cut_and_the_rest_counted(self):
        assert fill_slots([1, 2, 3, 4, 5, 6], 4) == {
            "shown": [1, 2, 3, 4],
            "more": 2,
            "total": 6,
        }

    def test_a_reserved_slot_is_kept_for_the_count_when_the_list_overflows(self):
        result = fill_slots(list(range(12)), 10, reserve=True)

        assert result["shown"] == list(range(9))
        assert result["more"] == 3
        assert result["total"] == 12

    def test_a_reserved_slot_is_not_taken_when_everything_fits(self):
        result = fill_slots(list(range(10)), 10, reserve=True)

        assert len(result["shown"]) == 10
        assert result["more"] == 0

    def test_nothing_gives_nothing_shown(self):
        assert fill_slots([], 5) == {"shown": [], "more": 0, "total": 0}


class TestActiveThenRecent:
    @staticmethod
    def _items():
        return [
            SimpleNamespace(name="old-active", modified=datetime(2020, 1, 1), on=True),
            SimpleNamespace(name="new-idle", modified=datetime(2026, 1, 1), on=False),
            SimpleNamespace(name="new-active", modified=datetime(2025, 1, 1), on=True),
            SimpleNamespace(name="old-idle", modified=datetime(2021, 1, 1), on=False),
        ]

    def test_active_items_come_first_and_each_group_is_newest_first(self):
        ordered = active_then_recent(
            self._items(), lambda item: item.modified, lambda item: item.on
        )

        assert [item.name for item in ordered] == [
            "new-active",
            "old-active",
            "new-idle",
            "old-idle",
        ]

    def test_without_an_active_state_everything_is_newest_first(self):
        ordered = active_then_recent(self._items(), lambda item: item.modified)

        assert [item.name for item in ordered] == [
            "new-idle",
            "new-active",
            "old-idle",
            "old-active",
        ]


class TestChecklist:
    def test_the_items_are_kept_in_order_with_the_done_count_and_the_total(self):
        items = [{"done": True}, {"done": False}, {"done": True}, {"done": False}]

        summary = checklist(items)

        assert summary["items"] == items
        assert summary["done"] == 2
        assert summary["total"] == 4
        assert summary["ready"] is False

    def test_a_checklist_with_everything_in_place_is_ready(self):
        summary = checklist([{"done": True}, {"done": True}])

        assert (summary["done"], summary["total"]) == (2, 2)
        assert summary["ready"] is True

    def test_one_missing_item_means_it_is_not_ready(self):
        assert checklist([{"done": True}, {"done": False}])["ready"] is False

    def test_nothing_in_place_counts_zero(self):
        summary = checklist([{"done": False}, {"done": False}])

        assert summary["done"] == 0
        assert summary["ready"] is False

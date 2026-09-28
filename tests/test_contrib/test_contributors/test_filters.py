"""Tests for `fairdm/contrib/contributors/filters.py`."""

from fairdm.contrib.contributors.filters import PersonFilter


class TestPersonFilter:
    def test_is_staff_is_offered_as_a_filter(self):
        assert "is_staff" in PersonFilter.base_filters

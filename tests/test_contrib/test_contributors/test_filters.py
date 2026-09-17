"""Tests for `fairdm/contrib/contributors/filters.py`."""

from fairdm.contrib.contributors.filters import PersonFilter


class TestPersonFilterIsStaffLabel:
    """T007: `is_staff` has never meant "Portal Administrators" — that name now
    belongs to a declared role (`fairdm/portal_roles.py`) with none of the
    field's group-name history."""

    def test_is_staff_label_does_not_claim_to_filter_portal_administrators(self):
        assert PersonFilter.base_filters["is_staff"].label != "Portal Administrators"

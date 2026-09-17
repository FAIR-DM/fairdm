"""Tests for contributor choice enumerations (User Story 4).

Covers:
- OrganizationType vocabulary: the nine ROR schema 2.1 organisation types
  (FS-009 US4 T047)
"""

from fairdm.contrib.contributors.choices import OrganizationType


class TestOrganizationTypeVocabulary:
    """Verify the ROR organisation-type vocabulary (FR-016, SC-006).

    Every member is asserted by name, rather than by iterating whatever the
    choices class happens to hold.
    """

    def test_organization_type_has_every_ror_schema_2_1_value(self):
        """Each of ROR schema 2.1's nine organisation types is present."""
        assert OrganizationType.EDUCATION == "education"
        assert OrganizationType.FUNDER == "funder"
        assert OrganizationType.HEALTHCARE == "healthcare"
        assert OrganizationType.COMPANY == "company"
        assert OrganizationType.ARCHIVE == "archive"
        assert OrganizationType.NONPROFIT == "nonprofit"
        assert OrganizationType.GOVERNMENT == "government"
        assert OrganizationType.FACILITY == "facility"
        assert OrganizationType.OTHER == "other"

    def test_organization_type_has_no_members_outside_the_ror_set(self):
        """The vocabulary holds exactly the nine ROR values, no more."""
        assert len(OrganizationType.values) == 9


class TestDefaultGroupsRemoved:
    """FR-036, FR-039: the three ungoverned group names are replaced by the four
    declared roles in `fairdm/portal_roles.py`, so this choice enumeration is gone."""

    def test_default_groups_is_gone(self):
        import fairdm.contrib.contributors.choices as choices

        assert not hasattr(choices, "DefaultGroups")

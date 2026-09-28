"""Tests for the contributor choice enumerations."""

from fairdm.contrib.contributors.choices import OrganizationType


class TestOrganizationTypeVocabulary:
    def test_organization_type_has_every_ror_schema_2_1_value(self):
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
        assert len(OrganizationType.values) == 9


class TestDefaultGroupsRemoved:
    def test_default_groups_is_gone(self):
        import fairdm.contrib.contributors.choices as choices

        assert not hasattr(choices, "DefaultGroups")

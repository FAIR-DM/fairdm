"""Tests for the four roles FairDM ships and installs into every portal.

See CONTEXT.md for how a *portal role* differs from a *contribution role* and
what a *rights-carrying role* is.
"""

from fairdm.portal_roles import PortalRoles

#: The Data Curator's declared rights: view/add/change/delete over Project,
#: Dataset, Sample and Measurement and their attached description, date and
#: contribution records, plus the two permissions the import and publish
#: plugin checks read directly (research R1, R9).
DATA_CURATOR_PERMISSIONS = {
    # Project
    "project.view_project",
    "project.add_project",
    "project.change_project",
    "project.delete_project",
    "project.view_projectdescription",
    "project.add_projectdescription",
    "project.change_projectdescription",
    "project.delete_projectdescription",
    "project.view_projectdate",
    "project.add_projectdate",
    "project.change_projectdate",
    "project.delete_projectdate",
    # Dataset
    "dataset.view_dataset",
    "dataset.add_dataset",
    "dataset.change_dataset",
    "dataset.delete_dataset",
    "dataset.view_datasetdescription",
    "dataset.add_datasetdescription",
    "dataset.change_datasetdescription",
    "dataset.delete_datasetdescription",
    "dataset.view_datasetdate",
    "dataset.add_datasetdate",
    "dataset.change_datasetdate",
    "dataset.delete_datasetdate",
    "dataset.import_data",
    "dataset.can_publish",
    # Sample
    "sample.view_sample",
    "sample.add_sample",
    "sample.change_sample",
    "sample.delete_sample",
    "sample.view_sampledescription",
    "sample.add_sampledescription",
    "sample.change_sampledescription",
    "sample.delete_sampledescription",
    "sample.view_sampledate",
    "sample.add_sampledate",
    "sample.change_sampledate",
    "sample.delete_sampledate",
    # Measurement
    "measurement.view_measurement",
    "measurement.add_measurement",
    "measurement.change_measurement",
    "measurement.delete_measurement",
    "measurement.view_measurementdescription",
    "measurement.add_measurementdescription",
    "measurement.change_measurementdescription",
    "measurement.delete_measurementdescription",
    "measurement.view_measurementdate",
    "measurement.add_measurementdate",
    "measurement.change_measurementdate",
    "measurement.delete_measurementdate",
    # Contribution
    "contributors.view_contribution",
    "contributors.add_contribution",
    "contributors.change_contribution",
    "contributors.delete_contribution",
}

COMMUNITY_MANAGER_PERMISSIONS = {
    "contributors.view_person",
    "contributors.change_person",
    "contributors.view_organization",
    "contributors.change_organization",
    "contributors.view_affiliation",
    "contributors.change_affiliation",
    "contributors.view_contribution",
    "contributors.change_contribution",
}


class TestDeclarations:
    """FR-001 to FR-005: exactly four roles, named and scoped as the spec requires."""

    def test_exactly_four_roles_with_the_shipped_names_in_order(self):
        assert PortalRoles.shipped_names() == [
            "Portal Administrator",
            "Data Curator",
            "Community Manager",
            "Developer",
        ]

    def test_portal_administrator_permissions_match_exactly(self):
        assert set(PortalRoles.PORTAL_ADMINISTRATOR.permissions) == {
            "auth.view_group",
            "contributors.view_person",
            "contributors.change_person",
            "identity.change_identity",
        }

    def test_portal_administrator_cannot_edit_a_group(self):
        """D15: the role that assigns roles must not be able to rewrite what any role may do."""
        assert not {
            "auth.add_group",
            "auth.change_group",
            "auth.delete_group",
        } & set(PortalRoles.PORTAL_ADMINISTRATOR.permissions)

    def test_data_curator_permissions_match_exactly(self):
        assert set(PortalRoles.DATA_CURATOR.permissions) == DATA_CURATOR_PERMISSIONS

    def test_community_manager_permissions_match_exactly(self):
        assert (
            set(PortalRoles.COMMUNITY_MANAGER.permissions)
            == COMMUNITY_MANAGER_PERMISSIONS
        )

    def test_community_manager_cannot_delete_a_person(self):
        """FR-004: the role must not hold the right to delete a person record."""
        assert (
            "contributors.delete_person"
            not in PortalRoles.COMMUNITY_MANAGER.permissions
        )

    def test_developer_holds_no_permissions(self):
        assert PortalRoles.DEVELOPER.permissions == ()

    def test_every_permission_is_an_explicit_app_label_codename(self):
        for role in PortalRoles.ROLES:
            for permission in role.permissions:
                assert permission.count(".") == 1, (
                    f"{role.name}'s {permission!r} is not an app_label.codename string"
                )

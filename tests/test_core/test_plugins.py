"""Tests for the plugin base classes the core record pages share."""

import pytest

from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.factories import (
    DatasetFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleIdentifierFactory,
)


def _plugin_for(record):
    plugin = RecordOverviewPlugin()
    plugin.base_object = record
    return plugin


@pytest.mark.django_db
class TestRecordOverviewPluginIdentifiers:
    def test_a_doi_links_to_doi_org(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(related=project, type="DOI", value="10.1234/abc")

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["type"] == "DOI"
        assert identifier["value"] == "10.1234/abc"
        assert identifier["link"] == "https://doi.org/10.1234/abc"

    def test_an_igsn_links_to_doi_org(self):
        from demo.models import RockSample

        sample = RockSample.objects.create(
            name="Core", dataset=DatasetFactory(), rock_type="igneous"
        )
        SampleIdentifierFactory(related=sample, type="IGSN", value="10.60516/AU1101")

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] == "https://doi.org/10.60516/AU1101"

    def test_an_identifier_of_another_type_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="GRANT-2024-001"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_grant_number_that_looks_like_a_doi_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project, type="GRANT_NUMBER", value="10.13039/501100001659"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_record_with_no_identifiers_gives_an_empty_list(self):
        assert _plugin_for(ProjectFactory()).get_identifiers() == []

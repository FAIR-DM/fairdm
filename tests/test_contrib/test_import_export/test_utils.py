"""Tests for the dataset's DataCite metadata built by ``build_metadata``."""

import xml.etree.ElementTree as ET

import pytest
from controlled_vocabularies.models import Record
from django.contrib.gis.geos import Point
from django.test import RequestFactory

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.import_export.utils import build_metadata
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES
from fairdm.factories import DatasetFactory, OrganizationFactory, PersonFactory
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db

NS = {"d": "http://datacite.org/schema/kernel-4"}


def metadata(dataset):
    return ET.fromstring(
        build_metadata(dataset, RequestFactory().get("/")).encode("utf-8")
    )


def at(longitude, latitude):
    return Point(longitude, latitude, srid=4326)


def box(root):
    found = root.find("d:geoLocations/d:geoLocation/d:geoLocationBox", NS)
    if found is None:
        return None
    return {
        side: float(found.find(f"d:{side}BoundLongitude", NS).text)
        for side in ("west", "east")
    } | {
        side: float(found.find(f"d:{side}BoundLatitude", NS).text)
        for side in ("south", "north")
    }


@pytest.fixture
def dataset():
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


class TestBuildMetadata:
    """A dataset's metadata renders, credits its contributors and describes it."""

    def test_a_described_and_credited_dataset_renders(self, dataset):
        person = PersonFactory()
        organization = OrganizationFactory()
        Contribution.add_to(
            person,
            dataset,
            roles=[f"{CONTRIBUTOR_ROLES}/creator", f"{CONTRIBUTOR_ROLES}/data-curator"],
        )
        Contribution.add_to(
            organization, dataset, roles=[f"{CONTRIBUTOR_ROLES}/creator"]
        )
        dataset.keywords.add(Record.objects.first())

        root = metadata(dataset)

        assert root.find("d:titles/d:title", NS).text == dataset.title
        creators = root.findall("d:creators/d:creator/d:creatorName", NS)
        assert {c.text for c in creators} == {person.name, organization.name}
        curators = root.findall("d:contributors/d:contributor", NS)
        assert [c.get("contributorType") for c in curators] == ["DataCurator"]
        assert root.find("d:subjects/d:subject", NS) is not None

    def test_a_dataset_with_nothing_but_a_title_renders(self, dataset):
        root = metadata(dataset)

        assert root.find("d:titles/d:title", NS).text == dataset.title


class TestBuildMetadataGeoLocation:
    """FS-030 US7 (#511): the geoLocationBox holds the dataset's public locations."""

    def test_the_box_holds_every_location_in_the_dataset(self, dataset):
        sample = RockSampleFactory(dataset=dataset, location=at(10.0, 10.0))
        RockSampleFactory(dataset=dataset, location=at(-5.0, 20.0))
        ExampleMeasurementFactory(
            sample=sample, dataset=dataset, location=at(40.0, -30.0)
        )

        assert box(metadata(dataset)) == {
            "west": -5.0,
            "east": 40.0,
            "south": -30.0,
            "north": 20.0,
        }

    def test_a_box_across_the_180th_meridian_has_west_east_of_east(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(176.0, -1.0))
        RockSampleFactory(dataset=dataset, location=at(-176.0, 1.0))

        found = box(metadata(dataset))

        assert found == {"west": 176.0, "east": -176.0, "south": -1.0, "north": 1.0}

    def test_a_dataset_with_no_locations_carries_no_geolocations(self, dataset):
        RockSampleFactory(dataset=dataset)

        assert metadata(dataset).find("d:geoLocations", NS) is None

    def test_a_location_the_public_may_not_see_is_not_counted(self, dataset):
        RockSampleFactory(dataset=dataset, location=at(10.0, 10.0))
        hidden = DatasetFactory(visibility=Visibility.PRIVATE, published=False)
        hidden_sample = RockSampleFactory(dataset=hidden, location=at(50.0, 50.0))
        ExampleMeasurementFactory(sample=hidden_sample, dataset=dataset)

        assert box(metadata(dataset)) == {
            "west": 10.0,
            "east": 10.0,
            "south": 10.0,
            "north": 10.0,
        }

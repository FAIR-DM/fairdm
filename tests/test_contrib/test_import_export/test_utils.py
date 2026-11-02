"""Tests for the dataset's DataCite metadata built by ``build_metadata``."""

import pytest
from controlled_vocabularies.models import Record
from defusedxml.ElementTree import fromstring
from django.contrib.gis.geos import Point
from django.test import RequestFactory
from licensing.models import License

from demo.factories import ExampleMeasurementFactory, RockSampleFactory
from fairdm.contrib.contributors.models import Contribution
from fairdm.contrib.import_export.utils import build_metadata
from fairdm.core.dataset.models import DatasetDate
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, DATE_TYPES
from fairdm.factories import DatasetFactory, OrganizationFactory, PersonFactory
from fairdm.utils.choices import Visibility

pytestmark = pytest.mark.django_db

NS = {"d": "http://datacite.org/schema/kernel-4"}


def metadata(dataset):
    return fromstring(
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


class TestBuildMetadataNameType:
    """A creator's name type is one of the two values DataCite accepts."""

    @pytest.mark.parametrize(
        ("factory", "name_type"),
        [(PersonFactory, "Personal"), (OrganizationFactory, "Organizational")],
    )
    def test_the_name_type_follows_the_kind_of_contributor(
        self, dataset, factory, name_type
    ):
        Contribution.add_to(factory(), dataset, roles=[f"{CONTRIBUTOR_ROLES}/creator"])

        creator = metadata(dataset).find("d:creators/d:creator/d:creatorName", NS)

        assert creator.get("nameType") == name_type


class TestBuildMetadataRights:
    """The rights entry points at the licence and names it by SPDX where it can."""

    def licensed(self, dataset, name, url):
        dataset.license = License.objects.create(name=name, canonical_url=url)
        return metadata(dataset).find("d:rightsList/d:rights", NS)

    @pytest.mark.parametrize(
        ("url", "identifier"),
        [
            ("https://creativecommons.org/licenses/by-nc-sa/4.0/", "CC-BY-NC-SA-4.0"),
            ("https://creativecommons.org/publicdomain/zero/1.0/", "CC0-1.0"),
        ],
    )
    def test_a_licence_spdx_lists_carries_its_identifier(
        self, dataset, url, identifier
    ):
        License.objects.filter(canonical_url=url).delete()

        rights = self.licensed(dataset, "A licence", url)

        assert rights.get("rightsURI") == url
        assert rights.get("rightsIdentifierScheme") == "SPDX"
        assert rights.get("rightsIdentifier") == identifier
        assert rights.get("schemeURI") == "https://spdx.org/licenses/"
        assert rights.text == "A licence"

    def test_a_licence_of_a_portal_s_own_names_no_scheme(self, dataset):
        url = "https://example.org/our-licence/"

        rights = self.licensed(dataset, "Our licence", url)

        assert rights.get("rightsURI") == url
        assert rights.get("rightsIdentifierScheme") is None
        assert rights.get("rightsIdentifier") is None
        assert rights.get("schemeURI") is None


class TestBuildMetadataDates:
    """Each dataset date is written with a type from DataCite's own list."""

    def dates(self, dataset):
        return [
            (date.get("dateType"), date.text)
            for date in metadata(dataset).findall("d:dates/d:date", NS)
        ]

    def add(self, dataset, kind, value):
        return DatasetDate.objects.create(
            related=dataset, type_id=f"{DATE_TYPES}/{kind}", value=value
        )

    @pytest.mark.parametrize(
        ("kind", "date_type"),
        [
            ("available", "Available"),
            ("submitted", "Submitted"),
            ("published", "Issued"),
            ("withdrawn", "Withdrawn"),
        ],
    )
    def test_a_date_is_written_as_datacite_s_type(self, dataset, kind, date_type):
        dataset.dates.all().delete()
        self.add(dataset, kind, "2024-03-02")

        assert self.dates(dataset) == [(date_type, "2024-03-02")]

    @pytest.mark.parametrize(
        ("start", "end", "value"),
        [
            ("2020-05", "2021", "2020-05/2021"),
            ("2020-05", None, "2020-05/"),
            (None, "2021", "/2021"),
        ],
    )
    def test_the_collection_dates_make_one_collected_range(
        self, dataset, start, end, value
    ):
        dataset.dates.all().delete()
        if start:
            self.add(dataset, "collection-start", start)
        if end:
            self.add(dataset, "collection-end", end)

        assert self.dates(dataset) == [("Collected", value)]

    def test_a_type_datacite_has_no_match_for_is_written_as_other(self, dataset):
        dataset.dates.all().delete()
        date = self.add(dataset, "available", "2024")
        DatasetDate.objects.filter(pk=date.pk).update(type_id=f"{DATE_TYPES}/archival")

        assert self.dates(dataset) == [("Other", "2024")]

    def test_a_dataset_with_no_dates_has_no_dates_element(self, dataset):
        dataset.dates.all().delete()

        assert metadata(dataset).find("d:dates", NS) is None


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

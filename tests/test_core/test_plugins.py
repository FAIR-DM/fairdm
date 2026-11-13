"""Tests for the plugin base classes the core record pages share."""

import uuid
from types import SimpleNamespace

import pytest
import rispy
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.contrib.sites.models import Site
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from pybtex.database import parse_string

from demo.factories import RockSampleFactory, XRFMeasurementFactory
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Organization, Person
from fairdm.contrib.contributors.services.crediting import Crediting
from fairdm.contrib.plugins import Plugin
from fairdm.core.citation import FORMATS
from fairdm.core.plugins import RecordOverviewPlugin
from fairdm.core.vocabularies import CONTRIBUTOR_ROLES, IDENTIFIER_TYPES
from fairdm.factories import (
    AffiliationFactory,
    ContributionFactory,
    DatasetFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
    ProjectIdentifierFactory,
    SampleIdentifierFactory,
    UserFactory,
)
from fairdm.utils.choices import Visibility
from fairdm.utils.location.coverage import Coverage


def _plugin_for(record):
    plugin = RecordOverviewPlugin()
    plugin.base_object = record
    return plugin


@pytest.mark.django_db
class TestRecordOverviewPluginIdentifiers:
    def test_a_doi_links_to_doi_org(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project, type_id=f"{IDENTIFIER_TYPES}/doi", value="10.1234/abc"
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["type"].uri == f"{IDENTIFIER_TYPES}/doi"
        assert identifier["value"] == "10.1234/abc"
        assert identifier["link"] == "https://doi.org/10.1234/abc"

    def test_an_igsn_links_to_doi_org(self):
        from demo.models import RockSample

        sample = RockSample.objects.create(
            name="Core",
            dataset=DatasetFactory(),
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        SampleIdentifierFactory(
            related=sample, type_id=f"{IDENTIFIER_TYPES}/igsn", value="10.60516/AU1101"
        )

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] == "https://doi.org/10.60516/AU1101"

    def test_a_legacy_igsn_handle_that_doi_org_cannot_resolve_is_not_linked(self):
        from demo.models import RockSample

        sample = RockSample.objects.create(
            name="Core",
            dataset=DatasetFactory(),
            rock_type="igneous",
            collection_date="2024-01-15",
        )
        SampleIdentifierFactory(
            related=sample, type_id=f"{IDENTIFIER_TYPES}/igsn", value="AU1101"
        )

        [identifier] = _plugin_for(sample).get_identifiers()

        assert identifier["link"] is None

    def test_an_identifier_of_another_type_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="GRANT-2024-001",
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_grant_number_that_looks_like_a_doi_is_not_linked(self):
        project = ProjectFactory()
        ProjectIdentifierFactory(
            related=project,
            type_id=f"{IDENTIFIER_TYPES}/grant-number",
            value="10.13039/501100001659",
        )

        [identifier] = _plugin_for(project).get_identifiers()

        assert identifier["link"] is None

    def test_a_record_with_no_identifiers_gives_an_empty_list(self):
        assert _plugin_for(ProjectFactory()).get_identifiers() == []


@pytest.mark.django_db
class TestRecordOverviewPluginCredits:
    @pytest.fixture
    def credited(self):
        project = ProjectFactory()
        person = PersonFactory(is_active=True)
        organisation = OrganizationFactory()
        project.add_contributor(
            person,
            with_roles=[
                f"{CONTRIBUTOR_ROLES}/creator",
                f"{CONTRIBUTOR_ROLES}/contact-person",
            ],
        )
        project.add_contributor(organisation, with_roles=[f"{CONTRIBUTOR_ROLES}/other"])
        return project, person, organisation

    def test_each_credit_carries_its_contributor_as_its_own_subtype(self, credited):
        project, person, organisation = credited

        contributions = _plugin_for(project).get_contributions()

        assert {type(c.contributor) for c in contributions} == {Person, Organization}
        assert {c.contributor.pk: c.is_person() for c in contributions} == {
            person.pk: True,
            organisation.pk: False,
        }

    def test_a_credit_names_the_roles_it_holds(self, credited):
        project, person, _ = credited
        plugin = _plugin_for(project)

        credit = next(
            c for c in plugin.get_contributions() if c.contributor.pk == person.pk
        )

        assert plugin.get_role_uris(credit) == {
            f"{CONTRIBUTOR_ROLES}/creator",
            f"{CONTRIBUTOR_ROLES}/contact-person",
        }

    def test_the_contributors_holding_a_role_are_picked_out_of_the_credits(
        self, credited
    ):
        project, person, _ = credited
        plugin = _plugin_for(project)

        entries = plugin.get_credits()

        assert [
            c.pk
            for c in plugin.get_contributors_with_role(
                entries, f"{CONTRIBUTOR_ROLES}/creator"
            )
        ] == [person.pk]
        assert (
            plugin.get_contributors_with_role(entries, f"{CONTRIBUTOR_ROLES}/editor")
            == []
        )


@pytest.mark.django_db
class TestRecordOverviewPluginOrder:
    @pytest.fixture
    def reordered(self):
        """A project credited organization, person, organization, person, then reordered."""
        project = ProjectFactory()
        first_org, second_org = OrganizationFactory(), OrganizationFactory()
        first_person, second_person = PersonFactory(), PersonFactory()
        for contributor in (first_org, first_person, second_org, second_person):
            project.add_contributor(contributor)
        crediting = Crediting(project)
        crediting.move(project.contributors.get(contributor=second_person), "up")
        crediting.move(project.contributors.get(contributor=first_org), "down")
        return project, [second_person, first_person], [second_org, first_org]

    def test_people_come_first_in_order_then_organizations_in_order(self, reordered):
        project, people, organizations = reordered

        contributions = _plugin_for(project).get_contributions()

        assert [c.contributor.pk for c in contributions] == [
            contributor.pk for contributor in (*people, *organizations)
        ]

    def test_the_credits_follow_the_same_order(self, reordered):
        project, people, organizations = reordered

        entries = _plugin_for(project).get_credits()

        assert [e["contributor"].pk for e in entries] == [
            contributor.pk for contributor in (*people, *organizations)
        ]

    def test_the_people_card_follows_the_same_order(self, reordered):
        project, people, organizations = reordered

        named = _plugin_for(project).get_people()["named"]

        assert [row["contributor"].pk for row in named] == [
            contributor.pk for contributor in (*people, *organizations)
        ]


@pytest.mark.django_db
class TestRecordOverviewPluginAffiliation:
    @pytest.fixture
    def person(self):
        person = PersonFactory(is_active=True)
        AffiliationFactory(person=person, is_primary=True)
        return person

    def test_a_person_credited_with_no_organization_is_shown_with_none(self, person):
        project = ProjectFactory()
        Crediting(project).add(person)

        (entry,) = _plugin_for(project).get_credits()

        assert entry["affiliation"] is None

    def test_a_person_credited_from_an_organization_is_shown_with_it(self, person):
        project = ProjectFactory()
        organization = OrganizationFactory()
        Crediting(project).add(person, organization=organization)

        entries = _plugin_for(project).get_credits()

        assert {e["contributor"].pk: e["affiliation"] for e in entries}[
            person.pk
        ] == organization


@pytest.mark.django_db
class TestRecordOverviewPluginPeople:
    @pytest.fixture
    def plugin(self):
        plugin = _plugin_for(ProjectFactory())
        plugin.people_named = 2
        plugin.people_faces = 3
        return plugin

    @staticmethod
    def entries(n, roles=("Creator",)):
        return [
            {
                "contributor": f"contributor {i}",
                "roles": {f"role-{r}": r for r in roles},
                "affiliation": None,
            }
            for i in range(n)
        ]

    def test_the_first_credits_are_named_then_faces_then_a_count(self, plugin):
        people = plugin.get_people(self.entries(7))

        assert [row["contributor"] for row in people["named"]] == [
            "contributor 0",
            "contributor 1",
        ]
        assert people["faces"] == ["contributor 2", "contributor 3", "contributor 4"]
        assert (people["more"], people["total"]) == (2, 7)

    def test_a_named_credit_shows_two_roles_and_counts_the_rest(self, plugin):
        people = plugin.get_people(self.entries(1, roles=("creator", "editor", "x")))

        [row] = people["named"]
        assert row["roles"] == ["Creator", "Editor"]
        assert row["more_roles"] == 1

    def test_with_nobody_credited_there_is_nothing_to_show(self, plugin):
        assert plugin.get_people([]) == {
            "named": [],
            "faces": [],
            "more": 0,
            "total": 0,
        }


class TestRecordOverviewPluginPrimaryIdentifier:
    def test_the_first_identifier_that_resolves_is_the_primary_one(self):
        identifiers = [
            {"type": "grant", "value": "G-1", "link": None},
            {"type": "doi", "value": "10.1/a", "link": "https://doi.org/10.1/a"},
            {"type": "igsn", "value": "10.2/b", "link": "https://doi.org/10.2/b"},
        ]

        primary = RecordOverviewPlugin.get_primary_identifier(identifiers)

        assert primary["value"] == "10.1/a"

    def test_a_record_with_no_resolving_identifier_has_none(self):
        identifiers = [{"type": "grant", "value": "G-1", "link": None}]

        assert RecordOverviewPlugin.get_primary_identifier(identifiers) is None


@pytest.mark.django_db
class TestRecordOverviewPluginTypeMix:
    def test_samples_and_measurements_are_counted_apart_with_the_largest_count(self):
        from demo.factories import RockSampleFactory, XRFMeasurementFactory
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        rocks = RockSampleFactory.create_batch(3, dataset=dataset)
        XRFMeasurementFactory(sample=rocks[0], dataset=dataset)

        mix = _plugin_for(dataset).get_type_mix(
            Sample.objects.filter(dataset=dataset),
            Measurement.objects.filter(dataset=dataset),
        )

        assert [n for _label, n in mix["samples"]] == [3]
        assert [n for _label, n in mix["measurements"]] == [1]
        assert mix["max"] == 3

    def test_with_no_records_there_is_no_mix(self):
        from fairdm.core.measurement.models import Measurement
        from fairdm.core.sample.models import Sample

        assert (
            _plugin_for(DatasetFactory()).get_type_mix(
                Sample.objects.none(), Measurement.objects.none()
            )
            is None
        )


@pytest.mark.django_db
class TestGetSamplePoints:
    def test_each_located_sample_is_one_point_and_an_unlocated_one_is_left_out(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory.create_batch(
            2, dataset=dataset, location=Point(7.9, 48.9, srid=4326)
        )
        RockSampleFactory.create_batch(3, dataset=dataset, location=None)

        points = _plugin_for(dataset).get_sample_points(
            Sample.objects.filter(dataset=dataset)
        )

        assert points["type"] == "FeatureCollection"
        assert len(points["features"]) == 2

    def test_a_feature_carries_the_samples_place_name_type_dataset_and_address(self):
        from django.urls import reverse

        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory(name="Black Forest cores")
        sample = RockSampleFactory(
            name="Basalt", dataset=dataset, location=Point(7.912345678, 48.9, srid=4326)
        )

        [feature] = _plugin_for(dataset).get_sample_points(
            Sample.objects.filter(dataset=dataset)
        )["features"]

        assert feature["type"] == "Feature"
        assert feature["geometry"] == {"type": "Point", "coordinates": [7.91235, 48.9]}
        assert feature["properties"] == {
            "name": "Basalt",
            "type": "Rock Sample",
            "dataset": "Black Forest cores",
            "url": reverse("sample:overview", kwargs={"uuid": sample.uuid}),
        }

    def test_the_features_come_in_the_order_of_the_sample_names(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        for name in ("Cobalt", "Alder", "Basalt"):
            RockSampleFactory(
                name=name, dataset=dataset, location=Point(7.9, 48.9, srid=4326)
            )

        points = _plugin_for(dataset).get_sample_points(
            Sample.objects.filter(dataset=dataset)
        )

        assert [f["properties"]["name"] for f in points["features"]] == [
            "Alder",
            "Basalt",
            "Cobalt",
        ]

    def test_a_type_whose_model_no_longer_exists_has_an_empty_label(self, monkeypatch):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))
        monkeypatch.setattr(ContentType, "model_class", lambda self: None)

        [feature] = _plugin_for(dataset).get_sample_points(
            Sample.objects.filter(dataset=dataset)
        )["features"]

        assert feature["properties"]["type"] == ""

    def test_no_samples_give_an_empty_collection(self):
        from fairdm.core.sample.models import Sample

        points = _plugin_for(DatasetFactory()).get_sample_points(Sample.objects.none())

        assert points == {"type": "FeatureCollection", "features": []}


@pytest.mark.django_db
class TestGetSampleMap:
    POINTS_URL = "/points/"

    def test_no_samples_give_no_map(self):
        from fairdm.core.sample.models import Sample

        assert (
            _plugin_for(DatasetFactory()).get_sample_map(
                Sample.objects.none(), None, self.POINTS_URL
            )
            is None
        )

    def test_located_and_missing_are_counted_from_what_was_seeded(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory.create_batch(
            2, dataset=dataset, location=Point(7.9, 48.9, srid=4326)
        )
        RockSampleFactory.create_batch(3, dataset=dataset, location=None)
        coverage = Coverage(west=7.9, south=48.9, east=7.9, north=48.9)

        result = _plugin_for(dataset).get_sample_map(
            Sample.objects.filter(dataset=dataset), coverage, self.POINTS_URL
        )

        assert result["located"] == 2
        assert result["missing"] == 3
        assert result["points_url"] == self.POINTS_URL

    def test_datasets_are_counted_only_when_asked(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        first, second = DatasetFactory(), DatasetFactory()
        RockSampleFactory(dataset=first, location=Point(7.9, 48.9, srid=4326))
        RockSampleFactory(dataset=first, location=Point(8.1, 49.0, srid=4326))
        RockSampleFactory(dataset=second, location=Point(8.2, 49.1, srid=4326))
        RockSampleFactory(dataset=DatasetFactory(), location=None)
        samples = Sample.objects.all()
        coverage = Coverage(west=7.9, south=48.9, east=8.2, north=49.1)
        plugin = _plugin_for(first)

        asked = plugin.get_sample_map(
            samples, coverage, self.POINTS_URL, count_datasets=True
        )
        not_asked = plugin.get_sample_map(samples, coverage, self.POINTS_URL)

        assert asked["datasets"] == 2
        assert "datasets" not in not_asked

    def test_the_bounds_are_the_coverage_as_west_south_east_north(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))
        coverage = Coverage(west=7.8, south=48.8, east=8.7, north=49.2)

        result = _plugin_for(dataset).get_sample_map(
            Sample.objects.filter(dataset=dataset), coverage, self.POINTS_URL
        )

        assert result["bounds"] == [7.8, 48.8, 8.7, 49.2]
        assert "48.80" in result["area"]
        assert "8.70" in result["area"]

    def test_a_box_across_the_180th_meridian_gets_east_plus_360(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory(dataset=dataset, location=Point(179.0, 10.0, srid=4326))
        RockSampleFactory(dataset=dataset, location=Point(-179.0, 20.0, srid=4326))
        coverage = Coverage(west=179.0, south=10.0, east=-179.0, north=20.0)

        result = _plugin_for(dataset).get_sample_map(
            Sample.objects.filter(dataset=dataset), coverage, self.POINTS_URL
        )

        assert result["bounds"] == [179.0, 10.0, 181.0, 20.0]

    def test_with_no_located_sample_there_are_no_bounds_and_no_area(self):
        from demo.factories import RockSampleFactory
        from fairdm.core.sample.models import Sample

        dataset = DatasetFactory()
        RockSampleFactory.create_batch(2, dataset=dataset, location=None)

        result = _plugin_for(dataset).get_sample_map(
            Sample.objects.filter(dataset=dataset), None, self.POINTS_URL
        )

        assert result["located"] == 0
        assert result["missing"] == 2
        assert result["bounds"] is None
        assert result["area"] is None


@pytest.mark.django_db
class TestSamplePoints:
    @pytest.fixture
    def mapped(self):
        """A public project: two sample types in two datasets, and a private one."""
        from types import SimpleNamespace

        from demo.factories import RockSampleFactory, SoilSampleFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        first = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        second = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        private = DatasetFactory(
            project=project, visibility=Visibility.PRIVATE, published=False
        )
        RockSampleFactory(
            name="Alder", dataset=first, location=Point(7.9, 48.9, srid=4326)
        )
        SoilSampleFactory(
            name="Basalt", dataset=second, location=Point(8.1, 49.0, srid=4326)
        )
        RockSampleFactory(
            name="Hidden", dataset=private, location=Point(1.0, 2.0, srid=4326)
        )
        return SimpleNamespace(
            project=project, first=first, second=second, private=private
        )

    @staticmethod
    def names(response):
        return {f["properties"]["name"] for f in response.json()["features"]}

    def test_the_projects_address_answers_the_visitors_samples_as_geojson(
        self, client, mapped
    ):
        response = client.get(
            reverse(
                "project:overview-sample-points", kwargs={"uuid": mapped.project.uuid}
            )
        )

        assert response.status_code == 200
        assert response.json()["type"] == "FeatureCollection"
        assert self.names(response) == {"Alder", "Basalt"}

    def test_the_datasets_address_answers_that_datasets_samples_only(
        self, client, mapped
    ):
        response = client.get(
            reverse(
                "dataset:overview-sample-points", kwargs={"uuid": mapped.first.uuid}
            )
        )

        assert response.status_code == 200
        assert self.names(response) == {"Alder"}

    def test_a_member_of_the_private_dataset_gets_its_samples_on_the_projects_address(
        self, client, mapped
    ):
        from fairdm.contrib.contributors.choices import ContributionLevel
        from fairdm.factories import ContributionFactory

        user = UserFactory()
        ContributionFactory(
            content_object=mapped.private,
            contributor=user,
            level=ContributionLevel.VIEW,
        )
        client.force_login(user)

        response = client.get(
            reverse(
                "project:overview-sample-points", kwargs={"uuid": mapped.project.uuid}
            )
        )

        assert self.names(response) == {"Alder", "Basalt", "Hidden"}

    @pytest.mark.parametrize("signed_in", [False, True])
    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_a_private_record_answers_not_found_to_a_visitor_and_to_a_stranger(
        self, client, kind, signed_in
    ):
        from demo.factories import RockSampleFactory

        if kind == "project":
            record = ProjectFactory(visibility=Visibility.PRIVATE)
            dataset = DatasetFactory(
                project=record, visibility=Visibility.PUBLIC, published=True
            )
        else:
            record = dataset = DatasetFactory(
                visibility=Visibility.PRIVATE, published=True
            )
        RockSampleFactory(dataset=dataset, location=Point(7.9, 48.9, srid=4326))
        if signed_in:
            client.force_login(UserFactory())

        response = client.get(
            reverse(f"{kind}:overview-sample-points", kwargs={"uuid": record.uuid})
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("kind", ["project", "dataset"])
    def test_an_address_naming_no_record_answers_not_found(self, client, kind):
        response = client.get(
            reverse(f"{kind}:overview-sample-points", kwargs={"uuid": uuid.uuid4()})
        )

        assert response.status_code == 404

    def test_the_projects_address_costs_the_same_queries_for_more_samples(
        self, client, mapped, django_assert_num_queries
    ):
        from demo.factories import RockSampleFactory, SoilSampleFactory

        project = ProjectFactory(visibility=Visibility.PUBLIC)
        one = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        two = DatasetFactory(
            project=project, visibility=Visibility.PUBLIC, published=True
        )
        RockSampleFactory(dataset=one, location=Point(7.9, 48.9, srid=4326))
        url = reverse("project:overview-sample-points", kwargs={"uuid": project.uuid})
        client.get(url)  # warm up one-time per-process setup
        with CaptureQueriesContext(connection) as single:
            assert client.get(url).status_code == 200
        baseline = len(single.captured_queries)

        RockSampleFactory.create_batch(
            4, dataset=two, location=Point(8.0, 49.0, srid=4326)
        )
        SoilSampleFactory.create_batch(
            4, dataset=one, location=Point(8.2, 49.1, srid=4326)
        )
        client.get(url)
        with django_assert_num_queries(baseline):
            response = client.get(url)

        assert len(response.json()["features"]) == 9

    @pytest.mark.parametrize(
        "overview",
        ["fairdm.core.project.plugins", "fairdm.core.dataset.plugins"],
    )
    def test_a_view_declared_on_the_shared_plugin_is_kept_beside_the_points(
        self, monkeypatch, overview
    ):
        import importlib

        from fairdm.core.plugins import SamplePoints

        class Citation(Plugin):
            name = "citation"

        monkeypatch.setattr(RecordOverviewPlugin, "extra_views", [Citation])

        views = importlib.import_module(overview).Overview.get_extra_views()

        assert views == [Citation, SamplePoints]


def public_dataset_for_citation():
    return DatasetFactory(visibility=Visibility.PUBLIC, published=True)


def private_dataset_for_citation():
    return DatasetFactory(visibility=Visibility.PRIVATE, published=False)


def sample_for_citation(dataset):
    return RockSampleFactory(dataset=dataset, name="Zq-4471 rift core")


def measurement_for_citation(dataset):
    return XRFMeasurementFactory(
        dataset=dataset, sample=sample_for_citation(dataset), name="Zq-9902 scan"
    )


#: kind: (namespace, makes a record from a dataset, the name the file is given)
KINDS = {
    "project": (
        "project",
        lambda dataset: ProjectFactory(
            visibility=dataset.visibility, name="Seismic survey"
        ),
        "seismic-survey",
    ),
    "dataset": ("dataset", lambda dataset: dataset, None),
    "sample": ("sample", sample_for_citation, "zq-4471-rift-core-rock-sample"),
    "measurement": (
        "measurement",
        measurement_for_citation,
        "zq-9902-scan-xrf-measurement-of-zq-4471-rift-core",
    ),
}


def address_for_citation(kind, record, key):
    return reverse(
        f"{KINDS[kind][0]}:overview-citation",
        kwargs={"uuid": record.uuid, "format": key},
    )


def page_address_for_citation(kind, record):
    return reverse(f"{KINDS[kind][0]}:overview", kwargs={"uuid": record.uuid})


def team_member_of_for_citation(kind, record):
    """A user with view access to the record, through its own team or its dataset's."""
    user = PersonFactory(is_active=True)
    held = record if kind in ("project", "dataset") else record.dataset
    ContributionFactory(
        content_object=held, contributor=user, level=ContributionLevel.VIEW
    )
    return user


@pytest.fixture(params=list(KINDS))
def kind(request):
    return request.param


@pytest.fixture
def public_record(kind):
    dataset = public_dataset_for_citation()
    record = KINDS[kind][1](dataset)
    if kind == "dataset":
        record.name = "Borehole logs"
        record.save()
    return record


@pytest.fixture
def private_record(kind):
    dataset = private_dataset_for_citation()
    record = KINDS[kind][1](dataset)
    if kind == "dataset":
        record.name = "Borehole logs"
        record.save()
    return record


def stem_for_citation(kind, record):
    return KINDS[kind][2] or "borehole-logs"


@pytest.mark.django_db
class TestCitationFile:
    """The address of each citation format, at ``<record address>cite/<format>/``."""

    @pytest.mark.parametrize("fmt", FORMATS, ids=lambda f: f.key)
    def test_each_format_answers_with_its_content_type_and_a_named_attachment(
        self, client, kind, public_record, fmt
    ):
        response = client.get(address_for_citation(kind, public_record, fmt.key))

        assert response.status_code == 200
        assert response["Content-Type"] == fmt.content_type
        stem = stem_for_citation(kind, public_record)
        assert response["Content-Disposition"] == (
            f'attachment; filename="{stem}.{fmt.extension}"'
        )

    @pytest.mark.parametrize("fmt", FORMATS, ids=lambda f: f.key)
    def test_the_body_is_the_formats_value_on_the_pages_context(
        self, client, kind, public_record, fmt
    ):
        page = client.get(page_address_for_citation(kind, public_record))
        values = {f["key"]: f["value"] for f in page.context["citation"]["formats"]}

        response = client.get(address_for_citation(kind, public_record, fmt.key))

        assert response.content.decode() == values[fmt.key]

    def test_a_stranger_gets_the_not_found_the_page_gives_for_a_private_record(
        self, client, kind, private_record
    ):
        page = client.get(page_address_for_citation(kind, private_record))

        for fmt in FORMATS:
            response = client.get(address_for_citation(kind, private_record, fmt.key))
            assert response.status_code == page.status_code == 404

    @pytest.mark.parametrize("fmt", FORMATS, ids=lambda f: f.key)
    def test_a_team_member_gets_the_file_for_a_private_record(
        self, client, kind, private_record, fmt
    ):
        client.force_login(team_member_of_for_citation(kind, private_record))

        response = client.get(address_for_citation(kind, private_record, fmt.key))

        assert response.status_code == 200
        assert response["Content-Type"] == fmt.content_type

    def test_an_unknown_record_is_not_found(self, client, kind, public_record):
        unknown = SimpleNamespace(uuid=uuid.uuid4())

        assert (
            client.get(address_for_citation(kind, unknown, "bibtex")).status_code == 404
        )

    def test_an_unknown_format_is_not_found(self, client, kind, public_record):
        assert (
            client.get(address_for_citation(kind, public_record, "csl")).status_code
            == 404
        )

    def test_a_site_with_no_name_gives_no_publisher(self, client, kind, public_record):
        Site.objects.filter(pk=Site.objects.get_current().pk).update(name="")
        Site.objects.clear_cache()

        bibtex = client.get(
            address_for_citation(kind, public_record, "bibtex")
        ).content.decode()
        ris = client.get(
            address_for_citation(kind, public_record, "ris")
        ).content.decode()

        [entry] = parse_string(bibtex, "bibtex").entries.values()
        assert "publisher" not in entry.fields
        assert "publisher" not in rispy.loads(ris)[0]

    def test_the_address_costs_no_more_queries_than_the_page(
        self, client, kind, public_record
    ):
        client.get(page_address_for_citation(kind, public_record))
        with CaptureQueriesContext(connection) as page:
            client.get(page_address_for_citation(kind, public_record))
        with CaptureQueriesContext(connection) as file:
            client.get(address_for_citation(kind, public_record, "bibtex"))

        assert len(file) <= len(page)

    def test_a_portal_plugin_without_the_view_gives_the_formats_no_address(self):
        person = PersonFactory(is_active=True)

        assert _plugin_for(person).get_citation_address("bibtex") is None

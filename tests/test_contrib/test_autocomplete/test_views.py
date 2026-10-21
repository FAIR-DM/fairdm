"""Tests for the autocomplete views, called through their real addresses."""

import pytest
from django.urls import reverse

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Affiliation
from fairdm.factories import AffiliationFactory, ContributionFactory, ProjectFactory
from fairdm.utils.choices import Visibility
from tests.registry_models.models import ConcreteMeasurement, ConcreteSample


def search(client, kind, scope, **params):
    """Return the decoded answer of one kind's address at one scope, or of a kind with none."""
    name = f"{kind}-{scope}" if scope else kind
    response = client.get(reverse(f"autocomplete:{name}"), params)
    assert response.status_code == 200
    return response.json()


def names(answer):
    return [result["name"] for result in answer["results"]]


@pytest.mark.django_db
class TestDatasetAutocompleteView:
    def test_edit_offers_a_private_dataset_the_researcher_can_edit(
        self, researcher_client, researcher, make_dataset
    ):
        dataset = make_dataset("Rock cores", holder=researcher)

        answer = search(researcher_client, "dataset", "edit")

        assert [r["id"] for r in answer["results"]] == [dataset.pk]

    def test_edit_does_not_offer_a_public_dataset_the_researcher_cannot_edit(
        self, researcher_client, make_dataset
    ):
        make_dataset("Open data", visibility=Visibility.PUBLIC)

        answer = search(researcher_client, "dataset", "edit")

        assert answer["results"] == []

    def test_edit_does_not_offer_a_private_dataset_the_researcher_cannot_see(
        self, researcher_client, make_dataset
    ):
        make_dataset("Secret data")

        answer = search(researcher_client, "dataset", "edit")

        assert answer["results"] == []

    def test_edit_does_not_offer_a_dataset_the_researcher_may_only_view(
        self, researcher_client, researcher, make_dataset
    ):
        make_dataset("Read only", holder=researcher, level=ContributionLevel.VIEW)

        answer = search(researcher_client, "dataset", "edit")

        assert answer["results"] == []

    def test_a_result_carries_its_project_and_a_private_flag(
        self, researcher_client, researcher, make_dataset
    ):
        private = make_dataset("Private one", holder=researcher)
        public = make_dataset(
            "Public one", visibility=Visibility.PUBLIC, holder=researcher
        )

        results = {
            r["name"]: r
            for r in search(researcher_client, "dataset", "edit")["results"]
        }

        assert results["Private one"]["project"] == private.project.name
        assert results["Private one"]["private"] is True
        assert results["Public one"]["project"] == public.project.name
        assert results["Public one"]["private"] is False

    def test_a_dataset_in_a_private_project_is_flagged_private(
        self, researcher_client, researcher, make_dataset
    ):
        make_dataset(
            "Public in private",
            visibility=Visibility.PUBLIC,
            project_visibility=Visibility.PRIVATE,
            holder=researcher,
        )

        results = search(researcher_client, "dataset", "edit")["results"]

        assert results[0]["private"] is True

    def test_the_search_text_narrows_the_results_by_name(
        self, researcher_client, researcher, make_dataset
    ):
        make_dataset("Basalt cores", holder=researcher)
        make_dataset("Granite cores", holder=researcher)

        answer = search(researcher_client, "dataset", "edit", q="basalt")

        assert names(answer) == ["Basalt cores"]

    def test_results_are_grouped_own_then_public_then_role_wide(
        self, researcher_client, researcher, make_dataset, grant_view_everywhere
    ):
        grant_view_everywhere(researcher)
        elsewhere = make_dataset("A elsewhere")
        public = make_dataset("B public", visibility=Visibility.PUBLIC)
        own = make_dataset("C own", holder=researcher)

        answer = search(researcher_client, "dataset", "view")

        assert [r["id"] for r in answer["results"]] == [own.pk, public.pk, elsewhere.pk]
        groups = [r["optgroup"] for r in answer["results"]]
        assert len(set(groups)) == 3

    def test_a_dataset_that_is_own_and_public_is_offered_once_among_the_own(
        self, researcher_client, researcher, make_dataset
    ):
        both = make_dataset("Both", visibility=Visibility.PUBLIC, holder=researcher)
        other = make_dataset("Other public", visibility=Visibility.PUBLIC)

        answer = search(researcher_client, "dataset", "view")

        assert [r["id"] for r in answer["results"]] == [both.pk, other.pk]

    def test_a_page_past_the_first_is_served_on_request(
        self, researcher_client, researcher, make_dataset
    ):
        for number in range(25):
            make_dataset(f"Dataset {number:02d}", holder=researcher)

        first = search(researcher_client, "dataset", "edit")
        second = search(researcher_client, "dataset", "edit", p=2)

        assert first["has_more"] is True
        assert len(first["results"]) == 20
        assert len(second["results"]) == 5
        assert not {r["id"] for r in first["results"]} & {
            r["id"] for r in second["results"]
        }

    def test_a_visitor_is_offered_nothing_at_edit(self, client, make_dataset):
        make_dataset("Open data", visibility=Visibility.PUBLIC)

        assert search(client, "dataset", "edit")["results"] == []

    @pytest.mark.parametrize("scope", ["public", "view"])
    def test_a_visitor_is_offered_public_datasets_at_public_and_view(
        self, client, make_dataset, scope
    ):
        open_dataset = make_dataset("Open data", visibility=Visibility.PUBLIC)
        make_dataset("Closed data")

        answer = search(client, "dataset", scope)

        assert [r["id"] for r in answer["results"]] == [open_dataset.pk]

    def test_public_does_not_offer_a_private_dataset_the_researcher_can_edit(
        self, researcher_client, researcher, make_dataset
    ):
        make_dataset("Mine", holder=researcher)

        assert search(researcher_client, "dataset", "public")["results"] == []


@pytest.mark.django_db
class TestRecordRows:
    def test_a_name_with_markup_is_escaped_once_in_the_drawn_row(
        self, researcher_client, researcher, make_dataset
    ):
        make_dataset("Rock & <b>core</b>", holder=researcher)

        row = search(researcher_client, "dataset", "edit")["results"][0]["html"]

        assert "Rock &amp; &lt;b&gt;core&lt;/b&gt;" in row
        assert "<b>" not in row

    def test_a_dataset_is_found_by_its_uuid_typed_exactly(
        self, researcher_client, researcher, make_dataset
    ):
        wanted = make_dataset("Unrelated name", holder=researcher)
        make_dataset("Another", holder=researcher)

        answer = search(researcher_client, "dataset", "edit", q=wanted.uuid)

        assert [r["id"] for r in answer["results"]] == [wanted.pk]


@pytest.mark.django_db
class TestProjectAutocompleteView:
    def test_edit_offers_the_private_projects_the_researcher_can_edit(
        self, researcher_client, researcher, make_project
    ):
        editable = make_project("Editable", holder=researcher)
        make_project("Read only", holder=researcher, level=ContributionLevel.VIEW)
        make_project("Public", visibility=Visibility.PUBLIC)
        make_project("Unseen")

        answer = search(researcher_client, "project", "edit")

        assert [r["id"] for r in answer["results"]] == [editable.pk]

    def test_a_result_carries_a_private_flag(
        self, researcher_client, researcher, make_project
    ):
        make_project("Private one", holder=researcher)
        make_project("Public one", visibility=Visibility.PUBLIC, holder=researcher)

        results = {
            r["name"]: r
            for r in search(researcher_client, "project", "edit")["results"]
        }

        assert results["Private one"]["private"] is True
        assert results["Public one"]["private"] is False

    def test_a_data_curator_gets_every_project_with_their_own_first(
        self, client, data_curator, make_project
    ):
        client.force_login(data_curator)
        elsewhere = make_project("A elsewhere")
        own = make_project("B own", holder=data_curator)

        answer = search(client, "project", "edit")

        assert [r["id"] for r in answer["results"]] == [own.pk, elsewhere.pk]
        assert answer["results"][0]["optgroup"] != answer["results"][1]["optgroup"]

    def test_a_visitor_is_offered_public_projects_at_view_and_none_at_edit(
        self, client, make_project
    ):
        public = make_project("Open", visibility=Visibility.PUBLIC)
        make_project("Closed")

        assert [r["id"] for r in search(client, "project", "view")["results"]] == [
            public.pk
        ]
        assert search(client, "project", "edit")["results"] == []


def narrowed_to(dataset):
    """Return the filter parameter django-tomselect sends for a field that depends on a dataset."""
    return {"f": f"'dataset__dataset={dataset.pk}'"}


def preferring(dataset):
    """Return the parameter a field that prefers a dataset sends with each search."""
    return {"prefer": f"dataset={dataset.pk}"}


@pytest.mark.django_db
class TestSampleAutocompleteView:
    def test_narrowed_by_a_dataset_only_that_datasets_samples_are_offered(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        wanted = make_dataset("Wanted", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        inside = make_sample("Inside", dataset=wanted)
        make_sample("Outside", dataset=other)

        answer = search(researcher_client, "sample", "view", **narrowed_to(wanted))

        assert [r["id"] for r in answer["results"]] == [inside.pk]

    def test_a_preferred_dataset_puts_its_samples_first_in_a_group_of_their_own(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        wanted = make_dataset("Wanted", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        elsewhere = make_sample("Alpha", dataset=other)
        inside = make_sample("Zulu", dataset=wanted)

        answer = search(researcher_client, "sample", "view", **preferring(wanted))

        assert [r["id"] for r in answer["results"]] == [inside.pk, elsewhere.pk]
        assert answer["results"][0]["optgroup"] != answer["results"][1]["optgroup"]

    def test_a_preference_does_not_offer_what_the_person_could_not_be_offered(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        unseen = make_dataset("Unseen")
        make_sample("Hidden", dataset=unseen)
        visible = make_sample("Seen", dataset=make_dataset("Mine", holder=researcher))

        answer = search(researcher_client, "sample", "view", **preferring(unseen))

        assert [r["id"] for r in answer["results"]] == [visible.pk]

    @pytest.mark.parametrize(
        "preference",
        ["visibility=1", "dataset=not a key", "dataset=", "dataset", "=3"],
    )
    def test_a_preference_the_view_cannot_use_changes_nothing(
        self,
        researcher_client,
        researcher,
        make_dataset,
        make_sample,
        preference,
    ):
        dataset = make_dataset("Cores", holder=researcher)
        for name in ("Alpha", "Bravo"):
            make_sample(name, dataset=dataset)

        plain = search(researcher_client, "sample", "view")
        preferred = search(researcher_client, "sample", "view", prefer=preference)

        assert preferred["results"] == plain["results"]

    def test_a_local_id_typed_exactly_comes_first(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        dataset = make_dataset("Cores", holder=researcher)
        make_sample("B-1 slab", dataset=dataset)
        exact = make_sample("Zeta", dataset=dataset, local_id="B-1")

        answer = search(researcher_client, "sample", "view", q="B-1")

        assert answer["results"][0]["id"] == exact.pk
        assert len(answer["results"]) == 2

    def test_an_identifier_typed_exactly_comes_first(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        dataset = make_dataset("Cores", holder=researcher)
        make_sample("AU1101 slab", dataset=dataset)
        exact = make_sample("Zeta", dataset=dataset, identifier="AU1101")

        answer = search(researcher_client, "sample", "view", q="AU1101")

        assert answer["results"][0]["id"] == exact.pk
        assert len(answer["results"]) == 2

    def test_a_sample_with_two_matching_lookups_is_offered_once(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        dataset = make_dataset("Cores", holder=researcher)
        sample = make_sample(
            "AU1101 core", dataset=dataset, local_id="AU1101", identifier="AU1101"
        )

        answer = search(researcher_client, "sample", "view", q="AU1101")

        assert [r["id"] for r in answer["results"]] == [sample.pk]

    def test_a_row_gives_the_type_the_local_id_and_the_dataset(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        dataset = make_dataset("Cores", holder=researcher)
        make_sample("Core one", dataset=dataset, local_id="C-1")

        row = search(researcher_client, "sample", "view")["results"][0]

        assert row["type"] == ConcreteSample._meta.verbose_name
        assert row["local_id"] == "C-1"
        assert row["dataset"] == "Cores"

    def test_a_sample_is_public_when_its_dataset_is_public_and_published(
        self, client, make_dataset, make_sample
    ):
        released = make_dataset(
            "Released", visibility=Visibility.PUBLIC, published=True
        )
        unpublished = make_dataset("Unpublished", visibility=Visibility.PUBLIC)
        private = make_dataset("Private", published=True)
        shown = make_sample("Shown", dataset=released)
        make_sample("Not published", dataset=unpublished)
        make_sample("Private dataset", dataset=private)

        answer = search(client, "sample", "public")

        assert [r["id"] for r in answer["results"]] == [shown.pk]
        assert answer["results"][0]["private"] is False

    def test_a_sample_of_a_dataset_the_researcher_holds_is_flagged_private(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        make_sample("Mine", dataset=make_dataset("Mine", holder=researcher))

        row = search(researcher_client, "sample", "view")["results"][0]

        assert row["private"] is True

    def test_edit_offers_only_samples_of_datasets_the_researcher_may_edit(
        self, researcher_client, researcher, make_dataset, make_sample
    ):
        editable = make_sample("Editable", dataset=make_dataset("A", holder=researcher))
        make_sample(
            "Read only",
            dataset=make_dataset("B", holder=researcher, level=ContributionLevel.VIEW),
        )

        answer = search(researcher_client, "sample", "edit")

        assert [r["id"] for r in answer["results"]] == [editable.pk]


@pytest.mark.django_db
class TestMeasurementAutocompleteView:
    def test_narrowed_by_a_dataset_only_that_datasets_measurements_are_offered(
        self, researcher_client, researcher, make_dataset, make_measurement
    ):
        wanted = make_dataset("Wanted", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        inside = make_measurement("Inside", dataset=wanted)
        make_measurement("Outside", dataset=other)

        answer = search(researcher_client, "measurement", "view", **narrowed_to(wanted))

        assert [r["id"] for r in answer["results"]] == [inside.pk]

    def test_a_preferred_dataset_puts_its_measurements_first_in_a_group_of_their_own(
        self, researcher_client, researcher, make_dataset, make_measurement
    ):
        wanted = make_dataset("Wanted", holder=researcher)
        other = make_dataset("Other", holder=researcher)
        elsewhere = make_measurement("Alpha", dataset=other)
        inside = make_measurement("Zulu", dataset=wanted)

        answer = search(researcher_client, "measurement", "view", **preferring(wanted))

        assert [r["id"] for r in answer["results"]] == [inside.pk, elsewhere.pk]
        assert answer["results"][0]["optgroup"] != answer["results"][1]["optgroup"]

    def test_a_local_id_typed_exactly_comes_first(
        self, researcher_client, researcher, make_dataset, make_measurement
    ):
        dataset = make_dataset("Runs", holder=researcher)
        make_measurement("R-7 repeat", dataset=dataset)
        exact = make_measurement("Zeta", dataset=dataset, local_id="R-7")

        answer = search(researcher_client, "measurement", "view", q="R-7")

        assert answer["results"][0]["id"] == exact.pk
        assert len(answer["results"]) == 2

    def test_a_row_gives_the_type_the_local_id_and_the_dataset(
        self, researcher_client, researcher, make_dataset, make_measurement
    ):
        dataset = make_dataset("Runs", holder=researcher)
        make_measurement("Run one", dataset=dataset, local_id="R-1")

        row = search(researcher_client, "measurement", "view")["results"][0]

        assert row["type"] == ConcreteMeasurement._meta.verbose_name
        assert row["local_id"] == "R-1"
        assert row["dataset"] == "Runs"

    def test_a_measurement_is_public_when_its_dataset_is_public_and_published(
        self, client, make_dataset, make_measurement
    ):
        released = make_dataset(
            "Released", visibility=Visibility.PUBLIC, published=True
        )
        unpublished = make_dataset("Unpublished", visibility=Visibility.PUBLIC)
        shown = make_measurement("Shown", dataset=released)
        make_measurement("Not published", dataset=unpublished)

        answer = search(client, "measurement", "public")

        assert [r["id"] for r in answer["results"]] == [shown.pk]
        assert answer["results"][0]["private"] is False


def every_address():
    """Return the kind and scope of each record address the app registers."""
    from fairdm.contrib.autocomplete import urls

    return [(kind, scope) for kind in urls.RECORD_VIEWS for scope in urls.SCOPES]


@pytest.mark.django_db
@pytest.mark.parametrize(("kind", "scope"), every_address())
class TestLimitedAutocompleteMixin:
    def test_every_address_answers_a_visitor(self, client, kind, scope):
        assert search(client, kind, scope)["results"] == []

    def test_a_requested_page_size_is_ignored(
        self, researcher_client, researcher, make_record, kind, scope
    ):
        for number in range(25):
            make_record(kind, f"Record {number:02d}", holder=researcher)

        for requested in (3, 1000):
            answer = search(researcher_client, kind, scope, page_size=requested)

            assert len(answer["results"]) == 20

    def test_a_search_is_cut_to_a_hundred_characters(
        self, researcher_client, researcher, make_record, kind, scope
    ):
        wanted = make_record(kind, "a" * 100, holder=researcher)

        answer = search(researcher_client, kind, scope, q="a" * 100 + "zzzz")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_no_page_past_the_limit_is_served(
        self, researcher_client, researcher, make_record, monkeypatch, kind, scope
    ):
        from fairdm.contrib.autocomplete.views import LimitedAutocompleteMixin

        monkeypatch.setattr(LimitedAutocompleteMixin, "max_pages", 2)
        for number in range(45):
            make_record(kind, f"Record {number:02d}", holder=researcher)

        last = search(researcher_client, kind, scope, p=2)
        past = search(researcher_client, kind, scope, p=3)

        assert len(last["results"]) == 20
        assert last["has_more"] is False
        assert past["results"] == []

    def test_a_page_past_the_last_is_empty(
        self, researcher_client, researcher, make_record, kind, scope
    ):
        make_record(kind, "Only one", holder=researcher)

        assert search(researcher_client, kind, scope, p=5)["results"] == []

    @pytest.mark.parametrize(
        ("parameter", "narrowing"),
        [
            ("f", f"field__visibility={int(Visibility.PUBLIC)}"),
            ("e", f"field__visibility={int(Visibility.PRIVATE)}"),
        ],
    )
    def test_a_filter_outside_the_allow_list_offers_nothing(
        self,
        researcher_client,
        researcher,
        make_record,
        kind,
        scope,
        parameter,
        narrowing,
    ):
        make_record(kind, "Record", holder=researcher)

        answer = search(researcher_client, kind, scope, **{parameter: narrowing})

        assert answer["results"] == []

    def test_an_ordering_outside_the_allow_list_changes_nothing(
        self, researcher_client, researcher, make_record, kind, scope
    ):
        for name in ("Alpha", "Bravo", "Charlie"):
            make_record(kind, name, holder=researcher)

        plain = search(researcher_client, kind, scope)
        reordered = search(researcher_client, kind, scope, ordering="-name")

        assert names(reordered) == names(plain) == ["Alpha", "Bravo", "Charlie"]

    def test_a_failing_search_reveals_only_the_failure(
        self, researcher_client, monkeypatch, settings, kind, scope
    ):
        from fairdm.contrib.autocomplete import urls

        settings.DEBUG = True

        def fail(self):
            raise RuntimeError("secret detail")

        monkeypatch.setattr(urls.RECORD_VIEWS[kind], "get_queryset", fail)

        response = researcher_client.get(reverse(f"autocomplete:{kind}-{scope}"))

        assert response.status_code == 500
        assert "secret detail" not in response.content.decode()
        assert response.json()["results"] == []
        assert set(response.json()) <= {"results", "page", "has_more"}


@pytest.mark.django_db
class TestOrganizationAutocompleteView:
    def test_an_organization_is_found_by_part_of_its_name(
        self, researcher_client, make_organization
    ):
        wanted = make_organization("Potsdam Research Institute")
        make_organization("Berlin Laboratory")

        answer = search(researcher_client, "organization", "public", q="potsdam")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_an_organization_is_found_by_an_alternative_name(
        self, researcher_client, make_organization
    ):
        wanted = make_organization(
            "Helmholtz Centre Potsdam", alternative_names=["GFZ"]
        )
        make_organization("Berlin Laboratory")

        answer = search(researcher_client, "organization", "public", q="gfz")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_a_ror_identifier_typed_exactly_comes_first(
        self, researcher_client, make_organization
    ):
        make_organization("Aardvark 04z8jg394 group")
        wanted = make_organization("Zeta Institute", ror="04z8jg394")

        answer = search(researcher_client, "organization", "public", q="04z8jg394")

        assert answer["results"][0]["id"] == wanted.pk
        assert len(answer["results"]) == 2

    def test_an_identifier_typed_in_part_finds_nothing(
        self, researcher_client, make_organization
    ):
        make_organization("Zeta Institute", ror="04z8jg394")

        answer = search(researcher_client, "organization", "public", q="04z8jg")

        assert answer["results"] == []

    def test_the_organizations_the_researcher_belongs_to_come_first(
        self, researcher_client, researcher, make_organization
    ):
        other = make_organization("Alpha Institute")
        member_of = make_organization("Zulu Institute")
        AffiliationFactory(person=researcher, organization=member_of)

        answer = search(researcher_client, "organization", "public")

        assert [r["id"] for r in answer["results"]] == [member_of.pk, other.pk]
        assert answer["results"][0]["optgroup"] != answer["results"][1]["optgroup"]

    def test_a_pending_request_does_not_make_an_organization_the_researchers_own(
        self, researcher_client, researcher, make_organization
    ):
        first = make_organization("Alpha Institute")
        requested = make_organization("Zulu Institute")
        AffiliationFactory(
            person=researcher,
            organization=requested,
            type=Affiliation.MembershipType.PENDING,
        )

        answer = search(researcher_client, "organization", "public")

        assert [r["id"] for r in answer["results"]] == [first.pk, requested.pk]
        assert {r.get("optgroup") for r in answer["results"]} == {None}

    def test_an_ended_membership_does_not_make_an_organization_the_researchers_own(
        self, researcher_client, researcher, make_organization
    ):
        first = make_organization("Alpha Institute")
        left = make_organization("Zulu Institute")
        AffiliationFactory(person=researcher, organization=left, end_date="2022")

        answer = search(researcher_client, "organization", "public")

        assert [r["id"] for r in answer["results"]] == [first.pk, left.pk]

    def test_a_row_gives_the_place_and_no_identifier(
        self, researcher_client, make_organization
    ):
        make_organization(
            "Potsdam Research Institute",
            ror="04z8jg394",
            city="Potsdam",
            country="DE",
        )

        row = search(researcher_client, "organization", "public")["results"][0]["html"]

        assert "Potsdam" in row
        assert "04z8jg394" not in row

    def test_a_visitor_is_offered_organizations_with_no_group(
        self, client, make_organization
    ):
        wanted = make_organization("Potsdam Research Institute")

        answer = search(client, "organization", "public")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]
        assert "optgroup" not in answer["results"][0]


@pytest.mark.django_db
class TestPersonAutocompleteView:
    def share_a_record(self, researcher, person, *, level=ContributionLevel.VIEW):
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(
            content_object=project, contributor=researcher, level=ContributionLevel.EDIT
        )
        ContributionFactory(content_object=project, contributor=person, level=level)
        return project

    def test_a_person_is_found_by_part_of_their_name(
        self, researcher_client, make_person
    ):
        wanted = make_person("Dana Smith")
        make_person("Ravi Patel")

        answer = search(researcher_client, "person", "public", q="smi")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_a_person_is_found_by_an_alternative_name(
        self, researcher_client, make_person
    ):
        wanted = make_person("Dana Smith", alternative_names=["D. Schmidt"])
        make_person("Ravi Patel")

        answer = search(researcher_client, "person", "public", q="schmidt")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_an_orcid_typed_exactly_comes_first(self, researcher_client, make_person):
        make_person("Aardvark 0000-0002-1825-0097 fan")
        wanted = make_person("Zed Zimmer", orcid="0000-0002-1825-0097")

        answer = search(researcher_client, "person", "public", q="0000-0002-1825-0097")

        assert answer["results"][0]["id"] == wanted.pk
        assert len(answer["results"]) == 2

    def test_the_people_the_researcher_has_worked_with_come_first(
        self, researcher_client, researcher, make_person
    ):
        stranger = make_person("Alpha Stranger")
        colleague = make_person("Zulu Colleague")
        self.share_a_record(researcher, colleague)

        answer = search(researcher_client, "person", "public")

        ids = [r["id"] for r in answer["results"] if r["id"] != researcher.pk]
        assert ids == [colleague.pk, stranger.pk]
        groups = {r["id"]: r["optgroup"] for r in answer["results"]}
        assert groups[colleague.pk] != groups[stranger.pk]

    def test_a_collaboration_only_through_a_record_the_researcher_cannot_open_does_not_group(
        self, researcher_client, researcher, make_person
    ):
        stranger = make_person("Alpha Stranger")
        met_in_private = make_person("Zulu Colleague")
        project = ProjectFactory(visibility=Visibility.PRIVATE)
        ContributionFactory(content_object=project, contributor=researcher, level=None)
        ContributionFactory(
            content_object=project,
            contributor=met_in_private,
            level=ContributionLevel.EDIT,
        )

        answer = search(researcher_client, "person", "public")

        ids = [r["id"] for r in answer["results"] if r["id"] != researcher.pk]
        assert ids == [stranger.pk, met_in_private.pk]
        assert {r.get("optgroup") for r in answer["results"]} == {None}

    def test_a_visitor_is_offered_people_with_no_group(self, client, make_person):
        wanted = make_person("Dana Smith")

        answer = search(client, "person", "public")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]
        assert "optgroup" not in answer["results"][0]

    def test_a_superuser_is_not_offered(self, researcher_client, make_person):
        make_person("Root Admin", superuser=True)
        wanted = make_person("Dana Smith")

        answer = search(researcher_client, "person", "public")

        assert [r["id"] for r in answer["results"] if r["name"] != "Test User"] == [
            wanted.pk
        ]

    def test_an_email_address_typed_finds_nobody(self, researcher_client, make_person):
        make_person("Dana Smith", email="dana.smith@example.org")

        for typed in ("dana.smith@example.org", "example.org", "dana.smith"):
            assert (
                search(researcher_client, "person", "public", q=typed)["results"] == []
            )

    def test_no_result_carries_an_email_address(self, researcher_client, make_person):
        make_person("Dana Smith", email="dana.smith@example.org")

        response = researcher_client.get(reverse("autocomplete:person-public"))

        assert "dana.smith@example.org" not in response.content.decode()

    @pytest.mark.parametrize("parameter", ["f", "e"])
    def test_a_filter_naming_the_email_offers_nothing(
        self, researcher_client, make_person, parameter
    ):
        make_person("Dana Smith", email="dana.smith@example.org")

        answer = search(
            researcher_client,
            "person",
            "public",
            **{parameter: "email__icontains=dana"},
        )

        assert answer["results"] == []

    @pytest.mark.parametrize("ordering", ["email", "-email"])
    def test_an_ordering_naming_the_email_changes_nothing(
        self, researcher_client, make_person, ordering
    ):
        make_person("Bravo", email="a@example.org")
        make_person("Alpha", email="z@example.org")

        plain = search(researcher_client, "person", "public")
        reordered = search(researcher_client, "person", "public", ordering=ordering)

        assert names(reordered) == names(plain)

    def test_an_unclaimed_person_is_marked_and_a_claimed_one_is_not(
        self, researcher_client, make_person
    ):
        make_person("Alpha Unclaimed")
        make_person("Zulu Claimed", claimed=True)

        results = {
            r["name"]: r
            for r in search(researcher_client, "person", "public")["results"]
        }

        assert results["Alpha Unclaimed"]["unclaimed"] is True
        assert results["Zulu Claimed"]["unclaimed"] is False

    def test_a_row_gives_the_primary_affiliation_and_the_orcid(
        self, researcher_client, make_person, make_organization
    ):
        organization = make_organization("Potsdam Research Institute")
        make_person(
            "Dana Smith", orcid="0000-0002-1825-0097", organization=organization
        )

        row = search(researcher_client, "person", "public", q="dana")["results"][0]

        assert "Potsdam Research Institute" in row["html"]
        assert "0000-0002-1825-0097" in row["html"]


@pytest.mark.django_db
class TestPublicationAutocompleteView:
    def test_a_publication_is_found_by_part_of_its_title(
        self, client, make_publication
    ):
        wanted = make_publication("Basalt cooling rates")
        make_publication("Granite ages")

        answer = search(client, "publication", None, q="cooling")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_a_publication_is_found_by_an_author(self, client, make_publication):
        wanted = make_publication("Untitled study", authors=[("Lovelace", "Ada")])
        make_publication("Other study", authors=[("Babbage", "Charles")])

        answer = search(client, "publication", None, q="lovelace")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_a_doi_typed_exactly_comes_first(self, client, make_publication):
        mentioned = make_publication("On the paper 10.1000/abc and others")
        exact = make_publication("Another title", doi="10.1000/ABC")

        answer = search(client, "publication", None, q="10.1000/abc")

        assert [r["id"] for r in answer["results"]] == [exact.pk, mentioned.pk]

    def test_a_doi_typed_as_an_address_finds_the_publication(
        self, client, make_publication
    ):
        wanted = make_publication("Some title", doi="10.1000/abc")

        answer = search(client, "publication", None, q="https://doi.org/10.1000/abc")

        assert [r["id"] for r in answer["results"]] == [wanted.pk]

    def test_a_doi_typed_in_part_finds_nothing(self, client, make_publication):
        make_publication("Some title", doi="10.1000/abcdef")

        assert search(client, "publication", None, q="10.1000/abc")["results"] == []

    def test_a_result_gives_the_authors_the_year_and_the_doi(
        self, client, make_publication
    ):
        make_publication(
            "Basalt",
            authors=[("Lovelace", "Ada"), ("Babbage", "Charles")],
            doi="10.1000/abc",
            year=2021,
        )

        row = search(client, "publication", None)["results"][0]

        assert row["authors"] == "Lovelace, Babbage"
        assert row["year"] == 2021
        assert row["doi"] == "10.1000/abc"
        assert "item" not in row

    def test_a_publication_with_no_authors_year_or_doi_still_has_a_row(
        self, client, make_publication
    ):
        make_publication("Bare")

        row = search(client, "publication", None)["results"][0]

        assert row["title"] == "Bare"
        assert row["authors"] == ""
        assert row["year"] is None
        assert row["doi"] == ""


@pytest.mark.django_db
class TestNewViewsTakeTheLimits:
    @pytest.mark.parametrize("name", ["publication"])
    def test_each_new_address_refuses_a_caller_over_the_burst_rate(
        self, client, settings, monkeypatch, name
    ):
        from django.core.cache.backends.locmem import LocMemCache
        from rest_framework.throttling import SimpleRateThrottle

        from fairdm.contrib.contributors.services.registries import Ror

        monkeypatch.setattr(
            Ror, "search", lambda self, term: {"results": [], "more": False}
        )
        cache = LocMemCache(f"limits-{name}", {})
        cache.clear()
        monkeypatch.setattr(SimpleRateThrottle, "cache", cache)
        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        monkeypatch.setitem(rates, "autocomplete_anon_burst", "2/minute")

        answers = [
            client.get(reverse(f"autocomplete:{name}")).status_code for _ in range(4)
        ]

        assert answers[-1] == 429
        assert 429 not in answers[:2]

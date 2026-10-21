"""Tests for the autocomplete views, called through their real addresses."""

import pytest
from django.urls import reverse

from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.utils.choices import Visibility


def search(client, kind, scope, **params):
    """Return the decoded answer of one kind's address at one scope."""
    response = client.get(reverse(f"autocomplete:{kind}-{scope}"), params)
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

"""Tests for the ORCID and ROR lookups, with ``requests.get`` replaced.

The replaced responses are trimmed copies of what each endpoint returned when recorded, kept in
``recorded/`` beside the contributor tests. Nothing here reaches the network.
"""

import copy

import pytest
import requests

from fairdm.contrib.contributors.choices import AccountState
from fairdm.contrib.contributors.models import (
    ContributorIdentifier,
    Organization,
    Person,
)
from fairdm.contrib.contributors.services.registries import (
    Orcid,
    RegistryUnavailable,
    Ror,
)
from fairdm.factories import (
    ContributorIdentifierFactory,
    OrganizationFactory,
    PersonFactory,
)

ORCID_SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"
ROR_SEARCH = "https://api.ror.org/v2/organizations"
JOSIAH = "0000-0002-1825-0097"
GFZ = "04z8jg394"
NOT_REACHED = [
    pytest.param(requests.Timeout("slow"), 200, id="timeout"),
    pytest.param(requests.ConnectionError("down"), 200, id="connection-error"),
    pytest.param(None, 500, id="server-error"),
    pytest.param(None, 429, id="rate-limited"),
]


def orcid_record_address(orcid_id):
    return f"https://pub.orcid.org/v3.0/{orcid_id}/record"


def ror_record_address(ror_id):
    return f"https://api.ror.org/v2/organizations/{ror_id}"


def make_unreachable(network, address, error, status):
    """Make the address fail the way a registry that cannot be reached would."""
    if error is not None:
        network.fail(address, error)
    else:
        network.answer(address, {"errors": ["Service unavailable"]}, status=status)


@pytest.mark.django_db
class TestSearchOrcid:
    def test_a_name_returns_what_the_template_reads(self, registry_network, recorded):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))

        found = Orcid().search("Carberry")

        results = found["results"]
        assert [r["id"] for r in results] == [
            "0000-0002-1825-0097",
            "0000-0002-9770-3460",
            "0000-0001-8121-2010",
        ]
        josiah = results[0]
        assert josiah["shown_id"] == JOSIAH
        assert josiah["name"] == "Josiah Carberry"
        assert (josiah["given"], josiah["family"]) == ("Josiah", "Carberry")
        assert josiah["employer"] == "Brown University"
        assert "Brown University" in josiah["detail"]
        assert results[2]["employer"] == ""
        assert results[2]["detail"]

    def test_the_term_goes_in_the_parameters_with_a_limit_and_a_timeout(
        self, registry_network, recorded
    ):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))

        Orcid().search("Carberry & rows=1000")

        (call,) = registry_network.calls
        assert call.url == ORCID_SEARCH
        assert call.params["q"] == "Carberry & rows=1000"
        assert 0 < call.params["rows"] <= 25
        assert call.headers["Accept"] == "application/json"
        assert call.timeout == 5

    def test_an_orcid_id_searches_by_identifier(self, registry_network, recorded):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search-by-id"))

        found = Orcid().search(JOSIAH)

        assert registry_network.calls[0].params["q"] == f"orcid:{JOSIAH}"
        assert [r["id"] for r in found["results"]] == [JOSIAH]
        assert found["more"] is False

    def test_an_orcid_address_searches_by_identifier(self, registry_network, recorded):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search-by-id"))

        Orcid().search(f" https://orcid.org/{JOSIAH} ")

        assert registry_network.calls[0].params["q"] == f"orcid:{JOSIAH}"

    def test_part_of_an_identifier_searches_by_name(self, registry_network, recorded):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))

        Orcid().search("0000-0002-1825")

        assert registry_network.calls[0].params["q"] == "0000-0002-1825"

    def test_a_record_with_no_public_name_is_left_out(self, registry_network, recorded):
        body = recorded("orcid-search")
        body["expanded-result"][1]["given-names"] = None
        body["expanded-result"][1]["family-names"] = None
        registry_network.answer(ORCID_SEARCH, body)

        found = Orcid().search("Carberry")

        assert [r["id"] for r in found["results"]] == [
            "0000-0002-1825-0097",
            "0000-0001-8121-2010",
        ]

    def test_a_person_with_only_a_given_name_can_be_chosen(
        self, registry_network, recorded
    ):
        body = recorded("orcid-search")
        body["expanded-result"][2]["family-names"] = None
        registry_network.answer(ORCID_SEARCH, body)

        found = Orcid().search("Trent")

        trent = found["results"][2]
        assert (trent["given"], trent["family"], trent["name"]) == (
            "Trent",
            "",
            "Trent",
        )

    def test_nothing_found_gives_no_results_and_no_flag(self, registry_network):
        registry_network.answer(ORCID_SEARCH, {"expanded-result": None, "num-found": 0})

        found = Orcid().search("Nobody")

        assert found == {"results": [], "more": False}

    def test_more_matches_than_are_returned_set_the_flag(
        self, registry_network, recorded
    ):
        registry_network.answer(ORCID_SEARCH, recorded("orcid-search"))

        found = Orcid().search("Carberry")

        assert len(found["results"]) == 3
        assert found["more"] is True

    def test_every_match_returned_leaves_the_flag_down(
        self, registry_network, recorded
    ):
        body = recorded("orcid-search")
        body["num-found"] = 3
        registry_network.answer(ORCID_SEARCH, body)

        assert Orcid().search("Carberry")["more"] is False

    def test_a_registry_that_returns_more_than_the_limit_is_cut_at_the_limit(
        self, registry_network, recorded
    ):
        body = recorded("orcid-search")
        body["expanded-result"] = body["expanded-result"] * 10
        body["num-found"] = 30
        registry_network.answer(ORCID_SEARCH, body)

        found = Orcid().search("Carberry")

        assert len(found["results"]) <= registry_network.calls[0].params["rows"]
        assert found["more"] is True

    @pytest.mark.parametrize(("error", "status"), NOT_REACHED)
    def test_a_registry_that_cannot_be_reached_raises(
        self, registry_network, error, status
    ):
        make_unreachable(registry_network, ORCID_SEARCH, error, status)

        with pytest.raises(RegistryUnavailable):
            Orcid().search("Carberry")

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(ValueError("not json"), id="not-json"),
            pytest.param(["not", "an", "object"], id="a-list"),
            pytest.param({"unexpected": True}, id="unexpected-keys"),
            pytest.param({"expanded-result": [None], "num-found": 1}, id="null-entry"),
        ],
    )
    def test_an_answer_that_cannot_be_read_raises(self, registry_network, body):
        registry_network.answer(ORCID_SEARCH, body)

        with pytest.raises(RegistryUnavailable):
            Orcid().search("Carberry")


@pytest.mark.django_db
class TestFetchOrcid:
    def test_a_record_is_fetched_by_identifier(self, registry_network, recorded):
        registry_network.answer(orcid_record_address(JOSIAH), recorded("orcid-record"))

        record = Orcid().fetch(JOSIAH)

        (call,) = registry_network.calls
        assert call.url == orcid_record_address(JOSIAH)
        assert call.headers["Accept"] == "application/json"
        assert call.timeout == 5
        assert record["id"] == JOSIAH
        assert record["shown_id"] == JOSIAH
        assert record["name"] == "Josiah Carberry"
        assert (record["given"], record["family"]) == ("Josiah", "Carberry")
        assert record["employer"] in {"Brown University", "Wesleyan University"}
        assert record["employer"] in record["detail"]

    def test_an_orcid_address_is_taken_for_its_identifier(
        self, registry_network, recorded
    ):
        registry_network.answer(orcid_record_address(JOSIAH), recorded("orcid-record"))

        record = Orcid().fetch(f"https://orcid.org/{JOSIAH}")

        assert record["id"] == JOSIAH

    def test_a_record_with_no_current_employment_has_no_employer(
        self, registry_network, recorded
    ):
        body = recorded("orcid-record")
        for group in body["activities-summary"]["employments"]["affiliation-group"]:
            for summary in group["summaries"]:
                summary["employment-summary"]["end-date"] = {
                    "year": {"value": "1990"}
                }
        registry_network.answer(orcid_record_address(JOSIAH), body)

        record = Orcid().fetch(JOSIAH)

        assert record["employer"] == ""
        assert record["detail"]

    @pytest.mark.parametrize(
        "identifier",
        [
            "",
            "Josiah Carberry",
            "0000-0002-1825-009",
            "0000-0002-1825-00977",
            "0000-0002-1825-009Y",
            f"{JOSIAH}/../0000-0001-5109-3700",
            f"{JOSIAH}?x=1",
            f"{JOSIAH}\n",
            f"https://evil.example/{JOSIAH}",
            f"../{JOSIAH}",
        ],
    )
    def test_a_malformed_identifier_makes_no_request(
        self, registry_network, identifier
    ):
        record = Orcid().fetch(identifier)

        assert record is None
        assert registry_network.calls == []

    def test_an_identifier_ending_in_x_is_well_formed(self, registry_network, recorded):
        body = recorded("orcid-record")
        registry_network.answer(orcid_record_address("0000-0002-9079-593X"), body)

        Orcid().fetch("0000-0002-9079-593X")

        assert len(registry_network.calls) == 1

    def test_an_identifier_orcid_does_not_know_gives_nothing(self, registry_network):
        registry_network.answer(
            orcid_record_address(JOSIAH), {"error": "not found"}, status=404
        )

        assert Orcid().fetch(JOSIAH) is None

    def test_a_record_with_no_public_name_gives_nothing(
        self, registry_network, recorded
    ):
        body = recorded("orcid-record")
        body["person"]["name"] = None
        registry_network.answer(orcid_record_address(JOSIAH), body)

        assert Orcid().fetch(JOSIAH) is None

    @pytest.mark.parametrize(("error", "status"), NOT_REACHED)
    def test_a_registry_that_cannot_be_reached_raises(
        self, registry_network, error, status
    ):
        make_unreachable(registry_network, orcid_record_address(JOSIAH), error, status)

        with pytest.raises(RegistryUnavailable):
            Orcid().fetch(JOSIAH)

    def test_an_answer_that_cannot_be_read_raises(self, registry_network):
        registry_network.answer(orcid_record_address(JOSIAH), ["not", "a", "record"])

        with pytest.raises(RegistryUnavailable):
            Orcid().fetch(JOSIAH)


@pytest.mark.django_db
class TestSearchRor:
    def test_a_name_returns_what_the_template_reads(self, registry_network, recorded):
        registry_network.answer(ROR_SEARCH, recorded("ror-search"))

        found = Ror().search("Potsdam")

        results = found["results"]
        assert [r["id"] for r in results] == [
            "https://ror.org/04z8jg394",
            "https://ror.org/032qgrc76",
            "https://ror.org/017bbsh25",
            "https://ror.org/03e8s1d88",
            "https://ror.org/03bnmw459",
        ]
        gfz = results[0]
        assert gfz["shown_id"] == "ror.org/04z8jg394"
        assert gfz["name"] == "GFZ Helmholtz Centre for Geosciences"
        assert "Potsdam" in gfz["detail"]
        assert "Germany" in gfz["detail"]
        assert results[1]["name"] == "State University of New York at Potsdam"
        assert "Berlin" in results[2]["detail"]

    def test_the_term_goes_in_the_parameters_with_a_timeout(
        self, registry_network, recorded
    ):
        registry_network.answer(ROR_SEARCH, recorded("ror-search"))

        Ror().search("Potsdam/../04z8jg394?x=1")

        (call,) = registry_network.calls
        assert call.url == ROR_SEARCH
        assert call.params["query"] == "Potsdam/../04z8jg394?x=1"
        assert call.timeout == 5

    @pytest.mark.parametrize(
        "term", [GFZ, f"https://ror.org/{GFZ}", f" https://ror.org/{GFZ} "]
    )
    def test_a_ror_id_searches_by_identifier(self, registry_network, recorded, term):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))

        found = Ror().search(term)

        assert [call.url for call in registry_network.calls] == [ror_record_address(GFZ)]
        assert [r["id"] for r in found["results"]] == [f"https://ror.org/{GFZ}"]
        assert found["more"] is False

    def test_a_ror_id_nobody_holds_finds_nothing(self, registry_network, recorded):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-missing"), 404)

        assert Ror().search(GFZ) == {"results": [], "more": False}

    def test_a_withdrawn_organization_is_left_out(self, registry_network, recorded):
        body = recorded("ror-search")
        body["items"][1]["status"] = "withdrawn"
        body["items"][2]["status"] = "inactive"
        registry_network.answer(ROR_SEARCH, body)

        found = Ror().search("Potsdam")

        assert [r["id"] for r in found["results"]] == [
            "https://ror.org/04z8jg394",
            "https://ror.org/03e8s1d88",
            "https://ror.org/03bnmw459",
        ]

    def test_a_withdrawn_organization_found_by_its_id_is_left_out(
        self, registry_network, recorded
    ):
        body = recorded("ror-record")
        body["status"] = "withdrawn"
        registry_network.answer(ror_record_address(GFZ), body)

        assert Ror().search(GFZ)["results"] == []

    def test_an_organization_with_no_display_name_is_left_out(
        self, registry_network, recorded
    ):
        body = recorded("ror-search")
        for name in body["items"][0]["names"]:
            name["types"] = [t for t in name["types"] if t != "ror_display"]
        registry_network.answer(ROR_SEARCH, body)

        found = Ror().search("Potsdam")

        assert "https://ror.org/04z8jg394" not in [r["id"] for r in found["results"]]

    def test_more_matches_than_are_returned_set_the_flag(
        self, registry_network, recorded
    ):
        body = recorded("ror-search")
        body["number_of_results"] = 214
        registry_network.answer(ROR_SEARCH, body)

        assert Ror().search("Potsdam")["more"] is True

    def test_every_match_returned_leaves_the_flag_down(
        self, registry_network, recorded
    ):
        registry_network.answer(ROR_SEARCH, recorded("ror-search"))

        assert Ror().search("Potsdam")["more"] is False

    def test_a_page_longer_than_the_limit_is_cut_and_sets_the_flag(
        self, registry_network, recorded
    ):
        body = recorded("ror-search")
        body["items"] = [copy.deepcopy(body["items"][0]) for _ in range(30)]
        body["number_of_results"] = 30
        registry_network.answer(ROR_SEARCH, body)

        found = Ror().search("Potsdam")

        assert 0 < len(found["results"]) < 30
        assert found["more"] is True

    @pytest.mark.parametrize(("error", "status"), NOT_REACHED)
    def test_a_registry_that_cannot_be_reached_raises(
        self, registry_network, error, status
    ):
        make_unreachable(registry_network, ROR_SEARCH, error, status)

        with pytest.raises(RegistryUnavailable):
            Ror().search("Potsdam")

    @pytest.mark.parametrize(("error", "status"), NOT_REACHED)
    def test_a_registry_that_cannot_be_reached_raises_when_searching_by_id(
        self, registry_network, error, status
    ):
        make_unreachable(registry_network, ror_record_address(GFZ), error, status)

        with pytest.raises(RegistryUnavailable):
            Ror().search(GFZ)

    @pytest.mark.parametrize(
        "body",
        [
            pytest.param(ValueError("not json"), id="not-json"),
            pytest.param(["not", "an", "object"], id="a-list"),
            pytest.param({"unexpected": True}, id="unexpected-keys"),
        ],
    )
    def test_an_answer_that_cannot_be_read_raises(self, registry_network, body):
        registry_network.answer(ROR_SEARCH, body)

        with pytest.raises(RegistryUnavailable):
            Ror().search("Potsdam")


@pytest.mark.django_db
class TestFetchRor:
    def test_a_record_is_fetched_by_identifier(self, registry_network, recorded):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))

        record = Ror().fetch(GFZ)

        (call,) = registry_network.calls
        assert call.url == ror_record_address(GFZ)
        assert call.timeout == 5
        assert record["id"] == f"https://ror.org/{GFZ}"
        assert record["shown_id"] == f"ror.org/{GFZ}"
        assert record["name"] == "GFZ Helmholtz Centre for Geosciences"

    def test_a_ror_address_is_taken_for_its_identifier(
        self, registry_network, recorded
    ):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))

        record = Ror().fetch(f"https://ror.org/{GFZ}")

        assert record["id"] == f"https://ror.org/{GFZ}"

    @pytest.mark.parametrize(
        "identifier",
        [
            "",
            "GFZ Helmholtz",
            "00000000x",
            "04z8jg39",
            "04z8jg3944",
            "14z8jg394",
            f"{GFZ}/../00xewv188",
            f"{GFZ}?x=1",
            f"https://evil.example/{GFZ}",
            f"https://ror.org/{GFZ}/extra",
            f"../{GFZ}",
        ],
    )
    def test_a_malformed_identifier_makes_no_request(
        self, registry_network, identifier
    ):
        record = Ror().fetch(identifier)

        assert record is None
        assert registry_network.calls == []

    def test_an_identifier_ror_does_not_know_gives_nothing(
        self, registry_network, recorded
    ):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-missing"), 404)

        assert Ror().fetch(GFZ) is None

    def test_a_withdrawn_organization_gives_nothing(self, registry_network, recorded):
        body = recorded("ror-record")
        body["status"] = "withdrawn"
        registry_network.answer(ror_record_address(GFZ), body)

        assert Ror().fetch(GFZ) is None

    @pytest.mark.parametrize(("error", "status"), NOT_REACHED)
    def test_a_registry_that_cannot_be_reached_raises(
        self, registry_network, error, status
    ):
        make_unreachable(registry_network, ror_record_address(GFZ), error, status)

        with pytest.raises(RegistryUnavailable):
            Ror().fetch(GFZ)


@pytest.mark.django_db
class TestProfileFromRegistry:
    @pytest.fixture
    def orcid_record(self, registry_network, recorded):
        registry_network.answer(orcid_record_address(JOSIAH), recorded("orcid-record"))
        return Orcid().fetch(JOSIAH)

    @pytest.fixture
    def ror_record(self, registry_network, recorded):
        registry_network.answer(ror_record_address(GFZ), recorded("ror-record"))
        return Ror().fetch(GFZ)

    def test_a_person_is_made_with_their_name_and_orcid_id_and_no_account(
        self, orcid_record
    ):
        person = Orcid().profile(orcid_record)

        person.refresh_from_db()
        assert isinstance(person, Person)
        assert (person.first_name, person.last_name) == ("Josiah", "Carberry")
        assert person.name == "Josiah Carberry"
        assert person.identifiers.get(type="ORCID").value == JOSIAH
        assert person.email is None
        assert not person.has_usable_password()
        assert person.account_state == AccountState.GHOST
        assert not person.can_sign_in()
        assert not person.socialaccount_set.exists()

    def test_the_person_the_portal_already_holds_under_the_id_is_returned(
        self, orcid_record
    ):
        held = PersonFactory(name="J. Carberry")
        ContributorIdentifierFactory(related=held, type="ORCID", value=JOSIAH)
        people, identifiers = Person.objects.count(), ContributorIdentifier.objects.count()

        person = Orcid().profile(orcid_record)

        assert person.pk == held.pk
        assert Person.objects.count() == people
        assert ContributorIdentifier.objects.count() == identifiers

    def test_a_namesake_without_the_id_is_not_taken_for_them(self, orcid_record):
        namesake = PersonFactory(first_name="Josiah", last_name="Carberry")

        person = Orcid().profile(orcid_record)

        assert person.pk != namesake.pk
        assert not namesake.identifiers.exists()

    def test_the_same_record_twice_makes_one_person(self, orcid_record):
        first = Orcid().profile(orcid_record)
        second = Orcid().profile(orcid_record)

        assert first.pk == second.pk
        assert Person.objects.filter(identifiers__value=JOSIAH).count() == 1

    def test_an_organization_is_made_with_its_name_and_ror_id(self, ror_record):
        organization = Ror().profile(ror_record)

        organization.refresh_from_db()
        assert isinstance(organization, Organization)
        assert organization.name == "GFZ Helmholtz Centre for Geosciences"
        assert organization.identifiers.get(type="ROR").value == GFZ

    @pytest.mark.parametrize("stored", [GFZ, f"https://ror.org/{GFZ}"])
    def test_the_organization_the_portal_already_holds_under_the_id_is_returned(
        self, ror_record, stored
    ):
        held = OrganizationFactory(name="GFZ Potsdam")
        ContributorIdentifierFactory(related=held, type="ROR", value=stored)
        count = Organization.objects.count()

        organization = Ror().profile(ror_record)

        assert organization.pk == held.pk
        assert Organization.objects.count() == count

    def test_an_organization_with_the_same_name_but_no_id_is_not_taken_for_it(
        self, ror_record
    ):
        namesake = OrganizationFactory(name="GFZ Helmholtz Centre for Geosciences")

        organization = Ror().profile(ror_record)

        assert organization.pk != namesake.pk

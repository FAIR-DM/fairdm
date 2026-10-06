"""Look people up in ORCID and organizations up in ROR, and make profiles from what is found."""

import re

import requests
from django.db import transaction
from django.utils.translation import gettext as _
from django_countries import countries

from ..choices import OrganizationType
from ..models import (
    ORCID_PATTERN,
    ROR_PATTERN,
    ContributorIdentifier,
    Organization,
    Person,
)
from ..utils.transforms import RORTransform

RESULTS_SHOWN = 10
"""The most matches a search returns."""

TIMEOUT = 5
"""The seconds a registry has to answer."""

JSON = {"Accept": "application/json"}


class RegistryUnavailable(Exception):
    """Signal that a registry could not be asked or its answer could not be read.

    Raised for a network error, a timeout, an answer that is not a success and an answer that is
    not in the form the registry documents.
    """


def ask(address, parse, *, params=None, headers=None, missing_ok=False):
    """Request an address from a registry and read its answer.

    Args:
        address: The address, which no search term is ever part of.
        parse: A function that turns the decoded answer into what the caller wants.
        params: Query parameters, which ``requests`` encodes.
        headers: Request headers.
        missing_ok: Whether a 404 is an answer ("there is no such record") rather than a failure.

    Returns:
        What ``parse`` returns, or None for a 404 when ``missing_ok`` is true.

    Raises:
        RegistryUnavailable: The request failed, the answer was not a 200, or ``parse`` could not
            read it.
    """
    try:
        response = requests.get(
            address, params=params, headers=headers, timeout=TIMEOUT
        )
    except requests.RequestException as error:
        raise RegistryUnavailable(f"{address} could not be reached") from error
    if missing_ok and response.status_code == 404:
        return None
    if response.status_code != 200:
        raise RegistryUnavailable(f"{address} answered {response.status_code}")
    try:
        return parse(response.json())
    except (ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
        raise RegistryUnavailable(
            f"{address} answered in an unexpected form"
        ) from error


class Orcid:
    """Search ORCID for people, fetch one record, and make a profile from it.

    A record is a dictionary with ``id`` and ``shown_id`` (the ORCID iD), ``name``, ``given``,
    ``family``, ``employer`` (the first current employer, or an empty string) and ``detail``
    (what tells namesakes apart).
    """

    SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"
    RECORD = "https://pub.orcid.org/v3.0/{}/record"

    def identifier_in(self, text):
        """Pick an ORCID iD out of text that is one, or an address of one.

        Args:
            text: A search term or an identifier.

        Returns:
            The bare iD, or None when the text is not in the form of one.
        """
        candidate = text.removeprefix("https://orcid.org/")
        return candidate if re.fullmatch(ORCID_PATTERN, candidate) else None

    def search(self, term):
        """Search by name, or by iD when the term is one.

        Args:
            term: A name, an ORCID iD or the address of one.

        Returns:
            ``{"results": [...], "more": bool}``: at most ``RESULTS_SHOWN`` records of people with
            a public name, and whether the registry holds more matches than that.

        Raises:
            RegistryUnavailable: ORCID could not be asked or answered badly.
        """
        term = term.strip()
        identifier = self.identifier_in(term)
        query = f"orcid:{identifier}" if identifier else term
        return ask(
            self.SEARCH,
            self.results_from,
            params={"q": query, "rows": RESULTS_SHOWN},
            headers=JSON,
        )

    def results_from(self, body):
        """Read a search answer, leaving out records with no public name.

        Args:
            body: The decoded answer of the search.

        Returns:
            The results and the flag, as ``search`` returns them.
        """
        found = body["expanded-result"] or []
        records = [r for r in map(self.found_in, found) if r is not None]
        return {
            "results": records[:RESULTS_SHOWN],
            "more": body["num-found"] > len(found) or len(records) > RESULTS_SHOWN,
        }

    def found_in(self, entry):
        """Shape one search result.

        Args:
            entry: One item of the answer's ``expanded-result``.

        Returns:
            The record, or None when the person has no public name.
        """
        given, family = entry.get("given-names") or "", entry.get("family-names") or ""
        employers = entry.get("institution-name") or []
        return self.record_of(
            entry["orcid-id"], given, family, employers[0] if employers else ""
        )

    def record_of(self, orcid_id, given, family, employer, place=""):
        """Shape a person for the templates, or return None when there is no name.

        Args:
            orcid_id: The bare ORCID iD.
            given: The given names, possibly empty.
            family: The family name, possibly empty.
            employer: The name of the current employer, possibly empty.
            place: Where the employer is, possibly empty.

        Returns:
            The record, or None when both names are empty.
        """
        if not (given.strip() or family.strip()):
            return None
        return {
            "id": orcid_id,
            "shown_id": orcid_id,
            "name": f"{given} {family}".strip(),
            "given": given,
            "family": family,
            "employer": employer,
            "detail": ", ".join(filter(None, [employer, place]))
            or _("No current employment listed"),
        }

    def fetch(self, identifier):
        """Fetch one person's public record.

        An identifier that is not in the form of an ORCID iD is refused before any request is
        made.

        Args:
            identifier: The bare ORCID iD, or its address.

        Returns:
            The record, or None when the identifier is malformed, ORCID has no such record, or
            the record has no public name.

        Raises:
            RegistryUnavailable: ORCID could not be asked or answered badly.
        """
        orcid_id = self.identifier_in(identifier)
        if orcid_id is None:
            return None
        return ask(
            self.RECORD.format(orcid_id),
            lambda body: self.read_record(orcid_id, body),
            headers=JSON,
            missing_ok=True,
        )

    def read_record(self, orcid_id, body):
        """Read a record answer: the public name and the first current employer.

        Args:
            orcid_id: The iD that was asked for.
            body: The decoded answer.

        Returns:
            The record, or None when the person has no public name.
        """
        name = body["person"]["name"]
        if not name:
            return None
        given = (name.get("given-names") or {}).get("value", "")
        family = (name.get("family-name") or {}).get("value", "")
        employments = (body.get("activities-summary") or {}).get("employments") or {}
        for group in employments.get("affiliation-group") or []:
            for summary in group["summaries"]:
                employment = summary["employment-summary"]
                if employment.get("end-date") is None:
                    organization = employment["organization"]
                    address = organization.get("address") or {}
                    return self.record_of(
                        orcid_id,
                        given,
                        family,
                        organization["name"],
                        ", ".join(
                            filter(
                                None,
                                [
                                    address.get("city"),
                                    countries.name(address.get("country") or ""),
                                ],
                            )
                        ),
                    )
        return self.record_of(orcid_id, given, family, "")

    def known(self, record):
        """Find the person the portal already holds under the record's ORCID iD.

        Args:
            record: A record from ``search`` or ``fetch``.

        Returns:
            The person, or None.
        """
        held = (
            ContributorIdentifier.objects.filter(type="ORCID", value=record["id"])
            .select_related("related")
            .first()
        )
        return held.related.get_real_instance() if held else None

    def profile(self, record):
        """Return the person the portal holds under the iD, or make one.

        A person made here has the name and the iD, no email address, an unusable password and
        no account.

        Args:
            record: A record from ``search`` or ``fetch``.

        Returns:
            The person.
        """
        with transaction.atomic():
            person = self.known(record)
            if person is None:
                person = Person.objects.create_unclaimed(
                    record["given"], record["family"], name=record["name"]
                )
                person.identifiers.create(type="ORCID", value=record["id"])
            return person


class Ror:
    """Search ROR for organizations, fetch one record, and make a profile from it.

    A record is a dictionary with ``id`` (the ROR address), ``shown_id`` (the address without its
    scheme), ``name`` (ROR's display name) and ``detail`` (its kind and where it is).
    """

    SEARCH = "https://api.ror.org/v2/organizations"
    RECORD = "https://api.ror.org/v2/organizations/{}"

    def identifier_in(self, text):
        """Pick a ROR ID out of text that is one, or an address of one.

        Args:
            text: A search term or an identifier.

        Returns:
            The bare ID, or None when the text is not in the form of one.
        """
        candidate = RORTransform.clean_ror_id(text)
        return candidate if re.fullmatch(ROR_PATTERN, candidate) else None

    def search(self, term):
        """Search by name, or by ID when the term is one.

        Args:
            term: A name, a ROR ID or the address of one.

        Returns:
            ``{"results": [...], "more": bool}``: at most ``RESULTS_SHOWN`` active organizations,
            and whether the registry holds more matches than that.

        Raises:
            RegistryUnavailable: ROR could not be asked or answered badly.
        """
        term = term.strip()
        if self.identifier_in(term):
            record = self.fetch(term)
            return {"results": [record] if record else [], "more": False}
        return ask(self.SEARCH, self.results_from, params={"query": term})

    def results_from(self, body):
        """Read a search answer, leaving out organizations that are not active.

        Args:
            body: The decoded answer of the search.

        Returns:
            The results and the flag, as ``search`` returns them.
        """
        items = body["items"]
        records = [r for r in map(self.record_of, items) if r is not None]
        return {
            "results": records[:RESULTS_SHOWN],
            "more": body["number_of_results"] > len(items)
            or len(records) > RESULTS_SHOWN,
        }

    def record_of(self, item):
        """Shape one organization for the templates, or return None when it cannot be chosen.

        Args:
            item: An organization as ROR describes it.

        Returns:
            The record, or None when the organization is not active or has no display name.
        """
        name = next(
            (n["value"] for n in item["names"] if "ror_display" in n["types"]), None
        )
        ror_id = item["id"]
        if item["status"] != "active" or not name or not self.identifier_in(ror_id):
            return None
        kinds = dict(OrganizationType.choices)
        first = (item.get("types") or [""])[0]
        kind = str(kinds.get(first, first.capitalize()))
        place = (item.get("locations") or [{}])[0].get("geonames_details") or {}
        where = ", ".join(filter(None, [place.get("name"), place.get("country_name")]))
        return {
            "id": ror_id,
            "shown_id": ror_id.removeprefix("https://"),
            "name": name,
            "detail": " · ".join(filter(None, [kind, where])),
        }

    def fetch(self, identifier):
        """Fetch one organization's record.

        An identifier that is not in the form of a ROR ID is refused before any request is made.

        Args:
            identifier: The bare ROR ID, or its address.

        Returns:
            The record, or None when the identifier is malformed, ROR has no such record, or the
            organization is not active.

        Raises:
            RegistryUnavailable: ROR could not be asked or answered badly.
        """
        ror_id = self.identifier_in(identifier)
        if ror_id is None:
            return None
        return ask(self.RECORD.format(ror_id), self.record_of, missing_ok=True)

    def known(self, record):
        """Find the organization the portal already holds under the record's ROR ID.

        Args:
            record: A record from ``search`` or ``fetch``.

        Returns:
            The organization, or None.
        """
        ror_id = self.identifier_in(record["id"])
        held = (
            ContributorIdentifier.objects.filter(
                type="ROR", value__in=[ror_id, f"https://ror.org/{ror_id}"]
            )
            .select_related("related")
            .first()
        )
        return held.related.get_real_instance() if held else None

    def profile(self, record):
        """Return the organization the portal holds under the ID, or make one.

        An organization made here has the name and the ID.

        Args:
            record: A record from ``search`` or ``fetch``.

        Returns:
            The organization.
        """
        with transaction.atomic():
            organization = self.known(record)
            if organization is None:
                organization = Organization.objects.create(name=record["name"])
                organization.identifiers.create(
                    type="ROR", value=self.identifier_in(record["id"])
                )
            return organization

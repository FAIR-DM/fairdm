"""Look people up in ORCID and organizations up in ROR, and make profiles from what is
found.
"""

import hashlib
import re
from email.utils import parsedate_to_datetime

import requests
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django_countries import countries

from fairdm.core.vocabularies import ORCID, ROR

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

KEPT = 300
"""The seconds an answer is kept, so that a repeated lookup asks the registry once."""

JSON = {"Accept": "application/json"}

SEARCHES_PER_MINUTE = 60
"""The most registry searches one person may make in a minute."""


FETCH_TIMEOUT = 10
"""The seconds a registry has to answer a fetch of one record for a profile."""


class RegistryRateLimited(requests.RequestException):
    """Signal that a registry answered 429 and asked for no requests for a while.

    Attributes:
        retry_after: The seconds the registry asked to wait, or None when it did not
            say.
    """

    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


def seconds_to_wait(retry_after):
    """Read a ``Retry-After`` header, which is a number of seconds or an HTTP date.

    Args:
        retry_after: The header's value, or None when it was not sent.

    Returns:
        The whole seconds to wait, never negative, or None when the value says nothing.
    """
    if not retry_after:
        return None
    if retry_after.strip().isdigit():
        return int(retry_after)
    try:
        until = parsedate_to_datetime(retry_after)
    except (TypeError, ValueError):
        return None
    return max(0, int((until - timezone.now()).total_seconds()))


def fetch_record(address, headers=None):
    """Fetch one registry record for a profile, uncached, as the sync and the transforms
    do.

    Every fetch of a record to store on a profile goes through here, so all of them
    share one timeout and one reading of a refusal. Retrying is the caller's: the sync
    task retries with a growing delay, or after the wait a 429 asks for.

    Args:
        address: The record's address.
        headers: Request headers.

    Returns:
        The decoded record, or None when the registry answers 404.

    Raises:
        RegistryRateLimited: The registry answered 429.
        requests.RequestException: The request failed or the answer was another error.
        ValueError: The answer was not JSON.
    """
    response = requests.get(address, headers=headers, timeout=FETCH_TIMEOUT)
    if response.status_code == 404:
        return None
    if response.status_code == 429:
        raise RegistryRateLimited(
            f"{address} answered 429",
            retry_after=seconds_to_wait(response.headers.get("Retry-After")),
        )
    response.raise_for_status()
    return response.json()


class RegistryUnavailable(Exception):
    """Signal that a registry could not be asked or its answer could not be read.

    Raised for a network error, a timeout, an answer that is not a success and an answer
    that is not in the form the registry documents.
    """


class SearchLimitReached(RegistryUnavailable):
    """Signal that a person has searched the registries more often than they may in a
    minute.
    """


def count_search(user):
    """Count one registry search against a person, refusing it past the limit.

    The count is kept in the default cache for the minute it began in, so it is shared
    by every process and forgotten after a minute.

    Args:
        user: The signed-in person searching.

    Raises:
        SearchLimitReached: The person has made ``SEARCHES_PER_MINUTE`` searches this
            minute.
    """
    key = f"fairdm:registry-searches:{user.pk}"
    cache.add(key, 0, 60)
    try:
        used = cache.incr(key)
    except ValueError:
        return  # A cache that keeps nothing cannot count.
    if used > SEARCHES_PER_MINUTE:
        raise SearchLimitReached(f"{user.pk} searched too often")


def ask(address, parse, *, params=None, headers=None, missing_ok=False):
    """Request an address from a registry and read its answer, unless it is kept.

    What a registry answers is kept for ``KEPT`` seconds in the default cache, under
    the address, the parameters and the active language, since an answer is read into
    text in that language. "There is no such record" is an answer and is kept. A
    failure is not, so the next request asks again.

    Args:
        address: The address, which no search term is ever part of.
        parse: A function that turns the decoded answer into what the caller wants.
        params: Query parameters, which ``requests`` encodes.
        headers: Request headers.
        missing_ok: Whether a 404 is an answer ("there is no such record") rather than a
            failure.

    Returns:
        What ``parse`` returns, or None for a 404 when ``missing_ok`` is true.

    Raises:
        RegistryUnavailable: The request failed, the answer was not a 200, or ``parse``
            could not read it.
    """
    asked = repr((address, sorted((params or {}).items()), get_language()))
    key = "fairdm:registry:" + hashlib.sha256(asked.encode()).hexdigest()
    kept = cache.get(key)
    if kept is not None:
        return kept["answer"]
    try:
        response = requests.get(
            address, params=params, headers=headers, timeout=TIMEOUT
        )
    except requests.RequestException as error:
        raise RegistryUnavailable(f"{address} could not be reached") from error
    if missing_ok and response.status_code == 404:
        answer = None
    elif response.status_code != 200:
        raise RegistryUnavailable(f"{address} answered {response.status_code}")
    else:
        try:
            answer = parse(response.json())
        except (ValueError, KeyError, TypeError, AttributeError, IndexError) as error:
            raise RegistryUnavailable(
                f"{address} answered in an unexpected form"
            ) from error
    cache.set(key, {"answer": answer}, KEPT)
    return answer


class Orcid:
    """Search ORCID for people, fetch one record, and make a profile from it.

    A record is a dictionary with ``id`` and ``shown_id`` (the ORCID iD), ``name``,
    ``given``, ``family``, ``employer`` (the first current employer, or an empty string)
    and ``detail`` (what tells namesakes apart).
    """

    SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"
    RECORD = "https://pub.orcid.org/v3.0/{}/record"
    ACTIVITIES = "https://pub.orcid.org/v3.0/{}/activities"

    def identifier_in(self, text):
        """Pick an ORCID iD out of text that is one, or an address of one.

        Args:
            text: A search term or an identifier.

        Returns:
            The bare iD, or None when the text is not in the form of one.
        """
        candidate = text.removeprefix("https://orcid.org/")
        return candidate if re.fullmatch(ORCID_PATTERN, candidate) else None

    @staticmethod
    def words_of(text):
        """Return the words of a name or an organization, with nothing ORCID's query
        language reads.

        Args:
            text: A name or an organization.
        """
        return [w for w in re.sub(r"[^\w'\-.]+", " ", text).split() if w.strip("-.'")]

    @classmethod
    def all_words(cls, field, words):
        """Return a clause needing every word in ``field``, the last one possibly typed
        in part.

        Args:
            field: The ORCID field to search.
            words: The words the field must contain.
        """
        *whole, last = words
        parts = [f'"{w}"' for w in whole]
        parts.append(f"{last}*" if re.fullmatch(r"\w+", last) else f'"{last}"')
        return f"{field}:({' AND '.join(parts)})"

    def queries_for(self, term, affiliation=""):
        """Return the fielded queries a name search tries in turn, the strictest first.

        ORCID reads a bare term against every field of a record and joins its words with
        OR, so a name alone finds thousands of unrelated people. Each query here asks
        the name fields
        only: first the name as typed, as a phrase, then every word of it in any order
        with the last word as a prefix, so a name still being typed or given family name
        first is found. An affiliation narrows each query to people with an organization
        of that name on their record.

        Args:
            term: The name searched for.
            affiliation: Part of the name of an organization on the person's record.

        Returns:
            The queries, none when the term has no words.
        """
        words = self.words_of(term)
        if not words:
            return []
        narrowed = ""
        if self.words_of(affiliation):
            narrowed = " AND " + self.all_words(
                "affiliation-org-name", self.words_of(affiliation)
            )
        phrase = f'given-and-family-names:"{" ".join(words)}"'
        loose = self.all_words("given-and-family-names", words)
        return [phrase + narrowed, loose + narrowed]

    def search(self, term, affiliation=""):
        """Search by name, or by iD when the term is one.

        Args:
            term: A name, an ORCID iD or the address of one.
            affiliation: Part of the name of an organization on the person's record, to
                narrow a name search.

        Returns:
            ``{"results": [...], "more": bool}``: at most ``RESULTS_SHOWN`` records of
            people with a public name, and whether the registry holds more matches than
            that.

        Raises:
            RegistryUnavailable: ORCID could not be asked or answered badly.
        """
        term = term.strip()
        identifier = self.identifier_in(term)
        queries = (
            [f"orcid:{identifier}"]
            if identifier
            else self.queries_for(term, affiliation)
        )
        found = {"results": [], "more": False}
        for query in queries:
            found = ask(
                self.SEARCH,
                self.results_from,
                params={"q": query, "rows": RESULTS_SHOWN},
                headers=JSON,
            )
            if found["results"]:
                break
        return found

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

        An identifier that is not in the form of an ORCID iD is refused before any
        request is made.

        Args:
            identifier: The bare ORCID iD, or its address.

        Returns:
            The record, or None when the identifier is malformed, ORCID has no such
            record, or the record has no public name.

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
            ContributorIdentifier.objects.filter(type_id=ORCID, value=record["id"])
            .select_related("related")
            .first()
        )
        return held.related.get_real_instance() if held else None

    def profile(self, record):
        """Return the person the portal holds under the iD, or make one.

        A person made here has the name and the iD, no email address, an unusable
        password and no account.

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
                person.identifiers.create(type_id=ORCID, value=record["id"])
            return person

    AFFILIATION_SECTIONS = (
        "employment",
        "education",
        "qualification",
        "invited-position",
        "membership",
        "service",
    )
    """The sections of an ORCID record that name an organization the person belongs or
    belonged to, in the order they are offered when nothing else separates them."""

    def affiliations(self, orcid_id):
        """Return every organization on a person's public ORCID record.

        All the affiliation sections are read, ended ones included, each organization
        once. ORCID identifies an organization by its ROR ID, or by a Funder Registry,
        Ringgold or GRID ID, and the last three are resolved to a ROR ID through ROR.

        Args:
            orcid_id: The bare ORCID iD.

        Returns:
            One dictionary per organization, current ones first, then the most recently
            ended: ``name``, ``ror`` (its ROR ID, or an empty string when none could be
            found) and ``current``. Empty when ORCID could not be reached.
        """
        try:
            found = ask(
                self.ACTIVITIES.format(orcid_id), self.affiliations_from, headers=JSON
            )
        except RegistryUnavailable:
            return []
        rows, seen = [], set()
        for entry in sorted(
            found, key=lambda e: (not e["current"], -e["year"], e["rank"])
        ):
            ror = entry["ror"] or self.ror_for(entry["source"], entry["value"])
            keys = {entry["name"].lower()} | ({ror} if ror else set())
            if keys & seen:
                continue
            seen |= keys
            rows.append(
                {"name": entry["name"], "ror": ror, "current": entry["current"]}
            )
        return rows

    @staticmethod
    def ror_for(source, value):
        """Return the ROR ID of an organization ORCID identifies another way, or an
        empty string.

        Args:
            source: The kind of identifier ORCID gives, such as ``FUNDREF``.
            value: The identifier.
        """
        if not source or not value:
            return ""
        try:
            return Ror().resolve(source, value) or ""
        except RegistryUnavailable:
            return ""

    def affiliations_from(self, body):
        """Read the affiliation sections of an activities answer.

        Args:
            body: The decoded answer.

        Returns:
            One dictionary per entry: ``name``, ``source`` and ``value`` of the
            identifier ORCID gives (``ror`` holds the bare ROR ID itself when that is
            the source), ``current``, the ``year`` it ended and the section's ``rank``.
        """
        found = []
        for rank, section in enumerate(self.AFFILIATION_SECTIONS):
            groups = (body.get(f"{section}s") or {}).get("affiliation-group") or []
            for group in groups:
                for summary in group["summaries"]:
                    entry = summary.get(f"{section}-summary") or {}
                    organization = entry.get("organization") or {}
                    if not organization.get("name"):
                        continue
                    place = organization.get("disambiguated-organization") or {}
                    source = place.get("disambiguation-source") or ""
                    value = place.get("disambiguated-organization-identifier") or ""
                    ended = entry.get("end-date") or {}
                    found.append(
                        {
                            "name": organization["name"],
                            "ror": (Ror().identifier_in(value) or "")
                            if source == "ROR"
                            else "",
                            "source": "" if source == "ROR" else source,
                            "value": "" if source == "ROR" else value,
                            "current": not ended,
                            "year": int(((ended.get("year") or {}).get("value")) or 0),
                            "rank": rank,
                        }
                    )
        return found


class Ror:
    """Search ROR for organizations, fetch one record, and make a profile from it.

    A record is a dictionary with ``id`` (the ROR address), ``shown_id`` (the address
    without its scheme), ``name`` (ROR's display name) and ``detail`` (its kind and
    where it is).
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
            ``{"results": [...], "more": bool}``: at most ``RESULTS_SHOWN`` active
            organizations, and whether the registry holds more matches than that.

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
        """Shape one organization for the templates, or return None when it cannot be
        chosen.

        Args:
            item: An organization as ROR describes it.

        Returns:
            The record, or None when the organization is not active or has no display
            name.
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

        An identifier that is not in the form of a ROR ID is refused before any request
        is made.

        Args:
            identifier: The bare ROR ID, or its address.

        Returns:
            The record, or None when the identifier is malformed, ROR has no such
            record, or the organization is not active.

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
                type_id=ROR, value__in=[ror_id, f"https://ror.org/{ror_id}"]
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
                    type_id=ROR, value=self.identifier_in(record["id"])
                )
            return organization

    EXTERNAL_IDS = {"FUNDREF": "fundref", "GRID": "grid", "RINGGOLD": "ringgold"}
    """The ways ORCID identifies an organization other than by its ROR ID."""

    def resolve(self, source, value):
        """Find the ROR ID of an organization another registry identifies.

        ORCID names many organizations by their Funder Registry, Ringgold or GRID ID.
        ROR lists the identifiers it knows for an organization, so a search on one finds
        it. An identifier that no organization holds, or that several do, finds nothing.

        Args:
            source: The registry as ORCID names it: ``FUNDREF``, ``GRID`` or
                ``RINGGOLD``.
            value: The identifier, in the form ORCID gives it.

        Returns:
            The bare ROR ID, or None.

        Raises:
            RegistryUnavailable: ROR could not be asked or answered badly.
        """
        if source not in self.EXTERNAL_IDS:
            return None
        bare = value.strip().rsplit("/", 1)[-1]
        if not re.fullmatch(r"[\w.\-]+", bare):
            return None
        return ask(
            self.SEARCH,
            self.sole_id_from,
            params={"query.advanced": f'external_ids.all:"{bare}"'},
        )

    def sole_id_from(self, body):
        """Read the ROR ID of the one active organization an identifier search found."""
        records = [r for r in map(self.record_of, body["items"]) if r is not None]
        return self.identifier_in(records[0]["id"]) if len(records) == 1 else None

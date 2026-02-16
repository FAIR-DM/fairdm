"""
Data transformation utilities for contributors.

This module provides bidirectional transformations between Contributor objects
and various external metadata formats (DataCite, Schema.org, CSL-JSON, ORCID, ROR, etc.).
"""

import decimal
from typing import Any

from fairdm.contrib.contributors.models import (
    Contributor,
    ContributorIdentifier,
    Organization,
    Person,
)


class BaseTransform:
    """
    Base class for bidirectional contributor data transformations.

    Provides utilities for converting between external data formats and
    Contributor model instances. Subclasses should implement:
    - export(): Convert Contributor → external format
    - import_data(): Convert external format → Contributor
    """

    def dictget(self, data: dict | list, path: list, default: Any = "") -> Any:
        """
        Navigate nested data structures using a path list.

        Safely retrieves values from deeply nested dictionaries or lists.

        Args:
            data: Nested dictionary or list structure
            path: List of keys/indices to navigate (e.g., ["person", "name", 0])
            default: Value to return if path doesn't exist

        Returns:
            The value at the specified path, or default if not found

        Example:
            >>> data = {"person": {"names": [{"given": "John"}]}}
            >>> self.dictget(data, ["person", "names", 0, "given"])
            'John'
        """
        value = data
        try:
            for key in path:
                value = value[key]
            return value  # noqa: TRY300
        except (KeyError, IndexError, TypeError):
            return default

    def export(self, contributor: Contributor) -> dict:
        """
        Export a Contributor instance to external format.

        Args:
            contributor: The Contributor instance to export

        Returns:
            dict: Data in the external format

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement export()")

    def import_data(self, data: dict, instance: Contributor | None = None, save: bool = True) -> Contributor:
        """
        Import external format data into a Contributor instance.

        Args:
            data: External format data dictionary
            instance: Existing Contributor to update (creates new if None)
            save: Whether to save the instance to the database

        Returns:
            Contributor: The created or updated Contributor instance

        Raises:
            NotImplementedError: Subclasses must implement this method
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement import_data()")

    def validate(self, data: dict) -> bool:
        """
        Validate that data conforms to the expected format.

        Args:
            data: Data to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # Default implementation - subclasses can override
        return isinstance(data, dict)


class DataCiteTransform(BaseTransform):
    """
    Bidirectional transformation for DataCite Metadata Schema 4.4.

    Converts between Contributor objects and DataCite creator/contributor format.
    See: https://schema.datacite.org/meta/kernel-4.4/
    """

    def export(self, contributor: Contributor) -> dict:
        """
        Export Contributor to DataCite creator/contributor format.

        Args:
            contributor: Person or Organization instance

        Returns:
            dict: DataCite-formatted contributor metadata
        """
        data = {
            "name": contributor.name,
            "nameType": ("Organizational" if isinstance(contributor, Organization) else "Personal"),
        }

        # Add name identifiers (ORCID/ROR)
        identifiers = []
        if default_id := contributor.get_default_identifier():
            identifiers.append(
                {
                    "nameIdentifier": default_id.value,
                    "nameIdentifierScheme": default_id.type,
                    "schemeURI": (default_id.get_url() if hasattr(default_id, "get_url") else None),
                }
            )

        if identifiers:
            data["nameIdentifiers"] = identifiers

        # Add person-specific fields
        if isinstance(contributor, Person):
            if hasattr(contributor, "given") and contributor.given:
                data["givenName"] = contributor.given
            if hasattr(contributor, "family") and contributor.family:
                data["familyName"] = contributor.family

            # Add affiliation
            if affiliation := contributor.primary_affiliation():
                affiliations = [
                    {
                        "name": affiliation.organization.name,
                    }
                ]
                if ror_id := affiliation.organization.get_default_identifier():
                    affiliations[0]["affiliationIdentifier"] = ror_id.value
                    affiliations[0]["affiliationIdentifierScheme"] = "ROR"
                data["affiliation"] = affiliations

        return data

    def import_data(self, data: dict, instance: Contributor | None = None, save: bool = True) -> Contributor:
        """
        Import DataCite creator/contributor data into a Contributor.

        Args:
            data: DataCite formatted contributor data
            instance: Existing Contributor to update (creates new if None)
            save: Whether to save to database

        Returns:
            Contributor: Created or updated instance
        """
        # Determine type from nameType
        is_organization = data.get("nameType") == "Organizational"

        if instance is None:
            # Create new instance of appropriate type
            instance = Organization() if is_organization else Person()

        # Set basic fields
        instance.name = data.get("name", "")

        # Set person-specific fields
        if isinstance(instance, Person):
            instance.first_name = data.get("givenName", "")
            instance.last_name = data.get("familyName", "")

        if save:
            instance.save()

            # Handle identifiers
            if identifiers := data.get("nameIdentifiers"):
                from fairdm.contrib.contributors.models import ContributorIdentifier

                for id_data in identifiers:
                    ContributorIdentifier.objects.update_or_create(
                        type=id_data.get("nameIdentifierScheme"),
                        value=id_data.get("nameIdentifier"),
                        defaults={"related": instance},
                    )

        return instance


class SchemaOrgTransform(BaseTransform):
    """
    Bidirectional transformation for Schema.org JSON-LD format.

    Converts between Contributor objects and Schema.org Person/Organization types.
    See: https://schema.org/Person and https://schema.org/Organization
    """

    def export(self, contributor: Contributor) -> dict:
        """
        Export Contributor to Schema.org JSON-LD format.

        Args:
            contributor: Person or Organization instance

        Returns:
            dict: Schema.org formatted data
        """
        if isinstance(contributor, Person):
            data = {
                "@type": "Person",
                "name": contributor.name,
            }

            if contributor.given:
                data["givenName"] = contributor.given
            if contributor.family:
                data["familyName"] = contributor.family

            # Add ORCID identifier
            if orcid := contributor.get_default_identifier():
                data["@id"] = f"https://orcid.org/{orcid.value}"

            # Add email if available
            if contributor.email:
                data["email"] = contributor.email

            # Add affiliation
            if affiliation := contributor.primary_affiliation():
                data["affiliation"] = {
                    "@type": "Organization",
                    "name": affiliation.organization.name,
                }
                if ror_id := affiliation.organization.get_default_identifier():
                    data["affiliation"]["@id"] = f"https://ror.org/{ror_id.value}"

        else:  # Organization
            data = {
                "@type": "Organization",
                "name": contributor.name,
            }

            # Add ROR identifier
            if ror := contributor.get_default_identifier():
                data["@id"] = f"https://ror.org/{ror.value}"

        # Add location if available (Organization-specific attributes)
        # Type ignore needed because these attrs only exist on Organization subclass
        if hasattr(contributor, "location") and contributor.location:  # type: ignore[attr-defined]
            data["address"] = {
                "@type": "PostalAddress",
            }
            if contributor.city:  # type: ignore[attr-defined]
                data["address"]["addressLocality"] = contributor.city  # type: ignore[attr-defined]
            if contributor.country:  # type: ignore[attr-defined]
                data["address"]["addressCountry"] = str(contributor.country.code)  # type: ignore[attr-defined]
        elif hasattr(contributor, "city") and contributor.city:  # type: ignore[attr-defined]
            # Fallback for city without full location
            data["address"] = {
                "@type": "PostalAddress",
                "addressLocality": contributor.city,  # type: ignore[attr-defined]
            }
            if contributor.country:  # type: ignore[attr-defined]
                data["address"]["addressCountry"] = str(contributor.country.code)  # type: ignore[attr-defined]

        # Add common fields
        if contributor.profile:
            data["description"] = contributor.profile

        if contributor.links:
            data["url"] = contributor.links[0] if isinstance(contributor.links, list) else contributor.links

        return data

    def import_data(self, data: dict, instance: Contributor | None = None, save: bool = True) -> Contributor:
        """
        Import Schema.org Person/Organization data into a Contributor.

        Args:
            data: Schema.org formatted data
            instance: Existing Contributor to update (creates new if None)
            save: Whether to save to database

        Returns:
            Contributor: Created or updated instance
        """
        # Determine type from @type
        is_organization = data.get("@type") == "Organization"

        if instance is None:
            instance = Organization() if is_organization else Person()

        # Set basic fields
        instance.name = data.get("name", "")

        # Set person-specific fields
        if isinstance(instance, Person):
            instance.first_name = data.get("givenName", "")
            instance.last_name = data.get("familyName", "")
            if email := data.get("email"):
                instance.email = email

        # Set common fields
        if description := data.get("description"):
            instance.profile = description

        if url := data.get("url"):
            instance.links = [url] if isinstance(url, str) else url

        if save:
            instance.save()

            # Extract and save identifier from @id
            if id_url := data.get("@id"):
                from fairdm.contrib.contributors.models import ContributorIdentifier

                if "orcid.org/" in id_url:
                    orcid = id_url.split("orcid.org/")[-1]
                    ContributorIdentifier.objects.update_or_create(
                        type="ORCID",
                        value=orcid,
                        defaults={"related": instance},
                    )
                elif "ror.org/" in id_url:
                    ror = id_url.split("ror.org/")[-1]
                    ContributorIdentifier.objects.update_or_create(
                        type="ROR",
                        value=ror,
                        defaults={"related": instance},
                    )

        return instance


class CSLJSONTransform(BaseTransform):
    """
    Bidirectional transformation for CSL-JSON (Citation Style Language) format.

    Converts between Contributor objects and CSL-JSON author/contributor format.
    See: https://citeproc-js.readthedocs.io/en/latest/csl-json/markup.html
    """

    def export(self, contributor: Contributor) -> dict:
        """
        Export Contributor to CSL-JSON author format.

        Args:
            contributor: Contributor instance

        Returns:
            dict: CSL-JSON formatted author object
        """
        if isinstance(contributor, Person):
            data = {
                "given": contributor.given or "",
                "family": contributor.family or "",
            }
        else:
            data = {
                "literal": contributor.name,
            }

        # Add ORCID if available
        if (orcid := contributor.get_default_identifier()) and orcid.type == "ORCID":
            data["ORCID"] = f"https://orcid.org/{orcid.value}"

        # Add affiliation for persons
        if isinstance(contributor, Person) and (affiliation := contributor.primary_affiliation()):
            data["affiliation"] = [{"name": affiliation.organization.name}]

        return data

    def import_data(self, data: dict, instance: Contributor | None = None, save: bool = True) -> Contributor:
        """
        Import CSL-JSON author data into a Contributor.

        Args:
            data: CSL-JSON formatted author data
            instance: Existing Contributor to update (creates new if None)
            save: Whether to save to database

        Returns:
            Contributor: Created or updated instance
        """
        # Check if this is an organization (has "literal") or person (has "given"/"family")
        is_person = "given" in data or "family" in data

        # Try to find existing contributor by ORCID
        if instance is None and (orcid := data.get("ORCID")):
            orcid_value = orcid.split("orcid.org/")[-1] if "orcid.org/" in orcid else orcid
            instance = Contributor.objects.filter(
                identifiers__type="ORCID",
                identifiers__value=orcid_value,
            ).first()

        if instance is None:
            instance = Person() if is_person else Organization()

        # Set fields
        if isinstance(instance, Person):
            instance.first_name = data.get("given", "")
            instance.last_name = data.get("family", "")
        else:
            instance.name = data.get("literal", "")

        if save:
            instance.save()

            # Save ORCID if provided
            if orcid := data.get("ORCID"):
                from fairdm.contrib.contributors.models import ContributorIdentifier

                orcid_value = orcid.split("orcid.org/")[-1] if "orcid.org/" in orcid else orcid
                ContributorIdentifier.objects.update_or_create(
                    type="ORCID",
                    value=orcid_value,
                    defaults={"related": instance},
                )

        return instance


class ORCIDTransform(BaseTransform):
    """
    Bidirectional transformation for ORCID Public API v3.0 data.

    Converts between Person objects and ORCID API response format.
    See: https://info.orcid.org/documentation/integration-guide/orcid-record/
    """

    @staticmethod
    def fetch_from_api(orcid_id: str) -> dict:
        """
        Fetch public data for a given ORCID ID from the ORCID Public API.

        Args:
            orcid_id: The ORCID identifier of the researcher

        Returns:
            dict: The JSON response from the ORCID API

        Raises:
            requests.RequestException: If the API request fails

        Example:
            data = ORCIDTransform.fetch_from_api("0000-0002-1825-0097")
        """
        import warnings

        import requests

        orcid_api = f"https://pub.orcid.org/v3.0/{orcid_id}"
        headers = {"Accept": "application/json"}
        try:
            response = requests.get(orcid_api, headers=headers, timeout=30)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                warnings.warn(
                    f"Rate limited by ORCID API (429). Retry after {retry_after} seconds.",
                    stacklevel=2,
                )
            elif 500 <= response.status_code < 600:
                warnings.warn(f"Server error {response.status_code} from ORCID API.", stacklevel=2)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch ORCID {orcid_id}: {e}"
            raise requests.RequestException(msg) from e

    def export(self, contributor: Contributor) -> dict:
        """
        Export Person to ORCID API format.

        Note: This creates a minimal ORCID-compatible structure for Person data.
        The full ORCID record has many more fields.

        Args:
            contributor: Person instance (Organizations not supported)

        Returns:
            dict: ORCID-formatted person data

        Raises:
            TypeError: If contributor is not a Person instance
        """
        if not isinstance(contributor, Person):
            msg = "ORCID export only supports Person instances"
            raise TypeError(msg)

        # Get ORCID identifier
        orcid = contributor.get_default_identifier()
        orcid_value = orcid.value if orcid and orcid.type == "ORCID" else None

        data = {
            "orcid-identifier": {
                "path": orcid_value,
            },
            "person": {
                "name": {
                    "credit-name": ({"value": contributor.name} if contributor.name else None),
                    "given-names": ({"value": contributor.first_name} if contributor.first_name else None),
                    "family-name": ({"value": contributor.last_name} if contributor.last_name else None),
                },
                "biography": ({"content": contributor.profile} if contributor.profile else None),
            },
        }

        # Add alternative names
        if contributor.alternative_names:
            data["person"]["other-names"] = {
                "other-name": [{"content": name} for name in contributor.alternative_names]
            }

        # Add researcher URLs
        if contributor.links:
            data["person"]["researcher-urls"] = {
                "researcher-url": [{"url": {"value": link}} for link in contributor.links]
            }

        return data

    def import_data(self, data: dict, instance: Person | None = None, save: bool = True) -> Person:
        """
        Import ORCID API data into a Person instance.

        Args:
            data: ORCID API response data
            instance: Existing Person to update (creates new if None)
            save: Whether to save to database

        Returns:
            Person: Created or updated Person instance
        """
        # Extract ORCID ID
        orcid = self.dictget(data, ["orcid-identifier", "path"])

        # Create or use provided instance
        person = instance or Person()
        person.synced_data = data  # Store raw data

        # Extract name fields
        person.name = self.dictget(data, ["person", "name", "credit-name", "value"])
        person.first_name = self.dictget(data, ["person", "name", "given-names", "value"])
        person.last_name = self.dictget(data, ["person", "name", "family-name", "value"])

        # If name is not set, compute it from first/last name
        if not person.name:
            person.name = f"{person.first_name} {person.last_name}".strip()

        person.profile = self.dictget(data, ["person", "biography", "content"])

        # Extract alternative names
        if other_names := self.dictget(data, ["person", "other-names", "other-name"], []):
            person.alternative_names = [name["content"] for name in other_names]

        # Extract researcher URLs
        if links := self.dictget(data, ["person", "researcher-urls", "researcher-url"], []):
            person.links = [link["url"]["value"] for link in links]

        if save:
            from django.db import transaction

            with transaction.atomic():
                person.save()
                # Create/update ORCID identifier
                if orcid:
                    ContributorIdentifier.objects.update_or_create(
                        type="ORCID",
                        value=orcid,
                        defaults={"related": person},
                    )

        return person

    @classmethod
    def update_or_create(cls, orcid: str, force: bool = False, **kwargs) -> tuple[Person, bool]:
        """
        Update an existing Person or create a new one using ORCID data.

        Attempts to find a Person matching the provided kwargs or with an identifier
        value matching the given ORCID. If found and not recently synced (or force=True),
        updates the Person with latest ORCID API data. If not found, creates a new Person.

        Args:
            orcid: The ORCID identifier to fetch data for
            force: If True, always fetch and update from ORCID API
            **kwargs: Additional lookup parameters for finding an existing Person

        Returns:
            tuple: (Person object, created boolean)

        Example:
            person, created = ORCIDTransform.update_or_create("0000-0002-1825-0097")
        """
        from datetime import timedelta

        from django.db.models import Q
        from django.utils import timezone

        try:
            obj = Person.objects.get(Q(**kwargs) | Q(identifiers__value=orcid))
            # Only fetch new data if last_synced is None or more than 1 day ago, unless force is True
            if force or not obj.last_synced or obj.last_synced < timezone.now().date() - timedelta(days=1):
                orcid_data = cls.fetch_from_api(orcid)
                person = cls().import_data(orcid_data, instance=obj, save=True)
            else:
                person = obj
            created = False
        except Person.DoesNotExist:
            orcid_data = cls.fetch_from_api(orcid)
            person = cls().import_data(orcid_data, save=True)
            created = True
        return person, created

    @classmethod
    def get_or_create(cls, orcid: str) -> tuple[Person, bool]:
        """
        Retrieve a Person instance matching the given ORCID.

        If no match is found, a Person instance is created by fetching data from
        the ORCID Public API.

        Args:
            orcid: The ORCID identifier to search for or create a Person with

        Returns:
            tuple: (Person instance, created boolean)

        Example:
            person, created = ORCIDTransform.get_or_create("0000-0002-1825-0097")
        """
        try:
            person = Person.objects.get(identifiers__value=orcid)
            created = False
        except Person.DoesNotExist:
            orcid_data = cls.fetch_from_api(orcid)
            person = cls().import_data(orcid_data, save=True)
            created = True
        return person, created


class RORTransform(BaseTransform):
    """
    Bidirectional transformation for ROR (Research Organization Registry) API data.

    Converts between Organization objects and ROR API response format.
    See: https://ror.readme.io/docs/data-structure
    """

    @staticmethod
    def clean_ror_id(ror_id_or_link: str) -> str:
        """
        Extract ROR ID from URL or return as-is.

        Args:
            ror_id_or_link: ROR ID or full URL

        Returns:
            str: Clean ROR ID without URL prefix
        """
        cleaned = ror_id_or_link.strip()
        if cleaned.startswith("https://ror.org/"):
            return cleaned.split("/")[-1]
        return cleaned

    @staticmethod
    def fetch_from_api(ror_id: str) -> dict:
        """
        Fetch public data for a given ROR ID from the ROR API.

        Args:
            ror_id: The ROR identifier of the organization (URL or ID)

        Returns:
            dict: The JSON response from the ROR API

        Raises:
            requests.RequestException: If the API request fails

        Example:
            data = RORTransform.fetch_from_api("https://ror.org/00x0x0x")
        """
        import warnings

        import requests

        # Clean the ROR ID if it's a full URL
        clean_id = RORTransform.clean_ror_id(ror_id)
        ror_api = f"https://api.ror.org/organizations/{clean_id}"

        try:
            response = requests.get(ror_api, timeout=30)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "unknown")
                warnings.warn(
                    f"Rate limited by ROR API (429). Retry after {retry_after} seconds.",
                    stacklevel=2,
                )
            elif 500 <= response.status_code < 600:
                warnings.warn(f"Server error {response.status_code} from ROR API.", stacklevel=2)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            msg = f"Failed to fetch ROR ID {ror_id}: {e}"
            raise requests.RequestException(msg) from e

    def export(self, contributor: Contributor) -> dict:
        """
        Export Organization to ROR API format.

        Note: This creates a minimal ROR-compatible structure for Organization data.
        The full ROR record has many more fields.

        Args:
            contributor: Organization instance (Person not supported)

        Returns:
            dict: ROR-formatted organization data

        Raises:
            ValueError: If contributor is not an Organization instance
        """
        if not isinstance(contributor, Organization):
            msg = "ROR export only supports Organization instances"
            raise TypeError(msg)

        # Get ROR identifier
        ror = contributor.get_default_identifier()
        ror_value = ror.value if ror and ror.type == "ROR" else None
        ror_url = f"https://ror.org/{ror_value}" if ror_value else None

        data = {
            "id": ror_url,
            "name": contributor.name,
        }

        # Add aliases and acronyms
        if contributor.alternative_names:
            data["aliases"] = [name for name in contributor.alternative_names if len(name) > 5]
            data["acronyms"] = [name for name in contributor.alternative_names if len(name) <= 5]

        # Add location data
        addresses = []
        if hasattr(contributor, "city") and contributor.city:  # type: ignore[attr-defined]
            address = {"city": contributor.city}  # type: ignore[attr-defined]

            if hasattr(contributor, "location") and contributor.location:  # type: ignore[attr-defined]
                address["lat"] = float(contributor.location.latitude)  # type: ignore[attr-defined]
                address["lng"] = float(contributor.location.longitude)  # type: ignore[attr-defined]

            addresses.append(address)

        if addresses:
            data["addresses"] = addresses

        # Add country
        if hasattr(contributor, "country") and contributor.country:  # type: ignore[attr-defined]
            data["country"] = {
                "country_code": str(contributor.country.code),  # type: ignore[attr-defined]
            }

        # Add links
        links = list(contributor.links) if contributor.links else []
        data["links"] = links

        return data

    def import_data(self, data: dict, instance: Organization | None = None, save: bool = True) -> Organization:
        """
        Import ROR API data into an Organization instance.

        Args:
            data: ROR API response data
            instance: Existing Organization to update (creates new if None)
            save: Whether to save to database

        Returns:
            Organization: Created or updated Organization instance
        """
        # Extract ROR ID from URL
        ror_id = self.dictget(data, ["id"]).split("/")[-1] if self.dictget(data, ["id"]) else None

        # Create or use provided instance
        org = instance or Organization()
        org.synced_data = data
        org.name = self.dictget(data, ["name"])

        # Combine aliases and acronyms
        org.alternative_names = self.dictget(data, ["aliases"], []) + self.dictget(data, ["acronyms"], [])

        # Set location fields
        org.city = self.dictget(data, ["addresses", 0, "city"])
        org.country = self.dictget(data, ["country", "country_code"])

        # Handle geographic coordinates
        lat = self.dictget(data, ["addresses", 0, "lat"])
        lon = self.dictget(data, ["addresses", 0, "lng"])
        if lat is not None and lon is not None:
            from fairdm.contrib.location.models import Point

            point, _created = Point.objects.get_or_create(
                x=decimal.Decimal(str(lon)),
                y=decimal.Decimal(str(lat)),
            )
            org.location = point

        # Extract links
        links = self.dictget(data, ["links"], [])
        if wiki_url := self.dictget(data, ["wikipedia_url"]):
            links.append(wiki_url)
        if links:
            org.links = links

        if save:
            org.save()
            # Create/update ROR identifier
            if ror_id:
                ContributorIdentifier.objects.update_or_create(
                    type="ROR",
                    value=ror_id,
                    defaults={"related": org},
                )

        return org

    @classmethod
    def update_or_create(cls, ror_id: str, force: bool = False, **kwargs) -> tuple[Organization, bool]:
        """
        Update an existing Organization or create a new one using ROR data.

        Attempts to find an Organization matching the provided kwargs or with an
        identifier value matching the given ROR ID. If found and not recently synced
        (or force=True), updates the Organization with latest ROR API data. If not
        found, creates a new Organization.

        Args:
            ror_id: The ROR identifier to fetch data for
            force: If True, always fetch and update from ROR API
            **kwargs: Additional lookup parameters for finding an existing Organization

        Returns:
            tuple: (Organization object, created boolean)

        Example:
            org, created = RORTransform.update_or_create("https://ror.org/00x0x0x")
        """
        from datetime import timedelta

        from django.db.models import Q
        from django.utils import timezone

        clean_id = cls.clean_ror_id(ror_id)
        try:
            obj = Organization.objects.get(Q(**kwargs) | Q(identifiers__value=clean_id))
            # Only fetch new data if last_synced is None or more than 1 day ago, unless force is True
            if force or not obj.last_synced or obj.last_synced < timezone.now().date() - timedelta(days=1):
                ror_data = cls.fetch_from_api(clean_id)
                org = cls().import_data(ror_data, instance=obj, save=True)
            else:
                org = obj
            created = False
        except Organization.DoesNotExist:
            ror_data = cls.fetch_from_api(clean_id)
            org = cls().import_data(ror_data, save=True)
            created = True
        return org, created

    @classmethod
    def get_or_create(cls, ror_id: str) -> tuple[Organization, bool]:
        """
        Retrieve an Organization instance matching the given ROR ID.

        If no match is found, an Organization instance is created by fetching data
        from the ROR API.

        Args:
            ror_id: The ROR identifier to search for or create an Organization with

        Returns:
            tuple: (Organization instance, created boolean)

        Example:
            org, created = RORTransform.get_or_create("https://ror.org/00x0x0x")
        """
        clean_id = cls.clean_ror_id(ror_id)

        try:
            org = Organization.objects.get(identifiers__value=clean_id)
            created = False
        except Organization.DoesNotExist:
            ror_data = cls.fetch_from_api(clean_id)
            org = cls().import_data(ror_data, save=True)
            created = True
        return org, created


def contributor_to_datacite(contributor: Contributor) -> dict:
    """Export contributor as DataCite JSON."""
    return DataCiteTransform().export(contributor)


def contributor_to_schema_org(contributor: Contributor) -> dict:
    """Export contributor as Schema.org JSON-LD."""
    return SchemaOrgTransform().export(contributor)


def contributor_to_csljson(contributor: Contributor) -> dict:
    """Export contributor as CSL-JSON."""
    return CSLJSONTransform().export(contributor)


def csljson_to_contributor(data: dict, save: bool = True) -> Contributor:
    """Import CSL-JSON data as Contributor."""
    return CSLJSONTransform().import_data(data, save=save)

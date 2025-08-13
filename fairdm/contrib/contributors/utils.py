import decimal
import json
import warnings
from datetime import timedelta

import requests
from benedict import benedict
from django.conf import settings
from django.db import models, transaction
from django.db.models import CharField, F, Q, Value
from django.templatetags.static import static
from django.utils import timezone
from easy_thumbnails.files import get_thumbnailer
from research_vocabs.models import Concept

from fairdm.contrib.contributors.models import ContributorIdentifier

from .models import Contributor, Organization, Person


def get_contributor_roles():
    """
    Returns a queryset of roles for a given contributor on a specific object.

    Args:
        contributor (Contributor): A Contributor object.
        obj (Project, Dataset, Sample): A database object containing a list of contributors.

    Returns:
        QuerySet: A queryset of roles for the contributor on the object.
    """
    return Concept.objects.filter(vocabulary__name="fairdm-roles")


def dictget(data, path, default=""):
    """
    Navigate `data`, a multidimensional array (list or dictionary), and returns
    the object at `path`.
    """
    value = data
    try:
        for key in path:
            value = value[key]
        return value  # noqa: TRY300
    except (KeyError, IndexError, TypeError):
        return default


def get_contributor_avatar(contributor):
    """Returns the avatar URL for a given contributor.

    Args:
        contributor (Contributor): A Contributor object.

    Returns:
        str: The URL of the contributor's avatar.
    """
    # This must handle the case where the contributor is a django-guardian AnonymousUser
    if not hasattr(contributor, "image") or not contributor.image:
        return static("icons/user.svg")

    return get_thumbnailer(contributor.image)["thumb"].url


def get_avatar_url(comment):
    if comment.user is not None:
        try:
            return get_contributor_avatar(comment.user)
        except Exception:
            pass
    return get_contributor_avatar(comment)


def current_user_has_role(request, obj, role):
    """Returns True if the current user has the specified role for the given object.

    Args:
        request (Request): The request object.
        obj (Project, Dataset, Sample): A database object containing a list of contributors.
        role (str, list): The role/s to check for.

    Returns:
        bool: True if the contributor has the specified roles.
    """
    current_user = request.user
    if not current_user.is_authenticated:
        return False

    if not isinstance(role, list):
        role = [role]

    if contribution_obj := obj.contributors.filter(contributor=current_user).first():
        return any([role in contribution_obj.roles for role in role])

    return False


def contributor_to_csljson(contributor):
    """Parse a Contributor object into a CSL-JSON author object.

    Args:
        contributor (Contributor): A Contributor object.

    Returns:
        dict: A CSL-JSON author object.
    """

    csljson = {
        "name": contributor.name,
        "given": contributor.given,
        "family": contributor.family,
    }

    ORCID = contributor.identifiers.filter(scheme="ORCID").first()
    if ORCID:
        csljson["ORCID"] = ORCID.identifier

    affiliation = contributor.primary_affiliation()
    if affiliation:
        csljson["affiliation"] = affiliation

    return csljson


def csljson_to_contributor(csljson_author):
    """Parse a CSL-JSON author object into a Contributor object.

    Args:
        author (dict): A CSL-JSON author object.

    Returns:
        Contributor: A Contributor object.
    """

    if csljson_author.get("ORCID"):
        # try to get the contributor by their ORCID
        contributor = Contributor.objects.filter(
            identifiers__scheme="ORCID",
            identifiers__identifier=csljson_author.get("ORCID"),
        ).first()

        if contributor:
            return contributor

    # initialise a new contributor object
    contributor = Contributor.objects.create()

    # add the name to the contributor object
    contributor.name = csljson_author.get("literal")

    # add the ORCID to the contributor object
    contributor.orcid = csljson_author.get("ORCID")

    # return the contributor object
    return contributor


def user_network(contributor):
    # get list of content_types that the contributor has contributed to
    object_ids = contributor.contributions.values_list("object_id", flat=True)

    # get all contributions to those content_types
    data = (
        contributor.get_related_contributions()
        .values("profile", "object_id")
        .annotate(
            id=models.F("profile__id"),
            label=models.F("profile__name"),
            image=models.F("profile__image"),
        )
        .values("id", "label", "object_id", "image")
    )

    models.Concat(
        F("model__user_first_name"),
        Value(" "),
        F("model__user_last_name"),
        output_field=CharField(),
    )

    # get unique contributors and count the number of times they appear in the queryset
    nodes_qs = data.values("id", "label", "image").annotate(value=models.Count("id")).distinct()

    nodes = []
    for d in nodes_qs:
        if d["image"]:
            d["image"] = settings.MEDIA_URL + d["image"]
        nodes.append(d)

    print("Nodes: ", nodes)

    object_ids = {d["object_id"] for d in data}

    edges = []
    for obj in object_ids:
        ids = list({i["id"] for i in data if i["object_id"] == obj})

        ids.sort()

        # get list of unique id pairs
        pairs = []
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j]))

        edges += pairs

    # count the number of times each pair appears in edges
    edges = [{"from": f, "to": t, "value": edges.count((f, t))} for f, t in set(edges)]

    vis_js = {"nodes": list(nodes), "edges": edges}
    print(edges)
    # serialize nodes queryset to json

    return json.dumps(vis_js)


def update_or_create_contribution(contributor, obj, roles=None):
    """
    Adds a contributor to the given object with specified roles.

    Behavior:
    - If the contributor already exists on the object and roles are provided, the roles are updated and the Contribution
      object is returned.
    - If the contributor already exists on the object and roles *are not* provided, the existing roles are retained and
      the Contribution object is returned unchanged.
    - If the contributor does not already exist on the object and roles are provided, a new Contribution object is created
      with the provided roles and returned.
    - If the contributor does not already exist on the object and roles are not provided, a new Contribution object is
      created with the object's DEFAULT_ROLES and returned.

    Args:
        contributor: The contributor instance to add.
        obj: The object to which the contributor is being added. Must have a 'contributors' manager and 'DEFAULT_ROLES' attribute.
        roles (optional): The roles to assign to the contributor. If not provided, uses obj.DEFAULT_ROLES.

    Returns:
        tuple: (contribution, created)
            contribution: The contribution instance.
            created (bool): True if a new contribution was created, False if it already existed.
    """
    contribution, created = obj.contributors.get_or_create(
        contributor=contributor,
    )
    roles_qs = Concept.objects.filter(vocabulary__name="fairdm-roles")
    if not roles:
        roles = obj.DEFAULT_ROLES

    contribution.roles.add(*roles_qs.filter(name__in=roles))

    return contribution, created


# def related_contributions(self):
#     """Returns a queryset of all contributions related to datasets contributed to by the current contributor."""

#     dataset_ids = self.contributions.filter(
#         content_type=ContentType.objects.get_for_model(Dataset),
#     ).values_list("object_id", flat=True)

#     return Contribution.objects.filter(object_id__in=dataset_ids)


# ======== ORCID related utilities ========


def contributor_from_orcid_data(data, person: Person | None = None, save=True) -> Person:
    """
    Creates or updates a Person instance from ORCID API data.
    This function extracts relevant fields from the provided ORCID data dictionary and populates a Person model instance.
    If a Person instance is provided, it updates that instance; otherwise, it creates a new one. The function also updates
    or creates a ContributorIdentifier of type "ORCID" linked to the person.
    Args:
        data (dict): The ORCID API response data containing contributor information.
        person (Person, optional): An existing Person instance to update. If None, a new Person is created.
    Returns:
        Person: The created or updated Person instance.
    Notes:
        - The function is atomic; all changes are committed together.
        - Alternative names and researcher URLs are extracted if present.
        - The ContributorIdentifier for ORCID is updated or created to link to the person.
        - External identifiers from ORCID are not currently processed (see commented code).
    """
    if not isinstance(data, benedict):
        data = benedict(data)
    orcid = data.get("orcid-identifier.path")
    person = person or Person()
    person.synced_data = data
    # person.name = dictget(data, ["person", "name", "credit-name", "value"])
    person.name = data.get("person.name.credit-name.value")
    person.first_name = data.get("person.name.given-names.value")
    person.last_name = data.get("person.name.family-name.value")
    person.profile = data.get("person.biography.content")

    if other_names := data.get("person.other-names.other-name", []):
        person.alternative_names = [name["content"] for name in other_names]

    if links := data.get("person.researcher-urls.researcher-url", []):
        person.links = [link["url"]["value"] for link in links]

    if save:
        with transaction.atomic():
            person.save()
            # WARNING: I don't like this. We shouldn't update the identifier with a new person object if it already exists.
            ContributorIdentifier.objects.update_or_create(type="ORCID", value=orcid, defaults={"related": person})

        # NOTE: need to work out the format for external-identifiers in ORCID

        # identifiers = dictget(data, ["person", "external-identifiers"], [])
        # for id_type, content in identifiers.items():
        #     # value is either list or string
        #     value = dictget(content, ["all"])
        #     if isinstance(value, list):
        #         value = value[0]
        #     ContributorIdentifier.objects.update_or_create(
        #         type=id_type,
        #         value=dictget(content, ["preferred"]) or value,  # utilize preferred value if available
        #         defaults={"content_object": person},
        # )

    return person


def fetch_orcid_data_from_api(orcid_id):
    """
    Fetches public data for a given ORCID ID from the ORCID public API.
    Args:
        orcid_id (str): The ORCID identifier of the researcher.
    Returns:
        dict: The JSON response from the ORCID API containing the researcher's public data.
    Raises:
        Exception: If the request to the ORCID API fails or returns an error.
    Example:
        data = fetch_orcid_data_from_api("0000-0002-1825-0097")
    """
    orcid_api = f"https://pub.orcid.org/v3.0/{orcid_id}"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(orcid_api, headers=headers, timeout=30)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            warnings.warn(f"Rate limited by ORCID API (429). Retry after {retry_after} seconds.")
        elif 500 <= response.status_code < 600:
            warnings.warn(f"Server error {response.status_code} from ROR API.")
        response.raise_for_status()
        # see https://github.com/fabiocaccamo/python-benedict
        data = benedict(response.json())
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch ORCID {orcid_id}: {e}")

    return data


def update_or_create_from_orcid(orcid, force=False, **kwargs):
    """
    Updates an existing Person object or creates a new one using ORCID data.
    This function attempts to find a Person object matching the provided keyword arguments
    or with an identifier value matching the given ORCID. If found, it updates the Person
    object with the latest data from the ORCID API, unless it was synced less than 1 day ago
    (unless force=True). If not found, it creates a new Person object using the ORCID data.
    Args:
        orcid (str): The ORCID identifier to fetch data for.
        force (bool): If True, always fetch and update from ORCID API.
        **kwargs: Additional lookup parameters for finding an existing Person.
    Returns:
        tuple: A tuple containing the Person object and a boolean indicating whether the
               object was created (True) or updated (False).
    """
    try:
        obj = Person.objects.get(Q(**kwargs) | Q(identifiers__value=orcid))
        # Only fetch new data if last_synced is None or more than 1 day ago, unless force is True
        if force or not obj.last_synced or obj.last_synced < timezone.now().date() - timedelta(days=1):
            orcid_data = fetch_orcid_data_from_api(orcid)
            person = contributor_from_orcid_data(orcid_data, obj)
        else:
            person = obj
        created = False
    except Person.DoesNotExist:
        orcid_data = fetch_orcid_data_from_api(orcid)
        person = contributor_from_orcid_data(orcid_data)
        created = True
    return person, created


def get_or_create_from_orcid(orcid) -> Person:
    """
    Retrieves a Person instance matching the given ORCID. If no match is found, a Person instance is created by fetching data from the ORCID Public API.

    Args:
        orcid (str): The ORCID identifier to search for or create a Person with.

    Returns:
        tuple: A tuple containing the Person instance and a boolean indicating whether the Person was created (True) or retrieved (False).

    Raises:
        Any exceptions raised by fetch_orcid_data_from_api or contributor_from_orcid_data if creation fails.
    """
    try:
        person = Person.objects.get(identifiers__value=orcid)
        created = False
    except Person.DoesNotExist:
        orcid_data = fetch_orcid_data_from_api(orcid)
        person = contributor_from_orcid_data(orcid_data)
        created = True
    return person, created


# ====== ROR related utilities========


def clean_ror(ror_id_or_link):
    """
    Cleans a ROR ID or link by extracting the ROR ID from the provided input.
    Args:
        ror_id_or_link (str): The ROR ID or link to clean.
    Returns:
        str: The cleaned ROR ID.
    """
    if ror_id_or_link.strip().startswith("https://ror.org/"):
        return ror_id_or_link.split("/")[-1]
    return ror_id_or_link


def contributor_from_ror_data(data, org: Organization | None = None, save=True) -> Organization:
    """
    Creates or updates an Organization instance from ROR (Research Organization Registry) data.
    This function extracts relevant organization information from the provided ROR data dictionary,
    optionally updates an existing Organization instance, or creates a new one if necessary. It also
    handles the creation or update of related ContributorIdentifier objects for ROR and other external IDs.
    Args:
        data (dict): The ROR data dictionary containing organization information.
        org (Organization, optional): An existing Organization instance to update. If not provided,
            the function will attempt to find an existing organization by ROR ID or create a new one.
    Returns:
        Organization: The created or updated Organization instance.
    """
    ror_id = dictget(data, ["id"]).split("/")[-1]

    # if an org is explicitly passed, use it, otherwise try to find an existing org by ROR ID, otherwise create a new org instance
    org = org or Organization()
    org.synced_data = data
    org.name = dictget(data, ["name"])
    org.alternative_names = dictget(data, ["aliases"]) + dictget(data, ["acronyms"], [])
    org.city = dictget(data, ["addresses", 0, "city"])
    org.country = dictget(data, ["country", "country_code"])
    if lat := dictget(data, ["addresses", 0, "lat"]):
        org.lat = decimal.Decimal(str(lat))
    if lon := dictget(data, ["addresses", 0, "lng"]):
        org.lon = decimal.Decimal(str(lon))

    links = dictget(data, ["links"])
    if wiki_url := dictget(data, ["wikipedia_url"]):
        links.append(wiki_url)
    if links:
        org.links = links

    if save:
        org.save()
        # ContributorIdentifier.objects.update_or_create(type="ROR", value=ror_id, defaults={"related": org})

        # identifiers = dictget(data, ["external_ids"], [])
        # for id_type, content in identifiers.items():
        #     # value is either list or string
        #     value = dictget(content, ["all"])
        #     if isinstance(value, list):
        #         value = value[0]
        #     ContributorIdentifier.objects.update_or_create(
        #         type=id_type,
        #         value=dictget(content, ["preferred"]) or value,  # utilize preferred value if available
        #         defaults={"content_object": org},
        #     )

    # tags = dictget(data, ["types"], [])
    # address = dictget(data, ["addresses", 0])

    return org


def fetch_ror_data_from_api(ror_id):
    """
    Fetches public data for a given ROR ID from the ROR API.
    Args:
        ror_id (str): The ROR identifier of the organization.
    Returns:
        dict: The JSON response from the ROR API containing the organization's public data.
    Raises:
        Exception: If the request to the ROR API fails or returns an error.
    Example:
        data = fetch_ror_data_from_api("https://ror.org/00x0x0x")
    """
    ror_api = f"https://api.ror.org/organizations/{ror_id}"
    try:
        response = requests.get(ror_api, timeout=30)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")
            warnings.warn(f"Rate limited by ROR API (429). Retry after {retry_after} seconds.")
        elif 500 <= response.status_code < 600:
            warnings.warn(f"Server error {response.status_code} from ROR API.")
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch ROR ID {ror_id}: {e}")

    return data


def update_or_create_from_ror(ror_id, force=False, **kwargs) -> tuple[Organization, bool]:
    """
    Updates an existing Organization object or creates a new one using ROR data.
    This function attempts to find an Organization object matching the provided keyword arguments
    or with an identifier value matching the given ROR ID. If found, it updates the Organization
    object with the latest data from the ROR API, unless it was synced less than 1 day ago
    (unless force=True). If not found, it creates a new Organization object using the ROR data.
    Args:
        ror_id (str): The ROR identifier to fetch data for.
        force (bool): If True, always fetch and update from ROR API.
        **kwargs: Additional lookup parameters for finding an existing Organization.
    Returns:
        tuple: A tuple containing the Organization object and a boolean indicating whether the
               object was created (True) or updated (False).
    """
    ror_id = clean_ror(ror_id)
    try:
        obj = Organization.objects.get(Q(**kwargs) | Q(identifiers__value=ror_id))
        # Only fetch new data if last_synced is None or more than 1 day ago, unless force is True
        if force or not obj.last_synced or obj.last_synced < timezone.now().date() - timedelta(days=1):
            ror_data = fetch_ror_data_from_api(ror_id)
            org = contributor_from_ror_data(ror_data, obj)
        else:
            org = obj
        created = False
    except Organization.DoesNotExist:
        ror_data = fetch_ror_data_from_api(ror_id)
        org = contributor_from_ror_data(ror_data)
        created = True
    return org, created


def get_or_create_from_ror(ror_id) -> tuple[Organization, bool]:
    """
    Retrieves an Organization instance matching the given ROR ID. If no match is found, an Organization instance is created by fetching data from the ROR API.

    Args:
        ror_id (str): The ROR identifier to search for or create an Organization with.

    Returns:
        tuple: A tuple containing the Organization instance and a boolean indicating whether the Organization was created (True) or retrieved (False).

    Raises:
        Any exceptions raised by fetch_ror_data_from_api or contributor_from_ror_data if creation fails.
    """
    ror_id = clean_ror(ror_id)

    try:
        org = Organization.objects.get(identifiers__value=ror_id)
        created = False
    except Organization.DoesNotExist:
        ror_data = fetch_ror_data_from_api(ror_id)
        org = contributor_from_ror_data(ror_data)
        created = True
    return org, created

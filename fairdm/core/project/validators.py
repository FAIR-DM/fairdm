"""Validators for the project app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

#: The keys a DataCite funding reference may carry. No others are accepted.
FUNDING_REFERENCE_KEYS = frozenset(
    {
        "funderName",
        "funderIdentifier",
        "funderIdentifierType",
        "awardNumber",
        "awardTitle",
        "awardURI",
    }
)

#: DataCite's controlled set of funder identifier schemes.
FUNDER_IDENTIFIER_TYPES = ("ISNI", "GRID", "Crossref Funder ID", "ROR", "Other")


def validate_funding(value):
    """Validate that ``value`` is a list of DataCite funding references.

    A project may carry several funding records, so the stored value must be
    a list. Each member must be an object carrying only keys from
    ``FUNDING_REFERENCE_KEYS``, with ``funderName`` required and every other
    key optional. A ``funderIdentifierType``, when present, must be one of
    DataCite's identifier schemes.
    """
    if not isinstance(value, list):
        raise ValidationError(
            _("Funding must be a list of funding reference objects."),
            code="funding_not_list",
        )

    for record in value:
        if not isinstance(record, dict):
            raise ValidationError(
                _("Funding must be a list of funding reference objects."),
                code="funding_not_list",
            )

        unknown_keys = set(record) - FUNDING_REFERENCE_KEYS
        if unknown_keys:
            raise ValidationError(
                _(
                    "'%(keys)s' is not a recognised funding reference field. "
                    "Accepted fields are: %(accepted)s."
                ),
                code="funding_unknown_key",
                params={
                    "keys": ", ".join(sorted(unknown_keys)),
                    "accepted": ", ".join(sorted(FUNDING_REFERENCE_KEYS)),
                },
            )

        if not record.get("funderName"):
            raise ValidationError(
                _("Every funding reference must name a funder."),
                code="funding_missing_funder_name",
            )

        identifier_type = record.get("funderIdentifierType")
        if identifier_type and identifier_type not in FUNDER_IDENTIFIER_TYPES:
            raise ValidationError(
                _(
                    "'%(value)s' is not a funder identifier scheme DataCite "
                    "defines. Accepted schemes are: %(schemes)s."
                ),
                code="funding_invalid_identifier_type",
                params={
                    "value": identifier_type,
                    "schemes": ", ".join(FUNDER_IDENTIFIER_TYPES),
                },
            )

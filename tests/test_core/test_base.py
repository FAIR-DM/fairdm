"""Tests for the FairDM model metadata layer (fairdm/core/base.py)."""

import pytest

from fairdm.config import Authority, Citation
from fairdm.core.base import Metadata
from fairdm_demo.models import RockSample


class _NewMeta:
    description = "A rock sample collected in the field."
    authority = Authority(name="FairDM", short_name="FDM", website="https://fairdm.org")
    citation = Citation(text="FairDM (2026). Rock samples.", doi="10.0000/example")
    repository_url = "https://example.org/repo"


class _Empty:
    pass


@pytest.mark.django_db
class TestMetadataToDict:
    """Tests for Metadata.to_dict()."""

    def test_to_dict_serialises_authority_and_citation(self):
        """Authority and Citation are frozen dataclasses, so to_dict() must expand
        them into plain dictionaries rather than call a method they do not have."""
        metadata = Metadata(RockSample, _NewMeta, _Empty(), _Empty())

        result = metadata.to_dict()

        assert result["authority"] == {
            "name": "FairDM",
            "short_name": "FDM",
            "website": "https://fairdm.org",
        }
        assert result["citation"] == [
            {"text": "FairDM (2026). Rock samples.", "doi": "10.0000/example"}
        ]

    def test_to_dict_leaves_authority_none_when_unset(self):
        """An unset authority stays None rather than becoming an empty dictionary."""

        class NoAuthority:
            description = "A rock sample."
            repository_url = "https://example.org/repo"

        metadata = Metadata(RockSample, NoAuthority, _Empty(), _Empty())

        assert metadata.to_dict()["authority"] is None

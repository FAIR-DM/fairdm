"""Tests for identifier type filtering based on contributor type."""

from django.test import TestCase

from fairdm.contrib.contributors.forms.forms import UserIdentifierForm, UserIdentifierFormSet
from fairdm.contrib.contributors.models import ContributorIdentifier, Organization, Person
from fairdm.core.vocabularies import FairDMIdentifiers


class TestIdentifierFiltering(TestCase):
    """Test that identifier choices are filtered based on contributor type."""

    def setUp(self):
        """Set up test vocabulary."""
        self.vocab = FairDMIdentifiers()
        self.person_vocab = self.vocab.from_collection("Person")
        self.org_vocab = self.vocab.from_collection("Organization")

    def test_person_identifier_choices(self):
        """Person form should only show ORCID and ResearcherID."""
        person = Person(first_name="Test", last_name="Person")
        form = UserIdentifierForm(contributor_instance=person)

        choices = [choice[0] for choice in form.fields["type"].choices]
        expected = self.person_vocab.values

        assert set(choices) == set(expected)
        assert "ORCID" in choices
        assert "RESEARCHER_ID" in choices
        assert "ROR" not in choices
        assert "WIKIDATA" not in choices

    def test_organization_identifier_choices(self):
        """Organization form should only show ROR, Wikidata, ISNI, and Crossref Funder ID."""
        org = Organization(name="Test Organization")
        form = UserIdentifierForm(contributor_instance=org)

        choices = [choice[0] for choice in form.fields["type"].choices]
        expected = self.org_vocab.values

        assert set(choices) == set(expected)
        assert "ROR" in choices
        assert "WIKIDATA" in choices
        assert "ISNI" in choices
        assert "CROSSREF_FUNDER_ID" in choices
        assert "ORCID" not in choices
        assert "RESEARCHER_ID" not in choices

    def test_generic_identifier_choices(self):
        """Form without contributor instance should show all identifier types."""
        form = UserIdentifierForm()

        choices = [choice[0] for choice in form.fields["type"].choices if choice[0]]  # Exclude empty choice
        expected = self.vocab.values

        assert set(choices) == set(expected)

    def test_vocabulary_collection_counts(self):
        """Verify the vocabulary collections have the expected number of items."""
        assert len(self.person_vocab.values) == 2
        assert len(self.org_vocab.values) == 4
        assert len(self.vocab.values) == 6

    def test_existing_identifier_excluded_from_new_forms(self):
        """When contributor has an identifier, new forms should not show that type in choices."""
        person = Person.objects.create(first_name="Test", last_name="Person", email="test@example.com")

        # Add an ORCID identifier
        vocab = FairDMIdentifiers()
        orcid_uri = next(c.uri for c in vocab.concepts() if "ORCID" in c.pref_label)
        ContributorIdentifier.objects.create(contributor=person, type=orcid_uri, value="0000-0002-1825-0097")

        # Create formset with existing data
        formset = UserIdentifierFormSet(
            instance=person, queryset=person.identifiers.all(), form_kwargs={"contributor_instance": person}
        )

        # First form (existing ORCID) should include ORCID in choices (for current value)
        existing_form_choices = [v for v, _label in formset.forms[0].fields["type"].choices if v]
        assert orcid_uri in existing_form_choices

        # Second form (new) should NOT include ORCID in choices
        new_form_choices = [v for v, _label in formset.forms[1].fields["type"].choices if v]
        assert orcid_uri not in new_form_choices

        # Only ResearcherID should be available for new forms
        researcher_id_uri = next(c.uri for c in vocab.concepts() if "ResearcherID" in c.pref_label)
        assert researcher_id_uri in new_form_choices
        assert len(new_form_choices) == 1  # Only ResearcherID left

    def test_formset_max_num_for_person(self):
        """Max number of forms should equal number of person identifier types (2)."""
        from fairdm.contrib.contributors.plugins import Identifiers

        person = Person.objects.create(first_name="Test", last_name="Person", email="test@example.com")
        plugin = Identifiers()
        plugin.object = person

        factory_kwargs = plugin.get_factory_kwargs()
        assert factory_kwargs["max_num"] == 2

    def test_formset_max_num_for_organization(self):
        """Max number of forms should equal number of organization identifier types (4)."""
        from fairdm.contrib.contributors.plugins import Identifiers

        org = Organization.objects.create(name="Test Organization", email="org@example.com")
        plugin = Identifiers()
        plugin.object = org

        factory_kwargs = plugin.get_factory_kwargs()
        assert factory_kwargs["max_num"] == 4

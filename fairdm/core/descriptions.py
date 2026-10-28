"""The vocabulary-driven descriptions form shared across the core record types.

A related model carries at most one description of each vocabulary type, so
this is a single form with one field per concept rather than a row set.
Driving the field set off the collection lets the descriptions page grow
when the vocabulary does, with no code change.
"""

from django import forms
from django.utils.translation import get_language

from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH


class VocabularyDescriptionsForm(forms.Form):
    """One text area per concept in the collection a related model's ``type`` offers.

    Each field is named after the concept's address, labelled with its name and helped by
    its definition.

    Args:
        *args: Positional arguments passed to ``forms.Form``.
        related_model: The description model whose ``type`` collection defines the fields
            and which stores the rows.
        instance: The record the descriptions belong to.
        **kwargs: Keyword arguments passed to ``forms.Form``.
    """

    def __init__(self, *args, related_model, instance, **kwargs):
        self.related_model = related_model
        self.instance = instance
        super().__init__(*args, **kwargs)

        existing = {
            row.type_id: row.value
            for row in related_model._default_manager.filter(related=instance)
        }
        self.concepts = {
            concept.uri: concept for concept in related_model.get_type_concepts()
        }
        for name, concept in self.concepts.items():
            self.fields[name] = forms.CharField(
                required=False,
                label=concept.display_label(),
                help_text=self.definition(concept),
                widget=forms.Textarea,
                initial=existing.get(concept.uri, ""),
                max_length=DESCRIPTION_MAX_LENGTH,
            )

    def definition(self, concept):
        """Return a concept's definition in the reading language, else in any language.

        Args:
            concept: A ``controlled_vocabularies.Record``.

        Returns:
            The definition, or an empty string when the concept has none.
        """
        entries = [
            entry for entry in concept.values("skos:definition") if "@value" in entry
        ]
        language = (get_language() or "").lower()
        for entry in entries:
            if entry.get("@language", "").lower() == language:
                return entry["@value"]
        return entries[0]["@value"] if entries else ""

    def save(self):
        """Write, update or delete one row per area, deleting the row when the area is blank."""
        for name, concept in self.concepts.items():
            value = (self.cleaned_data.get(name) or "").strip()
            row = self.related_model._default_manager.filter(
                related=self.instance, type=concept.uri
            ).first()
            if value:
                if row is None:
                    self.related_model._default_manager.create(
                        related=self.instance, type=concept, value=value
                    )
                elif row.value != value:
                    row.value = value
                    row.save()
            elif row is not None:
                row.delete()

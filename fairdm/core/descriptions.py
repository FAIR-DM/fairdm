"""The vocabulary-driven descriptions form shared across the core record
types (plan P2).

A related model carries at most one description of each vocabulary type, so
this is a single form with one field per concept rather than a row set -
driving the field set off the vocabulary is what lets the descriptions page
grow with no code change.

This module is not itself a page, view or URL - later stories register those
and use the form declared here.
"""

from django import forms


class VocabularyDescriptionsForm(forms.Form):
    """One text area per concept in ``related_model``'s vocabulary, labelled
    with the concept's name and helped by its definition."""

    def __init__(self, *args, related_model, instance, **kwargs):
        self.related_model = related_model
        self.instance = instance
        super().__init__(*args, **kwargs)

        existing = {
            row.type: row.value
            for row in related_model._default_manager.filter(related=instance)
        }
        for type_value in related_model.VOCABULARY.values:
            concept = related_model.VOCABULARY.get_concept(type_value)
            self.fields[type_value] = forms.CharField(
                required=False,
                label=concept.label(),
                help_text=concept.definition(),
                widget=forms.Textarea,
                initial=existing.get(type_value, ""),
            )

    def save(self):
        """Write, update or delete one row per area: a non-blank area
        becomes one row of its type, blank (including whitespace-only)
        removes any row already stored for that type."""
        for type_value in self.related_model.VOCABULARY.values:
            value = (self.cleaned_data.get(type_value) or "").strip()
            row = self.related_model._default_manager.filter(
                related=self.instance, type=type_value
            ).first()
            if value:
                if row is None:
                    self.related_model._default_manager.create(
                        related=self.instance, type=type_value, value=value
                    )
                elif row.value != value:
                    row.value = value
                    row.save()
            elif row is not None:
                row.delete()

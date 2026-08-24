# Filtering Projects by Vocabulary-Specific Keywords

`ProjectFilter` (`fairdm.core.project.filters.ProjectFilter`) can offer one keyword filter per
controlled vocabulary, so a portal can let visitors narrow projects by science keywords,
platforms, instruments, or any other `research_vocabs` vocabulary, each as its own filter field.

Editing a project's keywords through the portal is not part of this: keywords are deferred until
the controlled-vocabulary package is properly integrated (issue #171). This page covers filtering
only — reading and searching by keywords that already exist on projects.

## Configuring which vocabularies filter

Which vocabularies get their own filter field is a setting, not a subclass:

```python
# settings.py
FAIRDM_PROJECT = {
    "keywords": [
        "fairdm.core.vocabularies.FairDMRoles",
        # "myapp.vocabularies.ScienceKeywords",
    ],
}
```

Each entry is the dotted import path to a `research_vocabs` vocabulary class. `ProjectFilter`
reads the list with `get_setting("PROJECT", "keywords")` and, for each vocabulary, adds a
`django_filters.ModelMultipleChoiceFilter` restricted to concepts from that vocabulary that at
least one project actually uses.

## How filter names are generated

The filter field name is the vocabulary class's own name, prefixed with `keywords_`:

```
"fairdm.core.vocabularies.FairDMRoles"  →  keywords_FairDMRoles
```

Not the vocabulary's slug — `ProjectFilter.__init__` (`fairdm/core/project/filters.py`) uses
`vocab_class.__name__` for the field name, and the vocabulary's registered `name` (its `_meta.name`)
only to scope the queryset to that vocabulary's concepts.

## No configured vocabularies

If `FAIRDM_PROJECT["keywords"]` is empty or unset, `ProjectFilter` falls back to one generic
`keywords` filter spanning every vocabulary, rendered as a plain checkbox list rather than an
autocomplete widget.

## The filter widget

Each per-vocabulary filter uses `ConceptMultiSelect`
(`fairdm.contrib.autocomplete.fields.ConceptMultiSelect`), which wires up a
`django-autocomplete-light` widget scoped to that one vocabulary automatically:

```python
from fairdm.contrib.autocomplete.fields import ConceptMultiSelect

field = ConceptMultiSelect(vocabulary="fairdm.core.vocabularies.FairDMRoles")
```

`vocabulary` accepts either the class itself or its dotted path. This is what `ProjectFilter`
constructs internally for each configured vocabulary — a portal does not need to build one by
hand to get vocabulary-scoped filtering.

## Concept autocomplete endpoint

`ConceptAutocomplete` (`fairdm.contrib.autocomplete.views.ConceptAutocomplete`), mounted at
`/autocomplete/concept/`, backs every concept widget so large vocabularies load concepts on
demand rather than shipping the whole queryset to the browser. It requires an authenticated
request and filters by vocabulary name via a forwarded field or a `?vocabulary=` query parameter:

```python
from dal import autocomplete
from django import forms

field = forms.ModelMultipleChoiceField(
    queryset=Concept.objects.all(),
    widget=autocomplete.ModelSelect2Multiple(
        url="autocomplete:concept",
        forward=["vocabulary_name"],
    ),
)
```

`ConceptMultiSelect` and `ConceptSelect` build this widget for you, scoped to one vocabulary, so
reaching for `autocomplete.ModelSelect2Multiple` directly is only needed for a widget that isn't
tied to a single vocabulary.

## Performance

Per-vocabulary filters only query concepts that at least one project actually uses
(`projects__isnull=False`) and call `.distinct()` to avoid duplicate rows. For a vocabulary large
enough that this query itself is slow, an index on the `Concept` model's `vocabulary_id` field
helps.

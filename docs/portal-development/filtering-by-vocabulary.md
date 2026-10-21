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

## Selecting more than one keyword

Selecting two keywords in a filter keeps the projects that carry both, so each further keyword
narrows the list. The same holds across filters: a keyword chosen in one vocabulary's filter and
another chosen in a second vocabulary's filter keep the projects that carry both.

```python
from fairdm.core.project.filters import ProjectFilter
from fairdm.core.project.models import Project

filterset = ProjectFilter(
    data={"keywords_FairDMRoles": [first.pk, second.pk]},
    queryset=Project.objects.all(),
)
filterset.qs  # the visible projects that carry both keywords
```

## No configured vocabularies

If `FAIRDM_PROJECT["keywords"]` is empty or unset, `ProjectFilter` falls back to one generic
`keywords` filter spanning every vocabulary, rendered as a plain checkbox list rather than the counted
control.

## The filter widget

Each per-vocabulary filter draws its concepts with `mvp_forms.widgets.TomSelectMultiple(counted=True)`:
a searchable list with a tick beside each chosen concept and a count in place of the chosen
names. The list holds only the concepts of that vocabulary that a project uses, so it needs no
address of its own to load them from.

A portal that builds a keyword filter of its own uses the same widget:

```python
import django_filters
from mvp_forms.widgets import TomSelectMultiple
from research_vocabs.models import Concept

keywords = django_filters.ModelMultipleChoiceFilter(
    field_name="keywords",
    queryset=Concept.objects.filter(vocabulary__name="fairdm-roles", projects__isnull=False).distinct(),
    conjoined=True,
    widget=TomSelectMultiple(counted=True),
)
```

## Performance

Per-vocabulary filters only query concepts that at least one project actually uses
(`projects__isnull=False`) and call `.distinct()` to avoid duplicate rows. For a vocabulary large
enough that this query itself is slow, an index on the `Concept` model's `vocabulary_id` field
helps.

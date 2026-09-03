# Record-Page Building Blocks

Project, Dataset, Sample and Measurement each edit the same two shapes of related data on their own
page: a row set (dates, identifiers) and a fixed set of vocabulary-driven description areas. Rather
than each record type rebuilding these, `fairdm/core/related_records.py`, `fairdm/core/formsets.py`
and `fairdm/core/descriptions.py` declare the shared pieces once. None of these three modules is
itself a page, view or URL — a record type's own page (for example
`fairdm.core.project.plugins.Update`) assembles them.

## Related-record row sets

A related record that carries just a `type`/`value` pair — a date, an identifier — is edited as a
row set rather than as individual form fields, so adding a new type is a vocabulary entry rather
than a new field, a new save branch and a new test.

`RelatedRecordInline` (`fairdm.core.related_records.RelatedRecordInline`) is the shared base, built
on django-mvp's `InlineFormSet`. It fixes the two settings every one of these row sets needs:

- `fields = ("type", "value")` — a tuple, not a list. `BaseInlineFormSet.__init__` appends the
  parent foreign key's name to `form._meta.fields` in place; a list here would be that same list,
  mutated on every formset built from it.
- `extra = 0` — no blank rows beyond the ones that already exist. Django's own default of three
  blank rows applies otherwise.

A subclass names only its `model`:

```python
from fairdm.core.related_records import RelatedRecordInline
from .models import ProjectDate


class ProjectDateInline(RelatedRecordInline):
    model = ProjectDate
```

`fairdm.core.related_records` declares one such subclass per related model on Project and Dataset:
`ProjectDateInline`, `ProjectIdentifierInline`, `DatasetDateInline`, `DatasetIdentifierInline`. A
record's page lists the ones it wants by setting `inlines` directly — django-mvp's `InlinesMixin`
is mixed into `MVPUpdateView` (and so into `FairDMUpdateView`) by default, rather than being added
to each page's own base classes:

```python
class Update(Plugin, FairDMUpdateView):
    model = Project
    inlines = [ProjectIdentifierInline, ProjectDatesInline]
```

(`ProjectDatesInline` is `ProjectDateInline` plus the date-ordering rule below — see
`fairdm.core.project.plugins.ProjectDatesInline`.)

## Keeping a date pair in order

Only some record types have an ordered pair of dates, and the two that do today don't agree on
names — a project's are `Start`/`End`, a dataset's are `CollectionStart`/`CollectionEnd`. Rather than
a rule that silently checks nothing on a record type whose vocabulary doesn't have the pair,
`date_ordering_formset` (`fairdm.core.formsets.date_ordering_formset`) is opt-in and parameterised:

```python
def date_ordering_formset(start_type, end_type, message):
    """Return a BaseInlineFormSet that refuses a backwards start_type/end_type
    pair across the whole formset."""
```

`message` is passed whole (with `%(start)s`/`%(end)s` placeholders) rather than assembled from a
noun, so each record type states its own date vocabulary in its own words and the sentence stays
translatable as one unit. The check reads `start_type`/`end_type` values directly off each form's
`cleaned_data` rather than looking a sibling row up in the database — a per-row `clean()` that
queries the database sees no unsaved sibling when both rows are new in the same submission.

Project's own dates inline builds its formset this way:

```python
from fairdm.core.formsets import date_ordering_formset
from fairdm.core.related_records import ProjectDateInline
from .models import ProjectDate


class ProjectDatesInline(ProjectDateInline):
    formset = date_ordering_formset(
        ProjectDate.START_TYPE,
        ProjectDate.END_TYPE,
        _("The project's end date (%(end)s) cannot be before its start date (%(start)s)."),
    )
```

A record type with no ordered pair (Sample, Measurement) simply never calls
`date_ordering_formset` — that omission is a decision each record type states, not a rule left to
run and find nothing.

### Comparing two partial dates

Every date rule in the platform rests on one comparison, `precedes`
(`fairdm.core.dates.precedes`). Use it rather than comparing two `PartialDate` values with `<`.

```python
from fairdm.core.dates import precedes

precedes(start.value, end.value)  # True when start is earlier than end
```

A `PartialDate` folds precision into its own ordering, so comparing a year-precision value against
a day-precision one directly gives an answer that depends on which is which rather than on the
dates. `precedes` compares at the coarser of the two precisions: years alone if either value is
year-precision, year and month if either is month-precision, and the full date only when both carry
day precision. A project running from `2020` to `2020-03-14` is therefore accepted rather than
refused, because at year precision the two are the same year.

The comparison is shared; the rules built on it are not. Each record type still states its own date
rule in its own words, which is deliberate — see spec 004, Article III.

## One text area per vocabulary concept

A related model that carries at most one description of each vocabulary type — see
`ProjectDescription.VOCABULARY` — is edited as one text area per concept rather than an add/remove
row set, because the model allows exactly one row per type.
`VocabularyDescriptionsForm` (`fairdm.core.descriptions.VocabularyDescriptionsForm`) generates that
field set from the related model's vocabulary, so the descriptions page grows with the vocabulary
and needs no code change:

```python
class Descriptions(Plugin, MetadataMixin, MVPFormView):
    model = Project
    form_class = VocabularyDescriptionsForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["related_model"] = ProjectDescription
        kwargs["instance"] = self.base_object
        return kwargs
```

Each field is labelled with its concept's name and helped by its concept's definition. Saving writes,
updates or deletes one row per area: a non-blank area becomes one row of its type, and a blank one
(including whitespace-only) removes any row already stored for that type.

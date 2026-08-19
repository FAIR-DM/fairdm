# Research — 006 Core Measurements

Eight questions the plan depended on. Each was settled against the running code rather than by
reading, and the commands that settled them are named so anyone can repeat them.

## R1 — How a value with an uncertainty should be rendered

**Question.** FR-038 requires a measurement to render its value with its uncertainty and its units.
`print_value()` currently builds the string itself and reads an attribute that does not exist.

**Finding.** The framework already renders this correctly, and better than the model does. Pint's
`Quantity.plus_minus()` returns a `Measurement`, and `fairdm/templatetags/fairdm.py` installs a
formatter on the unit registry whose `format_uncertainty` and `format_measurement` produce exactly
the wanted shape. Measured:

```
(5.0 * ureg.meter).plus_minus(0.3)
  str(...)  -> '5.00 ± 0.30 m'
  .value    -> <Quantity(5.0, 'meter')>
  .error    -> <Quantity(0.3, 'meter')>
  hasattr('err') -> False
```

**Decision.** `print_value()` does not build a string. It returns `str(self.get_value())` and lets
the registry's formatter do the work, which also keeps one definition of how a quantity looks rather
than two that can drift. The `err` branch is removed rather than corrected — it was never a typo for
`error`, it was a second renderer nobody needed.

**Risk this raises.** The formatter is installed as an import side effect of a template tag module
(`ureg.formatter = MyFormatter(registry=ureg)` at module scope). Django imports template tag modules
lazily, when a template first loads them, so a value rendered outside a template — in an export, in
an API response, in a management command — can get pint's default `(5.00 +/- 0.30) meter` instead.
The registration belongs somewhere loaded at application startup. The plan carries this as its own
task; it is a real defect and it is what makes the requirement testable outside a template.

## R2 — How to narrow by a range of dates

**Question.** FR-034 requires narrowing by a range of measurement dates. The existing test for this
is skipped with the note "PartialDateField filtering requires investigation - field validation
complex".

**Finding.** It is not complex, and the field is not the problem. `MeasurementDate.value` is a
`PartialDateField` (dates may be a year, a year and month, or a full date). Range lookups work:

```
stored: ['2023-01', '2024-05-04', '2025']
value__gte='2024-01-01'          -> 2 rows
value__lte='2024-12-31'          -> 2 rows
value__gte=PartialDate('2024-01-01') -> 2 rows
value__gte=datetime.date(2024,1,1)   -> ValidationError
```

**Decision.** The filter passes a string or a `PartialDate`, never a `datetime.date`. That rules out
`django_filters.DateFilter`, whose form field cleans input to a `date` before it reaches the
queryset — which is what the skipped test actually hit. The date-range filters use a character
filter that hands the value through, validating the partial-date format on the way.

## R3 — Putting the mixins into what the registry generates

**Question.** FR-028 requires a measurement type supplying neither a form nor a filter set to
receive the mixins' behaviour anyway. Nothing does this today.

**Finding.** The pattern exists for samples and is documented in place. `FormFactory` has
`get_base_form_class()` (`fairdm/registry/factories.py:172`), which returns
`type("SampleFormBase", (SampleFormMixin, ModelForm), {})` for a sample type, because the form mixin
is a plain mixin and needs `ModelForm` mixed in. `FilterFactory` has `get_base_filterset_class()`
(`:479`), which returns `SampleFilterMixin` directly, because that mixin is already a `FilterSet`
subclass and needs no wrapping.

**Decision.** Add the measurement branch to both, matching each shape: the form mixin is wrapped
with `ModelForm`, the filter mixin is returned as it stands once R4 has made it a `FilterSet`.

## R4 — Why the filter mixin currently carries nothing

**Question.** FR-026 requires every filter the mixin declares to reach a filter set that inherits
it. The mixin declares none, and the concrete filter set that declares them all is out of scope.

**Finding.** The sample side hit the same wall from the other direction and solved it. Its docstring
records the reason: django-filter's metaclass collects declared filters from the class body and from
bases carrying `declared_filters`, which a plain Python class never has. So `SampleFilterMixin` is a
`django_filters.FilterSet` subclass whose `Meta` deliberately carries **no** `model` — setting one
would make the metaclass generate a full, unused filter set every time the class or any subclass is
defined.

Measured on the measurement side: a filter set built from `MeasurementFilterMixin` alone carries
`['dataset', 'sample', 'polymorphic_ctype']` and nothing else.

**Decision.** `MeasurementFilterMixin` becomes a `FilterSet` subclass with a model-less `Meta`, and
the filters move onto it from the concrete class. `Meta.fields` stays as a convenience list a
subclass's own `Meta` extends, which is how the demo's filter sets already use the sample one.

## R5 — Collapsing the two administrative base classes

**Question.** FR-045 requires one administrative class for the record and one base beneath it.
There are two of each.

**Finding.** `fairdm/core/measurement/admin.py` holds the configured pair: `MeasurementChildAdmin`
(inlines, fieldsets, autocomplete, read-only fields) and `MeasurementParentAdmin`, which is the one
actually registered and which discovers child models from the registry. `fairdm/core/admin.py` holds
a two-attribute `MeasurementAdmin` and a second `MeasurementParentAdmin` whose registration is
commented out and which discovers child models by walking subclasses instead.

The registry refers to the wrong pair twice: `config.py:377` validates a supplied admin against the
stub, and `factories.py:803` generates from it. Supplying the configured class to a configuration is
refused, with a message naming the stub. Nothing else imports either.

The demo's own admin classes inherit the configured base directly, which is why the defect is
invisible in the demo portal and why the registry tests pass — those tests import the stub under the
name `MeasurementChildAdmin` (`tests/test_registry/test_config.py:641`), so they assert against the
wrong class by construction.

**Decision.** Delete both classes in `fairdm/core/admin.py`, repoint the two registry references at
`fairdm.core.measurement.admin.MeasurementChildAdmin`, and correct the refusal message to name it.
The registry tests are rewritten to import the real class, which is what makes them fail if this
regresses.

## R6 — Which measurement types the type filter should offer

**Question.** FR-032 requires the type choices to be the registered measurement types.

**Finding.** The filter draws content types from a fixed list of two application labels
(`filters.py:151`). The measurement record's own label is `measurement`, so the base is absent; every
unrelated record in those two applications is present; and a portal's own types never can be. The
registry already answers this question for the administrative interface, which calls
`registry.measurements` and gets the registered model classes back.

**Decision.** The filter derives its choices from `registry.measurements` through
`ContentType.objects.get_for_models`, so a portal's own types appear and nothing else does.

## R7 — Whether the disabled permission tests describe a real problem

**Question.** Thirteen tests are switched off, with three distinct reasons, all deferring to a
specification that does not exist.

**Finding.** Two of the three reasons are false today. Granting view, change and delete on a dataset
gives all four corresponding rights over its measurements; a user holding nothing holds nothing;
creating a measurement whose sample belongs to another dataset succeeds.

The third reason was true and is now handled elsewhere. Guardian's own `assign_perm` raises when
handed a polymorphic subclass instance, because the permission is defined on the base record in a
different application. The framework's `fairdm.core.utils.assign_perm` normalises the instance
first, and with it the grant reads back — work that landed with the sample record.

**Decision.** The tests are re-enabled against `fairdm.core.utils.assign_perm`. The three that were
written against guardian's shortcut are rewritten rather than un-skipped, since the entry point they
used is the wrong one for this framework.

## R8 — What a framework measurement type carrying a value should look like

**Question.** FR-039 requires at least one measurement type distributed with the framework to
nominate a value and record an uncertainty, so the path is exercised.

**Finding.** No type does today. The framework already wraps django-pint's quantity fields in
`fairdm/db/fields.py` and re-exports them from `fairdm.db.models`, which is the same module the
measurement models already import their fields from, so no new dependency is involved.

Of the three demo types, `ICP_MS_Measurement` is the natural home: it already carries a
`concentration_ppb` and an `uncertainty_percent`, so it is the one whose science asks for the
convention.

**Decision.** `ICP_MS_Measurement` gains a `value` and an `uncertainty` as quantity fields. The
existing `concentration_ppb` and `uncertainty_percent` stay — they are what a portal's own type
looks like before it adopts the convention, and keeping both makes the demo show the difference.
The migration is additive and both fields are optional, so no existing row needs a value.

## What was not researched, and why

- **The unit library's API beyond `plus_minus`.** The convention needs one call and it is already in
  use. Widening it is out of scope.
- **Whether the value convention should be enforced rather than optional.** Settled in the
  specification: a type nominating no value reports its name, and that is a normal state.
- **How a measurement page should look.** That belongs to R16.

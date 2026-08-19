# Decisions — 006 Core Measurements

The original specification was written on 2026-02-16 as a companion to the sample specification, and
its own task list stopped part-way through: twenty-seven items ticked, four left open, and five of
its eight user stories reached GitHub as issues. It described seventy-two requirements across five
layers, twelve of which described the tests rather than the feature.

Unlike the sample rewrite, the vocabularies here are already correct — the metadata models draw from
measurement-scoped collections and have done since the sample work passed through. What this
rewrite found instead is a feature whose extension points do not connect: the mixins a portal
developer is meant to inherit carry almost nothing, the registry does not wire them into what it
generates, and the administrative base class the framework configures is not the one the registry
enforces or builds on.

This file records what the old text said, what the code does, which way each disagreement was
settled, and why. It is the reason the specification now says what it says.

Every decision was taken on 2026-08-19. Where one was settled without the maintainer present it is
marked **self-resolved**, and it stands unless he says otherwise.

## D-001 — Scope: the record and the reusable mixins, not the portal pages

**Settled by the maintainer, 2026-08-19.**

The original text owned the `Measurement` model, its metadata records, its queryset, its form, its
filter set, its admin and its permissions. The pages that create, list and edit a measurement do not
exist yet — roadmap item R16 covers them — so as with samples there is no sibling document to hand
the surface to.

The line is the one settled for samples: **a CRUD specification owns what its pages construct.**

**In scope** — the `Measurement` model and its fields, the polymorphic base and its integration with
the registry, the description, date and identifier records and their vocabularies, the queryset, the
administrative interface, the permission backend deriving a measurement's access from its dataset,
and `MeasurementFormMixin` and `MeasurementFilterMixin` together with their wiring into what the
registry generates.

**Out of scope, owned by the CRUD specification (R16)** — the list, detail, create, edit and delete
pages, the concrete `MeasurementForm` and `MeasurementFilter` those pages would instantiate, and the
view-level permission checks.

The evidence is the same shape as it was for samples. `MeasurementFormMixin` and
`MeasurementFilterMixin` are what a portal developer inherits. `MeasurementFilter` has no caller in
framework code at all — the one apparent reference, at `fairdm/views/base.py:262`, is a line inside
a docstring example.

## D-002 — Which samples a measurement may name: open, for now

**Settled by the maintainer, 2026-08-19.**

The old FR-011 and FR-014 required sample selection to be limited to samples "included in the
measurement's dataset", and the clarification session behind them described a workflow in which a
user first adds a sample to their own dataset, "either by creating new samples or adding references
to existing samples from other datasets", by way of `dataset.samples.add()`.

That workflow has never existed. `Sample.dataset` is a plain foreign key
(`fairdm/core/sample/models.py:77`) and `dataset.samples` is its reverse accessor. A sample belongs
to exactly one dataset, ownership is the only relationship there is, and adding a sample to a second
dataset would move it out of the first — taking it from the group that collected it.

That makes the old text self-contradictory. Its own headline story, US-2, exists so that a
measurement can describe a sample from a different dataset; FR-011 forbids exactly that, because
with a single foreign key "included in" and "belongs to" are the same set.

Settled: **no restriction here.** A measurement may name any sample. The measurement's dataset
governs the measurement and the sample's governs the sample, which is the separation US-2 was
after. Narrowing the choice is a later refinement and waits on the capability underneath it.

The capability itself — reusing another group's sample without taking ownership of it — is a real
want and is now tracked as issue #212. It is ordinary research practice to build on parts of an
existing dataset, and the framework cannot express it.

## D-003 — A measurement is a record with a page of its own

**Settled by the maintainer, 2026-08-19.**

The roadmap contradicted itself. R18 recorded a ruling taken when the plugin system was specified:
"a measurement is a component of the sample page rather than a record with a page of its own, so it
has no attachment point by design". Five plugins were removed on that basis, leaving
`fairdm/core/measurement/plugins.py` as a docstring explaining the removal. R16 says the opposite:
it names "a measurement has only a placeholder" as a deficiency and promises every registered
measurement type a detail page.

The code sides with R16. `get_absolute_url()` returns the measurement's own address
(`fairdm/core/measurement/models.py:164`), the URL is mounted, and there is a placeholder detail
view with a template behind it.

Settled in R16's favour, and for a reason neither roadmap entry gave: **every record in the database
needs a page of its own so that it can be audited, and having one keeps the editing interface
uniform across record types.** The earlier ruling was made when the question was where plugins
attach, and it generalised too far.

The consequences divide along the D-001 line. This specification owns the requirement that a
measurement has an address of its own rather than deflecting to its sample's (FR-009). The page
behind that address is R16's work. R18's note needs rewriting, and plugins become attachable to
measurements once R16 gives them pages — both routed out below.

## D-004 — The value convention is kept, and proved

**Settled by the maintainer, 2026-08-19. This is a defect.**

The old FR-015 and FR-016 describe a value-with-uncertainty convention: a measurement type may
nominate a `value`, and where it also records an `uncertainty` the reported value carries it,
rendered for a person as value ± uncertainty.

Neither method has ever done this.

- **No measurement type anywhere defines a value.** Not the base, not `ExampleMeasurement`, not
  `XRFMeasurement` (which has `concentration_ppm`), not `ICP_MS_Measurement` (which has
  `concentration_ppb` and `uncertainty_percent`). `get_value()` tests `hasattr(self, "value")`
  (`fairdm/core/measurement/models.py:136`) and so returns the record's name every time. The
  uncertainty branch below it has never executed.
- **The renderer reads an attribute that does not exist.** `print_value()` tests
  `hasattr(value, "err")` (`models.py:151`), but `plus_minus()` returns a measurement object whose
  attributes are `.value` and `.error` — checked against the installed library, version 0.25.3. So
  even for a type that did nominate a value, the required format is unreachable and the method falls
  through to the library's own rendering.

The old document also undercut itself: its OS-004 says the unit library is "available but not
required or enforced", while `get_value()` depends on it outright the moment an uncertainty exists.

Settled: **keep the convention and prove it.** `get_value()` reports whatever the type nominates and
falls back to the name; where an uncertainty is recorded the value carries it; `print_value()`
renders both with units intact. The attribute name is corrected. And FR-039 requires a measurement
type distributed with the framework to nominate a value and record an uncertainty, so the path is
exercised rather than described — the fault here was not the missing branch but that nothing ever
ran it.

The methods are load-bearing for display: `fairdm/core/sample/templates/sample/sample_detail.html:26`
and the measurement overview template both call `get_value`.

## D-005 — One administrative base, not two

**Settled by the maintainer, 2026-08-19. This is a defect.**

There are two administrative classes for measurement types and the framework uses the wrong one.

- `fairdm/core/measurement/admin.py:54` defines `MeasurementChildAdmin`: 176 lines carrying the
  inline editors, the fieldsets, the autocomplete configuration and the read-only fields.
- `fairdm/core/admin.py:33` defines `MeasurementAdmin`: two attributes, no configuration at all.
  Beside it sits a second `MeasurementParentAdmin` whose registration is commented out.

The registry points at the two-line class in both places it matters. Its validation of a supplied
administrative class requires inheritance from it (`fairdm/registry/config.py:377`), and the class
it generates for a type supplying none inherits from it (`fairdm/registry/factories.py:803`). I
supplied the configured class to a configuration and it was refused, with a message naming a class
that carries nothing.

The consequence is that a portal registering a measurement type and writing no administrative class
of its own gets none of the configuration this feature built. Samples take the same code path and
get their real base (`factories.py:799`).

The old text is not innocent here. Its FR-042 describes `MeasurementChildAdmin` as "the base class
defined in fairdm/core/admin.py, currently named MeasurementAdmin", so it intended one class and a
rename. What was built instead was a second class, and nothing was repointed.

Settled: **the configured class is the base.** The two-line class and the duplicate parent admin
beside it are removed, and the registry's validation and generation both point at the configured
one. FR-015 and FR-045 carry this.

The existing registry tests do not catch it, because they alias the two-line class under the other's
name to make their assertions (`tests/test_registry/test_config.py:641`) — a test passing for a
reason other than the behaviour it names.

## D-006 — Unmeasurable targets are dropped

**Settled by the maintainer, 2026-08-19.**

Five requirements and success criteria stated numbers nothing could measure as written: an 80%
reduction in queries against a "naive" baseline nobody defines (FR-024, SC-007, and a worked
example in the old M6), registering a type "in under 20 minutes" (SC-001), "60% less boilerplate"
reported by developers (SC-009), and page budgets of two seconds and one second (SC-002, SC-003).

This follows the same reasoning applied to the sample specification's query-reduction target. A
percentage against an undefined baseline is not a threshold, it is a number that will be asserted by
whatever the test happens to construct.

What replaces them is the property actually worth holding: **the number of queries does not grow
with the number of measurements** (FR-046, SC-010). That is checkable, it is what protects the page,
and it fails loudly when someone reintroduces a query per row.

## D-007 — Requirements about the tests are dropped

**Settled by the maintainer, 2026-08-19.**

Twelve of the seventy-two requirements, FR-061 to FR-072, described the test suite: which classes
must have unit tests, that factories must be used, and how the test directory must mirror the source
tree. One of them specified a directory layout that does not match where the tests actually live.

How tests are organised is settled by the project's own standards, which govern every feature rather
than being restated per specification. What belongs in a specification is what the tests must
establish, and that is now SC-012: no test covering this behaviour is skipped, and none passes when
the behaviour it names is removed.

That criterion is not a formality here. Seventeen tests in the measurement suite are skipped, and
thirteen of them are the permission tests — see D-011.

## D-008 — The registry does not wire the mixins into what it generates

**Self-resolved, 2026-08-19. This is a defect, and it is the largest omission this rewrite found.**

The maintainer's instruction for this rewrite was that the mixins stay in scope "plus any wiring
required to hook them into the registry system". That wiring exists for samples and does not exist
for measurements at all.

`fairdm/registry/factories.py:186` builds a generated form on `SampleFormMixin`, and `:492` builds a
generated filter set on `SampleFilterMixin`, so a specimen type supplying neither still receives the
mixins' widgets, dataset scoping and declared filters. There is no measurement equivalent anywhere
in the file. I generated the components for a registered measurement type and confirmed it: the form
carries neither mixin, and the generated filter set carries only the three filters the framework
derives from the model's own fields.

So the mixins reach only those portal developers who write their own form and filter classes, which
is precisely the group that needed them least.

Settled in the specification's favour by FR-028 and SC-006, which are the measurement wording of the
requirement the sample specification already carries.

## D-009 — Guidance text on the measurement form does not reach the form

**Self-resolved, 2026-08-19. This is a defect, and the second instance of it.**

`MeasurementForm.Meta` declares `help_text` (`fairdm/core/measurement/forms.py:150`). The attribute
Django reads is `help_texts`. All four strings are inert: instantiating the form gives an empty
guidance string for `name`, and the other three fields fall back to what the model says.

The identical mistake was found in `SampleForm` during the sample rewrite and fixed there. Nobody
looked for it anywhere else. FR-029 carries the requirement.

## D-010 — A control on the measurement form refers to an address that does not exist

**Self-resolved, 2026-08-19. This is a defect, and the second instance of it.**

The "add another dataset" control wraps its widget with `reverse_lazy("admin:core_dataset_add")`
(`fairdm/core/measurement/forms.py:64`). No such address exists; the dataset application's is
`admin:dataset_dataset_add`. I resolved both: the first raises, the second returns
`/admin/dataset/dataset/add/`.

Because the reversal is lazy it raises when the control renders rather than at import, and nothing
renders it — which is why a green suite has never noticed. The same defect was fixed in
`fairdm/core/sample/forms.py:64` during the sample rewrite, and again nobody carried the fix
across.

FR-030 generalises it: every address a form's controls refer to must resolve.

## D-011 — Thirteen permission tests are switched off against behaviour that works

**Self-resolved, 2026-08-19. This is a defect in the tests, not in the code.**

Of seventeen skipped tests in the measurement suite, thirteen are permission tests. Their stated
reasons are that inheritance of change and delete rights "needs debugging", that the factory fails
when a measurement names a sample from another dataset, and that rights cannot be granted directly
on a polymorphic subclass instance. All three defer to "Feature 007 (Permissions & Access Control)",
a specification that does not exist; the repository's `007` is the theme.

I ran each claim. A user holding view, change and delete over a dataset holds all four corresponding
rights over its measurements. A user holding nothing holds nothing. A right granted directly on a
registered measurement type reads back. A measurement in one dataset naming a sample from another is
created without complaint.

Only the third reason was ever true, and only of the permission library's own shortcut rather than
the framework's, which normalises a polymorphic instance to the record that owns the right — work
the sample rewrite landed. The tests were written against the wrong entry point and then disabled.

They are re-enabled against the framework's own function. SC-005 states what they must establish.

## D-012 — The measurement type filter offers the wrong types

**Self-resolved, 2026-08-19. This is a defect.**

The filter that narrows by measurement type draws its choices from every content type in two named
applications, `fairdm_core` and `fairdm_demo` (`fairdm/core/measurement/filters.py:151`). The
measurement record's own application is labelled `measurement`, so the base is absent from that
list; every unrelated record in those two applications is present; and a portal's own measurement
types, which live in the portal's application, can never appear.

The registry already knows which types are registered and the administrative interface already asks
it. FR-032 requires the filter to ask it too.

## D-013 — The filter mixin declares none of the filters it advertises

**Self-resolved, 2026-08-19. This is a defect.**

`MeasurementFilterMixin` documents itself as providing filtering by dataset, by sample, by
measurement type, a general search, description text and date ranges
(`fairdm/core/measurement/filters.py:20`). It declares none of them. Every one is declared on the
concrete `MeasurementFilter` below it, which D-001 places out of scope.

A filter set built from the mixin alone carries three filters, all of them derived automatically
from the model's fields. There is no general search, no description filter and no date range.

This is the same shape as the sample rewrite's finding and its opposite in cause. There the mixin
declared its filters and the library's metaclass never collected them, because a plain mixin carries
no declared filters for the metaclass to find. Here the mixin declares nothing to lose. Both leave a
portal developer inheriting an extension point that does not extend anything.

The filters move onto the mixin, which is what FR-026 requires and what D-001 makes necessary: the
substance has to live in the part that stays.

## D-014 — The framework's own fixtures create a record the specification forbids

**Self-resolved, 2026-08-19. This is a defect.**

FR-001 of the old text required direct creation of a bare measurement to be prevented. The model's
validation does refuse it (`fairdm/core/measurement/models.py:111`), but validation does not run on
a direct create, and `MeasurementFactory` is declared against the bare record
(`fairdm/factories/core.py:597`), so the framework's own fixtures produce exactly what the
specification forbids. The measurement test suite relies on this.

The sample specification settled the same question and closed it: creating a bare sample is refused
through validation, through a form, through the administrative interface and through the manager,
and the framework's fixtures do not create one. `SampleFactory` now refuses.

The measurement wording is FR-011 and SC-002, matching it.

## D-015 — What the old text called current issues, and what remains of them

**Self-resolved, 2026-08-19.**

The old document closed with six "current code issues to address". Three are already fixed and are
recorded here so that nobody re-opens them:

- **The vocabulary mismatch is gone.** Its headline complaint was that the description and date
  records drew from the sample collections. They draw from the measurement collections
  (`fairdm/core/measurement/models.py:184`, `:195`), and the identifier record draws from the
  measurement collection rather than the unscoped vocabulary (`:208`) — narrower than the old text
  asked for, and correct. I read the members of all four: descriptions, dates, identifiers and
  roles each return a measurement-specific set.
- **The plugin mismatch is gone.** `plugins.py` no longer configures anything; the plugin system
  specification emptied it. The old FR-059 and FR-060 have nothing left to correct.
- **The form's stale field exclusions are gone.** The form excludes nothing.

Two are real and are carried as requirements: the filter that was empty is now populated but on the
wrong class (D-013), and the queryset that did not exist now does (FR-046).

The sixth, the address that deflected to the sample, is resolved and settled by D-003.

## D-016 — Fields the record carries that the old text never mentioned

**Self-resolved, 2026-08-19.**

The measurement record carries a researcher's own label, an image, controlled-vocabulary terms and
free-form tags. None appears anywhere in the old seventy-two requirements, although the form offers
three of them and the configuration base lists the image among the fields every measurement type
gets.

They are real and they are carried, as FR-002 and FR-003. The label repeats the sample record's
treatment of the same field: it is the researcher's own, it is not a key, and two measurements in
different datasets may share one.

## Routed out

Findings this rewrite turned up that are not this specification's work.

| Finding | Where it goes |
|---|---|
| A sample cannot be reused by another dataset without its ownership moving, so provenance for shared material cannot be recorded | Issue #212, opened 2026-08-19 |
| R18 states that a measurement is a component of its sample's page rather than a record with a page of its own, which D-003 reverses | The roadmap, when it is next revised |
| Plugins become attachable to measurements once R16 gives them pages; the five removed on R18's reasoning may be worth restoring | R18, once R16 lands |
| The concrete `MeasurementForm` and `MeasurementFilter`, and the placeholder detail page, view and template | The CRUD specification, R16 (D-001, D-003) |

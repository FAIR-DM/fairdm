# Implementation Plan: Model registry and generated components

**Branch**: `002-fairdm-registry` | **Date**: 2026-08-17 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `specs/002-fairdm-registry/spec.md`

## Summary

A portal declares its sample and measurement types by registering a configuration class. The
configuration names a field list, and six component classes follow from it: form, table, filter set,
serializer, import and export resource, and admin. Each is replaceable by a supplied class, and each
accessor is overridable in code. Configuration is validated while the model is registered, so a
mistake stops the process at import rather than surfacing as a broken page.

The technical approach is deliberately thin. Each of the six libraries already ships a way to build
its class from a model and a field list, so this feature is a field-list resolver, a table mapping
each component to its factory and its configuration attributes, and validation. There is no caching
layer, no resolver object and no abstraction above the factories.

## Technical Context

**Language/Version**: Python 3.13, Django 5.2 and 6.0

**Primary Dependencies**: django-tables2, django-filter, django-import-export, Django REST Framework,
django-crispy-forms with crispy-tailwind, django-polymorphic. All hard dependencies.

**Storage**: not applicable. Component generation never touches the database.

**Testing**: pytest with pytest-django, factory_boy for model factories

**Target Platform**: Linux server, any Django deployment

**Project Type**: installable Django framework package

**Performance Goals**: validating 100 registered models under 5 ms in total; producing all six
components for one model under 5 ms

**Constraints**: registration runs while Django populates the app registry, so nothing may require
database access; component classes must not be cached, so every accessor is called on the hot path
of a view

**Scale/Scope**: a portal registers on the order of ten to fifty types. Six components each.

## Constitution Check

*Gate: passed before Phase 0.*

- **Article I, Test-First** — every task below is a red-green pair, and each of the five stories has
  its acceptance scenarios expressed as tests before the behaviour exists.
- **Article II, Simplicity** — the design removes two abstractions rather than adding any: the cache
  and the separate resolver object. No new dependency.
- **Article III, Anti-Abstraction** — the six accessors are named methods over one component table,
  not a base class hierarchy. The override hook in User Story 4 is the one piece of indirection with
  no present second use, and it is justified below rather than waved through.
- **Article IV, Integration-First** — the contract is the six accessors and the introspection
  surface. Acceptance scenarios exercise them the way the framework and a portal do.
- **Article X, Test structure** — test modules mirror the source tree, tests group into
  `Test<Subject>` classes, one factory per model, shared setup in `conftest.py`.
- **Article XI, Cohesion** — behaviour lives on `ModelConfiguration`, `FairDMRegistry` and
  `FieldInspector` rather than in loose module functions. Field introspection stays on
  `FieldInspector` because the model is its subject and the factories already need it.
- **Article XIV, Configuration over custom plumbing** — this feature *is* that article's mechanism.
  Defaults are inferred where they can be, and overriding is available at three levels of effort.

**On Article III and the override hook.** Article III forbids future-proofing indirection without a
present second use, and no code in this repository overrides an accessor today. It is kept for two
reasons that Article III accommodates rather than contradicts. Article XI states the framework's
position directly: in a published framework a class is the extension point, and a portal developer
who needs different behaviour subclasses it and overrides one method. Article XIV names the registry
as the primary extension point. The hook is therefore the article-sanctioned shape for a framework
class, not speculative generality, and it costs nothing: the accessor has to exist regardless, and
making it the implementation rather than a delegate to a cached property is strictly less code than
what exists now.

**Complexity tracking**: nothing to declare. No new dependency, no new abstraction, two removed.

## Project Structure

### Documentation (this feature)

```text
specs/002-fairdm-registry/
├── spec.md          rewritten specification
├── decisions.md     the audit: what the old spec said, what the code did, how each was settled
├── research.md      measured figures and library findings
├── plan.md          this file
└── tasks.md         the task list, written greenfield then reconciled
```

The previous run's `data-model.md`, `quickstart.md`, `RESEARCH.md`, `contracts/`, `research/` and
`checklists/` describe the superseded design, including a protocol for a resolver that is being
deleted. They are removed as a task rather than patched.

### Source code

```text
fairdm/registry/
├── __init__.py      public surface: register, registry, ModelConfiguration
├── registry.py      FairDMRegistry, the register decorator, the module-level registry
├── config.py        ModelConfiguration, its metadata classes, the component table, validation
├── factories.py     one generator class per component
└── exceptions.py    the errors this feature raises

fairdm/utils/inspection.py   FieldInspector: default field list, per-field widget and filter
                             choice, related-path resolution

tests/test_registry/
├── conftest.py      test models, factories, fixtures
├── test_registry.py registration, lookup, introspection
├── test_config.py   field resolution, the accessors, validation, overrides
└── test_factories.py each generator

tests/test_utils/test_inspection.py

fairdm_demo/config.py                    registrations covering every tier
fairdm_demo/tests/test_registry_api.py   the demo's registrations behave as documented
```

## Phases

**Phase 0, research** — complete, in `research.md`.

**Phase 1, design** — complete. The design is small enough that the specification's Key Entities
section carries it, so there is no separate data model document. There are no wire contracts: this
feature's contract is a Python API, and it is expressed as the acceptance scenarios.

**Phase 2, tasks** — `tasks.md`, written as though the repository were empty and then reconciled
against the code. The reconciliation is what scopes implementation, and a task counts as satisfied
only with a code citation and a passing test that covers it.

**Phase 3, implementation** — the open tasks, story by story in priority order.

## Dependency on other work

The removal of the superseded inner-class configuration system and the unreachable registry code is
tracked separately as issue #140, on its own branch. Two tasks in this feature depend on it:

- The task asserting that `manage.py check` reports nothing from the registry needs the check module
  gone, which #140 removes.
- The task asserting no attribute bypasses an accessor needs the cached properties gone, which is
  this feature's work, but the dead accessors #140 removes would otherwise appear in the same audit.

Neither task duplicates a deletion #140 already owns.

## Risks

- **Per-request generation is linear in field count.** A portal registering a very wide model pays
  about 0.1 ms per field per component on each request. The specification's second non-functional
  requirement pins the ceiling, and the decision to accept this rather than pre-empt it with a cache
  is recorded as D1. If profiling ever shows a hot spot, caching returns behind an explicit,
  clearable store, not a descriptor.
- **Framework consumers currently reach around the accessors.** One reads a cached property and one
  builds its own serializer. Migrating them is in scope for User Story 4's audit task; correcting the
  feature that built the parallel serializer is not, and is recorded against that feature instead.
- **Story renumbering.** The introspection story was numbered US-2 before the rewrite and is now
  US-5. Its issue was adopted in place rather than replaced, and says so.

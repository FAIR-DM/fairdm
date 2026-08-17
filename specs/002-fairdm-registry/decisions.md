# Decisions — 002 Model registry and generated components

This records the audit behind the rewritten `spec.md`, dated 2026-08-17. Each entry states what the
previous specification said, what the code did, which way it was settled and why. It exists so that
a later reader can tell a deliberate narrowing from an oversight.

The previous specification was written in January 2026 across two clarification sessions that
disagreed with each other, and the implementation followed neither consistently. Where the code and
the specification disagreed, the code was not assumed to be right.

---

## D1 — Component classes are never cached

**Previous specification**: contradicted itself. The 2026-01-08 session settled on generating every
component eagerly at registration. The 2026-01-12 session replaced that with lazy generation cached
by `cached_property`. Neither pass removed the earlier text, so the same document carried
`NFR-002` ("no lazy generation"), `SC-008` ("generated components are cached at startup"), and the
Key Entities note that components "are created eagerly at registration time (not lazily on first
use)", alongside eleven requirements describing lazy generation on first property access.

**Code**: lazy, with six `cached_property` accessors.

**Settled**: no caching at any tier. An accessor generates or resolves its class on every call.

**Why**: measured. Generating the components a page needs costs 0.18 ms for a table and filter set
on a six-field model, and 1.08 ms for a table, form and filter set on a ten-field model, at roughly
0.1 ms per field per component. Rendering a twenty-cell table fragment in the same process costs
0.12 ms, and a real page renders far more than that. Django's own `ModelFormMixin.get_form_class()`
calls `modelform_factory` on every request with no caching, so this is the framework's own pattern
rather than a departure from it. The cache also had a cost that was not obvious: a cached attribute
is read without consulting the method a portal may have overridden, which defeated the override
mechanism described in D2.

---

## D2 — The accessor is a method, and there is only one of them

**Previous specification**: `FR-023` required component access through properties implemented as
`cached_property`, and named the properties as the API.

**Code**: implemented both. The properties carried the logic. Six one-line methods delegated to
them and were documented as `.. deprecated:: Use the ... property instead.`

**Settled**: `get_<component>_class()` is the only public accessor. The properties are removed
rather than kept as aliases.

**Why**: the method form is the pattern Django uses across its view and mixin layer, so a portal
developer already knows it, and it is overridable where a `cached_property` is not. The previous
arrangement inverted the intent, and the inversion caused real drift: consumers that read the
docstrings moved onto the property and silently lost the ability to honour an override. An alias
would preserve that hazard, so the property is not kept. This was the original intent for the
feature and the previous specification recorded it wrongly.

---

## D3 — Ambiguous configuration is refused

**Previous specification**: an edge case stated that a custom Form "takes precedence" over field
lists, with no error.

**Code**: matched, silently.

**Settled**: declaring both a component's field list and its custom class raises
`ImproperlyConfigured` while the model is being registered.

**Why**: Django refuses the same combination on `ModelFormMixin` with "Specifying both 'fields' and
'form_class' is not permitted." The silent version leaves a developer holding a field list that has
no effect, with nothing in the logs and nothing to read that explains it. Following Django here
costs nothing and removes a whole class of confusion.

---

## D4 — Validation happens once, at registration

**Previous specification**: `FR-012` required validating field existence, related-path validity and
type compatibility with the usage context, all at registration time.

**Code**: three partial implementations. `_validate_fields` checked only the first segment of a
related path, so `dataset__nonexistent` registered cleanly. A Django system check module walked the
full path correctly but only runs from management commands, never on a WSGI or ASGI boot. A third
copy sat in a module nothing imported. Type compatibility was implemented nowhere.

**Settled**: validation happens while the model is registered and nowhere else. Every field name is
checked for existence and every segment of a related path is resolved. The system check module is
deleted. Type compatibility is dropped from the specification.

**Why, on placement**: registration runs at import, so it fails on every start including production.
A system check is a weaker guarantee wearing the same clothes. Two half-validators are worse than
one complete one, because each looks like the other's safety net.

**Why, on dropping type compatibility**: whether a field can be used by a component depends on the
backend, the declared lookups and third-party field types. Any rule the registry encodes will refuse
fields that would have worked, and false refusals in a framework are worse than a clear error from
the component library, which already raises on its own terms and is right more often. This narrows a
requirement that was signed off, deliberately, because the strict version cannot be made reliable.

**Cost measured before deciding**: strict validation of every path segment costs 0.0069 ms per
configuration, against 0.0046 ms for the first-segment check already running. For 100 registered
models that is 0.69 ms in total, and 1.7 ms at 250 models.

---

## D5 — No warnings about field counts

**Previous specification**: the 2026-01-08 session settled explicitly on "No limit or warnings, let
developers manage" for the number of columns in a table.

**Code**: shipped a system check warning for any configuration with more than 50 fields.

**Settled**: the specification was right and the code was wrong. The warning goes, along with the
rest of the check module under D4.

**Why**: a portal developer who lists 60 fields has a reason. This is the one adjudication in the
audit where the previous specification was clearer than what replaced it.

---

## D6 — Duplicate registration reports where the first one was

**Previous specification**: `FR-013` required the model name and the original registration location.

**Code**: raised the error with `original_location="Unknown"` and a `TODO` beside it.

**Settled**: requirement kept, and the module and qualified name of the first registration are
captured when it happens.

**Why**: import order decides which registration arrives first, and that order is not visible from
either file. Without the location the error names a problem the developer cannot locate.

---

## D7 — Presentation requirements removed as obsolete

**Previous specification**: `FR-018`, `FR-019` and `FR-020` required Bootstrap 5 styling, a
`django_tables2/bootstrap5.html` template and crispy-forms Bootstrap 5 integration.

**Code**: the framework depends on `crispy-tailwind`, and the constitution's Article XV requires the
interface to be built on the shared application shell using Tailwind and daisyUI.

**Settled**: these requirements are removed rather than restated for Tailwind.

**Why**: they were stale, and they do not belong to this feature in either form. Which stylesheet a
generated component renders under is a property of the theme, and pinning it in the registry's
specification would make a theme change a registry change. The rewritten specification says nothing
about styling.

---

## D8 — A missing registration raises

**Previous specification**: silent on the question.

**Code**: `Model.config` returned `None` for an unregistered model, and callers such as the
import and export views then dereferenced it.

**Settled**: requesting the configuration of an unregistered model raises and names the model.
`is_registered()` is the way to ask without raising.

**Why**: returning `None` converts a missing registration into an `AttributeError` at a call site
some distance from the cause. Raising at the point of the question names the actual problem.

---

## D9 — The configuration class is a plain class

**Previous specification**: silent on the question.

**Code**: `ModelConfiguration` was a `@dataclass`. Because subclasses declare class attributes, and
the generated `__init__` sets every field to its default as an instance attribute, the class
attributes were shadowed. Around 80 lines of `__post_init__` then copied them back, with a separate
rule per attribute for deciding what counted as unset.

**Settled**: a plain class with class attributes.

**Why**: a registration class is a declaration, which is how `Meta` and `ModelAdmin` are written and
what a portal developer expects to write. The dataclass fought that shape and then needed bespoke
code to undo itself. Removing the decorator removes the block entirely.

---

## D10 — Admin registration failures propagate

**Previous specification**: silent on the question.

**Code**: admin site registration was wrapped in a bare `except Exception: pass`, with a comment
calling the failures expected and non-critical.

**Settled**: registration of the admin class is explicit, and any failure propagates.

**Why**: a model whose admin silently failed to register is indistinguishable from one nobody asked
to register. The specification's whole error model is that misconfiguration stops the process.

---

## D11 — No handling for absent optional dependencies

**Previous specification**: silent on the question.

**Code**: the serializer factory caught `ImportError` and returned the built-in `type` object as a
placeholder. That sentinel then leaked into the API layer, which grew a guard to detect it.

**Settled**: Django REST Framework and the other component libraries are hard dependencies. The
branch and the sentinel are removed.

**Why**: nothing in the packaging makes them optional, so the branch guarded a case that cannot
occur while producing a value that broke a downstream consumer.

---

## D12 — Two superseded systems removed

**Previous specification**: did not mention either.

**Code**: an earlier inner-class configuration system survived alongside the registry, with its own
metaclass, its own configuration and metadata classes and its own component factories. Nothing read
it: no model used the metaclass, and its options object was never accessed. Separately, a field
resolution module that the specification's own contracts named as the central mechanism had no
importers, while six factory docstrings claimed to use it.

**Settled**: both removed. Tracked and carried out separately so that this feature's work stays
reviewable, and because the removal touches files outside the registry.

**Why**: they are why the registry reads as more complicated than its job. The documentation
describing the unused resolver as central is very likely why it survived, so the documentation was
corrected in the same pass.

---

## D13 — Five user stories instead of two

**Previous specification**: the 2026-01-12 session narrowed the feature to two stories, registration
and programmatic access, and deleted the rest.

**Settled**: five stories — registration with generated components, replacing one component,
refusing bad configuration, overriding an accessor, and introspection.

**Why**: the narrowing removed scope that belonged to views and was right to remove, but it left the
customisation tiers and the validation behaviour with no story of their own. Both are load-bearing
and both were where the implementation drifted, so each now has acceptance scenarios that would have
caught what went wrong.

---

## D14 — Test registrations move to concrete subclasses

**Previous specification**: silent. The registry accepts `Sample` and `Measurement` themselves and
any abstract subclass (`registry.py:201-207`), so 23 test constructions across
`tests/test_registry/test_config.py` and `test_registry.py` build configurations against the base
classes directly.

**Settled**: FR-002 stands — only a concrete subclass registers — and those 23 constructions are
rewritten against the concrete test models from `conftest.py`.

**Why**: registering a polymorphic base generates six components for a class no portal stores rows
in, and registers a second admin against it. Article I forbids modifying a pre-existing test without
a recorded decision, and this is that decision. The tests are asserting on a shortcut the suite took
before concrete test models existed, not on behaviour the framework promises.

---

## D15 — Generated components carry exactly the declared fields

**Previous specification**: SC-001 and SC-002 say so, and the code disagrees.
`SerializerFactory.generate` and `ResourceFactory.generate` prepend `id` unconditionally
(`factories.py:797`, `:871-872`), and the generated table carries a hidden `id` column.

**Settled**: the serializer and the resource carry the resolved field list and nothing else. A
portal that wants an identifier in its API or its export declares one.

**Why**: `id` is the internal primary key, and SC-002 names it as the example of what must not leak.
A framework that silently adds a field to a declared list makes the declaration untrustworthy for
every other field too. The table's hidden `id` column is out of scope here and stays until a portal
asks for it to go — it is not rendered and django-tables2 uses it for row identity.

---

## D16 — A portal's own admin registration wins

**Previous specification**: silent on the question.

**Code**: `register_admin` wrapped the whole method in `except Exception: pass`. That
did express a real rule — Django's admin autodiscovery runs before registration, so a portal that
wrote `@admin.register(RockSample)` got `AlreadyRegistered`, the exception was dropped, and the
hand-written class survived. The rule was never written down anywhere, and D10 nearly deleted it.

**Settled**: a model already present in the admin site is left alone, and every other failure
propagates.

**Why**: the rule itself is right. A portal that registered an admin class has said which one it
wants, and the registry does not overrule that. What was wrong was expressing it as a swallowed
exception, because the same swallow hid a genuinely broken admin class, which then registered as
nothing and looked identical to a model nobody had registered. Both halves now have tests: an
explicit registration survives, and an admin class that cannot be built raises.

**How it was found**: making the failure propagate, per D10, replaced five hand-written demo admin
classes with generated ones and dropped their fieldsets. The tests caught it.

---

## D17 — `Model.config` keeps returning None for now

**Previous specification**: FR-006 says requesting the configuration of an unregistered model must
raise, and that no accessor may return `None` in its place.

**Code**: `registry.get_for_model()` now raises `NotRegisteredError`, which satisfies FR-006 at the
registry. The `Model.config` shortcut still returns `None`.

**Settled**: the shortcut is migrated separately, under T037, and the reason is recorded at the
call site.

**Why**: templates reach for it on models that may not be registered.
`sample/sample_detail.html:13` reads `object.config.description`, and the polymorphic admin resolves
it on the base class, which is never registered. Making it raise takes those pages down, and a
template is exactly the place where asking rather than raising is the idiom. Closing this needs a
survey of every template and admin path that touches `.config`, which is more than a one-line
change, so it is left open rather than half-migrated.

---

## Not settled here

Existing framework consumers that reach around the registry, most visibly the API building its own
serializers rather than using the registry's, are recorded against their own features. This
specification defines the registry's contract and does not depend on those consumers being corrected
first.

# ADR 0001 — Environment overrides are found by existence, beside a known anchor

**Status:** accepted

## Decision

`fairdm.setup()` composes settings in five layers, later ones overriding earlier: the production
baseline in `fairdm/conf/settings/`, then `fairdm/conf/<environment>.py`, then settings contributed
by addons, then `<environment>.py` beside the portal's own settings module, then whatever the portal
assigns after the call.

`DJANGO_ENV` names the environment and defaults to `production`. **A layer applies if its module
exists, and is skipped silently if it does not.** There is no list of permitted environment names,
and no name is special apart from being the one FairDM happens to ship a module for. An environment
nobody ships a module for resolves to the production baseline without error.

The portal's override is resolved **beside its settings module**, captured before `split_settings`
overwrites `__file__`. It is not resolved from a directory named `config`.

## Why

The alternative — an allowlist of environment names mapped to filenames — was what FairDM had, and
it needed two structures kept in step: a tuple of valid names and a dict of name-to-file. Adding an
environment meant editing both, removing one meant editing both, and a name in one but not the other
failed in a way neither structure described. Selection by existence collapses them into a single
question the filesystem already answers, and makes dropping the staging profile a deletion rather
than a special case.

Falling back to the production baseline on an unrecognised name is deliberate, and it is the safe
direction: an unrecognised name yields the *strictest* configuration, not the loosest. A developer
notices within seconds because the portal behaves as if in production. The opposite default — an
unrecognised name resolving to development, or raising — would either loosen security on a typo or
turn a harmless misspelling into an outage.

Anchoring the portal's override to its settings module rather than to `config/` costs nothing for the
recommended layout, where the two resolve to the same file. They diverge for a portal created by
`django-admin startproject`, whose settings module sits in a package named after the project. Under a
hardcoded lookup, that portal's override is never found — and because "no module means no overrides"
is a legitimate outcome, the failure is silent. A rule anchored to the settings module is true in
both layouts. The documentation still presents the recommended structure in every example.

A corollary worth stating: no setting may need special-case handling in the entry point. If the
layering cannot express a case, the layering is the defect, not the case.

## Revisit if

A layer needs to apply conditionally on something other than the environment's name — a feature flag,
a deployment target, a tenant. Existence-based selection answers "does this environment have an
override?" and nothing else, and stretching it to answer a second question is how the two structures
this decision removed would come back.

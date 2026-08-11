# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the
codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the glossary of core domain concepts.
- **`docs/adr/`** — the architectural decisions that touch the area you are about to work in.

FairDM is a single-context repo. There is no `CONTEXT-MAP.md` and no per-package glossary.

## File structure

```
/
├── CONTEXT.md          ← domain glossary
├── docs/adr/           ← architectural decision records
├── fairdm/             ← the framework
├── fairdm_demo/        ← demo application
└── specs/NNN-slug/     ← per-feature specs, plans, and tasks
```

## Use the glossary's vocabulary

When your output names a domain concept — in an issue title, a refactor proposal, a hypothesis, or
a test name — use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary
explicitly rules out.

If the concept you need is not in the glossary, that is a signal. Either you are inventing language
the project does not use, in which case reconsider, or there is a real gap worth recording.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding
it:

> _Contradicts ADR-0007 — but worth reopening because…_

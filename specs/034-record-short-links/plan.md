# Implementation Plan: Open any record from its portal ID at a short, permanent link

**Branch**: `034-record-short-links` | **Date**: 2026-11-04 | **Spec**: [spec.md](spec.md) |
**Research**: [research.md](research.md) | **Sketch**: [sketch.md](sketch.md)

## Summary

A new module, `fairdm/views/permalink.py`, holds the path converter, the model map built from the
records' `uuid` fields, `get_permalink(record, request=None)` and `PermalinkView`, a temporary
redirect to the record's page. `fairdm/conf/urls.py` registers the converter and appends the
`permalink` pattern after every other root pattern. A `permalink` template tag gives the absolute
link to the identifiers card, which gains a Permalink row beneath the Portal ID, and to the Share
menu on every overview page. Citations without a DOI or IGSN, and the DataCite export, use
`get_permalink`. The sketch's `fairdm/views/links.py` is replaced.

## Technical Context

**Language/Version**: Python 3.13, Django 6.0
**Primary Dependencies**: shortuuid (present), django-polymorphic (present), django-mvp (present). No
new dependency.
**Storage**: no change. No migration.
**Testing**: pytest through the shared development container
(`~/.openclaw/devserver/fairdm-shared-test.sh <worktree> suite`)

## Constitution Check

No new dependency, model, migration or setting. Every public name is documented in the story that
adds it. Templates use Cotton components. Line length 88. No leading-underscore names.

## Design

### URL and view (US1)

- `PortalIDConverter.regex` is `[<letters>][<alphabet>]{<length>}`, where the letters are the
  `prefix` of the `uuid` field on `Project`, `Dataset`, `Sample`, `Measurement` and `Contributor`,
  the alphabet is `shortuuid.get_alphabet()` and the length is the fields' shared `length`. Built
  once at import from `apps.get_model` lookups inside a function the converter calls lazily, so the
  URL module can import before the apps are ready.
- `record_managers()` maps each prefix to the manager whose lookup the view uses: `Project.objects`,
  `Dataset.all_objects`, `Sample.objects`, `Measurement.objects` and `Contributor.objects`.
- `PermalinkView(RedirectView)`: `permanent = False`, `query_string = True`.
  `get_redirect_url` looks the record up by `uuid` with `get_object_or_404` and returns
  `record.get_absolute_url()`.
- `get_permalink(record, request=None)` returns the path from `reverse("permalink", ...)`, or the
  absolute link through `request.build_absolute_uri` when a request is given.
- `fairdm/conf/urls.py`: `register_converter(PortalIDConverter, "portal_id")`, and
  `path("<portal_id:portal_id>/", PermalinkView.as_view(), name="permalink")` appended after the
  addon routes.

### Where the link is handed out (US2)

- `fairdm/templatetags/fairdm.py`: `@register.simple_tag(takes_context=True) permalink(context,
  record)` returns `get_permalink(record, context["request"])`.
- `<c-card.identifiers>` gains a `permalink` attribute. When it is set, a Permalink row beneath the
  Portal ID row shows it as a link with a button that copies it. The Portal ID row copies the bare
  ID, as on main.
- `overview/page.html`, `contributors/overview/person.html` and `organization.html`:
  `{% permalink <record> as permalink %}`, passed to the card and as `url` to the share dropdown.
- The citation `link` for a dataset with no DOI, a sample with no IGSN and a measurement with no DOI,
  and `uri` in `fairdm/contrib/import_export/utils.py`, use `get_permalink(record, request)`.

### Documentation

- User docs: in each record page's "How to reach it" (project, dataset, sample, measurement, person,
  organization), one sentence on the permalink. `docs/users/editing-a-record/identifiers.md`,
  "Where the identifiers appear": the Permalink row and the citation and Share menu that use it.
- Developer reference: the `permalink` URL name, `get_permalink`, the `permalink` tag, and that a root
  page always wins, in the URL reference page that lists the portal's routes, or a new
  `docs/developers/reference/permalinks.md` if none lists them.
- `CONTEXT.md`: a **Portal ID** entry and a **Permalink** entry under the core data model.
- `docs/changelog.md`: an entry.

## Risks

- A portal that declares a root page whose path is shaped like a portal ID shadows those links. The
  page wins by design, and the developer reference says so.

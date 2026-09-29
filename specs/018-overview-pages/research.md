# Research: One consistent overview page

## The prototype is the design source

The four pages were reviewed with the maintainer over seven rounds on a working prototype, and the
specification was then rewritten to match it. Implementation starts from that code (decision D1).

## What the prototype lacks

Measured on the merged branch on 2026-09-29:

- 12 of 2,876 existing tests fail. They request samples or measurements in unpublished datasets,
  read context keys the new pages renamed, or look for the Delete link the new Manage menus lost.
- `deptry` reports `pyecharts` used without being declared and `django-mvp-charts` declared
  without a visible use.
- The docs check reports one stale passage and 37 undocumented public names, most of them module
  functions that move onto classes (plan D3).
- The pages have no tests of their own.

## Libraries

- **django-mvp-charts** draws the two charts. It writes no colours itself: `fairdm/static/js/chart-theme.js` paints them from the theme's tokens.
- **MapLibre GL 5.24.0**, the last release with a script build, loaded with SRI. Version 6 ships
  ES modules only. Tiles from OpenFreeMap, which need no key.

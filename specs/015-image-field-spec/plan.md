# Implementation Plan: Image Field Requirements for Core Models

**Branch**: `015-image-field-spec` | **Date**: 2026-05-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/015-image-field-spec/spec.md`

## Summary

All four core FairDM models (Project, Dataset, Sample, Measurement) inherit a `ThumbnailerImageField` from `BaseModel`. This plan formalises the aspect ratio (3:2), defines two named thumbnail size aliases (small, large), caps the stored source resolution to screen-appropriate dimensions, and makes the form widgets consistent and informative so users understand upload expectations before submitting.

## Technical Context

**Language/Version**: Python 3.13, Django 5.x  
**Primary Dependencies**: easy-thumbnails =2.10,<3.0 (already installed); Pillow (transitive via easy-thumbnails); django-mvp (Bootstrap 5 UI)  
**Storage**: `FileSystemStorage` (local dev), S3-compatible (production) � both already configured  
**Testing**: pytest + pytest-django  
**Target Platform**: Django web server (Linux container / local dev)  
**Project Type**: Django framework library (fairdm core)  
**Performance Goals**: Thumbnail generation is synchronous on upload; must not block the request for longer than a standard file write  
**Constraints**: Stored source images capped at 2400�1600 px (3:2, 200 DPI-equivalent at full screen); max upload file size 5 MB; no ultra-high-res originals stored  
**Scale/Scope**: Affects 4 core models, ~6 form/settings files; no migrations required (field already present, only `resize_source` kwarg added)

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I � FAIR-First | ? Pass | Representative images improve discoverability metadata in cards/listings |
| II � Domain-Driven Modeling | ? Pass | Change is confined to `BaseModel` field kwarg and THUMBNAIL_ALIASES settings � declarative |
| III � Configuration Over Custom Plumbing | ? Pass | Uses `THUMBNAIL_ALIASES` + `resize_source` � no custom processors or one-off upload handlers |
| IV � Opinionated Production Defaults | ? Pass | easy-thumbnails is the existing, approved library; defaults (5 MB, 2400�1600 cap, named aliases) align with ecosystem norms |
| V � Test-First Quality | ? Pass | Tests must be written first; plan includes test tasks for all form changes and thumbnail alias resolution |

## Project Structure

### Documentation (this feature)

```text
specs/015-image-field-spec/
+-- plan.md              ? this file
+-- research.md          ? Phase 0 output
+-- data-model.md        ? Phase 1 output
+-- quickstart.md        ? Phase 1 output
+-- tasks.md             ? Phase 2 output (/speckit.tasks)
```

### Source Code (affected files)

```text
fairdm/conf/settings/static_media.py      # Add THUMBNAIL_ALIASES[""] with core_small + core_large (project-wide key)
fairdm/core/abstract.py                   # Add resize_source to ThumbnailerImageField
fairdm/core/project/forms.py              # Add image help text + file size validator
fairdm/core/dataset/forms.py              # Fix help text (currently says 16:9), add validator
fairdm/core/sample/forms.py               # Replace ClearableFileInput with explicit ImageField
fairdm/core/measurement/forms.py          # Replace ClearableFileInput with explicit ImageField

tests/
+-- test_forms/
    +-- test_image_fields.py              # NEW � form validation + help text tests
```

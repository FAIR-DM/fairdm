# Research — 002 Model registry and generated components

Dated 2026-08-17, for the rewritten specification. Everything here was verified in this repository
or in the installed dependency source, and each finding names where.

## Django's own precedent for the accessor shape

`ModelFormMixin.get_form_class()` (`django/views/generic/edit.py:88-108`) returns `self.form_class`
when one is set, and otherwise calls `model_forms.modelform_factory(model, fields=self.fields)`. It
does this on every request, with no caching anywhere in the path.

Two things follow. The method-with-fallback shape this feature needs is Django's own, not a variation
on it, so a portal developer meets it already knowing how it behaves. And per-request regeneration is
normal in Django rather than something to design around.

The same method carries the precedent for refusing ambiguous configuration:

```python
if self.fields is not None and self.form_class:
    raise ImproperlyConfigured(
        "Specifying both 'fields' and 'form_class' is not permitted."
    )
```

## Measured cost of generating components

Measured in this repository against the demo models, 200 repetitions per figure, medians.

| What | Cost |
|---|---|
| table + filter set, six-field model | 0.18 ms |
| table + form + filter set, six fields | 0.61 ms |
| table + form + filter set, ten fields | 1.08 ms |
| all six components, widest demo model | 0.68 ms |
| rendering a twenty-cell table fragment, same process | 0.12 ms |

Cost is roughly linear in field count, about 0.1 ms per field per component. A real list page renders
far more than twenty cells, so generation is low single-digit percent of a page at worst. This is
what settled the no-caching decision, recorded as D1 in `decisions.md`.

## Measured cost of registration-time validation

| What | Per configuration | 100 models |
|---|---|---|
| existence check on the first path segment only | 0.0046 ms | 0.46 ms |
| existence plus every segment of every related path | 0.0069 ms | 0.69 ms |

A single `Model._meta.get_field()` call costs 0.14 microseconds, which is why walking whole paths is
close to free. Strict validation for 250 registered models costs 1.7 ms. Startup cost is not a reason
to weaken validation, which settled D4.

## Path resolution

Django exposes the separator as `django.db.models.constants.LOOKUP_SEP` rather than a literal `"__"`.
Walking a path means calling `_meta.get_field(segment)` and stepping to `field.related_model` for
every segment but the last. A segment whose field has no related model, followed by further segments,
is an invalid path rather than an error to swallow.

## What each component library needs

- **Forms**: `django.forms.models.modelform_factory(model, form=..., fields=...)`.
- **Tables**: `django_tables2.table_factory(model, table=..., fields=...)`.
- **Filter sets**: `django_filters.filterset.filterset_factory(model, fields=...)`. Filter type per
  field is the library's decision unless overridden.
- **Serializers**: DRF has no factory. A serializer class is built with a `Meta` naming the model and
  fields.
- **Import and export**: `import_export.resources.modelresource_factory(model, resource_class=...)`.
- **Admin**: a `ModelAdmin` subclass built with `list_display` and related options. For a polymorphic
  child model the base class must be the framework's child admin for that hierarchy, because
  django-polymorphic's parent and child admins are not interchangeable.

All six libraries are hard dependencies (`pyproject.toml`), including `djangorestframework` at line
80 with nothing marking it optional. No generation path needs to handle one being absent, which
settled D11.

## Fields that must stay out of the default list

Django's admin rejects a many-to-many field with an explicit `through` model in `list_display` and
related options, check `admin.E013`. A generated admin including such a field fails to load, so the
default field list has to exclude it. The remaining exclusions are the framework's own plumbing:
`id`, polymorphic type columns, multi-table inheritance pointers, `auto_now` and `auto_now_add`
fields, anything with `editable=False`, and reverse relations.

## When Django system checks actually run

`BaseCommand.execute()` calls `self.check()` (`django/core/management/base.py:461`). `django.setup()`
does not. A check therefore runs for `manage.py` commands and never on a plain WSGI or ASGI boot,
which is why validation belongs at registration and not in a check. This settled D4.

## Presentation is not this feature's concern

The previous specification required Bootstrap 5 and a `django_tables2/bootstrap5.html` template. The
framework depends on `crispy-tailwind` and the constitution's Article XV requires the shared
application shell built on Tailwind and daisyUI. Rather than restate the requirement for Tailwind,
the rewritten specification says nothing about styling, because pinning a stylesheet here would make
a theme change a registry change. Recorded as D7.

## Open questions

None. Every question raised during the audit was settled and recorded in `decisions.md`.

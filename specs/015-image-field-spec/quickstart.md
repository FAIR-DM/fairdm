# Quickstart: Image Fields in Core Model Templates

**Phase 1 output** for `015-image-field-spec`  
**Date**: 2026-05-28

This guide covers how to render representative images and their thumbnails in Django templates after implementation.

---

## Load the template tag library

```django
{% load thumbnail %}
```

---

## Render a card thumbnail (listing views)

Use the `core_small` alias (600×400, 3:2, smart-cropped):

```django
{% if obj.image %}
    <img src="{{ obj.image|thumbnail_url:'core_small' }}"
         alt="{{ obj.name }}"
         width="600" height="400"
         class="card-img-top">
{% else %}
    <img src="{% static 'fairdm/img/placeholder-3x2.png' %}"
         alt="No image"
         width="600" height="400"
         class="card-img-top">
{% endif %}
```

---

## Render a detail page header (large variant)

Use the `core_large` alias (1200×800, 3:2, smart-cropped):

```django
{% thumbnail obj.image 'core_large' as thumb %}
{% if thumb %}
    <img src="{{ thumb.url }}"
         width="{{ thumb.width }}" height="{{ thumb.height }}"
         alt="{{ obj.name }}"
         class="img-fluid rounded">
{% else %}
    <img src="{% static 'fairdm/img/placeholder-3x2.png' %}"
         alt="No image"
         class="img-fluid rounded">
{% endif %}
```

---

## Fallback shorthand using `default` filter

easy-thumbnails supports a `default` filter for a concise inline fallback:

```django
{% thumbnail obj.image|default:'fairdm/img/placeholder-3x2.png' 'core_small' %}
```

Note: the default path is relative to `MEDIA_ROOT`.

---

## Generating thumbnails from Python (management commands / migrations)

```python
from easy_thumbnails.files import generate_all_aliases

instance = Project.objects.get(pk=pk)
generate_all_aliases(instance.image, include_global=True)
```

---

## Form usage

Each core model form (Project, Dataset, Sample, Measurement) declares the image field with the shared `ImageClearableFileInput` widget. No additional template work is required — the widget renders the preview automatically.

```python
# In ProjectForm (and equivalents for other core models):
from easy_thumbnails.widgets import ImageClearableFileInput

image = forms.ImageField(
    required=False,
    label=_("Representative image"),
    help_text=IMAGE_HELP_TEXT,      # defined in fairdm/core/image_utils.py
    validators=[validate_image_file_size],
    widget=ImageClearableFileInput(
        thumbnail_options={"size": (150, 100), "crop": True}
    ),
)
```

---

## Running tests

```bash
pytest tests/test_forms/test_image_fields.py -v
```

Key test scenarios to cover (test-first, write these before implementation):

1. `test_image_field_accepts_valid_jpeg` — upload a 5 MB JPEG within 2400×1600; form is valid.
2. `test_image_field_rejects_oversized_file` — upload a 6 MB file; form is invalid with the expected error message.
3. `test_image_field_rejects_non_image` — submit a `.pdf`; form is invalid.
4. `test_image_field_help_text_present` — instantiate each of the four forms; assert `image` field `help_text` contains "3:2".
5. `test_image_field_uses_clearable_widget` — assert `image` field widget is `ImageClearableFileInput` for all four forms.
6. `test_thumbnail_alias_core_small_resolves` — create a Project with an image; assert `thumbnail_url` for `core_small` returns a non-empty URL.
7. `test_thumbnail_alias_core_large_resolves` — same for `core_large`.

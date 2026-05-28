# Data Model: Image Field Requirements for Core Models

**Phase 1 output** for `015-image-field-spec`  
**Date**: 2026-05-28

---

## Overview

No new models are introduced. This feature modifies the existing `image` field on `BaseModel` (the shared abstract base inherited by Project, Dataset, Sample, and Measurement) and the corresponding form declarations and settings.

---

## Field: `BaseModel.image`

**Location**: `fairdm/core/abstract.py`

### Current state

```python
image = ThumbnailerImageField(
    verbose_name=_("image"),
    blank=True,
    null=True,
    upload_to=default_image_path,
)
```

### Target state

```python
image = ThumbnailerImageField(
    verbose_name=_("image"),
    blank=True,
    null=True,
    upload_to=default_image_path,
    resize_source=dict(size=(2400, 1600), crop=False),
)
```

**Change**: Add `resize_source`. This instructs easy-thumbnails to downscale the source image proportionally before persisting to storage if either dimension exceeds the specified bounds. Images already within 2400×1600 are stored as-is.

**Migration required**: No. `resize_source` is a Python-level kwarg consumed by `ThumbnailerImageField.__init__`; it does not alter the database schema. No migration file is needed.

---

## Settings: `THUMBNAIL_ALIASES`

**Location**: `fairdm/conf/settings/static_media.py`

### Current state

```python
THUMBNAIL_ALIASES = {
    "contributors": {
        "thumb": {"size": (48, 48), "crop": False},
        "small": {"size": (150, 150), "crop": False},
        "medium": {"size": (600, 600), "crop": False},
    },
}
```

### Target state

```python
THUMBNAIL_ALIASES = {
    "contributors": {
        "thumb": {"size": (48, 48), "crop": False},
        "small": {"size": (150, 150), "crop": False},
        "medium": {"size": (600, 600), "crop": False},
    },
    "": {  # project-wide aliases available to all models
        "core_small": {"size": (600, 400), "crop": "smart"},
        "core_large": {"size": (1200, 800), "crop": "smart"},
    },
}
```

**Alias definitions**:

| Alias        | Width (px) | Height (px) | Ratio | Crop   | Use context                          |
|--------------|-----------|------------|-------|--------|--------------------------------------|
| `core_small` | 600       | 400        | 3:2   | smart  | Card/grid listing views              |
| `core_large` | 1200      | 800        | 3:2   | smart  | Detail page headers, featured images |

---

## Shared Image Form Field

**Location**: Declared individually in each model's form; shares a constant for help text.

### Shared constants (proposed location: `fairdm/core/image_utils.py` or inline in each form)

```python
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

IMAGE_HELP_TEXT = _(
    "Upload a representative image. "
    "Recommended: 3:2 landscape ratio (e.g., 1200\u00d7800\u00a0px). "
    "Accepted formats: JPEG, PNG, WebP. Max size: 5\u00a0MB. "
    "Images that do not match the 3:2 ratio will be centre-cropped during display."
)
```

### Shared validator

```python
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_image_file_size(file):
    if hasattr(file, "size") and file.size > MAX_IMAGE_UPLOAD_BYTES:
        mb = file.size / (1024 * 1024)
        raise ValidationError(
            _("Image file size must be 5\u00a0MB or less. Your file is %(mb).1f\u00a0MB."),
            params={"mb": mb},
        )
```

### Per-form field declaration pattern

The same field declaration is applied to the `image` field in all four forms (Project, Dataset, Sample, Measurement):

```python
from easy_thumbnails.widgets import ImageClearableFileInput

image = forms.ImageField(
    required=False,
    label=_("Representative image"),
    help_text=IMAGE_HELP_TEXT,
    validators=[validate_image_file_size],
    widget=ImageClearableFileInput(
        thumbnail_options={"size": (150, 100), "crop": True}
    ),
)
```

---

## Form Files to Update

| File                                    | Current state                                              | Required change                                                   |
|-----------------------------------------|------------------------------------------------------------|-------------------------------------------------------------------|
| `fairdm/core/project/forms.py`          | `ImageField(required=False, label=False)` — no help text   | Add help text, validator, `ImageClearableFileInput` widget        |
| `fairdm/core/dataset/forms.py`          | `ImageField` with incorrect "16:9" help text               | Fix help text to 3:2, add validator, add `ImageClearableFileInput`|
| `fairdm/core/sample/forms.py`           | `ClearableFileInput` widget in `Meta.widgets` only         | Replace with explicit `ImageField` declaration (same pattern)     |
| `fairdm/core/measurement/forms.py`      | `ClearableFileInput` widget in `Meta.widgets` only         | Replace with explicit `ImageField` declaration (same pattern)     |

---

## Validation Rules

| Rule                | Enforcement point     | Detail                                              |
|---------------------|-----------------------|-----------------------------------------------------|
| File type           | Django `ImageField`   | Rejects non-image MIME types automatically          |
| File size = 5 MB    | Form validator        | `validate_image_file_size` raises `ValidationError` |
| Format (JPEG/PNG/WebP) | `ImageField` + Pillow | Pillow rejects unsupported formats on open          |
| Source dimension cap | `resize_source`      | Applied at save time; transparent to the user       |

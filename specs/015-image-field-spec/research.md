# Research: Image Field Requirements for Core Models

**Phase 0 output** for `015-image-field-spec`  
**Date**: 2026-05-28

---

## 1. easy-thumbnails: Capping the Stored Source Resolution

**Decision**: Use `resize_source=dict(size=(2400, 1600), crop=False)` on the `ThumbnailerImageField` in `BaseModel`.

**Rationale**: `resize_source` is a built-in kwarg on `ThumbnailerImageField` that runs the source image through easy-thumbnails processors *before* saving to storage. Setting `crop=False` (i.e., the `scale_and_crop` processor in scale-only mode) means the image is scaled down proportionally to fit within the 2400�1600 box without cropping or distorting the original, and only if the uploaded file exceeds those dimensions. 2400�1600 px at 3:2 is equivalent to a 4K source scaled to fit a 27" iMac � generous for any portal display use case without storing raw camera files.

**How it works in code**:
```python
from easy_thumbnails.fields import ThumbnailerImageField

image = ThumbnailerImageField(
    ...,
    resize_source=dict(size=(2400, 1600), crop=False),
)
```

**Alternatives considered**:
- *Validate at form level only (reject files over a pixel limit)*: Rejected � adds complexity and a poor UX; users with a 6000�4000 camera RAW export have a valid image that simply needs resizing, not rejection.
- *Use Django signals to post-process after save*: Rejected � more moving parts than the built-in `resize_source` kwarg.

---

## 2. Thumbnail Size Aliases

**Decision**: Add a project-wide empty-string key (`""`) to `THUMBNAIL_ALIASES` with two named aliases:

| Alias   | Size (px) | Aspect | Crop   | Usage                                      |
|---------|-----------|--------|--------|--------------------------------------------|
| `small` | 600�400   | 3:2    | smart  | Card/grid listing views                    |
| `large` | 1200�800  | 3:2    | smart  | Detail page headers, featured image slots  |

```python
THUMBNAIL_ALIASES = {
    ...,
    "": {  # project-wide � available to all apps/models
        "core_small": {"size": (600, 400), "crop": "smart"},
        "core_large": {"size": (1200, 800), "crop": "smart"},
    },
}
```

**Rationale**:
- Project-wide key (`""`) is necessary because the field is on `BaseModel` (abstract) and the concrete models live in separate app labels (`project`, `dataset`, `sample`, `measurement`). Scoping by app label would require four identical entries.
- `crop="smart"` uses entropy-based edge cropping, preserving the most visually important region when the uploaded image's aspect ratio differs from 3:2. This is safer than center-crop for scientific imagery (field photos, maps, diagrams) where the subject is not always centered.
- 600�400 for small: fits a standard Bootstrap 5 card image at 1� and up to 1.5� DPR.
- 1200�800 for large: fits a full-width detail header at 1� on a 1200px container, 2� on a retina laptop.

**Alternatives considered**:
- *Per-field scoping (`'fairdm_core.Project.image'` etc.)*: Rejected � four identical alias definitions; no practical benefit.
- *Single alias for all uses*: Rejected � forces all contexts to download the large image even in card lists.
- *crop=True (center crop)*: Rejected in favour of `crop="smart"` � center crop frequently decapitates the subject of landscape field photos.

---

## 3. Form Widget � Preview + Guidance

**Decision**: Use `easy_thumbnails.widgets.ImageClearableFileInput` with a `thumbnail_options` size of `(150, 100)` (3:2 preview).

**Rationale**: This built-in widget renders the currently saved image as a thumbnail inline next to the file input, satisfying FR-011 (edit mode preview) with no additional template work. The preview thumbnail options are passed directly to the widget constructor:

```python
from easy_thumbnails.widgets import ImageClearableFileInput

image = forms.ImageField(
    widget=ImageClearableFileInput(thumbnail_options={"size": (150, 100), "crop": True}),
    ...
)
```

The widget falls back gracefully to a plain file input when no image exists.

**Alternatives considered**:
- *Custom Cotton widget with JavaScript preview*: Deferred to a future enhancement; the built-in widget satisfies the spec without additional JS.
- *Plain ClearableFileInput (current state for Sample/Measurement)*: Does not show an existing image preview; does not satisfy FR-011.

---

## 4. File Size Validation

**Decision**: Add a shared validator function `validate_image_file_size` to `fairdm/core/validators.py` (or `fairdm/utils/utils.py` alongside other helpers) and attach it via `validators=` on the `ImageField` in each form.

```python
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

def validate_image_file_size(file):
    if file.size > MAX_IMAGE_UPLOAD_BYTES:
        mb = file.size / (1024 * 1024)
        raise ValidationError(
            _("Image file size must be 5 MB or less. Uploaded file is %(mb).1f MB."),
            params={"mb": mb},
        )
```

**Rationale**: Form-level validation gives an immediate, friendly error before any disk I/O happens. The 5 MB limit was established in the spec assumption and is a reasonable threshold for JPEG/PNG images at the recommended 2400�1600 source size (a typical 2400�1600 JPEG at quality 85 is ~1�2 MB).

**Alternatives considered**:
- *Model-level validator on the field*: Could be added but runs after the file is already received by the server; form-level check is preferred for early rejection.
- *10 MB limit*: Rejected as unnecessarily permissive given the `resize_source` cap.

---

## 5. Help Text � Conveying Expectations

**Decision**: All four forms use a shared help text constant or i18n string with the following information:
- Recommended aspect ratio: 3:2 (landscape, e.g., 1200�800 px)
- Accepted formats: JPEG, PNG, WebP
- Maximum file size: 5 MB
- Note about centred cropping when the ratio does not match

**Example**:
```
Upload a representative image. Recommended: 3:2 landscape ratio (e.g., 1200�800 px).
Accepted formats: JPEG, PNG, WebP. Max size: 5 MB.
Images that are not 3:2 will be cropped from the centre during display.
```

**Rationale**: Consistent, pre-upload guidance directly addresses the spec goal of avoiding user surprise at cropping. The note about cropping removes the need for FR-009's dynamic aspect-ratio mismatch warning for v1, which would require JavaScript and is disproportionate to the scope.

**Alternatives considered**:
- *Dynamic aspect-ratio detection with JS warning (FR-009)*: Deferred to a future enhancement; static help text is sufficient for v1 and avoids adding JavaScript to a form that currently has none.

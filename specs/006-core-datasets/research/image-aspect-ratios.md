# Research: Dataset Image Aspect Ratios

**Feature**: 006-core-datasets
**Task**: T012
**Purpose**: Determine optimal aspect ratio for dataset images in card displays, responsive layouts, and meta tags

---

## Requirements Analysis

### Display Contexts

1. **Bootstrap Cards** - List/grid views of datasets
2. **Detail Pages** - Hero image or prominent display
3. **Social Media** - Open Graph and Twitter Card previews
4. **Thumbnails** - Small previews in tables/lists
5. **Responsive Layouts** - Mobile, tablet, desktop

---

## Bootstrap 5 Card Best Practices

### Recommended Aspect Ratios

**16:9 (Landscape)**

- ✅ **Best for**: General dataset images, charts, maps
- ✅ **Responsive**: Works well on all screen sizes
- ✅ **Social media**: Matches Open Graph default (1.91:1)
- Resolution: 1200x675px (high DPI), 800x450px (standard)

**4:3 (Standard)**

- ✅ **Best for**: Scientific equipment photos, laboratory setups
- ✅ **Classic**: Traditional photo aspect ratio
- Resolution: 1200x900px (high DPI), 800x600px (standard)

**1:1 (Square)**

- ✅ **Best for**: Logos, icons, sample photos
- ✅ **Consistent height**: Easier grid alignment
- ❌ **Inefficient**: Wastes space in landscape layouts
- Resolution: 800x800px (standard), 1200x1200px (high DPI)

**3:2 (Photography)**

- ✅ **Best for**: Field photos, landscape photography
- ✅ **Natural**: Common camera native aspect
- Resolution: 1200x800px (high DPI), 900x600px (standard)

---

## Recommendation: 16:9 (Landscape)

**Primary Rationale**:

1. **Bootstrap Card Support**: Card images work best with wider aspects
2. **Open Graph Standard**: 1.91:1 (very close to 16:9)
3. **Responsive Design**: Maintains proportions across breakpoints
4. **Content Versatility**: Works for charts, maps, equipment, field photos

**Recommended Dimensions**:

- **Upload Max**: 1920x1080px (Full HD, 16:9)
- **Display Standard**: 800x450px (16:9)
- **Display High-DPI**: 1600x900px (16:9, 2x)
- **Thumbnail**: 400x225px (16:9)
- **Card Display**: 100% width, auto height (maintains aspect)

---

## Implementation

### Model Field

```python
class Dataset(BaseModel):
    image = models.ImageField(
        upload_to='datasets/',
        blank=True,
        null=True,
        validators=[validate_image_aspect_ratio],
        help_text=_(
            'Dataset image for cards and social media. '
            'Recommended: 1920x1080px (16:9 aspect ratio). '
            'Minimum: 800x450px. Maximum file size: 5MB.'
        )
    )
```

### Validation

```python
from django.core.exceptions import ValidationError
from PIL import Image

def validate_image_aspect_ratio(image):
    """
    Validate image aspect ratio is close to 16:9.

    Allows slight variance (±10%) to accommodate various resolutions.
    """
    try:
        img = Image.open(image)
        width, height = img.size

        # Calculate aspect ratio
        aspect = width / height
        target_aspect = 16 / 9  # 1.778

        # Allow 10% variance
        min_aspect = target_aspect * 0.9  # 1.600
        max_aspect = target_aspect * 1.1  # 1.956

        if not (min_aspect <= aspect <= max_aspect):
            raise ValidationError(
                _(
                    'Image aspect ratio (%(actual).2f) should be close to 16:9 (1.78). '
                    'Acceptable range: 1.60 to 1.96. Try cropping to 16:9 before upload.'
                ) % {'actual': aspect}
            )

        # Validate minimum dimensions
        min_width = 800
        min_height = 450
        if width < min_width or height < min_height:
            raise ValidationError(
                _(
                    'Image dimensions (%(width)dx%(height)d) are too small. '
                    'Minimum: %(min_width)dx%(min_height)d pixels.'
                ) % {
                    'width': width,
                    'height': height,
                    'min_width': min_width,
                    'min_height': min_height,
                }
            )

        # Validate maximum file size (5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if image.size > max_size:
            raise ValidationError(
                _(
                    'Image file size (%(size).1f MB) exceeds maximum (5 MB). '
                    'Please compress or resize the image.'
                ) % {'size': image.size / (1024 * 1024)}
            )

    except (IOError, OSError) as e:
        raise ValidationError(_('Invalid image file: %(error)s') % {'error': str(e)})
```

---

## Bootstrap Card Integration

### Basic Card Layout

```html
<div class="card">
    {% if dataset.image %}
        <img src="{{ dataset.image.url }}"
             class="card-img-top"
             alt="{{ dataset.name }}"
             loading="lazy"
             style="aspect-ratio: 16/9; object-fit: cover;">
    {% else %}
        <div class="card-img-top bg-light d-flex align-items-center justify-content-center"
             style="aspect-ratio: 16/9;">
            <i class="bi bi-file-earmark-text text-muted" style="font-size: 4rem;"></i>
        </div>
    {% endif %}
    <div class="card-body">
        <h5 class="card-title">{{ dataset.name }}</h5>
        <p class="card-text">{{ dataset.description|truncatewords:20 }}</p>
    </div>
</div>
```

### CSS Optimization

```css
/* Ensure consistent aspect ratio across all cards */
.dataset-card img,
.dataset-card .card-img-top {
    aspect-ratio: 16/9;
    object-fit: cover;
    width: 100%;
    height: auto;
}

/* Placeholder for missing images */
.dataset-card-placeholder {
    aspect-ratio: 16/9;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
}
```

---

## Responsive Breakpoints

### Bootstrap 5 Breakpoints

| Breakpoint | Viewport Width | Card Width | Image Display Width |
|------------|---------------|------------|---------------------|
| xs | <576px | 100% | ~350px |
| sm | ≥576px | 100% / 50% | ~270px / ~540px |
| md | ≥768px | 33.33% | ~240px |
| lg | ≥992px | 25% | ~230px |
| xl | ≥1200px | 20% / 25% | ~230px / ~290px |
| xxl | ≥1400px | 20% | ~270px |

### Responsive Grid

```html
<div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
    {% for dataset in datasets %}
        <div class="col">
            <div class="card h-100 dataset-card">
                {% if dataset.image %}
                    <img src="{{ dataset.image.url }}"
                         class="card-img-top"
                         alt="{{ dataset.name }}"
                         loading="lazy">
                {% else %}
                    <div class="dataset-card-placeholder">
                        <i class="bi bi-database text-muted fs-1"></i>
                    </div>
                {% endif %}
                <div class="card-body">
                    <h5 class="card-title">{{ dataset.name }}</h5>
                    <p class="card-text text-muted small">
                        {{ dataset.project.name }}
                    </p>
                </div>
            </div>
        </div>
    {% endfor %}
</div>
```

---

## Social Media Meta Tags

### Open Graph (Facebook, LinkedIn)

```html
<!-- In templates/dataset/detail.html -->
{% load meta_tags %}

<meta property="og:type" content="dataset">
<meta property="og:title" content="{{ dataset.name }}">
<meta property="og:description" content="{{ dataset.description|truncatewords:30 }}">
{% if dataset.image %}
    <meta property="og:image" content="{{ request.scheme }}://{{ request.get_host }}{{ dataset.image.url }}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="675">
    <meta property="og:image:alt" content="{{ dataset.name }}">
{% endif %}
<meta property="og:url" content="{{ request.build_absolute_uri }}">
```

**Open Graph Recommended**: 1200x630px (1.91:1) - Our 16:9 (1.78:1) is close enough

### Twitter Card

```html
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{{ dataset.name }}">
<meta name="twitter:description" content="{{ dataset.description|truncatewords:30 }}">
{% if dataset.image %}
    <meta name="twitter:image" content="{{ request.scheme }}://{{ request.get_host }}{{ dataset.image.url }}">
    <meta name="twitter:image:alt" content="{{ dataset.name }}">
{% endif %}
```

**Twitter Recommended**: 1200x675px (16:9) - Perfect match!

---

## Thumbnails with easy-thumbnails

### Configuration

```python
# settings.py
THUMBNAIL_ALIASES = {
    '': {
        'dataset_card': {'size': (800, 450), 'crop': 'smart', 'quality': 85},
        'dataset_card_2x': {'size': (1600, 900), 'crop': 'smart', 'quality': 85},
        'dataset_thumbnail': {'size': (400, 225), 'crop': 'smart', 'quality': 80},
        'dataset_preview': {'size': (200, 113), 'crop': 'smart', 'quality': 75},
    },
}
```

### Template Usage

```html
{% load thumbnail %}

{% if dataset.image %}
    {% thumbnail dataset.image "dataset_card" as im %}
        <img src="{{ im.url }}"
             srcset="{{ im.url }} 1x,
                     {% thumbnail dataset.image 'dataset_card_2x' %}{{ im.url }}{% endthumbnail %} 2x"
             alt="{{ dataset.name }}"
             loading="lazy"
             width="{{ im.width }}"
             height="{{ im.height }}">
    {% endthumbnail %}
{% endif %}
```

---

## Detail Page Hero Image

### Full-Width Hero

```html
<div class="dataset-hero">
    {% if dataset.image %}
        <img src="{{ dataset.image.url }}"
             alt="{{ dataset.name }}"
             class="img-fluid w-100"
             style="max-height: 500px; object-fit: cover; object-position: center;">
    {% endif %}
</div>

<div class="container mt-4">
    <h1>{{ dataset.name }}</h1>
    <p class="lead">{{ dataset.description }}</p>
</div>
```

### Constrained Hero

```html
<div class="container">
    <div class="row">
        <div class="col-lg-8 mx-auto">
            {% if dataset.image %}
                <img src="{{ dataset.image.url }}"
                     alt="{{ dataset.name }}"
                     class="img-fluid rounded shadow-sm mb-4"
                     style="aspect-ratio: 16/9; object-fit: cover; width: 100%;">
            {% endif %}
            <h1>{{ dataset.name }}</h1>
            <p>{{ dataset.description }}</p>
        </div>
    </div>
</div>
```

---

## Placeholder Images

### No Image Placeholder

```html
{% if dataset.image %}
    <img src="{{ dataset.image.url }}" alt="{{ dataset.name }}" class="card-img-top">
{% else %}
    <div class="card-img-top bg-gradient-primary d-flex align-items-center justify-content-center text-white"
         style="aspect-ratio: 16/9;">
        <div class="text-center">
            <i class="bi bi-database fs-1 mb-2"></i>
            <div class="small">No Image</div>
        </div>
    </div>
{% endif %}
```

### Dynamic Background Color

```python
# In view context or template tag
def dataset_placeholder_color(dataset):
    """Generate consistent color from dataset name."""
    import hashlib
    hash_val = int(hashlib.md5(dataset.name.encode()).hexdigest()[:6], 16)
    hue = hash_val % 360
    return f"hsl({hue}, 60%, 80%)"
```

```html
<div class="card-img-top d-flex align-items-center justify-content-center"
     style="aspect-ratio: 16/9; background: {{ dataset|placeholder_color }};">
    <i class="bi bi-database fs-1 text-white opacity-50"></i>
</div>
```

---

## Testing

### Image Validation Tests

```python
def test_valid_16_9_image():
    """16:9 aspect ratio images should validate."""
    from PIL import Image
    from io import BytesIO
    from django.core.files.uploadedfile import SimpleUploadedFile

    # Create 1920x1080 image
    img = Image.new('RGB', (1920, 1080), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)

    image_file = SimpleUploadedFile(
        "test.jpg",
        img_io.getvalue(),
        content_type="image/jpeg"
    )

    # Should not raise
    validate_image_aspect_ratio(image_file)

def test_invalid_aspect_ratio_rejected():
    """Images far from 16:9 should be rejected."""
    img = Image.new('RGB', (1000, 1000), color='red')  # 1:1 square
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)

    image_file = SimpleUploadedFile("test.jpg", img_io.getvalue())

    with pytest.raises(ValidationError):
        validate_image_aspect_ratio(image_file)

def test_minimum_dimensions_enforced():
    """Images below 800x450 should be rejected."""
    img = Image.new('RGB', (400, 225), color='red')  # Too small
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)

    image_file = SimpleUploadedFile("test.jpg", img_io.getvalue())

    with pytest.raises(ValidationError):
        validate_image_aspect_ratio(image_file)
```

---

## Documentation

### User Guidance

**In admin/forms**:
> **Image Guidelines**:
>
> - Recommended size: 1920x1080 pixels (16:9 aspect ratio)
> - Minimum size: 800x450 pixels
> - Maximum file size: 5MB
> - Accepted formats: JPEG, PNG, WebP
> - Use high-quality images for best display on social media and high-DPI screens

**In developer docs**:
> Dataset images use a 16:9 aspect ratio optimized for:
>
> - Bootstrap card displays (responsive grid layouts)
> - Open Graph social media previews
> - Twitter Card images
> - Responsive breakpoints from mobile to desktop
>
> The system validates uploaded images and provides helpful error messages for incorrect dimensions or aspect ratios.

---

## Decision Summary

✅ **Primary Aspect Ratio**: 16:9 (1.778:1)
✅ **Recommended Upload**: 1920x1080px
✅ **Minimum Size**: 800x450px
✅ **Maximum File Size**: 5MB
✅ **Validation**: ±10% aspect ratio variance allowed
✅ **Thumbnails**: Auto-generated at 800x450px (1x) and 1600x900px (2x)
✅ **Placeholder**: Consistent aspect ratio with dynamic background colors
✅ **Social Media**: Optimized for Open Graph (1.91:1) and Twitter Card (16:9)

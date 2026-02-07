# Research: Bootstrap Card Image Best Practices

**Feature**: 004-core-datasets
**Task**: T014
**Purpose**: Document Bootstrap 5 best practices for dataset card image display

---

## Bootstrap 5 Card Structure

### Basic Card with Image

```html
<div class="card">
    <img src="..." class="card-img-top" alt="...">
    <div class="card-body">
        <h5 class="card-title">Card title</h5>
        <p class="card-text">Card content</p>
    </div>
</div>
```

**Key Classes**:

- `.card` - Container
- `.card-img-top` - Image at top of card
- `.card-body` - Content area
- `.card-title` - Card heading
- `.card-text` - Card paragraph text

---

## Responsive Grid Layout

### Recommended Pattern

```html
<div class="row row-cols-1 row-cols-sm-2 row-cols-md-3 row-cols-lg-4 g-4">
    {% for dataset in datasets %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                {% if dataset.image %}
                    <img src="{{ dataset.image.url }}"
                         class="card-img-top"
                         alt="{{ dataset.name }}"
                         style="aspect-ratio: 16/9; object-fit: cover;">
                {% else %}
                    <div class="card-img-top bg-light d-flex align-items-center justify-content-center"
                         style="aspect-ratio: 16/9;">
                        <i class="bi bi-file-earmark-text text-muted fs-1"></i>
                    </div>
                {% endif %}
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">{{ dataset.name }}</h5>
                    <p class="card-text text-muted small mb-2">
                        {{ dataset.project.name }}
                    </p>
                    <p class="card-text flex-grow-1">
                        {{ dataset.description|truncatewords:15 }}
                    </p>
                    <a href="{% url 'dataset_detail' dataset.pk %}"
                       class="btn btn-primary btn-sm mt-auto">
                        View Details
                    </a>
                </div>
            </div>
        </div>
    {% endfor %}
</div>
```

**Key Utility Classes**:

- `row-cols-*` - Responsive column counts
- `g-4` - Gutter spacing (1.5rem)
- `h-100` - Full height cards in grid
- `shadow-sm` - Subtle shadow for depth
- `d-flex flex-column` - Flexbox layout for card body
- `flex-grow-1` - Description takes available space
- `mt-auto` - Button pushes to bottom

---

## Image Sizing & Aspect Ratio

### CSS Best Practices

```css
/* Ensure consistent aspect ratio */
.card-img-top {
    aspect-ratio: 16/9;
    object-fit: cover;
    object-position: center;
}

/* Prevent image overflow */
.card img {
    max-width: 100%;
    height: auto;
}

/* Smooth image loading */
.card-img-top {
    background-color: #f8f9fa;  /* Placeholder while loading */
}
```

### Inline Styles (If Not Using CSS File)

```html
<img src="{{ dataset.image.url }}"
     class="card-img-top"
     alt="{{ dataset.name }}"
     style="aspect-ratio: 16/9; object-fit: cover; object-position: center;">
```

**Properties Explained**:

- `aspect-ratio: 16/9` - Maintains 16:9 regardless of source image dimensions
- `object-fit: cover` - Crops to fill container (alternative: `contain` shows full image)
- `object-position: center` - Centers cropped area (alternatives: `top`, `bottom`)

---

## Loading Performance

### Lazy Loading

```html
<img src="{{ dataset.image.url }}"
     class="card-img-top"
     alt="{{ dataset.name }}"
     loading="lazy"
     decoding="async">
```

**Attributes**:

- `loading="lazy"` - Defers loading until near viewport (native browser feature)
- `decoding="async"` - Non-blocking image decode

### Responsive Images with srcset

```html
{% load thumbnail %}

{% thumbnail dataset.image "800x450" crop="smart" as im %}
{% thumbnail dataset.image "1600x900" crop="smart" as im_2x %}
<img src="{{ im.url }}"
     srcset="{{ im.url }} 1x, {{ im_2x.url }} 2x"
     class="card-img-top"
     alt="{{ dataset.name }}"
     loading="lazy"
     width="{{ im.width }}"
     height="{{ im.height }}">
{% endthumbnail %}
{% endthumbnail %}
```

**Benefits**:

- Serves appropriate resolution for device
- Reduces bandwidth on standard displays
- Sharp images on high-DPI screens (Retina)

---

## Placeholder for Missing Images

### Icon Placeholder

```html
{% if dataset.image %}
    <img src="{{ dataset.image.url }}" class="card-img-top" alt="{{ dataset.name }}">
{% else %}
    <div class="card-img-top bg-light d-flex align-items-center justify-content-center text-muted"
         style="aspect-ratio: 16/9;">
        <i class="bi bi-database fs-1"></i>
    </div>
{% endif %}
```

### Gradient Placeholder

```html
<div class="card-img-top d-flex align-items-center justify-content-center"
     style="aspect-ratio: 16/9;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
    <i class="bi bi-file-earmark-text text-white fs-1 opacity-50"></i>
</div>
```

### Dynamic Color Placeholder

```python
# templatetags/dataset_tags.py
@register.simple_tag
def dataset_placeholder_gradient(dataset):
    """Generate consistent gradient from dataset name."""
    import hashlib
    hash_val = int(hashlib.md5(dataset.name.encode()).hexdigest()[:6], 16)
    hue1 = hash_val % 360
    hue2 = (hue1 + 60) % 360  # Complementary hue
    return f"linear-gradient(135deg, hsl({hue1}, 70%, 60%) 0%, hsl({hue2}, 70%, 50%) 100%)"
```

```html
{% load dataset_tags %}
<div class="card-img-top d-flex align-items-center justify-content-center"
     style="aspect-ratio: 16/9; background: {% dataset_placeholder_gradient dataset %};">
    <i class="bi bi-database text-white fs-1 opacity-75"></i>
</div>
```

---

## Card Hover Effects

### Subtle Elevation

```css
.dataset-card {
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.dataset-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15) !important;
}
```

### Image Zoom on Hover

```css
.dataset-card {
    overflow: hidden;
}

.dataset-card .card-img-top {
    transition: transform 0.3s ease-in-out;
}

.dataset-card:hover .card-img-top {
    transform: scale(1.05);
}
```

### Combined Effect

```html
<div class="col">
    <div class="card h-100 shadow-sm dataset-card">
        <div class="overflow-hidden">
            <img src="{{ dataset.image.url }}"
                 class="card-img-top"
                 alt="{{ dataset.name }}"
                 style="aspect-ratio: 16/9; object-fit: cover; transition: transform 0.3s;">
        </div>
        <div class="card-body">
            ...
        </div>
    </div>
</div>

<style>
.dataset-card {
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.dataset-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.15) !important;
}

.dataset-card:hover .card-img-top {
    transform: scale(1.05);
}
</style>
```

---

## Badge Overlays

### Visibility Badge

```html
<div class="card h-100 position-relative">
    {% if dataset.image %}
        <img src="{{ dataset.image.url }}" class="card-img-top" alt="{{ dataset.name }}">
        <span class="position-absolute top-0 end-0 m-2 badge bg-{{ dataset.visibility|lower }}">
            {{ dataset.get_visibility_display }}
        </span>
    {% endif %}
    <div class="card-body">
        ...
    </div>
</div>
```

### Custom CSS for Badge Colors

```css
.badge.bg-public { background-color: #28a745 !important; }
.badge.bg-registered { background-color: #17a2b8 !important; }
.badge.bg-embargoed { background-color: #ffc107 !important; color: #000; }
.badge.bg-private { background-color: #dc3545 !important; }
```

### License Icon

```html
{% if dataset.license %}
    <span class="position-absolute bottom-0 start-0 m-2 badge bg-dark bg-opacity-75">
        <i class="bi bi-cc-circle"></i> {{ dataset.license.short_name }}
    </span>
{% endif %}
```

---

## Equal Height Cards

### Flexbox Approach

```html
<div class="row row-cols-1 row-cols-md-3 g-4">
    <div class="col d-flex">
        <div class="card w-100">
            <!-- Card content -->
        </div>
    </div>
</div>
```

### Height Matching

```css
.card-group .card {
    height: 100%;
}
```

### Body Flex Layout

```html
<div class="card h-100">
    <img src="..." class="card-img-top">
    <div class="card-body d-flex flex-column">
        <h5 class="card-title">Title</h5>
        <p class="card-text flex-grow-1">Description that varies in length...</p>
        <a href="#" class="btn btn-primary mt-auto">View</a>
    </div>
</div>
```

**Key**:

- `d-flex flex-column` on card-body
- `flex-grow-1` on description (takes available space)
- `mt-auto` on button (pushes to bottom)

---

## Accessibility

### Alt Text

```html
<img src="{{ dataset.image.url }}"
     class="card-img-top"
     alt="{{ dataset.name }} - {{ dataset.description|truncatewords:10 }}">
```

**Best Practice**: Descriptive alt text, not just "dataset image"

### Semantic HTML

```html
<article class="card h-100">
    <img src="..." class="card-img-top" alt="...">
    <div class="card-body">
        <h3 class="card-title h5">{{ dataset.name }}</h3>
        <p class="card-text">{{ dataset.description }}</p>
        <a href="..." class="btn btn-primary" aria-label="View details for {{ dataset.name }}">
            View Details
        </a>
    </div>
</article>
```

### Keyboard Navigation

```html
<a href="{% url 'dataset_detail' dataset.pk %}"
   class="card h-100 text-decoration-none text-dark dataset-card"
   role="article">
    <img src="..." class="card-img-top" alt="...">
    <div class="card-body">
        <h5 class="card-title">{{ dataset.name }}</h5>
        <p class="card-text">{{ dataset.description }}</p>
    </div>
</a>
```

**Note**: Entire card is clickable, keyboard-accessible link

---

## Complete Example

### Production-Ready Dataset Card

```html
{% load thumbnail dataset_tags %}

<div class="col">
    <article class="card h-100 shadow-sm dataset-card position-relative">
        <!-- Image with placeholder fallback -->
        <div class="position-relative overflow-hidden">
            {% if dataset.image %}
                {% thumbnail dataset.image "800x450" crop="smart" as im %}
                {% thumbnail dataset.image "1600x900" crop="smart" as im_2x %}
                <img src="{{ im.url }}"
                     srcset="{{ im.url }} 1x, {{ im_2x.url }} 2x"
                     class="card-img-top"
                     alt="{{ dataset.name }}"
                     loading="lazy"
                     decoding="async"
                     width="{{ im.width }}"
                     height="{{ im.height }}"
                     style="aspect-ratio: 16/9; object-fit: cover;">
                {% endthumbnail %}
                {% endthumbnail %}
            {% else %}
                <div class="card-img-top d-flex align-items-center justify-content-center"
                     style="aspect-ratio: 16/9; background: {% dataset_placeholder_gradient dataset %};">
                    <i class="bi bi-database text-white fs-1 opacity-75"></i>
                </div>
            {% endif %}

            <!-- Visibility badge overlay -->
            <span class="position-absolute top-0 end-0 m-2 badge bg-{{ dataset.visibility|lower }}">
                {{ dataset.get_visibility_display }}
            </span>
        </div>

        <!-- Card body with flex layout -->
        <div class="card-body d-flex flex-column">
            <h5 class="card-title">{{ dataset.name }}</h5>

            <p class="text-muted small mb-2">
                <i class="bi bi-folder"></i> {{ dataset.project.name }}
            </p>

            <p class="card-text flex-grow-1">
                {{ dataset.description|truncatewords:20 }}
            </p>

            <!-- Metadata badges -->
            <div class="mb-2">
                {% if dataset.license %}
                    <span class="badge bg-secondary">
                        <i class="bi bi-cc-circle"></i> {{ dataset.license.short_name }}
                    </span>
                {% endif %}
                {% if dataset.has_data %}
                    <span class="badge bg-success">
                        <i class="bi bi-check-circle"></i> Has Data
                    </span>
                {% endif %}
            </div>

            <!-- Action button -->
            <a href="{% url 'dataset_detail' dataset.pk %}"
               class="btn btn-primary btn-sm mt-auto w-100"
               aria-label="View details for {{ dataset.name }}">
                <i class="bi bi-eye"></i> View Details
            </a>
        </div>
    </article>
</div>

<style>
.dataset-card {
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.dataset-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 0.5rem 1.5rem rgba(0, 0, 0, 0.15) !important;
}

.dataset-card:hover .card-img-top {
    transform: scale(1.05);
}

.dataset-card .card-img-top {
    transition: transform 0.3s ease-in-out;
}

.badge.bg-public { background-color: #28a745 !important; }
.badge.bg-registered { background-color: #17a2b8 !important; }
.badge.bg-embargoed { background-color: #ffc107 !important; color: #000; }
.badge.bg-private { background-color: #dc3545 !important; }
</style>
```

---

## Testing Checklist

### Visual Testing

- [ ] Cards display correctly at all breakpoints (xs, sm, md, lg, xl, xxl)
- [ ] Images maintain 16:9 aspect ratio
- [ ] Images don't distort or stretch
- [ ] Placeholder shows for datasets without images
- [ ] Equal heights work across rows
- [ ] Hover effects are smooth and consistent
- [ ] Badges are legible and positioned correctly

### Accessibility Testing

- [ ] All images have descriptive alt text
- [ ] Cards are keyboard navigable
- [ ] Focus indicators are visible
- [ ] Screen reader announces card content correctly
- [ ] Color contrast meets WCAG AA standards (4.5:1 for text)

### Performance Testing

- [ ] Images lazy load outside viewport
- [ ] Thumbnails generated at appropriate sizes
- [ ] srcset provides different resolutions
- [ ] No layout shift during image load
- [ ] Cards render quickly on slow connections

---

## Decision Summary

✅ **Card Structure**: Bootstrap 5 `.card` with `.card-img-top`
✅ **Grid Layout**: Responsive columns (1/2/3/4 across breakpoints)
✅ **Image Aspect**: 16:9 with `object-fit: cover`
✅ **Placeholder**: Dynamic gradient with icon for missing images
✅ **Loading**: Lazy loading + srcset for responsive images
✅ **Height**: Equal height cards with flexbox layout
✅ **Hover**: Subtle elevation + image zoom
✅ **Badges**: Visibility and license overlays
✅ **Accessibility**: Descriptive alt text, keyboard navigation, semantic HTML

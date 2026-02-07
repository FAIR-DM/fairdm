# Demo App Preparation: Models

**Feature**: 004-core-datasets
**Purpose**: Prepare fairdm_demo for updated Dataset model implementation
**File**: `fairdm_demo/models.py`

---

## Changes Required

### 1. Remove Simple ManyToMany (if exists)

**Current Pattern** (if exists):

```python
class CustomDataset(Dataset):
    related_literature = models.ManyToManyField(
        'literature.LiteratureItem',
        blank=True
    )
```

**Action**: Remove this field - now handled by base Dataset model with `through` parameter

---

### 2. Add Custom Sample Models (Example)

To demonstrate dataset-sample relationships:

```python
from fairdm.core.models import Sample

class RockSample(Sample):
    """Example geological sample type."""
    rock_type = models.CharField(max_length=100)
    weight_grams = models.DecimalField(max_digits=8, decimal_places=2)
    collection_location = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"
```

---

### 3. Add Custom Measurement Models (Example)

To demonstrate dataset-measurement relationships:

```python
from fairdm.core.models import Measurement

class XRFMeasurement(Measurement):
    """Example X-ray fluorescence measurement."""
    element = models.CharField(max_length=10)
    concentration_ppm = models.DecimalField(max_digits=10, decimal_places=2)
    detection_limit_ppm = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "XRF Measurement"
        verbose_name_plural = "XRF Measurements"
```

---

### 4. Add Custom Dataset Subclass (Optional)

To demonstrate dataset inheritance:

```python
class GeologicalDataset(Dataset):
    """Extended dataset for geological data."""
    region = models.CharField(max_length=200, blank=True)
    geological_age = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Geological Dataset"
        verbose_name_plural = "Geological Datasets"
```

---

## Full Example: fairdm_demo/models.py

```python
"""
Demo app models showcasing FairDM dataset functionality.

This module demonstrates:
- Custom Sample types (RockSample)
- Custom Measurement types (XRFMeasurement)
- Dataset subclassing (GeologicalDataset)
- Relationships between datasets, samples, and measurements
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from fairdm.core.models import Dataset, Sample, Measurement


class RockSample(Sample):
    """
    Geological rock sample.

    Demonstrates custom Sample subclass with domain-specific fields.
    Each RockSample can belong to multiple datasets.
    """
    rock_type = models.CharField(
        max_length=100,
        help_text=_("Type of rock (igneous, sedimentary, metamorphic)")
    )
    weight_grams = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text=_("Sample weight in grams")
    )
    collection_location = models.CharField(
        max_length=200,
        help_text=_("Geographic location where sample was collected")
    )
    collection_date = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date sample was collected")
    )

    class Meta:
        verbose_name = _("Rock Sample")
        verbose_name_plural = _("Rock Samples")

    def __str__(self):
        return f"{self.name} ({self.rock_type})"


class XRFMeasurement(Measurement):
    """
    X-ray fluorescence measurement.

    Demonstrates custom Measurement subclass with scientific data.
    Each XRFMeasurement belongs to a Sample and can be part of multiple datasets.
    """
    element = models.CharField(
        max_length=10,
        help_text=_("Chemical element measured (e.g., Fe, Si, Ca)")
    )
    concentration_ppm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Concentration in parts per million")
    )
    detection_limit_ppm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Minimum detectable concentration")
    )
    measurement_date = models.DateField(
        help_text=_("Date measurement was taken")
    )
    instrument = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("XRF instrument model used")
    )

    class Meta:
        verbose_name = _("XRF Measurement")
        verbose_name_plural = _("XRF Measurements")

    def __str__(self):
        return f"{self.element}: {self.concentration_ppm} ppm"


class GeologicalDataset(Dataset):
    """
    Extended dataset for geological data.

    Demonstrates Dataset subclassing to add domain-specific fields.
    Inherits all Dataset functionality (descriptions, dates, identifiers, etc.)
    """
    region = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Geographic region of study")
    )
    geological_age = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Geological age/period (e.g., Cretaceous, Jurassic)")
    )
    survey_type = models.CharField(
        max_length=50,
        choices=[
            ('field', _('Field Survey')),
            ('aerial', _('Aerial Survey')),
            ('satellite', _('Satellite Imagery')),
            ('laboratory', _('Laboratory Analysis')),
        ],
        default='field',
        help_text=_("Type of geological survey conducted")
    )

    class Meta:
        verbose_name = _("Geological Dataset")
        verbose_name_plural = _("Geological Datasets")

    def __str__(self):
        if self.region:
            return f"{self.name} - {self.region}"
        return self.name
```

---

## Migration Notes

### After Implementation

1. **Generate migrations**:

   ```bash
   poetry run python manage.py makemigrations fairdm_demo
   ```

2. **Review migration**:
   - Check for conflicts with core Dataset migrations
   - Verify foreign key relationships

3. **Apply migrations**:

   ```bash
   poetry run python manage.py migrate fairdm_demo
   ```

---

## Testing Integration

Add these models to factories:

```python
# In fairdm_demo/factories.py

import factory
from factory.django import DjangoModelFactory
from .models import RockSample, XRFMeasurement, GeologicalDataset


class RockSampleFactory(DjangoModelFactory):
    class Meta:
        model = RockSample

    name = factory.Sequence(lambda n: f"Rock Sample {n}")
    rock_type = factory.Iterator(['igneous', 'sedimentary', 'metamorphic'])
    weight_grams = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    collection_location = factory.Faker('city')
    collection_date = factory.Faker('date_this_decade')


class XRFMeasurementFactory(DjangoModelFactory):
    class Meta:
        model = XRFMeasurement

    sample = factory.SubFactory(RockSampleFactory)
    element = factory.Iterator(['Fe', 'Si', 'Ca', 'Mg', 'Al', 'K', 'Na'])
    concentration_ppm = factory.Faker('pydecimal', left_digits=6, right_digits=2, positive=True)
    detection_limit_ppm = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    measurement_date = factory.Faker('date_this_year')
    instrument = factory.Iterator(['Bruker M4 Tornado', 'Olympus Vanta', 'Thermo Niton XL3t'])


class GeologicalDatasetFactory(DjangoModelFactory):
    class Meta:
        model = GeologicalDataset

    name = factory.Sequence(lambda n: f"Geological Dataset {n}")
    project = factory.SubFactory('fairdm.factories.ProjectFactory')
    region = factory.Faker('state')
    geological_age = factory.Iterator(['Cretaceous', 'Jurassic', 'Triassic', 'Permian'])
    survey_type = factory.Iterator(['field', 'aerial', 'satellite', 'laboratory'])
```

---

## Documentation Comments

Add comprehensive docstrings to demonstrate best practices:

```python
class RockSample(Sample):
    """
    Geological rock sample.

    This model extends the base Sample class to add domain-specific fields
    for geological research. Demonstrates custom Sample type creation.

    Relationships:
        - Can belong to multiple datasets (inherited from Sample)
        - Can have multiple measurements (inherited from Sample)
        - Belongs to a project (inherited via Sample)

    Example:
        ```python
        from fairdm_demo.models import RockSample

        sample = RockSample.objects.create(
            name="Granite-001",
            rock_type="igneous",
            weight_grams=245.6,
            collection_location="Mount Rushmore, SD"
        )
        ```

    See Also:
        - :class:`fairdm.core.models.Sample`: Base Sample model
        - :class:`XRFMeasurement`: Related measurement type
        - Developer Guide: Custom Sample Types
    """
```

---

## Next Steps

After model updates:

1. Update `fairdm_demo/config.py` or `fairdm_demo/admin.py` (see T010)
2. Generate factories (factories.py)
3. Create test fixtures
4. Update demo app documentation

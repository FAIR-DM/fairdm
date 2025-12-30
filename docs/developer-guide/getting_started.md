# Getting Started

This guide walks you through your first FairDM experience: running a demo portal, defining your first custom Sample and Measurement models, and seeing them come to life in both the UI and via the API.

```{note}
**Prerequisites**: Before starting, ensure you've reviewed [Before You Begin](before_you_begin.md) and have Python 3.13+, Poetry, and Git installed.
```

## What You'll Build

By the end of this guide, you will have:

1. A working FairDM demo portal running locally
2. A custom `RockSample` model with domain-specific fields
3. A custom `MineralAnalysis` measurement model
4. Both models registered with FairDM and visible in the portal UI
5. Programmatic access to your models via the API

## Step 1: Run the Demo Portal

The fastest way to explore FairDM is to run the included demo portal. This portal comes pre-configured with example data and demonstrates all core features.

### Clone the Repository

```bash
git clone https://github.com/FAIR-DM/fairdm.git
cd fairdm
```

### Install Dependencies

```bash
poetry install
```

### Set Up the Database

```bash
poetry run python manage.py migrate
poetry run python manage.py loaddata fairdm/fixtures/demo.json.bz2
```

### Start the Development Server

```bash
poetry run python manage.py runserver
```

### Access the Portal

Open your browser and navigate to:

```
http://127.0.0.1:8000
```

You should see the FairDM demo portal homepage. Take a moment to explore:

- Browse existing **Projects** and **Datasets**
- View **Samples** and **Measurements**
- Click into detail pages to see the metadata structure

```{tip}
The demo includes a test user account. Check the demo fixture or create a new superuser with: `poetry run python manage.py createsuperuser`
```

## Step 2: Define Your First Custom Sample Model

Now that you have the demo running, let's create a domain-specific Sample model. We'll create a `RockSample` model for geological research.

### Create a Custom App

In a real FairDM project (generated from the cookiecutter), you would create custom models in your own Django app. For this tutorial, we'll create a simple example in the `fairdm_demo` app.

Create a new file: `fairdm_demo/models/samples.py`

```python
from django.db import models
from fairdm.samples.models import Sample

class RockSample(Sample):
    """
    A geological rock sample with domain-specific fields.
    """
    # Geological properties
    rock_type = models.CharField(
        max_length=100,
        help_text="Type of rock (e.g., igneous, sedimentary, metamorphic)"
    )
    
    mineral_composition = models.TextField(
        help_text="Primary minerals present in the sample",
        blank=True
    )
    
    collection_depth_m = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Depth in meters at which the sample was collected"
    )
    
    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"
    
    def __str__(self):
        return f"{self.sample_id}: {self.rock_type}"
```

### Key Points

- **Extend `Sample`**: Your custom model inherits from `fairdm.samples.models.Sample`, which provides core fields like `sample_id`, `name`, `description`, and FAIR metadata
- **Add domain fields**: Define fields specific to your research domain
- **Use Django conventions**: Standard Django model patterns apply

## Step 3: Define a Custom Measurement Model

Measurements represent observations or analyses performed on samples. Let's create a `MineralAnalysis` measurement model.

Create a new file: `fairdm_demo/models/measurements.py`

```python
from django.db import models
from fairdm.measurements.models import Measurement

class MineralAnalysis(Measurement):
    """
    A mineral composition analysis measurement.
    """
    analysis_method = models.CharField(
        max_length=200,
        help_text="Method used for analysis (e.g., X-ray diffraction, mass spectrometry)"
    )
    
    mineral_name = models.CharField(
        max_length=100,
        help_text="Name of the mineral analyzed"
    )
    
    percentage_composition = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage of this mineral in the sample"
    )
    
    detection_limit = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Detection limit of the analysis method (percentage)"
    )
    
    class Meta:
        verbose_name = "Mineral Analysis"
        verbose_name_plural = "Mineral Analyses"
    
    def __str__(self):
        return f"{self.mineral_name} analysis: {self.percentage_composition}%"
```

## Step 4: Register Your Models with FairDM

To make your models visible in the FairDM UI and API, you need to register them with the FairDM registry. This auto-generates forms, tables, filters, and serializers.

Create a new file: `fairdm_demo/registry.py`

```python
from fairdm.registry import registry, SampleConfig, MeasurementConfig
from .models.samples import RockSample
from .models.measurements import MineralAnalysis

# Register the RockSample model
registry.register(
    RockSample,
    config=SampleConfig(
        list_display=['sample_id', 'rock_type', 'collection_depth_m', 'created'],
        search_fields=['sample_id', 'name', 'rock_type'],
        list_filter=['rock_type', 'created'],
    )
)

# Register the MineralAnalysis model
registry.register(
    MineralAnalysis,
    config=MeasurementConfig(
        list_display=['mineral_name', 'percentage_composition', 'analysis_method', 'created'],
        search_fields=['mineral_name', 'analysis_method'],
        list_filter=['mineral_name', 'analysis_method', 'created'],
    )
)
```

### Import Your Registry

Ensure your registry is imported when Django starts. Add to `fairdm_demo/apps.py`:

```python
from django.apps import AppConfig

class FairdmDemoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fairdm_demo'
    
    def ready(self):
        # Import registry to ensure models are registered
        import fairdm_demo.registry  # noqa
```

## Step 5: Create and Apply Migrations

Now that you've defined your models, create Django migrations:

```bash
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

## Step 6: Verify in the UI

### Access the Admin Interface

Navigate to:

```
http://127.0.0.1:8000/admin/
```

Log in with your superuser credentials. You should see:

- **Rock Samples** section with options to add/edit rock samples
- **Mineral Analyses** section with options to add/edit measurements

### Create a Test Rock Sample

1. Click **"Add Rock Sample"**
2. Fill in required fields:
   - Sample ID: `ROCK-001`
   - Name: `Basalt from Mt. Example`
   - Rock type: `Igneous`
   - Mineral composition: `Olivine, pyroxene, plagioclase`
   - Collection depth: `15.50` meters
3. Click **"Save"**

### Create a Test Measurement

1. Click **"Add Mineral Analysis"**
2. Associate it with your rock sample
3. Fill in:
   - Mineral name: `Olivine`
   - Percentage composition: `45.00`%
   - Analysis method: `X-ray diffraction`
4. Click **"Save"**

### Browse in the Portal

Navigate back to the main portal:

```
http://127.0.0.1:8000/samples/
```

You should see your new `ROCK-001` sample listed. Click on it to view the detail page, which will show:

- All standard Sample metadata
- Your custom fields (rock type, mineral composition, collection depth)
- Associated measurements

## Step 7: Verify Programmatic Access

FairDM automatically generates a REST API for registered models. Let's confirm your models are accessible programmatically.

### Using the Browsable API

Navigate to:

```
http://127.0.0.1:8000/api/samples/
```

You should see a JSON response listing all samples, including your `RockSample`. The API is browsable - you can click links and navigate the data structure.

### Using curl

From your terminal:

```bash
curl http://127.0.0.1:8000/api/samples/
```

You should see JSON output including your custom fields:

```json
{
  "count": 1,
  "results": [
    {
      "id": "...",
      "sample_id": "ROCK-001",
      "name": "Basalt from Mt. Example",
      "rock_type": "Igneous",
      "mineral_composition": "Olivine, pyroxene, plagioclase",
      "collection_depth_m": "15.50",
      ...
    }
  ]
}
```

### Using Python

You can also access the API programmatically:

```python
import requests

response = requests.get('http://127.0.0.1:8000/api/samples/')
data = response.json()

for sample in data['results']:
    print(f"Sample: {sample['sample_id']} - {sample['name']}")
    print(f"  Rock type: {sample.get('rock_type', 'N/A')}")
```

## What You've Accomplished

Congratulations! You've completed your first FairDM journey:

✅ Ran a local FairDM demo portal  
✅ Defined a custom `RockSample` model with domain-specific fields  
✅ Defined a custom `MineralAnalysis` measurement model  
✅ Registered both models with the FairDM registry  
✅ Created test data and verified it appears in the UI  
✅ Confirmed programmatic access via the REST API  

## Next Steps

Now that you understand the basics, explore:

- **[Defining Models](defining_models.md)**: Learn more about Sample and Measurement model patterns
- **[Model Configuration](model_configuration.md)**: Customize auto-generated forms, tables, and filters
- **[Using the Registry](using_the_registry.md)**: Deep dive into registration options
- **[Deployment](deployment_guide/production.md)**: Deploy your portal to production

```{seealso}
For more advanced topics like custom views, plugins, and integration with external services, see the [How-to Guides](create_a_plugin.md) section.
```

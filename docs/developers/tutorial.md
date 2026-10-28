# Build your first sample and measurement types

In this tutorial you build a new portal that records rock samples and the density measurements made on them. You finish with both types in the portal's menus and listings, in the administration interface and in the API.

## Before you start

You need:

- [Docker](https://docs.docker.com/get-started/get-docker/) with Compose. The portal runs on PostGIS and needs the GDAL libraries, and the images used below hold both. See [The technology stack](../explanation/the-technology-stack.md).
- Port 8000 free on your machine.
- Some Django. The [Django tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) covers the models and migrations used here.
- A terminal and a text editor.

`yourportal` is a placeholder for your portal's name. Keep it for this tutorial, so that every command works as written. Run every command from the `yourportal` folder you create in step 1.

## 1. Start the database

1. Create the folder and open it.

   ```bash
   mkdir yourportal
   cd yourportal
   ```

2. Create `compose.yaml`.

   ```yaml
   name: yourportal

   services:
     postgres:
       image: postgis/postgis:17-3.5
       environment:
         POSTGRES_PASSWORD: postgres
         POSTGRES_DB: yourportal
       volumes:
         - postgres:/var/lib/postgresql/data
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U postgres"]
         interval: 5s
         retries: 20

     django:
       image: ghcr.io/fair-dm/fairdm:1.0.0-dev
       depends_on:
         postgres:
           condition: service_healthy
       environment:
         POSTGRES_HOST: postgres
         POSTGRES_PASSWORD: postgres
         POSTGRES_DB: yourportal
       volumes:
         - ./:/app
         - venv:/opt/venv
       ports:
         - "8000:8000"
       command: python manage.py runserver 0.0.0.0:8000

   volumes:
     postgres:
     venv:
   ```

   The `django` service runs FairDM's development image. The image version and the PostGIS version are the ones the FairDM release in step 2 is tested on. See [Container images](reference/container-images.md).

3. Start the database.

   ```bash
   docker compose up --detach --wait postgres
   ```

The command ends with the line `Container yourportal-postgres-1  Healthy`.

## 2. Install FairDM

1. Create `pyproject.toml`.

   ```toml
   [project]
   name = "yourportal"
   version = "0.1.0"
   requires-python = ">=3.13"
   dependencies = ["fairdm", "django-browser-reload"]
   ```

   uv installs the latest FairDM release from [PyPI](https://pypi.org/project/fairdm/). FairDM's development settings load `django-browser-reload` without installing it, so the portal lists it.

2. Install the locked dependencies into the image's virtual environment.

   ```bash
   docker compose run --rm django uv sync
   ```

The first run pulls the image, which takes a few minutes. It ends with a list of installed packages that includes a line beginning `+ fairdm==`.

## 3. Create the portal and its app

1. Create the Django project, named `config`, and an app named `rocks`.

   ```bash
   docker compose run --rm django django-admin startproject config .
   docker compose run --rm django django-admin startapp rocks
   ```

2. Replace the contents of `config/settings.py`. One call to `fairdm.setup()` gives the portal its whole configuration, and `apps` lists your own apps. See [How FairDM configures a portal](../explanation/how-fairdm-configures-a-portal.md).

   ```python
   """Settings for yourportal."""

   import fairdm

   fairdm.setup(apps=["rocks"])
   ```

3. Replace the contents of `config/urls.py`.

   ```python
   """URL configuration for yourportal."""

   from django.urls import include, path

   urlpatterns = [
       path("", include("fairdm.conf.urls")),
   ]
   ```

4. Check the portal.

   ```bash
   docker compose run --rm django python manage.py check
   ```

The command ends with `System check identified no issues (1 silenced).` A warning that `REDIS_URL` is not set comes first. It is expected in development.

## 4. Define the types

1. Replace the contents of `rocks/models.py`. A sample type extends `Sample` and a measurement type extends `Measurement`. Every record already has `name`, `dataset` and `location`, and a measurement also has `sample`. A measurement type names its result `value` and its uncertainty `uncertainty`.

   ```python
   from fairdm.core.measurement.models import Measurement
   from fairdm.core.sample.models import Sample
   from fairdm.db import models


   class RockSample(Sample):
       rock_type = models.CharField(max_length=100)
       collection_date = models.DateField()
       weight_grams = models.FloatField(null=True, blank=True)

       class Meta:
           verbose_name = "Rock Sample"
           verbose_name_plural = "Rock Samples"


   class DensityMeasurement(Measurement):
       value = models.FloatField(help_text="Density in grams per cubic centimetre.")
       uncertainty = models.FloatField(null=True, blank=True)
       method = models.CharField(max_length=200, blank=True)

       class Meta:
           verbose_name = "Density Measurement"
           verbose_name_plural = "Density Measurements"
   ```

2. Create the migration and apply it.

   ```bash
   docker compose run --rm django python manage.py makemigrations rocks
   docker compose run --rm django python manage.py migrate
   ```

`makemigrations` reports `+ Create model DensityMeasurement` and `+ Create model RockSample`. Among the lines that `migrate` prints is `Applying rocks.0001_initial... OK`.

## 5. Register the types

Create `rocks/config.py`. FairDM imports the `config` module of every installed app when the portal starts, so nothing else has to import it.

```python
from fairdm.core.measurement.config import BaseMeasurementConfiguration
from fairdm.core.sample.config import BaseSampleConfiguration
from fairdm.registry import register

from .models import DensityMeasurement, RockSample


@register
class RockSampleConfig(BaseSampleConfiguration):
    model = RockSample
    fields = [
        *BaseSampleConfiguration.fields,
        "rock_type",
        "collection_date",
        "weight_grams",
    ]


@register
class DensityMeasurementConfig(BaseMeasurementConfiguration):
    model = DensityMeasurement
    fields = [
        *BaseMeasurementConfiguration.fields,
        "value",
        "uncertainty",
        "method",
    ]
```

`fields` names the fields that every generated component uses. See [Model configuration](reference/model-configuration.md).

Ask the registry what it holds.

```bash
docker compose run --rm django python manage.py shell -c "from fairdm.registry import registry; print(registry.samples, registry.measurements)"
```

The last line of the output is `[<class 'rocks.models.RockSample'>] [<class 'rocks.models.DensityMeasurement'>]`.

## 6. Start the portal

```bash
docker compose up --detach django
```

Open <http://localhost:8000>. Under **Samples and measurements**, the home page lists **Rock Samples** and **Density Measurements**. Each shows `None`, because the portal holds no records yet.

## 7. Add records in the administration interface

1. Create your account. Enter an email address and a password when asked.

   ```bash
   docker compose run --rm django python manage.py createsuperuser
   ```

2. Open <http://localhost:8000/admin/> and sign in. The page, headed **Portal Administration**, has a group headed **ROCKS** that lists **Density Measurements** and **Rock Samples**. Your two types are there.
3. In the **PROJECT** group, select **Add** beside **Projects**. In **Name**, type `Rock study` and select **Save**.
4. In the **DATASET** group, select **Add** beside **Datasets**. In **Name**, type `Granite survey`. In **Project**, choose **Rock study**. Set **Visibility** to **Public**, tick **Published** and select **Save**. A listing shows only records in published datasets. See [How access to a record is decided](../explanation/how-access-to-a-record-is-decided.md).
5. In the **ROCKS** group, select **Add** beside **Rock Samples**. In **Name**, type `Granite G-1`. In **Dataset**, choose **Granite survey**. In **Rock type**, type `Igneous`. In **Collection date**, type `2026-10-01`. In **Weight grams**, type `512.5`. Select **Save**.
6. In the **ROCKS** group, select **Add** beside **Density Measurements**. In **Name**, type `Bulk density`. In **Sample**, choose **Granite G-1**. In **Dataset**, choose **Granite survey**. In **Value**, type `2.65`. In the **Uncertainty** that follows **Value**, type `0.05`. In **Method**, type `Archimedes`. Select **Save**.

After you save the rock sample, the list of samples opens. It shows `Granite G-1`, with `Rock Sample` in the **Sample type** column.

## 8. Browse the records in the portal

1. Open <http://localhost:8000/collections/samples/rocksample/>. The page, headed **Rock Samples**, has a table with one row. The columns are **Name**, **Latitude**, **Longitude**, **Collection date**, **Status**, **Rock type** and **Weight grams**, and the row is `Granite G-1`.
2. Select **Granite G-1**. The sample's own page opens. Its measurements include a **Density Measurement** with the value `2.65`.
3. Open <http://localhost:8000/collections/measurements/densitymeasurement/>. The page, headed **Density Measurements**, has one row. It names the sample `Granite G-1` and shows the value `2.65`, the uncertainty `0.05` and the method `Archimedes`.

Neither page needed a view or a template. See [What registering a type produces](explanation/what-registering-a-type-produces.md).

## 9. Read the records through the API

Open <http://localhost:8000/api/v1/samples/rock-samples/>, or run:

```bash
curl http://localhost:8000/api/v1/samples/rock-samples/
```

The response lists one sample. These are the fields that come from your model:

```json
{
  "count": 1,
  "results": [
    {
      "name": "Granite G-1",
      "rock_type": "Igneous",
      "collection_date": "2026-10-01",
      "weight_grams": 512.5
    }
  ]
}
```

The real response carries the fields every sample has as well. Open <http://localhost:8000/api/v1/measurements/density-measurements/> for the measurement, and <http://localhost:8000/api/v1/docs/> for the documentation of both.

## What you have built

You have a portal with a sample type and a measurement type. Registering each one gave it a listing page, a menu entry, a form, a filter set, an administration page and an API endpoint, from the one class in `rocks/config.py`.

To go on from here:

- [How to add a sample type](how-to/add-a-sample-type.md) and [How to add a measurement type](how-to/add-a-measurement-type.md) cover the fields a type can have.
- [How to customise a generated component](how-to/customise-a-generated-component.md) replaces the table, the form or another part of a registered type.
- [How to search a registered type by more than its name](how-to/search-a-registered-type-by-more-than-its-name.md) widens the listing's search box.
- [How to test a portal with FairDM factories](how-to/test-a-portal-with-fairdm-factories.md) tests the new types.
- [How to deploy a portal in a container](how-to/deploy-a-portal-in-a-container.md) puts the portal on a server.

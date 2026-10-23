# How to add a viewset to the API router

A sample or measurement type you register is served by the API without any code. A viewset of your own is for a model that is not one of those, such as a table of boreholes that belongs to a dataset. It is served at `/api/v1/<prefix>/` beside the generated addresses and appears in the API documentation.

## Before you start

- You have a model with a `uuid` field and a foreign key named `dataset`. The viewset finds a record by its `uuid`. The `dataset` foreign key is what lets the API's visibility rules apply. The examples use a `Borehole` model with `name` and `depth_m` fields.
- Your app is listed after `fairdm` in `INSTALLED_APPS`. Apps run `ready()` in the order they are listed, and the router must be loaded after FairDM has registered the portal's types.

## Steps

1. Write a serializer. Declare the dataset as a reference, so the response carries its short identifier and address and never a database number.

   ```python
   # boreholes/api.py
   from rest_framework import serializers

   from fairdm.api.serializers import RecordReferenceField

   from .models import Borehole


   class BoreholeSerializer(serializers.ModelSerializer):
       dataset = RecordReferenceField(read_only=True)

       class Meta:
           model = Borehole
           fields = ["uuid", "name", "depth_m", "dataset"]
   ```

2. Write the viewset on `BaseViewSet`. It finds a record by `uuid` and requires a signed-in person to write. Its permissions and filters come from the API's settings, so it is held to the same visibility rules as the generated ones.

   ```python
   # boreholes/api.py
   from fairdm.api.viewsets import BaseViewSet


   class BoreholeViewSet(BaseViewSet):
       queryset = Borehole.objects.all()
       serializer_class = BoreholeSerializer
       ordering_fields = ["name", "depth_m"]
   ```

3. Register the viewset on the router from your app's `ready()` method.

   ```python
   # boreholes/apps.py
   from django.apps import AppConfig


   class BoreholesConfig(AppConfig):
       name = "boreholes"

       def ready(self):
           from fairdm.api.router import fairdm_api_router

           from .api import BoreholeViewSet

           fairdm_api_router.register(
               r"boreholes", BoreholeViewSet, basename="borehole"
           )
   ```

4. Optionally, put the viewset under a heading of your own in the documentation. Decorate it with `under_heading`.

   ```python
   from fairdm.api.viewsets import BaseViewSet, under_heading


   @under_heading("Boreholes")
   class BoreholeViewSet(BaseViewSet):
       ...
   ```

5. Restart the portal and open `/api/v1/`.

## The result

The root lists `boreholes`. `/api/v1/boreholes/` and `/api/v1/boreholes/{uuid}/` answer, and the route names are `api:borehole-list` and `api:borehole-detail`. The operations appear in `/api/v1/docs/`, under the heading you chose if you did step 4.

The router reads its routes once, when `fairdm.api.urls` is first loaded. A viewset registered from `ready()`, or from any module imported before the URL configuration is used, is served from the first request. One registered later is not served until that module is loaded again.

```{warning}
The visibility filter lists every record of a model that has neither an integer `visibility` field nor a `dataset` relation, to every caller. Give the viewset a `get_queryset` that returns only what the caller may see.
```

A record of a model with a `dataset` relation is listed for a visitor only when the dataset is public and published. A signed-in person also sees the records they hold a stored django-guardian `view` permission on. A contribution level on the dataset does not reach a model of your own.

You do not need this for a registered type. Its endpoints are generated, and a mistake in its registration stops the portal with the real error instead of leaving a route missing. To choose which of a registered type's fields the API returns, see [How to choose the fields the API returns](choose-the-fields-the-api-returns.md).

The addresses and the permissions the API applies are in the [REST API reference](../reference/rest-api.md).

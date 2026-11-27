# How to change a type's API address

Each sample and measurement type is served at an address made from its plural name. You change the address by changing that name on the model. Do this when the name the portal derived is not the one you want people to call.

## Before you start

- Know who calls the type's address today. Changing it moves the address, and nothing redirects from the old one.
- The examples use a sample type `PlantSample`, served at `/api/v1/samples/plant-samples/` until the name changes.

## Steps

1. Open the model and set `verbose_name` and `verbose_name_plural` in its `Meta`.

   ```python
   class PlantSample(Sample):
       species = models.CharField(max_length=100)

       class Meta:
           verbose_name = "leaf sample"
           verbose_name_plural = "leaf samples"
   ```

   The address is the plural name in lower case with spaces replaced by hyphens, so this gives `/api/v1/samples/leaf-samples/`. When you set no `Meta`, Django makes the plural name from the class name, so `PlantSample` gives `plant samples` and `XRFMeasurement` gives `xrf measurements`.

2. Create and apply the migration. Django records a change of `verbose_name` in a migration.

   ```bash
   uv run python manage.py makemigrations
   uv run python manage.py migrate
   ```

3. Restart the portal and open `/api/v1/`.

## The result

The root lists the type at its new address, and the two addresses `/api/v1/samples/leaf-samples/` and `/api/v1/samples/leaf-samples/{uuid}/` answer. The route names change with them: `reverse("api:samples-leaf-samples-list")` gives the list address. The old address answers `404`.

The plural name also titles each operation of the type in the API documentation, written as the model gives it, such as `leaf samples: list`.

A sample type and a measurement type with the same plural name do not collide, because samples are served under `samples/` and measurements under `measurements/`.

Tell the people who use the API before you rename a type that has been published. The list of addresses is in the [REST API reference](../reference/rest-api.md).

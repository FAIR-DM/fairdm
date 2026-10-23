# How to customise the API documentation

The API documentation at `/api/v1/docs/` is generated from the routes the portal runs. You change the title, the introduction and the version it shows, and the words that describe each sample or measurement type. Do this so a person who opens the page knows what your portal's API is for and who stands behind each type.

## Before you start

You need to edit the portal's settings module, the one that calls `fairdm.setup()`. The settings used here are described in [Settings](../reference/settings.md).

## Steps

1. After the `fairdm.setup()` call, assign items of `SPECTACULAR_SETTINGS`.

   ```python
   import fairdm

   fairdm.setup()

   SPECTACULAR_SETTINGS["TITLE"] = "Palaeo-Climate Data Portal API"
   SPECTACULAR_SETTINGS["DESCRIPTION"] = """\
   ## Palaeo-Climate Data Portal API

   Programmatic access to all published palaeo-climate data in this portal.

   ### Resources

   - `/api/v1/projects/` Research projects
   - `/api/v1/datasets/` Datasets
   - `/api/v1/samples/{type}/` Sample types
   """
   SPECTACULAR_SETTINGS["VERSION"] = "2.0.0"
   ```

   Assign items, as above, and never a new dictionary. `SPECTACULAR_SETTINGS` also holds the bundled Swagger assets, the path prefix and the hook that writes the limits into the description, and a new dictionary drops all of them.

2. Open the registration of each sample or measurement type and describe it with `metadata`.

   ```python
   import fairdm
   from fairdm.registry import Authority, Citation, ModelMetadata, SampleConfig

   from .models import PlantSample


   @fairdm.register
   class PlantSampleConfig(SampleConfig):
       model = PlantSample
       metadata = ModelMetadata(
           description=(
               "Plant samples collected from field sites. Each sample records "
               "the species and the date it was collected."
           ),
           authority=Authority(name="Institute of Botany", short_name="IoB"),
           citation=Citation(
               text="Institute of Botany (2026). Plant sampling protocol.",
               doi="10.1234/plants",
           ),
           keywords=["botany", "plants"],
           repository_url="https://github.com/example/plants",
       )
   ```

3. Restart the portal and open `/api/v1/docs/`.

## The result

The page shows your title and version, and your text at the top of the description. The description ends with FairDM's own sections on authentication, limits and paging. They are read from your settings each time the schema is generated, so they stay correct when you change a limit or a page size. Do not write those numbers into your own text.

What a type's registration gives appears in these places:

| Registration | Appears in |
|---|---|
| `metadata.description`, else `description` on the configuration, else the model's docstring, else a sentence naming the type | The description of every operation of the type, and of the type's record |
| `metadata.authority` (`name`, `short_name`, `website`) | The description of the type's list operation, as the authority |
| `metadata.citation` (`text`, `doi`) | The same place, as the citation |
| `metadata.keywords` | The same place, as the keywords |
| `metadata.repository_url` | The external documentation link of the type's list operation |
| The model's `verbose_name_plural` | The title of each operation, such as `plant samples: list` |
| The model's `verbose_name` | The title of the type's record |

`metadata.maintainer` and `metadata.maintainer_email` are never published, because the documentation is public and those are a person's details.

Setting `FAIRDM_API_TITLE` or `FAIRDM_API_DESCRIPTION` in your settings changes nothing. They are the defaults `SPECTACULAR_SETTINGS` is built from when FairDM loads, before your settings run. If you do replace `SPECTACULAR_SETTINGS` altogether, keep `fairdm.api.schema.describe_api` in its `POSTPROCESSING_HOOKS` list, after `drf_spectacular.hooks.postprocess_schema_enums`, or the limits, the headings and the type descriptions are lost.

To place a viewset of your own under a heading, see [How to add a viewset to the API router](add-a-viewset-to-the-api-router.md). The screen itself is described in [API documentation](../../users/api/api-docs.md).

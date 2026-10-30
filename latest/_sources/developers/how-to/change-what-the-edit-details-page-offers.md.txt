# How to change what the edit details page offers

The edit details page of a sample or measurement edits the record with the form its type creates records with. You change what the page offers by changing the form on the type's configuration.

## Before you start

You need a registered sample or measurement type. The page is described in [Record editing pages](../reference/record-editing-pages.md#edit-details), and the options in [Model configuration](../reference/model-configuration.md). A project and a dataset are edited with `ProjectForm` and `DatasetForm`, which a configuration does not change.

## Steps

1. Open the type's configuration, the class registered for it.

2. To offer fewer or different fields, set `form_fields`:

   ```python
   import fairdm
   from fairdm.core.sample.config import BaseSampleConfiguration

   from .models import CoreSample


   @fairdm.register
   class CoreSampleConfig(BaseSampleConfiguration):
       model = CoreSample
       fields = ["name", "dataset", "local_id", "depth_m", "lithology"]
       form_fields = ["name", "dataset", "local_id", "depth_m"]
   ```

3. To replace the form altogether, set `form_class` to your own `ModelForm`, or its dotted path. Declare either `form_fields` or `form_class`, not both. FairDM refuses a configuration that declares both for the same component.

4. Open the sample's edit details page.

## The result

The page offers the fields you chose, less `dataset`. The page removes the `dataset` and `sample` fields whatever the form declares, so a record cannot be moved from here. Dates and identifiers are not on this page. They have pages of their own. If your form's crispy-forms helper has a form tag or buttons, the page turns them off and draws its own Save buttons.

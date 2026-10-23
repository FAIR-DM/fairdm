# How to place an organization on a map

This guide gives an organization a point in a form of your own, so its page shows a map. You would do this when a portal edits organizations through a form other than the ones FairDM provides.

## Steps

1. Declare a `LocationField` on the form with `full=False`, which asks for a latitude and a longitude only, and list `location` in the form's fields.

   ```python
   from django import forms

   from fairdm.contrib.contributors.models import Organization
   from fairdm.utils.location.forms import LocationField


   class MyOrganizationForm(forms.ModelForm):
       location = LocationField(full=False, label="Coordinates")

       class Meta:
           model = Organization
           fields = ["name", "location"]
   ```

2. Keep the point of the cleaned value. The model field takes a point, and the form field cleans to a `Location`.

   ```python
   class MyOrganizationForm(forms.ModelForm):
       location = LocationField(full=False, label="Coordinates")

       class Meta:
           model = Organization
           fields = ["name", "location"]

       def clean_location(self):
           location = self.cleaned_data["location"]
           return location.point if location is not None else None
   ```

3. To place an organization from code instead, assign a point.

   ```python
   from django.contrib.gis.geos import Point

   organization.location = Point(8.4115, 49.0094, srid=4326)
   organization.save()
   ```

## The result

The form asks for a latitude and a longitude in signed decimal degrees, WGS 84. Leaving both empty gives the organization no point. One coordinate without the other is refused. The organization's page shows a map with the point marked when it has a point, and no map when it does not.

Two organizations at the same coordinates each hold their own point, so moving one leaves the other where it was. FairDM's own organization forms, the profile editing form and the form that adds an organization, already ask for **Coordinates** in this way. An organization created or updated from ROR takes the coordinates ROR publishes, and one for which ROR gives none keeps the point it had.

See [Location fields](../reference/location-fields.md) for the input's rules, and [How to find records by where they are](find-records-by-where-they-are.md) to search organizations by place.

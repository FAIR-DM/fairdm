# How to add a transform for another format

A transform converts a `Contributor` to and from an external format. FairDM ships transforms for DataCite, Schema.org, CSL-JSON, ORCID and ROR. Add one of your own when your portal exchanges people and organizations with a system that uses another format.

## Steps

1. Subclass `BaseTransform` and write `export`. It takes a contributor and returns a `dict` in your format. The example below uses a staff directory that lists a title and a list of websites.

   ```python
   # myportal/transforms.py
   from fairdm.contrib.contributors.models import Contributor, Organization, Person
   from fairdm.contrib.contributors.utils.transforms import BaseTransform


   class DirectoryTransform(BaseTransform):
       """Convert a contributor to and from the entries of a staff directory."""

       def export(self, contributor: Contributor) -> dict:
           return {
               "kind": "organization" if contributor.is_organization else "person",
               "title": contributor.name,
               "websites": list(contributor.links or []),
           }
   ```

2. Write `import_data` in the same class. It takes the external data, an optional `instance` to update and a `save` flag. It returns the contributor, saved only when `save` is true. A person made here gets an unusable password, because the import gives them no account.

   ```python
       def import_data(
           self, data: dict, instance: Contributor | None = None, save: bool = True
       ) -> Contributor:
           if instance is None:
               if data.get("kind") == "organization":
                   instance = Organization()
               else:
                   instance = Person()
                   instance.set_unusable_password()
           instance.name = data["title"]
           instance.links = self.dictget(data, ["websites"], [])
           if save:
               instance.save()
           return instance
   ```

   `self.dictget(data, path, default)` reads a nested value by a list of keys and indexes, and gives `default` when the path does not exist.

3. Override `validate` when you want to check data before importing it. The base method only checks that the data is a `dict`.

   ```python
       def validate(self, data: dict) -> bool:
           return super().validate(data) and "title" in data
   ```

4. If the format carries identifiers, record them after the contributor is saved. A value is unique across every identifier in the portal, and a contributor holds one identifier of each type.

   ```python
   from fairdm.contrib.contributors.models import ContributorIdentifier

   ContributorIdentifier.objects.update_or_create(
       type="ORCID",
       value=orcid,
       defaults={"related": person},
   )
   ```

5. Call the transform from your own code. FairDM does not wire a custom transform into any page or command.

   ```python
   from myportal.transforms import DirectoryTransform

   transform = DirectoryTransform()
   entry = transform.export(person)
   person = transform.import_data(
       {"kind": "person", "title": "Ada Lovelace", "websites": ["https://example.org"]}
   )
   ```

6. Test the round trip.

   ```python
   import pytest

   from myportal.transforms import DirectoryTransform


   @pytest.mark.django_db
   def test_a_person_survives_the_round_trip():
       data = {"kind": "person", "title": "Ada Lovelace", "websites": ["https://example.org"]}
       person = DirectoryTransform().import_data(data)
       assert DirectoryTransform().export(person) == data
   ```

   Run it with `uv run pytest`.

## The result

`DirectoryTransform().export(contributor)` returns your format for a person or an organization, and `import_data` makes or updates a contributor from it. The built-in transforms and their helper functions are listed in [Contributor models](../reference/contributor-models.md#transforms).

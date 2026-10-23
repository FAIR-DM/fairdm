# How to create a ghost person

A ghost person is a profile with a name and no email address, made so that data can be credited to someone who has no account. You make one in a script or a shell when you attribute imported data to people you cannot invite yet.

## Steps

1. Create the person with the manager method.

   ```python
   from fairdm.contrib.contributors.models import Person

   person = Person.objects.create_unclaimed(first_name="Jane", last_name="Doe")
   ```

   The display name is built from the two names. Pass `name="..."` to set it yourself. Any other `Person` field can follow as a keyword argument.

2. Optional. Link the person to an organization.

   ```python
   from fairdm.contrib.contributors.models import Affiliation, Organization

   university = Organization.objects.get(name="Example University")
   Affiliation.objects.create(
       person=person,
       organization=university,
       type=Affiliation.MembershipType.MEMBER,
       start_date="2020",
       is_primary=True,
   )
   ```

3. Optional. Credit the person on a record.

   ```python
   from fairdm.contrib.contributors.models import Contribution

   Contribution.add_to(person, dataset, roles=["DataCollector"])
   ```

   `dataset` is a project, dataset, sample or measurement you already hold. `roles` are names from the roles vocabulary.

## The result

The person is active and unclaimed, has no email address and has an unusable password, so nobody can sign in to the profile. Its account state is **Ghost**. The profile still appears on the records it is credited on.

To list the ghosts in a portal, or to find those with no credits, use the state filter.

```python
Person.objects.ghost()
Person.objects.ghost().filter(contributions__isnull=True, affiliations__isnull=True)
```

A ghost becomes a claimed account when its owner claims the profile, as described in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md). To give a ghost an email address so that it is **Invited**, edit the person in the administration interface. See [People](../../administrators/reference/people.md).

The manager method and the fields are in [Contributor models](../reference/contributor-models.md). To create a person from an ORCID record in bulk, see [How to import people from a list of ORCID iDs](import-people-from-orcid.md).

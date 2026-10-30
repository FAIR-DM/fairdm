# How to credit a person on a record

A credit lists a person on a project, dataset, sample or measurement, with the roles they had and what they may do on the record. Make one from your own code when a page, an import or a script of yours needs to name the people behind a record.

## Before you start

- The person exists as a `Person`. To make one for attribution alone, see [How to create a ghost person](create-a-ghost-person.md).
- The contributor roles vocabulary is loaded into the database. Run `uv run python manage.py sync_vocabularies` on a fresh database.

## Steps

1. Credit the person with `Crediting`. It is the one place a record's contributors change, and it applies the rules that keep a record manageable.

   ```python
   from fairdm.contrib.contributors.services.crediting import Crediting

   crediting = Crediting(dataset)
   contribution = crediting.add(person)
   ```

   The person is listed last among the people, at the view level, and credited from no organization. If the person is already listed, `add` raises a `duplicate` refusal. Change the existing credit with `update` instead.

2. To credit the person from an organization, pass it. The organization is listed on the record too, if it is not already.

   ```python
   contribution = crediting.add(person, organization=institute)
   ```

3. Give the person roles and, if they should do more than open the record, a level. `update` replaces the roles, so pass every role the person should hold. The roles are concepts, and `offered_roles()` returns the ones the record's type offers.

   ```python
   from fairdm.contrib.contributors.choices import ContributionLevel

   offered = crediting.offered_roles()
   creator = [role for role in offered if role.name == "Creator"]
   crediting.update(contribution, roles=creator, level=ContributionLevel.EDIT)
   ```

   Leave `level` out and it stays as it is. A role carries no rights.

4. Catch the refusals. Each is a `ValidationError` with a code, and nothing is saved when one is raised.

   ```python
   from django.core.exceptions import ValidationError

   try:
       crediting.update(contribution, roles=creator, level=ContributionLevel.VIEW)
   except ValidationError as error:
       codes = [refusal.code for refusal in error.error_list]
   ```

   The codes are listed in [Crediting](../reference/crediting.md#refusal-codes). Show the user the message, or attach it to a form field.

5. If your page lets the user choose the organization, use `AffiliationChoice`. It offers the person's own affiliations, another organization by name, or none. Call `organization()` inside the transaction that saves the credit, so that an organization made for a save that is then refused is not kept.

   ```python
   from django.db import transaction

   from fairdm.contrib.contributors.plugins.shared import AffiliationChoice

   choice = AffiliationChoice(request.POST, person=person)
   if choice.is_valid():
       with transaction.atomic():
           organization = choice.organization()
           Crediting(dataset).add(person, organization=organization)
   ```

6. Check the credit. Read the people on the record in the order the team set, and the roles each holds.

   ```python
   from fairdm.contrib.contributors.models import Contribution

   Contribution.objects.for_entity(dataset).people()
   Contribution.objects.for_entity(dataset).by_role("Creator")
   person.has_contribution_to(dataset)
   ```

## A credit without the rules

A script that only needs to record a credit and its roles can call `person.add_to(dataset, roles=["Creator"])` instead. It adds the roles to a credit already there and starts a new person at the view level. It does not check for a superuser, for the last manager, or for a role that the record's type does not offer.

## The result

The person appears on the record's **Contributors** tab with the roles and level you set. Crediting the same person again adds roles and does not make a second credit. To list the credits of one contributor, see `get_credit_counts()` and `get_visible_contributions()` in [Contributor models](../reference/contributor-models.md). The levels are in [Contribution levels and record access](../reference/contribution-levels-and-record-access.md).

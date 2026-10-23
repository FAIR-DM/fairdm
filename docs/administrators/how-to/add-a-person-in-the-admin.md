# How to add a person in the administration interface

Adding a person creates a profile that can be credited on records, and gives it an email address so its owner can claim it later. You do this for someone who has not signed up yet but whom you know by email address.

## Before you start

Your account needs the permission to add people, `contributors.add_person`. The four shipped portal roles do not hold it, so by default only a superuser sees the **Add user** button.

To add a person who has no email address, see [How to create a ghost person](../../developers/how-to/create-a-ghost-person.md). To add a person from ORCID in bulk, see [How to import people from a list of ORCID iDs](../../developers/how-to/import-people-from-orcid.md).

## Steps

1. In the administration interface, open **Community** and select **Users**. The administration interface lists people under this name.

2. Select **Add user** at the top right.

3. Enter the **First name**, the **Last name** and the **Email address**. FairDM builds the display name from the two names when you save.

4. Type a password in both password fields.

5. Select **Save**. The administration interface opens the person's change form.

6. Optional. Add an ORCID iD on the change form. In the **Identifiers** section, select **Add another Identifier**, choose the type **ORCID**, enter the iD without its address (`0000-0002-1825-0097`) in **Identifier** and select **Save**.

## The result

The person exists and appears in the **Users** list. Their account state is **Invited**, because the profile has an email address and has not been claimed. The profile is active, so the person can claim it. See [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).

The person is not listed on any record yet. A manager credits them from a record's **Contributors** tab. See [How to add a person or organization](../../users/contributors/add-a-person-or-organization.md).

Saving an ORCID identifier queues a background sync with ORCID. The sync fills in the stored ORCID record and needs a worker. If **Last synced** stays empty, see [How to fix an ORCID or ROR sync that does not update](fix-an-orcid-or-ror-sync-that-does-not-update.md).

The form's fields are listed in [People](../reference/people.md).

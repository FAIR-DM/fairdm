# How to correct a profile that nobody has claimed

Correcting a profile fixes the name, photo, biography, links or languages of a person who cannot yet look after their own profile. You do this for a profile that an import filled in wrongly, or for an account that has been deactivated.

## Before you start

You must hold the Community Manager role. The portal offers **Edit profile** only while nobody can sign in to the profile and keep it. That is true when:

- the account is inactive, or
- the profile is unclaimed and its owner has never signed in, whether or not an invitation has been sent.

A profile with an active account that has been claimed or used belongs to its owner, and you are not offered the action. That includes an account made with `createsuperuser`. Who may edit which profile is set out in [Portal roles](../reference/portal-roles.md).

## Steps

1. Open the person's page in the portal. You can reach it from the **People** list, or from a record the person is credited on.

2. Select **Edit profile** in the page header.

3. Change the fields. The page offers the same fields the person would get. They are listed in [Edit profile](../../users/account/edit-profile.md).

4. Select **Save**.

## The result

The profile shows the corrected values and the portal returns to the person's page with the message "Your changes were saved."

Saving does not claim the profile, activate the account or mark the edit as yours. If the person claims the profile, or the account is reactivated, while the page is open, the save is refused and nothing is stored.

A background sync with ORCID fills a blank name and nothing else, so it does not undo your correction. A manual sync that rewrites the whole profile does. See [How to sync a profile from ORCID or ROR without Celery](../../developers/how-to/sync-a-profile-from-orcid-or-ror-without-celery.md).

The email address and the account fields are not on this page. A superuser, or a person who can change people, edits them in the administration interface. See [People](../reference/people.md).

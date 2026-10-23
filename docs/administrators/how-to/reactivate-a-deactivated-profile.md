# How to reactivate a deactivated profile

Reactivating a profile lets its owner sign in and claim it again, because a deactivated profile is refused by every claiming route. You do this when a profile was deactivated by mistake, or when its owner returns.

## Before you start

You must be able to change people. The Portal Administrator and Community Manager roles can, and so can a superuser.

## Steps

1. In the administration interface, open **Community** and select **Users**.

2. Find the person. Choose **No** in the active filter on the right, or search by name or email.

3. Open the person.

4. In the **Account** section, tick **Active**.

5. Select **Save**.

## The result

The profile leaves the **Inactive** account state and returns to the state its other fields give it. A claimed profile is **Claimed**, an unclaimed one with an email address is **Invited**, and an unclaimed one with none is a **Ghost**. The **Account state** column of the list shows the outcome.

Reactivating does not claim the profile. The person still claims it by one of the usual routes, described in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md). Until then a Community Manager can still correct the profile, as described in [How to correct a profile that nobody has claimed](correct-an-unclaimed-profile.md).

Signing in with ORCID never reactivates a deactivated profile by itself. A failed claim against a deactivated profile is recorded in the audit log, and its reason reads "Person is banned (is_active=False)." See [Claiming audit logs](../reference/claiming-audit-log.md).

The fields of the screen are listed in [People](../reference/people.md).

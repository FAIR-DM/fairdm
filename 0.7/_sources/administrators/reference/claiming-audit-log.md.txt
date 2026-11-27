# Claiming audit logs

The claiming audit log records every attempt to claim a profile, and every merge of two people. This page describes the log's screen in the administration interface as FairDM configures it, and the values its columns hold. It does not explain what each claiming route does, which is in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).

You reach the screen from the administration index. Open **Community** and select **Claiming audit logs**.

## Who can open it

A person needs the permission to view claiming audit logs, `contributors.view_claimingauditlog`. None of the four shipped portal roles holds it, so by default only a superuser opens the screen.

The log is read-only. Nobody can add, change or delete an entry, and a stored entry cannot be updated by any code. The screen offers no page for a single entry, so every fact it holds is in the list.

## The list

The list is ordered with the newest entry first.

### Columns

| Column | Shows |
|---|---|
| Timestamp | When the event happened. |
| Method | The route used. See [Methods](#methods). |
| Source person | The profile that was being claimed, or the record merged away. Empty when no profile was identified, and also after a merge, because that record no longer exists. |
| Target person | The profile that resulted. Empty when the attempt failed before a profile was linked. |
| Initiated by | The person who used a claim link. It is empty for every other method. |
| Success | A tick for a successful event and a cross for a failed one. |

The failure reason, the requester's address and the event's details are stored with each entry. The screen does not show them.

### Search

The search box matches against the name of the source person, the target person and the person who initiated the event.

### Filters

| Filter | Options |
|---|---|
| By method | One option for each method. |
| By success | **Yes** or **No**. |

A date navigation above the list narrows the entries by year, month and day.

### Actions

The screen offers no action, because the log cannot be changed.

### When the list is empty

With no entry the list has no rows. A portal where nobody has claimed a profile or merged two people has an empty log.

## Methods

| Value | Label | Written when |
|---|---|---|
| `orcid` | ORCID Social Login | A person signs in with an ORCID iD that matches an unclaimed profile. |
| `email` | Email Verification | The email address of an unclaimed profile is confirmed, while email verification is mandatory. |
| `token` | Claim Token Link | A person follows a signed claim token. |
| `admin_merge` | Admin-Initiated Merge | Two people are merged. A merge is recorded only when it succeeds. |
| `admin_manual` | Admin Manual Activation | Reserved. No code writes it. |

## Failure reasons

A failed entry holds one of these reasons.

| Reason | Cause |
|---|---|
| Person is already claimed. | The profile was claimed before the attempt arrived. |
| Person is banned (is_active=False). | The profile is deactivated. A deactivated profile can be claimed by no route. |
| Claim token has expired. | The token is older than `CLAIM_TOKEN_MAX_AGE`. See [Settings](../../developers/reference/settings.md). |
| Claim token is invalid or has been tampered with. | The token's signature does not verify. |
| No Person found for this claim token. | The token names a person who no longer exists. |
| This profile has already been claimed. | The token names a profile that was claimed before the token was used. |

The stored text of the second reason uses the word "banned". The profile is in the **Inactive** account state.

## What you can do here

- Reactivate a profile that failed with the second reason. See [How to reactivate a deactivated profile](../how-to/reactivate-a-deactivated-profile.md).
- Check that a merge happened. See [How to merge two person records](../how-to/merge-two-person-records.md).

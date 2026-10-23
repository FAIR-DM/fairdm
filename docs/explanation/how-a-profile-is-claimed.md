# How a profile is claimed

This page explains how a person takes over a profile that was created for them before they had an account, why FairDM offers the routes it does, and what each route changes. It covers the routes a person can use in a portal today. It does not cover how to run a merge or correct a profile, which are tasks for administrators, or the account states themselves, which are in [How contributor accounts and credits work](how-contributor-accounts-and-credits-work.md).

## Why profiles are claimed

A portal is often filled before its users arrive. Datasets are imported, and the people who collected them are credited from publications, spreadsheets or a registry. Those credits need a person to attach to, so the portal creates a profile for each one. The profile has a name, may have an ORCID iD or an email address, and has no account behind it. It is **unclaimed**.

When the real person turns up, there are two ways it could go wrong. They might register a second, separate account, leaving their past work credited to a profile they cannot reach. Or someone else might take over the profile. Claiming is the rule that joins the two safely. The person proves they are the profile's owner, and the existing profile becomes their account. Their past credits are already on it, so their history is intact and they have one identity instead of two.

## What claiming changes

A successful claim marks the profile claimed and active, so the person can sign in to it. It changes nothing else about the profile's credits, affiliations or identifiers. Whichever route is used, the attempt is written to an audit log. The log records the method used, the profile concerned, whether it succeeded and, for a failure, the reason. Entries are never changed or deleted.

A profile that has been deactivated cannot be claimed by any route. The attempt fails and is logged, and the profile stays as it is. An administrator must reactivate it first. A profile that is already claimed also refuses a second claim.

## The routes

### Signing in with ORCID

If an unclaimed profile holds the ORCID iD that you sign in with, the portal links the two. The profile becomes your account, and the ORCID login is connected to it.

An ORCID iD is proof only for a profile that is still unclaimed. The identifier on a claimed profile is never treated as a credential, because an identifier can also be written by an administrator or an import, and it would not prove who is signing in. Someone whose ORCID iD matches a claimed profile is not signed in to it. They go through the ordinary sign-up flow, like anyone with no matching record.

### Confirming an email address

If an unclaimed profile holds an email address, and you register with that address and confirm it, the portal claims the profile when the confirmation is recorded.

This route works only while email verification is mandatory, which is the default. If verification is set to any other value, the route does nothing, because an unconfirmed address proves nothing about who owns it.

### Merging into an existing account

Sometimes a person has already registered by the time anyone notices the imported profile, or the same researcher appears twice in the portal. An administrator who holds the right to change people merges the two records. They choose the record to discard and the one to keep. The kept record is marked claimed and active, and the discarded record is deleted.

A merge moves everything the discarded record held onto the kept one:

- Its credits on records. Where both people are credited on the same record, one credit remains, at the higher of the two levels.
- Its external identifiers, unless the kept person already holds one of that type.
- Its affiliations, unless the kept person already has an affiliation with that organization.
- Its confirmed email addresses and its linked social accounts.
- Its permissions stored on objects other than projects, datasets, samples and measurements, which gain their rights from credits instead.
- Its profile text and image, when the kept profile has none.

Any active sessions of the discarded person are ended. A merge cannot be undone, which is why the choice of which record to keep matters.

Merging belongs to administrators because it destroys an identity. Rather than limiting it to superusers, FairDM ties it to the permission to change people, which the Portal Administrator and Community Manager roles hold. See [ADR 0021](../adr/0021-claims-and-merges-belong-to-a-named-role.md).

To help an administrator find records that need merging, the administration page of an unclaimed person lists other people with a similar name. The list is only a pointer. Nothing is claimed or merged because two names look alike, since two people can share a name.

## Why a claim needs proof

Each route requires something only the real owner holds: the ORCID login, access to the email inbox, or a decision by an administrator who knows both records. None of them lets a visitor claim a profile on a guess. A profile found by name alone is never claimed, which is also why the portal matches people by identifier and not by name when it credits them.

A deactivated profile refuses every route for a reason of the same kind. Deactivation is a decision about the account, and claiming would otherwise undo it as a side effect of signing in.

## Related pages

- [Profile claiming](../developers/reference/profile-claiming.md) lists the functions and exceptions.
- [Claiming audit logs](../administrators/reference/claiming-audit-log.md) describes the log an administrator reads.
- [How to merge two person records](../administrators/how-to/merge-two-person-records.md) walks through a merge.
- [How to claim your profile with ORCID](../users/account/claim-your-profile-with-orcid.md) and [How to claim your profile by email](../users/account/claim-your-profile-by-email.md) are the user guides for the first two routes.
- [Settings](../developers/reference/settings.md) lists the settings that affect claiming.

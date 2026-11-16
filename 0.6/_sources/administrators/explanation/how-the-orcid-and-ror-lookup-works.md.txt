# How the ORCID and ROR lookup works

This page explains how a portal looks a person up in ORCID or an organization up in ROR when a manager adds a contributor to a record, what the portal needs for that, and what happens when a registry cannot be reached. It does not explain how a manager uses the lookup, which is in the user guide under [How to add a person or organization](../../users/contributors/add-a-person-or-organization.md), or how a stored profile is synced afterwards, which is in [How to fix an ORCID or ROR sync that does not update](../how-to/fix-an-orcid-or-ror-sync-that-does-not-update.md).

## The portal's server asks, not the visitor's browser

The lookup runs on the server that runs the portal. It makes outbound HTTPS requests to two public addresses.

| Registry | Address |
|---|---|
| ORCID | `pub.orcid.org` |
| ROR | `api.ror.org` |

The person using the page never reaches a registry from their own browser. A portal that sits behind a firewall or proxy blocking outbound traffic must allow these two hosts, and no others are involved.

Both registries are public. The lookup needs no account, no key and no setting, and it does not use the ORCID sign-in credentials.

## A slow or failing registry is treated as unavailable

Each request is allowed five seconds. A request that fails, times out or is answered with anything other than success counts as the registry being unavailable. So does an answer in a form the portal cannot read. This includes a refusal because the registry received too many requests from your server's address.

The page waits at most five seconds for a registry, then reports it unavailable and carries on. The five seconds is a fixed value with no setting.

## Answers are kept for five minutes

The portal keeps what a registry answers for five minutes in its default cache. Repeating a search, or opening a record that was just searched for, sends no second request in that time. A change made at the registry can therefore take up to five minutes to show in the lookup.

A record the registry does not hold is an answer and is kept. A failure is never kept, so the next search asks again. The period has no setting.

The registries limit how often one address may ask, and every manager of the portal asks from the server's single address. Keeping answers means repeated searches do not use up that allowance.

## Ten matches, and a note when there are more

Each search returns at most ten matches, and the page says when the registry holds more. A manager who sees that note narrows the search by typing more of the name, or pastes the iD. An iD or an address of one finds exactly one record.

Only people who have a public name appear. Only organizations ROR lists as active appear.

## When a registry cannot be reached

The tab for that registry says that searching it is unavailable and offers nothing to choose. The page still answers, and the other two ways of adding a contributor keep working. A manager can search the portal's own people or organizations, or enter a contributor by hand. A team can always credit someone while a registry is down. Nothing needs to be switched off or restarted, and the lookup works again as soon as the registry does.

If managers report that the lookup is always unavailable, check from the portal's server that the two hosts above can be reached over HTTPS.

## What adding a match makes

Adding a match makes a profile from the registry's record as the portal fetched it, or as it fetched it within the last five minutes.

- A person made this way has the name and the ORCID iD, is active, and has no email address, an unusable password and no account. That is a ghost. Anyone who later signs in with that ORCID iD claims the profile. See [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).
- An organization made this way has its name and its ROR ID.
- A person entered by hand is made the same way, without the identifier. The page does not ask for an address, so such a person cannot be reached by email until they claim the profile.

The identifier is saved on the profile, and saving it queues the usual background sync with the registry. That sync fills in the rest of the profile and needs a worker. Without a worker the profile keeps the name and the identifier. The account states are described in [How contributor accounts and credits work](../../explanation/how-contributor-accounts-and-credits-work.md).

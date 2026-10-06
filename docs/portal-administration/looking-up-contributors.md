# Looking up contributors in ORCID and ROR

The pages for adding a person or an organization to a record can look the contributor up in a
registry: ORCID for people and ROR for organizations. This page says what your portal needs for
that and what happens when it cannot reach them. How a manager uses the lookup is described in the
user guide page [Crediting a record](../user-guide/crediting-a-record.md).

## What the portal needs

The lookup needs the server that runs the portal to make outbound HTTPS requests to two public
addresses:

| Registry | Address |
|---|---|
| ORCID | `pub.orcid.org` |
| ROR | `api.ror.org` |

Both are public APIs. The lookup needs no account, no API key and no setting, and it does not use
the ORCID sign-in credentials. A firewall or proxy that blocks outbound traffic must allow these
two hosts. The portal sends no other request for the lookup, and the person looking someone up
never reaches the registry from their own browser.

Each request is allowed five seconds. A request that fails, times out, or is answered with anything
but a success counts as the registry being unavailable.

The lookup is limited to ten matches for each search, and the page says when a registry holds more.
The registries limit how often one address may ask, so a portal that many managers use at once
may see a search refused for a moment. The page treats that like any other unavailable registry.

## When a registry cannot be reached

The tab for that registry says that searching it is unavailable and offers nothing to choose. The
page still answers, and the other two ways of adding a contributor keep working: searching the
portal, and entering a contributor by hand. A team can always credit someone while a registry is
down. Nothing needs to be switched off or restarted, and the lookup works again as soon as the
registry does.

If managers report that the lookup is always unavailable, check from the portal's server that the
two hosts above can be reached over HTTPS.

## What is made

Adding a match from a registry makes a profile with the name and the identifier from the record
the portal fetches at that moment. A person made this way is active, has no email address, an
unusable password and no account, which the account states in
[Managing Contributors](managing_contributors.md) call a ghost. Anyone who then signs in with that
ORCID iD claims the profile.

The identifier is saved on the profile, and saving it queues the usual background sync with the
registry. That sync fills in the rest of the profile and needs the task workers described in
[ORCID/ROR sync troubleshooting](managing_contributors.md). Without workers the profile keeps the
name and the identifier.

A person entered by hand with an email address is made in the invited state: active, not claimed,
with an email address and no usable password. The address is not shown on the portal and nothing is
sent to it by the page that adds the person. Such a person cannot sign in with a password. The
portal's password reset page treats the address like that of any other profile, so it mails the
address when someone asks for a reset with it.

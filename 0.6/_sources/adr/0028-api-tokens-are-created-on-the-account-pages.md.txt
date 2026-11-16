# ADR 0028 — API tokens are created on the account pages, never exchanged for a password

**Status:** accepted

## Decision

A person gets an API token on their account pages, after signing in the usual way. The pages are
django-mvp-accounts' list, create and revoke pages for tokens kept by django-rest-knox, routed at
`account/tokens/`. The API accepts a token in `Authorization: Token <token>` and the portal's own
sign-in session, and nothing else.

The API has no address that exchanges a password for a token, none that signs out, and none that
resets or changes a password or edits an account. A test walks every route under the `api`
namespace and fails if a name or path contains `login`, `logout`, `password`, `registration` or
`auth/user`.

Each token has an expiry the person picks, from 7 days to never. A person holds at most ten
working tokens (`REST_KNOX["TOKEN_LIMIT_PER_USER"]`), and using a token does not extend it
(`AUTO_REFRESH` is off). A portal can limit who may hold tokens with
`MVP_ACCOUNTS_API_TOKEN_ACCESS`.

Any website may call the API (`CORS_ALLOW_ALL_ORIGINS` is on for `/api/` and for nothing else).
Credentials are not allowed, so a sign-in cookie is never accepted from another origin, and a page
on another site writes only with a token. A session write from the portal's own pages carries
Django's CSRF token, and one without it is refused.

## Why

A login endpoint that returns a token for an email address and a password undoes two-factor
sign-in for everyone who turned it on, because it asks for nothing else. Signing in on the portal
asks for the second factor, and creating a token there inherits that.

One permanent token per person cannot be revoked without cutting off every script that person
runs. Tokens from the account pages are several per person, expire, are stored as a digest and are
revoked one at a time.

The pages already exist and are kept up to date by the package that provides the portal's account
pages. Building a second set would duplicate them.

Allowing every origin is safe here because the API accepts no ambient credentials from another
site: a token has to be sent deliberately in a header, and the sign-in cookie is withheld.

## Consequences

- A script cannot sign in with a password. It uses a token made by hand, and a token lost is
  revoked and replaced.
- Tokens issued by the earlier login endpoint do not exist in the new store and stop working. No
  release carried them.
- Restricting who may hold tokens hides the pages. It does not delete a token a person already
  holds, and is not asked when a token is used.
- A request is judged by the levels its holder has when it arrives, so removing a level takes
  effect on the next request without revoking the token.
- A portal that wants to answer only some websites sets `CORS_ALLOW_ALL_ORIGINS = False` and lists
  them in `CORS_ALLOWED_ORIGINS`.

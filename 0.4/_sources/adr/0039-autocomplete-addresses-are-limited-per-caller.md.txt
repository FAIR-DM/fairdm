# ADR 0039 — Autocomplete addresses are limited per caller

**Status:** accepted

## Decision

Every autocomplete address limits each caller over a minute and over a day, with four throttles
that reuse the API's own classes under their own scopes: `autocomplete_anon_burst`,
`autocomplete_anon_day`, `autocomplete_user_burst` and `autocomplete_user_day`. A signed-in caller
is counted by account and anyone else by network address. A caller over a limit is answered 429
with `Retry-After` before anything is searched. A portal sets the rates in
`REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`, and a scope it leaves out uses the default on its
throttle class.

The view fixes everything else a request could use to make a search costly: 20 results a page,
no page past the 25th, a search cut to 100 characters, and only the filters and ordering the view
allows.

## Why

The addresses serve public pages, so anyone can call them. The API already limits callers this way
and a portal already knows where to set its rates. The search fields get scopes of their own
because typing comes in bursts the API's rates were not set for, and a search box should not use
up anyone's API allowance.

## Revisit if

A portal needs limits shared across several servers that the cache it configures cannot give.

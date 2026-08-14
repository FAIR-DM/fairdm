# ADR 0003 — The baseline ships no working default for a security-critical value

**Status:** accepted

## Decision

FairDM ships no usable default for any value whose absence would weaken a deployment: the secret key,
the site domain and the allowed-hosts list it composes, and any administrative password. These
variables resolve to an explicitly unusable sentinel — an empty string — until the deployment sets
them, and the production-critical checks in ADR 0002 are what refuse the boot.

**The read is never the thing that raises.** A settings module that raises when a variable is unset
would kill the process during the baseline layer, which is layer 1, before the development override
at layer 2 could supply a value. That takes development startup and the whole test suite with it.
Development values live in `fairdm/conf/development.py`, clearly marked as such, where they cannot
reach a production deployment.

## Why

FairDM previously declared its secret key with a literal default in `fairdm/conf/environment.py` —
a real, high-entropy key published in the package source on GitHub and PyPI. A production portal that
never set `DJANGO_SECRET_KEY` started successfully on a key anyone could read, so its session cookies
and every signed value could be forged. `DJANGO_SITE_DOMAIN` defaulted to `localhost:8000`, and so
composed an allowed-hosts list that was wrong everywhere it mattered.

Django does detect this: `security.W009` catches the `django-insecure-` prefix. But it reports a
**Warning**, and only under `--deploy`, which nothing triggered automatically. A default that is safe
only because a check elsewhere might catch it is safe only while that check runs, and ADR 0002
documents the seven months in which it did not. Removing the value makes the failure structural
rather than conditional.

The sentinel rather than a raising read is the load-bearing detail. It is tempting to let
`django-environ` raise on a missing variable and call that fail-fast, but the layering makes that
wrong: the baseline cannot know what a later layer is about to supply. Failing at the read would also
falsify the requirement that development starts quietly with these variables unset.

## Revisit if

A value now on this list stops being security-critical, or a new one joins it. The list is the
decision; the mechanism generalises to whatever is on it.

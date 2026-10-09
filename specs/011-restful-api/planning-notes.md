# Planning notes: 011-restful-api

Suggestions from the maintainer, in his words, given on 2026-10-08 when he approved the audit's
reading. Research answers each one by name before the plan is written.

## Tokens through django-mvp-accounts

"Make sure to update django-mvp-accounts as it now supports token generation via drf rest knox
which will significantly help things."

## orjson as the default renderer

"Investigate orjson as the default json renderer which is far faster than the standard renderer."

## Limits, access and paging for a small server

"Make sensible decisions on rate limiting, access, pagination, etc. That will benefit users while
being maintainable for a small server setup."

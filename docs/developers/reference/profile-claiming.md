# Profile claiming

This page lists the functions, exceptions, adapters and models that take an unclaimed profile over for a person: the claiming services, the merge service, the duplicate finder, `ClaimingError`, `ClaimMethod` and `ClaimingAuditLog`. It does not explain why claiming works as it does, which is in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md), and it does not list settings, which are in [Settings](settings.md). To change the flow, see [How to extend the profile-claiming flow](../how-to/extend-the-profile-claiming-flow.md).

| Module | Holds |
|---|---|
| `fairdm.contrib.contributors.services.claiming` | `claim_via_orcid`, `claim_via_email` |
| `fairdm.contrib.contributors.services.merge` | `merge_persons` |
| `fairdm.contrib.contributors.services.matching` | `find_duplicate_candidates` |
| `fairdm.contrib.contributors.utils.audit` | `log_claiming_event` |
| `fairdm.contrib.contributors.exceptions` | `ClaimingError` |
| `fairdm.contrib.contributors.adapters` | `AccountAdapter`, `SocialAccountAdapter`, `is_provider` |
| `fairdm.contrib.contributors.signals` | `handle_email_confirmed` |
| `fairdm.contrib.contributors.models` | `ClaimMethod`, `ClaimingAuditLog` |

## Claiming services

Both services mark the person claimed and active, save only `is_claimed` and `is_active`, and write the outcome to the audit log, failures included.

| Function | Returns | What it does |
|---|---|---|
| `claim_via_orcid(person, sociallogin)` | `Person` | Activates an unclaimed person through an ORCID sign-in and connects the social login to them. Raises `ClaimingError` when the person is already claimed or is deactivated (`is_active` false) |
| `claim_via_email(person)` | `Person` or `None` | Activates an unclaimed person after their email address is confirmed. Does nothing and returns `None` unless `ACCOUNT_EMAIL_VERIFICATION` is `"mandatory"`, so a signal handler can call it without checking. Raises `ClaimingError` when the person is already claimed or is deactivated |

The adapter and the signal handler call these. A portal that keeps the shipped adapter and handler does not call them itself.

## Adapters and handlers

`SocialAccountAdapter` is the value of `SOCIALACCOUNT_ADAPTER`, and `AccountAdapter` is the value of `ACCOUNT_ADAPTER`.

| Member | What it does |
|---|---|
| `SocialAccountAdapter.get_db_user_by_orcid(orcid_id)` | Returns the contributor that holds the ORCID iD in a `ContributorIdentifier`, or `None` |
| `SocialAccountAdapter.pre_social_login(request, sociallogin)` | For an ORCID sign-in, finds the profile that holds the iD. When that profile is unclaimed, it calls `claim_via_orcid` and raises allauth's `ImmediateHttpResponse` with a redirect to the sign-up step. A claimed profile is left to allauth's normal flow, because an identifier row can be written by an administrator or an import and does not prove identity |
| `SocialAccountAdapter.save_user(request, sociallogin, form=None)` | For an ORCID sign-up, adopts the unclaimed profile that holds the iD. When no profile holds it, creates the user and attaches the iD |
| `SocialAccountAdapter.populate_user(request, sociallogin, data)` | Fills the user from the ORCID record with `ORCIDTransform` |
| `SocialAccountAdapter.is_open_for_signup(request, sociallogin)` | True when the `allow_signup` waffle switch is active and allauth agrees |
| `AccountAdapter.is_open_for_signup(request)` | False when the `allow_signup` switch is off. True when the session holds a verified email address (`account_verified_email`). Otherwise true unless `FAIRDM_INVITATION_ONLY_SIGNUP` is set |
| `handle_email_confirmed(sender, request=None, email_address=None, **kwargs)` | Connected to allauth's `email_confirmed` signal. Does nothing unless `ACCOUNT_EMAIL_VERIFICATION` is `"mandatory"`. Finds the unclaimed person with the confirmed address and calls `claim_via_email`. A failure is logged and not raised |

## Merge service

`merge_persons(person_keep, person_discard)` merges `person_discard` into `person_keep` in one transaction and returns `person_keep`. Any error rolls the whole merge back. It raises `ClaimingError` when both arguments are the same person.

What moves from the discarded person to the kept person:

| Data | Rule |
|---|---|
| Contributions | A record both people are credited on keeps the kept person's credit, with its organization as it is, at the higher of the two levels. The discarded person's credit there is deleted. A credit only the discarded person held moves, with its level |
| `ContributorIdentifier` rows | Moved unless the value exists elsewhere or the kept person already holds an identifier of that type. Those are deleted |
| `Affiliation` rows | Moved unless the kept person already has an affiliation with that organization. Those are deleted |
| allauth `EmailAddress` rows | Moved unless the kept person already has the address (ignoring case). Those are deleted |
| allauth `SocialAccount` rows | All moved |
| django-guardian `UserObjectPermission` rows | Copied for objects that are not projects, datasets, samples or measurements. A stored row grants nothing on those four, so none is copied for them |
| `profile` and `image` | Copied when the kept person's field is empty |

The kept person is marked claimed and active, the sessions of the discarded person are ended, an audit entry with the method `admin_merge` is written, and the discarded person is deleted.

## Duplicate finder

`find_duplicate_candidates(person, threshold=0.85)` returns a `list` of `{"person": Person, "score": float}`, highest score first. The score runs from 0 to 1 and is the `rapidfuzz` `token_sort_ratio` of the two names divided by 100, so reordered names such as "Smith, John" and "John Smith" score alike. Only candidates with a score of at least `threshold` are returned. The person itself is excluded, and a person with an empty name gives an empty list. Nothing is stored. The administration page of an unclaimed person calls it.

## ClaimingError

`ClaimingError` is an `Exception`. The claiming functions raise it for an expected, user-facing failure: a person who is already claimed, a person who is deactivated, or an attempt to merge a person with itself. Its message is safe to show to the user. Unexpected programmer errors are other exceptions.

## ClaimMethod

`ClaimMethod` is a `TextChoices` in `fairdm.contrib.contributors.models`.

| Name | Value | Label | Written by |
|---|---|---|---|
| `ORCID` | `orcid` | ORCID Social Login | `claim_via_orcid` |
| `EMAIL` | `email` | Email Verification | `claim_via_email` |
| `ADMIN_MERGE` | `admin_merge` | Admin-Initiated Merge | `merge_persons` |
| `ADMIN_MANUAL` | `admin_manual` | Admin Manual Activation | Nothing in FairDM. Available to your own code |

## ClaimingAuditLog

`ClaimingAuditLog` is an audit trail of claiming events. `save()` on a row that already exists raises `ValueError`, so entries are created once. Rows are ordered by `timestamp`, newest first.

| Field | Type | Default | What it holds |
|---|---|---|---|
| `timestamp` | `DateTimeField` | Set on creation | When the event happened |
| `method` | `CharField(max_length=20)` | None, required | A `ClaimMethod` value |
| `source_person` | `ForeignKey` to `Person` | `None` | The unclaimed person being claimed. Set to `None` if that person is deleted. Reached as `claim_log_as_source` |
| `target_person` | `ForeignKey` to `Person` | `None` | The resulting claimed person. Reached as `claim_log_as_target` |
| `initiated_by` | `ForeignKey` to `Person` | `None` | The user who started an admin-driven claim. Reached as `claim_log_initiated` |
| `ip_address` | `GenericIPAddressField` | `None` | The requester's address |
| `success` | `BooleanField` | None, required | Whether the claim succeeded |
| `failure_reason` | `CharField(max_length=255)` | `""` | Why the claim failed |
| `details` | `JSONField` | `{}` | Further structured details |

`ClaimingAuditLog.objects` is a `ClaimingAuditLogManager`:

| Method | Returns | What it does |
|---|---|---|
| `for_person(pk)` | Queryset | Events where the person was the source or the target |
| `failures()` | Queryset | Events where `success` is false |
| `by_method(method)` | Queryset | Events with one `ClaimMethod` value |
| `recent(days=30)` | Queryset | Events within the last `days` days |

### log_claiming_event

`log_claiming_event(method, source, target, initiated_by=None, ip_address=None, success=True, failure_reason="", details=None)` creates a `ClaimingAuditLog` row and returns it. `source` and `target` are people or `None`. `details` is a JSON-serialisable `dict`.

```python
from fairdm.contrib.contributors.models import ClaimMethod
from fairdm.contrib.contributors.utils.audit import log_claiming_event

log_claiming_event(
    method=ClaimMethod.ADMIN_MANUAL,
    source=unclaimed_person,
    target=activated_person,
    initiated_by=request.user,
    ip_address=request.META.get("REMOTE_ADDR"),
    success=True,
    details={"note": "Activated by hand."},
)
```

The services do not record an `ip_address`.

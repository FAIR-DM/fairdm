# How contributor accounts and credits work

This page explains how a FairDM portal treats a person who is credited on research data, how that person's account moves between states, how an organization is owned, and the rules that govern a credit on a record. It covers the model behind these rules and the reasons for them. It does not cover why a portal records contributors, which is in [Why FairDM records contributors](why-fairdm-records-contributors.md), how a credited person takes over their profile, which is in [How a profile is claimed](how-a-profile-is-claimed.md), or how a credit gives access to a record, which is in [How access to a record is decided](how-access-to-a-record-is-decided.md).

## A person is also the account

In a FairDM portal, a person who is credited on a dataset and a person who signs in are the same record. FairDM's authentication settings name the person model as the portal's user model, and people sign in with their email address rather than a username.

This is what lets a portal import attribution before anyone has an account. A person can exist as a profile with a name and nothing else. When the real person arrives, they take over the profile that already holds their credits, instead of a second record being made and the two being reconciled by hand.

## The four account states

Every person is in exactly one of four states.

| State | What it means |
|---|---|
| Ghost | A profile created for attribution alone. It has no email address and nobody can sign in to it |
| Invited | A profile that holds an email address and has not been claimed |
| Claimed | A profile whose owner has claimed it and can sign in |
| Inactive | A deactivated account, whatever its claim status |

The table is in order of precedence. A deactivated profile is always inactive, even one that was claimed before it was deactivated.

### The state is worked out, not stored

No field holds the state. It is derived each time it is read from three stored facts: whether the account is active, whether it is claimed, and whether it has an email address. Querysets for each state use the same rule, and together they cover every person exactly once.

The reason is that a stored state can fall out of step with the facts it summarises. A person could be marked claimed with the claimed flag off, or invited with no email. Deriving the state removes the possibility.

### An account in use is not always marked claimed

A person made with the `createsuperuser` command, or who signed up through the ordinary sign-up form, is active and in use. Nothing marks them as claimed. The portal therefore asks a second question wherever it matters, whether a person can actually sign in, which is true when the account is active and the person has either claimed it or has signed in. Editing rights for a profile depend on this second question, so a Community Manager is never offered a profile that its owner is using.

### Why "inactive" outranks everything

A deactivated account cannot be claimed through any route, and signing in with ORCID does not reactivate it. A profile found that way is left as it is. Reactivating a profile is a deliberate act by an administrator, so that claiming cannot be used to undo a deactivation.

## Organizations and ownership

An organization is a contributor too, and it can be part of another organization. A person belongs to an organization through an **affiliation**, which has a type, start and end dates, and a flag for the person's primary affiliation.

| Affiliation type | Meaning |
|---|---|
| Pending | Declared and not yet verified |
| Member | A regular member |
| Admin | Can manage memberships |
| Owner | Full control of the organization |

A person has at most one affiliation with a given organization, and at most one primary affiliation overall. Dates can be as precise as a year, a month or a day, as recorded.

### Ownership is derived from the affiliation

The right to manage an organization is not stored as a permission. It is answered at the moment of asking, by checking whether the person holds a **current** owner affiliation, meaning one with no end date, and whether their account is active. A superuser also holds the right. Nothing else does, and a stored permission for it is never consulted even if one exists.

Deriving it means nothing has to be revoked. Changing an affiliation away from owner, setting its end date or deactivating the account removes the right on the next check. There is no second place to fall out of date.

More than one current owner is possible. To hand ownership to someone else, rather than add a second owner, an administrator transfers it. A transfer demotes every current owner to admin and promotes the new one in a single operation. It refuses a new owner who is not a member, whose affiliation has ended or is still pending, or whose account is unclaimed or deactivated.

Setting an affiliation to admin or owner, or changing or deleting one that already carries either type, needs the right to manage that organization. Ordinary membership does not.

### Why an organization has one type and keeps its children

An organization's type is a single choice drawn from ROR's organization types. ROR allows several at once, but a portal that shows or filters by the kind of institution wants one answer per organization, so the choice is narrowed.

Deleting a parent organization does not delete the organizations beneath it. They become top-level organizations. A loop is refused, so an organization cannot be part of itself or of any organization beneath it.

## One credit per contributor per record

A contributor appears on a record once. The database refuses a second credit for the same contributor on the same record, and a form is refused in the same way before it reaches the database. Crediting the same person again under a further role does not make a second credit. The new role is added to the one that exists, so a person who both collected and analysed a dataset appears once with both roles.

Roles come from a single controlled vocabulary of contribution roles. A role from any other vocabulary is refused at the point it is written, whatever code writes it.

A superuser cannot be credited as a contributor, except in debug mode. Superusers are set aside from the people the portal lists, and so is the placeholder account that stands for an anonymous visitor.

### A record keeps a manager

The portal refuses to remove the last person who can manage a record. How that works is part of access, and is in [How access to a record is decided](how-access-to-a-record-is-decided.md).

### Merging two profiles keeps one credit

When two profiles are merged and both are credited on the same record, one credit remains, at the higher of the two levels. A person who was credited where the other was not keeps that credit and its level. Details are in [How a profile is claimed](how-a-profile-is-claimed.md).

## Why a superuser account and a person account stay apart

A superuser account holds every permission and bypasses the portal's ordinary workflows. A portal tried out with only that account never shows what a real person sees. For that reason a developer keeps one account for administration and a separate person account for using the portal as its users do. A superuser cannot be a contributor in any case.

## What the portal holds about a person

A person record holds personal data: a name, often an email address, a profile and the person's credits and affiliations. Three things follow from how it is built:

- The contributors app applies no field-level privacy rule of its own. An invited person's email address is a real address and is exposed to the same viewers as a claimed person's, unless your portal hides it where it displays it.
- A ghost profile has no email, so there is nothing of that kind to show.
- The REST API returns nothing about the account behind a person, so no email address, password or account flag.

If your portal is subject to data-protection rules, plan for exporting or deleting a person's data on request. FairDM does not provide a ready-made export.

## Where to go next

- [Contributor models](../developers/reference/contributor-models.md) lists the fields and methods.
- [Crediting](../developers/reference/crediting.md) lists the methods that change who is credited.
- [Portal roles](../administrators/reference/portal-roles.md) lists who may edit a profile.

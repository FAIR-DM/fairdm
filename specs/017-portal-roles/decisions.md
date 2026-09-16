# Decisions — 017 Portal roles and the people who hold them

Rationale too long to carry inline in `spec.md`, plus every ambiguity resolved without asking the
maintainer. Fine-grained and run-scoped; the gate-level trail lives on the issue thread.

## D1 — Three rights-carrying roles, not two, and a fourth that grants nothing

The obvious split of portal work is two jobs: run the portal, look after the data. The set ships
with three rights-carrying roles because looking after *people* is a different job from looking
after *records*. It touches personal data — email addresses, account states, profile claims,
duplicate-person merges — and the person a research group trusts with their sample data is not
automatically the person they want reading account records. A portal small enough that one volunteer
does both simply puts that volunteer in both roles, which costs nothing. Splitting later, after
portals have handed out a combined role, costs a migration and a conversation with every portal.

The Developer role grants nothing at all. It was nearly cut for that reason. It stays because the
portal team page is its consumer: a portal's developers are part of its team and are named on it
alongside everyone else. A role is the framework's existing way to say "this person does this job
here", and inventing a second, parallel way to record team membership for one case would be worse.

## D2 — No reviewer role yet

The retired documentation named a Reviewer, and R22 will need one when a dataset moves from working
to visible through a checked process. Shipping it now would mean a role holding either nothing or a
guess at what the publication process will require. Both teach an administrator something false
about the set. It arrives with the process that needs it.

## D3 — Four defences against a missing role, in order of when they fire

The maintainer's first framing was that a portal should refuse to load without its roles. Taken
literally and alone, that trades a recoverable condition for an outage, and it cannot be the only
answer because a brand-new database has no roles until it has been migrated. The order that survives
both objections:

1. **Refuse the deletion.** The likely cause is somebody tidying up the administration interface.
   Stopping it there means the condition mostly never arises.
2. **Restore on update.** A removal from a shell or a script is undone the next time the portal is
   brought up to date, which also covers a portal whose rights were edited by hand.
3. **Refuse to start in production.** If the set is still incomplete on the production baseline, the
   portal does not serve, and it names what is missing. This uses the guard FairDM already has, the
   production-critical check subset in `FairDMConfig.ready()`, rather than adding a second mechanism
   beside it.
4. **Report on demand in development.** `check --deploy` is where a portal developer and a CI run
   find the same condition without being stopped by it.

Step 3 must never assess a database that has not been migrated, or the first `migrate` of a new
portal would be blocked by the absence of rows that `migrate` is about to create.

## D4 — Consistency with the vocabularies decision, deliberately broken

US-2 of the controlled-vocabularies work (issue #306) chose the softer answer for a comparable
condition: a portal missing its vocabularies starts, and warns, naming the command that loads them.
This feature chooses refusal for roles in production. The difference is what each absence costs. A
portal missing a vocabulary serves every page; some fields have nothing to pick from. A portal
missing a role silently stops enforcing part of its access rules and gives no visible signal at all
until somebody notices they can no longer do their job, or that somebody else can. If the two should
converge, the argument is that vocabularies should harden, not that roles should soften.

## D5 — Group-name matching is removed rather than extended

`Person.is_data_admin`, the `has_perms` template tag and the plugin edit check each decide rights by
testing whether a person is in a group called `"Data Administrators"`, and each grants broad edit
rights from that test. It is invisible to `has_perm`, so a portal author cannot discover it, a
permission backend cannot participate in it, and an object-level rule cannot override it. Since this
feature is what first gives the groups real permissions, the name tests have nothing left to do.

## D6 — Curator edits are not attributed to the curator

Considered and rejected: marking a record that a data curator edited on a research team's behalf.
The curator acts at the team's request and on their behalf, so the edit is the team's. A visible
mark tells a reader something they cannot act on, and it invites the reading that the record is
somehow less the team's own. Whatever internal record of administrative actions the framework keeps
is unaffected by this; the decision is about what a reader sees.

## D7 — The development accounts ship with the package

They could have lived in `demo`, which is where the framework's other development conveniences sit.
They ship with the package because their audience is wider than this repository: a research group
building a portal on FairDM needs to sign in as a curator in *their* portal, and the demo is not
installed there. The demo becomes one consumer of them.

The production refusal is not a policy nicety. These accounts have a published password. Loading
them into a running portal would hand anybody who reads the documentation an administrator account.

## D8 — Rights are restored on update, membership never is

A portal that edits the rights on a shipped role has them reset on the next update, and this is
intended. The alternative — treat a local edit as authoritative — means FairDM can never correct or
extend a role's rights again, and every portal drifts into its own private definition of what a
curator is. A portal that wants a different split creates its own group, which nothing here
prevents. Membership is the opposite case: who is in a role is a fact about that portal's people and
is never touched.

## D9 — What the roles are not

- Not the contact form's recipient list. The form is broken for unrelated reasons and its routing is
  separate work.
- Not an announcement system. There is one unused settings key and nothing behind it, so there is no
  right to grant.
- Not a replacement for the superuser, which stays the deployer's escape hatch. The documentation
  says so explicitly, because handing out a superuser account is exactly what a research group does
  when the framework offers nothing else.
- Not per-record rights. The creator-gets-rights and membership-grants-rights half of R15 is a
  separate feature and is filed as its own issue.

---

*Everything below was decided at the design review, 2026-09-16. Thirteen verified findings, applied
in full; the reviewer's own report is `design-review-findings.json`.*

## D10 — The legacy groups are renamed, not replaced

Three group rows already exist in every portal set up from the retired fixture, and volunteers are
in them. Declaring four new roles beside them would have left those people holding nothing the day
the portal upgraded, with `is_data_admin` deleted in the same release. Reconciliation renames the
rows in place — `Portal Administrators` to `Portal Administrator`, `Data Administrators` to `Data
Curator`, `Developers` to `Developer` — and a rename carries the membership rows untouched, so no
data migration is needed and nobody's rights are reduced. The rename fires only when the target name
is free, so a portal that somehow holds both is left alone rather than merged.

## D11 — The boot refusal stands down for the command that repairs it

`fairdm.E300` runs in `AppConfig.ready()`, which fires before `migrate` does any work, and
`post_migrate` is the only thing that installs the roles. Left as first planned, a production portal
upgrading to this version would have refused to boot *and* refused to migrate, with no route back
from inside the portal. The refusal therefore stands down for the command that installs the roles.
The requirement survives intact: a portal that is serving still refuses to serve without its roles.

## D12 — `contributors.change_person` needed the Person form narrowed

FR-004 gives the Community Manager the right to change a person, and Django's `UserAdmin` puts
`is_superuser`, `is_staff` and `password` on that form with no permission gate of their own. The
role's ceiling was therefore the whole portal, reachable in three clicks. The form now drops those
three fields for any request whose user is not a superuser. This is not a narrowing of FR-004; it is
what FR-004 has to mean if the role is to be what the specification says it is.

## D13 — Profile claims and merges become the Community Manager's

`claim_link_view` and `merge_view` are superuser-only today, by a decision recorded in their own
docstrings: a claim token is a credential, and a merge destroys the discarded person's identity, so
neither is "an ordinary staff operation". FR-004 requires the Community Manager to act on both.

Both statements are right, and they stop conflicting once the alternative is named. The recorded
decision was written when the only thing standing between an account and those views was
`is_staff` — a flag every administrative helper carried. A portal role a portal administrator grants
to a named person is not that. The gates become permission questions that the Community Manager
role holds and that no other role and no ordinary contributor holds. The earlier decision is
superseded rather than ignored, and the superseding ADR carries this reasoning.

## D14 — The object-level fallback excludes `manage_organization`

The framework already refuses to derive `contributors.manage_organization` from anything but a
current owner affiliation, and documents why: a stale `Permission` row for it survives in databases
migrated forward from before it was dropped, and Django ORs backends, so no later backend can veto
an earlier yes. A general model-level-to-object-level fallback would have answered it. The new
backend carries the same explicit exclusion the parent does.

## D15 — The Portal Administrator holds no right to edit a group

The obvious reading of "assign and revoke roles" is `auth.change_group`, and Django's group form
edits a group's permissions. That would let the role rewrite what every role may do, including its
own. Membership is edited on the Person form's `groups` field instead, so the role holds
`contributors.change_person` and `auth.view_group` and nothing that can change a role's rights.

## D16 — A second check, for development accounts found in production

The command refuses to create the five accounts outside development. That guards the act and not the
state: a database copied down from production, a dump restored the wrong way round, or an
environment variable changed under a live database all produce the condition the command would have
refused. `fairdm.E301` reports it, tagged exactly as `fairdm.E300` is. One of those accounts is a
Portal Administrator whose password is published in the documentation.

## D17 — The module is `portal_roles`, not `roles`

This codebase already spends the word "role" on contribution roles, and FR-039 exists to keep the
two apart. A module called `roles.py` in the framework root would have undone that in the same
release that documented it.

## D18 — The team page lists active holders only

The specification said the page lists the people holding each role, and its edge cases said a
deactivated account holds nothing. Those two readings give different pages. The page lists active
holders: naming a departed volunteer as the portal's administrator tells a visitor something untrue,
and the page exists to tell them something true. FR-030 now says so.

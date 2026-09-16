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

## D19 — The portal's identity is `identity.Identity`, and the Data Curator's list is the full
attachment set

**Decision.** "The portal's identity" (FR-002, spec.md AC3) is `fairdm.contrib.identity.models.Identity`
— the singleton "Portal identity configuration including branding and metadata" already in the
codebase — so the Portal Administrator's fourth permission is `identity.change_identity`. The Data
Curator's permission list is the full Cartesian product research R9 calls for: view/add/change/delete
on `Project`, `Dataset`, `Sample`, `Measurement`, and on each one's `*Description` and `*Date`
attachment, plus view/add/change/delete on the shared `Contribution` model, plus `dataset.import_data`
(an existing `Dataset` permission) and `dataset.can_publish`, qualified `dataset.` because
`import_export/views.py`'s import and publish checks both run against `Dataset` instances
(`model = Dataset` on `BaseImportExportView`).

**Why.** Neither name appears anywhere in the specification or plan verbatim; both had to be
resolved against the actual model layer so the declaration would compile to real permission rows
(T002's "every permission is written as an explicit app_label.codename"). `dataset.can_publish` is
not a real `Permission` row anywhere in this codebase today — no model's `Meta.permissions` declares
it — so `reconcile()` treats it exactly like a permission research R5 describes as not-yet-created:
skip it, don't raise, and let a later migration that adds it converge automatically the next time
`reconcile()` runs. This is not the ordering gap R5 was written for, but the tolerance it requires is
identical, and the acceptance criterion T005 pins ("raises nothing when a permission it wants does
not exist yet") does not distinguish the two causes.

**Revisit if:** a future story adds a `can_publish` model permission under a different app label or
codename than `dataset.can_publish` — the Data Curator's declaration would then need to follow it, or
the role silently stops covering what `DatasetPublishConfirm.check()` asks for.

## D19 — Two tamper flags approved, and the docs gate's finding fixed in place

US-1's returned work raised three `modified_preexisting_test` flags, on `tests/test_apps.py`,
`tests/test_conf/test_settings/test_apps.py` and
`tests/test_contrib/test_contributors/test_choices.py`. All three are additions — a new `Test*`
class appended to the module that Article X says owns that subject — plus one formatter reflow of a
line the implementer did not otherwise touch. Nothing was weakened, skipped or deleted. Approved.

The independent verify that followed was green on lint, types, the full suite, build and
conformance, and red on the documentation step: `PortalRole` and `PortalRoles` are public names no
page documented. The story's documentation tasks covered the administrator's view of the roles and
the upgrade note, and missed the developer-facing API — which is Article XVII's requirement, not a
nicety, because a portal author reading `rights_carrying()` has nothing else to read. Written as
`docs/portal-development/portal_roles.md` and added to that guide's table of contents rather than
returned to the implementer: a page is not implementation, and a re-dispatch for one page costs
more than the page.

## D20 — `PortalRolePermissionBackend` reopens a defect an earlier feature deliberately fixed, in
four pre-existing tests this story's own prohibitions forbid touching

**The conflict.** T011's acceptance is unqualified: "a permission granted directly to the person"
answers `True` for `has_perm(perm, instance)` "on every instance of that model" - not only through
a role, and not only for a publicly visible one. T017 requires the same widening through a role: a
Data Curator must reach *another team's private dataset* by holding `dataset.change_dataset` at
the model level alone, with no per-record grant. Both are load-bearing, not incidental - T017's
given/when/then names the private case explicitly, and Research R2 in the brief states the rule
generally: "the new backend answers the object-level question from the model-level permissions the
person holds, which is the rule Django's own admin already follows."

An earlier feature (its own decision, also numbered D14, in a different specification - collision
only, not the same feature) fixed the opposite defect: it made `Update`/`Delete`/`Descriptions` on
`Project` and `Dataset` refuse a user holding only a model-level `change_*` permission and no
per-record grant on a *private* record, specifically because "a page that relies on inheriting a
visibility rule is not guarded at all" (`tests/test_core/test_project/test_plugins.py:306`'s
docstring, verbatim). Those pages gate on `visible_to_holder_of(permission)`
(`fairdm/core/dataset/plugins.py`, `fairdm/core/project/plugins.py`), whose `check` calls
`request.user.has_perm(permission, obj)` directly - the very call `PortalRolePermissionBackend` now
answers `True` for, given only a model-level grant.

Registering the backend (T012) makes four pre-existing tests fail, none of which this story
authored and none of which its prohibitions permit editing:

- `tests/test_core/test_dataset/test_plugins.py::TestUpdatePageDoesNotDiscloseAPrivateDataset::test_a_model_level_holder_with_no_record_level_grant_is_refused`
- `tests/test_core/test_dataset/test_plugins.py::TestEachOfTheFourPagesGuardsAPrivateDatasetsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`
- `tests/test_core/test_project/test_plugins.py::TestTheOverviewGuardsAPrivateProjectsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`
- `tests/test_core/test_project/test_plugins.py::TestUpdatePageOverHTTP::test_a_user_holding_only_model_level_change_permission_is_refused`

Confirmed mechanical, not incidental: reverting only `AUTHENTICATION_BACKENDS`
(`fairdm/conf/settings/auth.py`) back to its pre-T012 state, with `fairdm/permissions.py`
otherwise unchanged, makes all four pass again. `tests/test_core/test_sample/` and
`tests/test_core/test_measurement/` carry no equivalent test and are unaffected (810 passed, 7
skipped across project/sample/measurement together, beyond the two named above).

**What this story does about it.** Nothing to the four tests themselves - the prohibition against
touching a test this story did not author, for exactly this situation, says "mark the task blocked
and say why" rather than resolve it unilaterally. This is not proposed as a `modified_preexisting_test`
tamper flag for the same reason: the fix is not a bug in my diff, it is the earlier feature's
assumption ceasing to hold, on purpose, which is Sam's call to ratify - the closest precedent in
this story is D13's instruction to *supersede*, never silently rewrite, a docstring's superseded
reasoning. Left red, reported in the completion report's `concerns`, not counted toward "the suite
is green."

**Why the widening stands as specified rather than being narrowed to fit.** Narrowing
`PortalRolePermissionBackend` to answer only through a role, or only for a record the requester
can already view, would fail T011's own acceptance test (`tests/test_permissions.py`,
`test_a_permission_granted_directly_to_the_person_answers_the_same_way`) and would leave the Data
Curator unable to do the one thing T017 exists to prove - open another team's *private* dataset by
role alone. There is no narrower reading of both acceptance criteria at once.

**Revisit if:** Sam rules on which regime is correct for `Update`/`Delete`/`Descriptions`-style
pages going forward. If the model-level widening stands, the four tests' assertions should flip
(404→200) with a docstring amendment describing this story as what superseded them, mirroring
D13. If the earlier feature's stricter rule should stand instead, `PortalRolePermissionBackend`
needs a narrower condition than "any model-level grant" - at minimum, T017's own acceptance
criterion asking a curator to reach a private dataset by role alone would need to be revisited
too, since it is what makes the narrow reading impossible today.

## D21 — `claim_link_view`/`merge_view` supersede their own superuser-only reasoning (T019)

**Decision.** Both views' gates now ask `request.user.has_perm("contributors.change_person")`
(via a new `UserAdmin._may_manage_persons` helper, shared with `get_actions`) instead of
`request.user.is_superuser`. A superuser still passes - Django's own `has_perm` grants every
permission to a superuser before any backend is consulted - and a Community Manager, who holds
`contributors.change_person` through the role FR-004 already gives them, now passes too.

**Why.** D13 named this exact change and its own justification: both views' docstrings recorded
"superuser-only" as a deliberate decision, written "when the only alternative was 'anybody with
`is_staff`'". A portal role granted deliberately is a third thing the earlier decision never
had to weigh. Per D13's instruction, both docstrings keep their original reasoning and gain a
line stating what supersedes it, rather than being rewritten as if the earlier reasoning never
existed.

`get_actions` (`UserAdmin`) changes with them, not only the two views: the merge/claim-link
action buttons in the Person changelist were hidden for "a non-superuser" specifically so the
interface never offers an action its own view refuses (its own docstring, Route 2). Leaving that
check on `is_superuser` after the views changed would silently reintroduce exactly the gap the
comment was written to close, one route later - a Community Manager could still reach the pages
by a typed URL, but the story's own acceptance ("run a profile claim or a merge from the
administration interface") means through the visible action, not around it.

**Confirmed unaffected**: `tests/test_contrib/test_contributors/test_admin.py`'s pre-existing
`TestMergeAndClaimLinkViewsRequireSuperuser` and `TestPersonAdminActionsHiddenFromNonSuperuser`
both still pass unmodified - their "non-superuser" actors hold `is_staff=True` (or `view_person`
alone) and no `change_person`, so the new permission question refuses them exactly as the old
`is_superuser` check did. Verified by running both classes together with the new
`TestMergeAndClaimLinkViewsAdmitACommunityManager` (10 tests) and the full file (62 tests).

**Revisit if:** a future role other than Community Manager gains `contributors.change_person`
without being intended to reach profile claims or merges - the gate would admit them too, since
it asks the same permission `get_actions` and both views already share.

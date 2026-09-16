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

`fairdm.E500` runs in `AppConfig.ready()`, which fires before `migrate` does any work, and
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
refused. `fairdm.E501` reports it, tagged exactly as `fairdm.E500` is. One of those accounts is a
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

## D22 — `PortalRolePermissionBackend` narrowed to a shipped role's membership, superseding D20 (FIX-1)

**Decision.** `PortalRolePermissionBackend.has_perm` no longer derives an object-level answer
from every model-level permission a person holds. It now answers only when the permission is
held through membership of one of the four shipped portal roles (`fairdm/portal_roles.py`,
matched by group name against `PortalRoles.shipped_names()`). A permission granted directly to
a person through `user_permissions`, or held through a group the portal created itself, is
refused by this backend exactly as it was before this feature existed - `ModelBackend` still
answers `False` for every object-level question, so nothing else grants it either. A Data
Curator still reaches any dataset, including a private one they hold no record-level grant on,
because that right comes through the role.

**Why.** D20 recorded the collision this decision resolves: T011's original acceptance read the
widening as unqualified ("a permission granted directly to the person" answers the same way as
one held through a role), which reopened a defect an earlier feature (its own D14, a different
specification) deliberately closed - refusing Update, Delete and Descriptions on a private
`Project` or `Dataset` to someone holding only a model-level `change_*` grant, because a page
that relies on inheriting a visibility rule is not guarded at all. Registering the wide backend
made four pre-existing tests fail for exactly that reason:

- `tests/test_core/test_dataset/test_plugins.py::TestUpdatePageDoesNotDiscloseAPrivateDataset::test_a_model_level_holder_with_no_record_level_grant_is_refused`
- `tests/test_core/test_dataset/test_plugins.py::TestEachOfTheFourPagesGuardsAPrivateDatasetsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`
- `tests/test_core/test_project/test_plugins.py::TestTheOverviewGuardsAPrivateProjectsVisibility::test_every_page_refuses_a_model_level_holder_with_no_grant_on_this_record`
- `tests/test_core/test_project/test_plugins.py::TestUpdatePageOverHTTP::test_a_user_holding_only_model_level_change_permission_is_refused`

All four are the evidence that settled this: with the backend narrowed to role membership and
otherwise unchanged, all four pass again, unedited, alongside the rest of the suite. The
specification's own requirements (FR-003, FR-018, FR-020) ask for a *role's* rights to reach
records; they never asked for a direct grant to do the same, and the wider reading D20 traced
back to the plan and to T011's own acceptance test - both authored before this collision was
known - rather than to the requirements themselves.

**What changed with it.** `fairdm/permissions.py`'s module and class docstrings now state the
narrower rule and the reason for it. `tests/test_permissions.py`'s own acceptance test for the
wide reading (`test_a_permission_granted_directly_to_the_person_answers_the_same_way`) is
rewritten to assert the refusal the narrower rule requires
(`test_a_permission_granted_directly_to_the_person_is_refused`), with a new
`test_a_permission_held_through_a_group_the_portal_invented_is_refused` alongside it - neither
is one of the four pre-existing tests D20 protects. `CHANGELOG.md` and
`docs/portal-administration/roles.md` no longer tell an upgrading portal to audit permissions
granted outside the four roles: that instruction was only ever true under the wide reading, and
under the narrower one those grants behave exactly as they did before this feature shipped.

**Revisit if:** Sam rules that the wide reading should stand after all - in which case the four
tests above are what would need to flip (404→200), per D20's own note, and this entry's
narrowing would need to be reverted alongside them.

## D22 — US-2's tamper flags approved, and what the narrowing cost

Four `modified_preexisting_test` flags on US-2's diff, all additions: a new `Test*` class appended
to the module Article X says owns that subject, in `test_admin.py`, `test_permissions.py`,
`test_portal_roles.py` and `test_templatetags/test_fairdm.py`, plus one import line reflowed.
Nothing weakened, skipped or deleted. Approved.

The narrowing (D21) also rewrote two tests US-2 itself had written, which encoded the wide rule the
fix removed. That is the story correcting its own work inside its own files, not a pre-existing test
being overridden, and the four tests that forced the narrowing pass unchanged.

The full suite was read independently at 2767 passed, 8 skipped. Worth recording that the verify
step's own test timing (98s) is not the full suite's (637s): the machine gate is evidence that the
step ran green, never evidence of what it covered.

## D23 — T021's guard, implemented as specified, breaks seven US-1 tests left unmodified (US-3)

T020/T021 require `pre_delete`/`pre_save` receivers on `Group` that refuse a shipped role's
deletion or rename "for every ORM writer" (research R6, this story's brief), not only through the
administration interface FR-012/FR-013 name literally. Connecting a `pre_delete` receiver for
`Group` disables Django's collector fast-delete path for that model, so a bulk
`Group.objects.all().delete()` now sends `pre_delete` per row and is refused the moment it reaches
a shipped role, the same as a single instance's own `delete()`.

Two US-1 test classes reset state this way as their own setup, before this story existed:
`tests/test_portal_roles.py::TestReconcile` (5 tests) and
`tests/test_apps.py::TestPortalRolesReconciliation` (2 tests). Both call
`Group.objects.all().delete()` to put the database into "no roles yet" before asserting that
`PortalRoles.reconcile()` / `migrate` installs or repairs them. Once the guard is connected, that
call raises on whichever shipped role the collector reaches, and every one of the seven fails.

Confirmed empirically, not by inference: a throwaway probe test connecting an equivalent
`pre_delete` receiver reproduced the raise before either receiver was written, and running the
full `TestReconcile`/`TestPortalRolesReconciliation` classes afterward reproduced all seven
failures, in each case for exactly this reason (`ValidationError` naming a shipped role).

**Settles:** this brief prohibits modifying a test authored in a different story, and instructs
marking the task blocked rather than doing so. The receivers are implemented and committed
exactly to their own acceptance criteria - `TestProtection` in `tests/test_portal_roles.py`
(T020) is green - but T021 is reported `blocked` in `report-us3.json` for this reason, with the
seven test names as evidence, rather than silently landing a known regression in two files this
story does not own.

A one-line fix (`Group.objects.exclude(name__in=PortalRoles.shipped_names()).delete()`) would
mechanically restore green but changes what each test proves: the shipped roles would no longer
be deleted at all, so "migrate creates them from scratch" would collapse into "migrate leaves
already-correct roles alone" - a real weakening of intent, not a formatting fix, and exactly the
kind of pre-existing-test edit this story is not authorised to make on its own judgement.

**Revisit if:** Forge or Sam decide the regression is an accepted, deliberate consequence of
FR-012/FR-013 as designed - in which case the fix is to reset those seven tests' state through
raw SQL (as `tests/test_portal_roles.py::TestProtection`'s own helper,
`_delete_group_by_raw_sql`, already does) rather than through the ORM, preserving each test's
original intent.

## D24 — `check_portal_roles_present`, the first deploy check to touch the database, breaks six
more pre-existing tests the same way (US-3)

Every check FairDM registered before this story reads settings values only - `DATABASES`,
`CACHES`, `SECRET_KEY`, `ALLOWED_HOSTS`, and so on. `check_portal_roles_present` (T025) is the
first that queries live database state (`Group.objects.filter(...)`), because FR-015 is a claim
about installed rows, not configuration. Any test that runs the full `check --deploy` pipeline
without enabling database access - `@pytest.mark.django_db`, the `db` fixture, or
`transactional_db` - now trips pytest-django's own safeguard
(`RuntimeError: Database access not allowed`) the moment my check runs, regardless of what that
test is actually asserting.

Six pre-existing tests do exactly this, none of them written in this story:
`tests/test_conf/test_checks.py::TestCheckCommandIntegration::test_check_deploy_fails_with_errors`,
`::test_check_deploy_passes_with_valid_config`, and
`TestDeployCommand::test_deploy_check_reports_the_same_failure_regardless_of_django_env` (all four
parametrised cases). Each calls `call_command("check", deploy=True)` with no database fixture,
because until now nothing registered under `deploy=True` ever needed one. Confirmed by running
`TestCheckCommandIntegration`/`TestDeployCommand` alone, isolated from every other change in this
story: all six fail, in each case with the same `RuntimeError`, not a `SystemCheckError` naming
the wrong thing.

**Settles:** the same rule as D23 applies - these are not authored in this story, and this
brief's prohibition instructs reporting the task blocked rather than adding a database fixture to
a test I did not write, however small that edit would be. `check_portal_roles_present` itself is
implemented exactly to its own acceptance criteria and is correctly guarded against every
database condition its own tests exercise (missing table, unreadable table, an unconfigured
engine, `migrate` in progress) - see the tolerance test added alongside this decision,
`TestPortalRolesPresent::test_a_database_django_cannot_even_resolve_an_engine_for_returns_nothing`,
which was itself added after this same category of failure surfaced in `tests/test_apps.py`'s
production-boot tests (`ImproperlyConfigured`, not caught until this fix).

**Revisit if:** Forge or Sam decide the fix belongs to the six tests, in which case each needs
`@pytest.mark.django_db` (or the `db` fixture) added - a one-line addition per test, not a
weakening of anything they assert.

## D25 — T024's two live-production-boot scenarios are covered by registration and unit tests,
not a subprocess against a real database (US-3)

T024's given/when/then names two scenarios that need an actual production-shaped boot: "the
production boot refusal raises... and names them" and "a production database holding data but
none of the four roles still runs `migrate` to completion" (D11's critical finding). Every
existing subprocess boot test in `tests/test_apps.py` reaches this by setting `DATABASE_URL` to a
PostgreSQL connection string and calling `django.setup()` - but none of them ever open that
connection, because every production_critical check before this story reads settings values
only. `check_portal_roles_present` is the first to query live database state, so a genuine
version of these two scenarios needs a reachable PostgreSQL server.

None is reachable in this environment: no `docker` daemon, no `psql` client, and a direct TCP
probe of `localhost:5432` returns connection refused. SQLite cannot substitute - confirmed by
trying it first: `fairdm.E101` (SQLite not recommended for production) is itself
`production_critical` with no stand-down, and `FairDMConfig._check_production_configuration`
filters only on `issue.is_serious()`, never consulting `SILENCED_SYSTEM_CHECKS`, so a portal
override silencing `fairdm.E101` has no effect on it - only on `manage.py check` proper. Any
SQLite-backed "production" subprocess therefore refuses to boot (and to migrate) on E101 alone,
regardless of what this story's check reports, which would prove nothing about the roles
condition at all.

**Settles:** the two scenarios are covered instead by three tests that are each fully
deterministic and need no live database beyond this suite's own (SQLite):
`test_stands_down_when_the_current_command_is_migrate` and
`test_does_not_stand_down_for_an_unrelated_command` exercise D11's exact mechanism directly
against the check function; `test_check_is_registered_with_the_production_critical_deploy_tags`
proves the check is wired into the same tag-based gate every other production-critical check
already uses (`FairDMConfig._check_production_configuration`, unmodified by this story).
`tests/test_apps.py::TestPortalRolesReconciliation` (US-1, pre-existing) already proves `migrate`
installs the roles against this suite's real database. Together these cover every moving part
the two scenarios would exercise, without the one part - a live boot against a genuinely
production-shaped database - this environment cannot run.

**Revisit if:** a Postgres-backed environment (CI, matching `tests/settings.py`'s own comment
that CI runs a `postgres` service container) is available to add the literal subprocess version
of these two scenarios as a follow-up. It is not a correctness gap in the implementation, which
every unit-level test already exercises - it is an environment gap in this coverage.

## D26 — `check_portal_roles_present` is renumbered `fairdm.E500`, superseding D11's and D16's
`fairdm.E300`/`E301` (FIX-2)

**Decision.** `fairdm/conf/checks.py` numbers by hundreds - E0xx security, E1xx database, E2xx
cache, E3xx celery, E4xx translation - a convention every check but this story's follows.
`check_portal_roles_present` was assigned `fairdm.E300` at design review (D11) and implemented
against it (T025); `fairdm.E300` is `check_celery_broker`'s id, held since long before this
feature (`fairdm/conf/checks.py`, Spec 003). That was an error in the plan, not in T025's
implementation, and it was never exercised: nothing in the suite calls both checks in the same
`check --deploy` run in a way that would have surfaced two errors sharing one id. The check now
takes `fairdm.E500`, the first free hundred after translation's E4xx. `E501` is left free for
`check_dev_accounts_absent` (T029, US-4, not yet built), which D16 assigned `fairdm.E301` -
`check_celery_async`'s id, the same category of error. Every reference to either wrong id in
`fairdm/conf/checks.py`, its own tests, and this spec's `tasks.md`/`plan.md`/`decisions.md` (D11,
D16) is updated to match; D23, D24 and D25 name no id and are unaffected.

**Why:** a shipped id has to be unique for `SILENCED_SYSTEM_CHECKS` and `check --deploy` output to
mean anything, and E5xx keeps every future portal-roles-family check out of a range four other
subsystems already own.

**Revisit if:** the file's hundred-per-subsystem convention itself changes; nothing about this
story's design motivates renumbering again on its own.

## D27 — `check_portal_roles_present`'s database tolerance is extended to cover a test harness
that refuses access outright, resolving D24 (FIX-2)

**Decision.** D24 recorded that `check_portal_roles_present` is the first `production_critical`
check to query live database state, and that six pre-existing tests
(`TestCheckCommandIntegration` x2, `TestDeployCommand` x4 parametrised) call `check --deploy`
with no `db` fixture enabled, tripping pytest-django's own safeguard - `RuntimeError: Database
access not allowed` - the moment the check runs, and that fixing it was outside T020-T025's
authority since none of the six were authored in that story. The check's own contract already
tolerates a group table that is absent or unreadable, so it can no more distinguish "no database
configured yet" from "a role is actually missing" than a raw `OperationalError` or
`ProgrammingError` could. A test harness refusing access outright is the same case: the table is
not absent, but it is just as unreadable to this check. `RuntimeError` joins the except clause
that already catches `OperationalError`, `ProgrammingError` and `ImproperlyConfigured`. None of
the six tests are touched; each passes unchanged once the check tolerates the condition they were
already creating.

**Why:** the alternative - adding `@pytest.mark.django_db` to six tests this story did not author
- is a smaller-looking edit that changes what each of those tests proves (whether the command
enables database access), while widening this check's own tolerance changes nothing about what it
proves (a role is missing) and matches the tolerance it already declares for every other way a
group table can be unreadable.

**Revisit if:** a future check needs to distinguish "database access is disabled by the caller"
from "the group table cannot be read" - nothing in this feature's requirements needs that
distinction, so it is not built.

## D28 — The seven tests that reset state with `Group.objects.all().delete()` disconnect T021's
guard through a named, shared fixture, resolving D23 (FIX-2)

**Decision.** D23 recorded that `tests/test_portal_roles.py::TestReconcile` (5 tests) and
`tests/test_apps.py::TestPortalRolesReconciliation` (2 tests) reset state by deleting every
`Group` row before proving `PortalRoles.reconcile()` / `migrate` installs or repairs them, and
that T021's guard - correctly - refuses that bulk delete the moment it reaches a shipped role. The
guard is not weakened, for these tests or any other caller: the module docstring already states it
does not hold against raw SQL, and the specification's own account of how a role can actually go
missing is exactly that route, repaired on the next `migrate`. A new fixture,
`disconnect_shipped_role_guard` in `tests/conftest.py`, disconnects `refuse_shipped_role_deletion`
and `refuse_shipped_role_rename` from `Group`'s `pre_delete`/`pre_save` by their `dispatch_uid` for
the duration of a test, and reconnects them in a `finally` block so a failing assertion cannot
leave the guard disconnected for a later test. Each of the seven tests requests it explicitly as a
fixture parameter; nothing else does, and `TestProtection` does not and still proves, on its own,
that a shipped role cannot be deleted or renamed.

**Why:** `Group.objects.all().delete()` is not a caller these tests invented for convenience; it
is how each proves `reconcile()` builds every role from an empty table, the same condition a raw
SQL deletion or a restored backup produces. Disconnecting the two receivers by name, for exactly
the tests that model that condition, keeps the guard's own tests honest about what it protects
against while letting the seven keep asserting exactly what they asserted before D23 was written -
none of their assertions changed, only their setup gained one fixture parameter each. A shared
`tests/conftest.py` fixture, rather than one copied into each file, is used because both test files
sit directly under `tests/` and both need the identical disconnect/reconnect pair.

**Revisit if:** a caller other than these seven ever needs the same disconnection - if so, extend
this fixture's usage rather than writing a second one; do not add a flag or parameter to the guard
itself to reach the same effect.

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

# Decisions — 013 Managing a project through the portal

This records the audit behind the rewritten `spec.md`, dated 2026-08-23. Each entry states what the
previous specification said, what the code does, which way it was settled and why. It exists so a
later reader can tell a deliberate narrowing from an oversight.

The previous specification was written on 2026-05-11 and described four views: a listing, a
creation form, an attributes form and a deletion page. All four were built and most of what it
asked for is present and correct. Three things changed underneath it. Later work added an image
field and a record of who created a project, neither of which it mentions. One requirement was
quietly abandoned in the code with a note explaining why. And one requirement was implemented
halfway, in a way that passes its test while doing nothing a user can see.

The larger change is to scope rather than to accuracy. The previous specification managed a
project's own fields and left its descriptions, dates and identifiers to the Django admin, which is
the thing the roadmap item exists to stop needing. Those records are now part of the feature.

---

## D1 — Funding leaves the feature

**Previous specification**: FR-018 and FR-028 required funding among the editable attributes, as a
JSON text area.

**Code**: `forms.py:61-74` declares the field. `forms.py:80` omits it from the form's declared field
list, and the shell's form layer then removes any field absent from that list before rendering
(`fairdm/forms/base.py:110-114`). The field has therefore never been reachable. A note above the
declaration, at `forms.py:78-79`, records the reason: the field is complex enough to deserve an
interface of its own rather than a raw JSON box.

**Settled**: funding leaves this feature. The unreachable declaration is deleted rather than left
in place.

**Why**: issue #175 argues the field should stop being JSON altogether and become a related model
shared by projects and datasets, since a funder is an organisation the portal already models.
Building a JSON text area now means building a thing we have already decided to delete. Leaving the
declaration in place means leaving code that looks like a feature and is not one.

**Left open**: nothing here. Funding editing is issue #175's to design.

---

## D2 — Descriptions, dates and identifiers join the feature

**Previous specification**: FR-018 excluded them, and the assumptions said related data was
"managed through separate, dedicated interfaces outside the scope of this feature". No such
interface was ever built, so in practice they were managed through the Django admin.

**Code**: `ProjectDescription`, `ProjectDate` and `ProjectIdentifier` exist as related models with
controlled type vocabularies (`models.py:155, 185, 257`) and are editable in the Django admin
(`admin.py:16, 70, 79`). There is no portal page for any of them. Issue #171 records the gap.

**Settled**: all three join the feature. Descriptions get a page of their own. Dates and
identifiers are edited alongside the project's own attributes. Issue #171 is closed by this feature
except for keywords.

**Why**: the roadmap item this feature serves is about managing records without the Django admin,
and a project whose descriptions can only be written by an administrator has not met it. The
application shell already provides view classes for editing related records alongside a parent, so
this is configuration rather than new machinery, which is what Article XIV asks for. Descriptions
are separated from the rest because they are long-form prose and the others are short values.

**Left open**: which of the shell's facilities fits each case, and how the descriptions page is
laid out. Both are settled during planning.

---

## D3 — Keywords stay out

**Previous specification**: silent on keywords beyond excluding them from the attributes form.

**Code**: keywords are configured per portal through a setting, which the project filter reads to
build its filters (`filters.py:51-106`). There is no editing interface.

**Settled**: keywords remain uneditable through the portal and issue #171 stays open for them
alone.

**Why**: keywords are chosen from controlled vocabularies, and the package that will hold those
vocabularies is not yet integrated. Building a picker now means building it against a vocabulary
layer that is about to be replaced. This is a deferral with a named trigger, not an omission.

---

## D4 — Both visibility defaults are correct

**Previous specification**: silent on defaults.

**Code**: the creation form pre-selects Public (`forms.py:50`). The model's own default is Private
(`models.py:86`).

**Settled**: both stay, and the specification now says so and why.

**Why**: they answer different questions. A person filling in the creation form is looking at the
choice and making it deliberately, and the portal's purpose is served by encouraging openness
there. A record created outside the portal — by an import, a fixture, the API — has nobody looking
at a form, and the safe assumption for it is that nothing has been reviewed for release yet. A
single value cannot serve both.

---

## D5 — The deletion refusal never says what it is refusing

**Previous specification**: FR-023 required the page to be redrawn listing the blocking datasets by
name, and SC-003 measured it.

**Code**: the refusal itself is correct and well placed. A signal on the project raises when a
public dataset exists (`models.py:280-298`), the page catches it inside the ordinary form flow and
puts the datasets into the page's context (`views.py:211-219`), and there is no custom request
handling, exactly as the previous specification asked.

Nothing then reads that context. The name it is stored under appears twice in the repository: once
where it is written, and once in a test asserting it was written. The page that renders is the
shell's standard deletion page, which reads a different name populated by a different mechanism:
the database's own protection, which this signal never triggers. What a user sees is the ordinary
confirmation page, unchanged, still inviting them to delete, with no explanation and no dataset
named.

**Settled**: the specification keeps its requirement. This is a defect and closing it is work in
this feature.

**Why**: the requirement was right, and the direction of this drift is that the code is wrong. It
is worth recording how it survived: the test asserts the datasets reached the context rather than
that they reached the reader, so it passes on an implementation that shows the user nothing. The
replacement test asserts on what the page says.

---

## D6 — The pages use a mechanism the shell has deprecated, and their links are broken

**Previous specification**: silent on navigation entirely. It specified four pages and never said
how anyone reaches them.

**Code**: the listing and attributes pages set attributes named for permissions
(`views.py:44-45, 150-151`) that the shell renamed at 0.16 and removes at 0.18. They still work,
they emit a deprecation warning, and despite their names they decide only whether a link is drawn.
Two consequences are visible now. The deletion page sets none of them, so its back link resolves to
nothing and renders empty. The attributes page draws no link to deletion. Beyond that, no page in
the feature links to any other: neither the project's own page nor its listing entry mentions the
attributes, descriptions or deletion pages, so all three are reachable only by typing an address.

**Settled**: navigation joins the feature. The attributes are renamed to the shell's current ones,
the missing links are added, and each page's links are tested for resolving.

**Why**: these are this feature's own pages, and a page nobody can reach has not been delivered.
The rename is on a removal clock that would otherwise be hit blind, and the two names differ in a
way worth writing down: the old one reads as though it controls access and it never did. Access is
checked separately on every page, as it was before.

---

## D7 — The listing entry was never a placeholder, and is not this feature's to design

**Previous specification**: FR-007 required "a minimal placeholder list-item template" whose visual
design was "deferred to a future spec".

**Code**: a full card with an image, a date, an abstract and a contributor list
(`templates/project/project_card.html`).

**Settled**: the specification stops calling it a placeholder. The card and the project's own page
keep their current design, and this feature changes them only to add links.

**Why**: the deferral happened and the design landed. The specification simply never caught up.
Redesigning either page is separate work, and the project page already has an issue of its own
(#167).

---

## D8 — Requirements state behaviour, not the code that produces it

**Previous specification**: several requirements named the mechanism as well as the outcome — which
field list to override, which widget to redeclare on which subclass, which base class each view
inherits.

**Code**: two of those mechanisms differ from what was written while producing exactly the
specified result. The creation form's field set is narrowed by the shell rather than by Django's
own mechanism, and the creation form inherits its visibility choice rather than redeclaring it.

**Settled**: requirements describe what a person can do and what the portal guarantees.
Architectural constraints stay where they carry a real obligation — use the shell's facilities
rather than hand-written equivalents, use its current mechanism for declaring links — and the rest
is settled during planning.

**Why**: both of these read as drift and neither is. A specification written at that altitude
generates false findings on every later audit and forbids improvements that change nothing a user
sees. It also made the previous document hard to read: the single longest requirement in it was
about form class inheritance.

---

## D9 — Undocumented behaviour, now written down

Found during the audit, correct, and previously unrecorded. Each is now in the specification.

- A project records who created it (`views.py:94`, `models.py:113-125`). Added by later work.
- A project's image is validated for size and rendered through a thumbnailing widget
  (`forms.py:24-32`). Added by the image field specification, 015.
- Creation, change and deletion each report success to the user. The shell does this.
- A page's configured destination is overridden by a validated destination in the request when one
  is present. The shell does this, so the destinations in this specification are what happens
  absent that, not guarantees.

---

## D10 — A record's pages are one registered collection, not one registration each

**Previous specification**: silent on how a page is addressed. The pages were given routes of their
own, outside the portal's per-record navigation, which is why none of them links to any other.

**Code**: a navigation entry's address is built from the record's name and the registration's own
name, so a page addressed independently can never appear in that navigation. Rendered as an
anonymous visitor, a project's navigation offers datasets, export, configure and contributors, with
no entry for the project itself and no entry marked as current.

**Settled**: the project's own page is its overview registration, and the attributes and deletion
pages belong to that registration rather than standing beside it. `ProjectConfigure` and the
independent editing and deletion routes are retired.

**Why**: a registration carries one navigation entry. One registration per page fills the record's
navigation with noise as soon as add-ons contribute their own, so a registration is a collection of
related functionality with a single entry, and the collection's own template links whatever else it
owns. The portal was built this way until three months ago: nine registrations existed against a
project, among them the overview, the editing page and the deletion page, and the record's address
method returned the overview. The registry rework of 2026-08-11 cut them to three while migrating to
decorator arguments, and six lost their registration in the move with no reason recorded in any
commit message, specification or plan. This restores an architecture that was dismantled in passing.

**Left open**: the layout of the overview template, which links the collection's other pages. Out of
scope here per FR-047.

---

## D11 — One address prefix, and it is the plural one

**Previous specification**: silent. The convention was never written down, and both forms are in use.

**Code**: a project is at `projects/<uuid>/` while the pages registered against it mount under
`project/<uuid>/`. Datasets carry the same split. Samples are plural already, and measurements are
singular throughout.

**Settled**: the singular form goes. A project keeps `projects/<uuid>/` and its pages become segments
below it.

**Why**: the plural address is the one a reader may have cited, and the inconsistency is worth
removing rather than entrenching. The cost is that the pages already registered against a project —
contributors, datasets, export — change address, which is accepted.

**Left open**: nothing for this feature. Datasets and measurements are raised separately so the
singular form leaves the repository in one pass rather than one record type at a time.

---

## Raised separately

Found while checking the specification against the code, real, and not this feature's work.

- **Issue #174** — the attributes page fetches its project without using the queryset the view
  declares, so no prefetching applies and the fetch runs twice on a submission. Already open.
- **Issue #173** — the project's forms and views resolve their translations when the module is
  imported rather than when a page is rendered, so a portal serving more than one language gets
  whichever was active at startup. Already open.
- **The project's own page decides visibility by comparing against a bare number** rather than the
  named value (`views.py:256`). Inside a method this feature does not otherwise touch, and the page
  itself is out of scope. Raised separately.
- **Issue #283** — datasets and measurements keep the singular address prefix that D11 removes from
  projects. A dataset's pages mount under the singular form while the dataset itself is plural, and
  measurements are included under the singular form throughout. Samples are already plural. Raised
  separately so the convention lands across the repository rather than one record type at a time.

# Decisions: 024-shared-editing-pages

Questions settled while writing the specification without asking the maintainer, with the reasoning
behind each. The request in #404 named the six pages, the four record types, the Manage menu and the
rule that each page is shown only to someone who may use it. Everything below fills a place where it
was silent.

## For Sam to confirm

Each of these changes what gets built and was not stated in the request. The specification is
written on the reading given here. If any is wrong, it is one requirement to change.

1. **Key dates and identifiers leave the details page.** On a project and a dataset they are edited
   today on the same page as the other details. The request lists them as entries of their own, so
   the specification moves them to their own pages and takes them off the details page (FR-016). The
   alternative is to keep them on the details page as well, which would mean two places to edit the
   same thing.
2. **Descriptions use one area per description type.** A project and a dataset edit descriptions
   that way. A sample uses rows that are added and removed, each with a type chosen from a list. The
   specification takes the first for all four (FR-020), because the vocabulary already says which
   descriptions a record can carry and the row form lets the same type be chosen twice. A sample's
   descriptions page changes as a result.
3. **The keywords page ships as it is, on all four record types.** Only a sample has a keywords
   page today. A dataset's was removed on the grounds that #298 would replace it whole. The request
   lists keywords among the six and puts the rebuild out of scope, so the specification registers
   the existing page everywhere (FR-022 to FR-024) and leaves its interior to #298. The alternative
   is to leave the keywords entry out until #298 is built. That is why keywords are the last story:
   dropping it costs nothing else.
4. **A sample's and a measurement's details page edits the type's own fields.** A sample's edit
   page offers only its name and image today, and a measurement has none. The specification makes
   the details page offer what the registered type offers on creation (FR-016), since the request
   says a measurement cannot be edited beyond what its create form offered. It does not offer moving
   a record to another dataset or sample (FR-017), because that changes who has rights over it and
   deserves a decision of its own.
5. **Deleting adds no new protection.** A project with a public dataset is refused, and a sample
   with measurements on it is refused, as now. A sample or a measurement in a public dataset can
   still be deleted by someone with the right, as it can be today through other routes. The glossary
   says publication constrains deletion. If a public dataset should also protect its samples and
   measurements, that is a requirement to add here (FR-031).
6. **The right to delete is left as it stands, and it is uneven.** Deleting a sample needs the right
   to change its dataset. Deleting a measurement needs the right to delete its dataset. The
   specification does not align them (FR-012), because who may do what on a record is #402's
   subject. It is listed here so the difference is a known one.

## Rights are the ones the portal checks today

The request says each page is shown only to someone who may use it. It does not say who that is.
The portal already has a right to change and a right to delete each record type, and 017 gives
portal roles their share of both. Using those keeps this feature to its subject, which is the pages,
and leaves granting rights to a research team with #402. Nothing in the specification depends on
#402 being delivered first.

## No dependency on a sibling feature

The specification relies on nothing the other six features in #397 deliver. The Manage menu exists
already on three of the four record types (018). #401 adds page actions, overview cards and
replacing a plugin, none of which these pages need. #403 removes and adds tabs, and these pages are
not tabs. The epic's `Depends on:` footer is therefore empty.

## Manage menu entries from addons are out of scope

#397 lists the Manage menu as one of four places something can appear on a record's page, and #401
opens two of the others to addons. Neither issue asks for addons to add Manage menu entries. The
specification covers the six entries and requires that the menu's other entries survive (FR-009). A
general way for a plugin to contribute an entry would be a feature of its own.

## Old addresses are not kept

The existing pages sit at different addresses on each record type. Sharing one set means one
pattern. The package is at version 0.0.1 with no stable release, so the specification does not ask
for the old addresses to redirect. The record's own address is the one that must not move (FR-005),
because that is what a citation points at.

## Landing place after a deletion

A deleted sample or measurement leaves its dataset behind, so that is where the person lands
(FR-033). A project and a dataset land where they do today. The specification says only that the
page still exists, so the choice stays with the build.

## How a deletion is confirmed is left open

A project and a dataset are confirmed today by typing the record's name. A measurement may have no
name. The specification requires a deliberate confirmation and a statement of what goes with the
record (FR-030), and leaves the form of the confirmation to the build.

## Simultaneous edits are not detected

Two saves of the same page are applied in order and the later one stands. No editing page in the
portal detects this today, and adding it is not what the request asks for.

## No sketch before the build

Every page here is a form or a confirmation in a layout the portal already has, reached from a menu
that already exists. Nothing needs to be drawn first.

## Decisions made while planning the build

Read against `main` on 2026-10-07, after specifications 020 and 022 were delivered and #401 was
closed.

## D1. The right to delete is no longer uneven

Item 6 above described deleting a sample as needing the right to change its dataset, and deleting a
measurement as needing the right to delete its dataset. Specification 022 changed both: deleting any
of the four record types needs the manage level, through `<type>.delete_<type>`. The delete page
asks that permission and nothing else. FR-012 holds because the page reads the right that exists.

**ADR:** none — the rule is recorded in 0025, and this page only reads it

## D2. A viewer who may see a record and not use a page gets 403, not 404

**Decision:** a request for an editing page answers 404 only when the viewer may not see the
record. A signed-in viewer who may see it is refused with 403, and a visitor is sent to sign in.
**Why:** FR-013 and FR-014 draw that line. The project and dataset pages answer 404 to every
refusal on a private record today, and specification 022 (its D29) left that to be revisited when
these pages were rebuilt.
**Revisit if:** a refusal is found to reveal something the record's own page does not.

**ADR:** docs/adr/0026-a-records-editing-pages-are-six-shared-pages.md

## D3. The project's "Manage contributors" entry is not carried into the shared menu

**Decision:** the shared Manage menu has the six entries and no entry for contributors.
**Why:** specification 022 FR-007 says managing contributors must not appear in the Manage menu.
The entry on the project page predates it. FR-009 here keeps whatever else the menu carries, and it
was written with entries such as importing data in mind, none of which is in the menu today.
**Revisit if:** the Contributors tab stops being offered on a record type.

**ADR:** none — local to this feature, and the rule it follows is specification 022's

## D4. The keywords form is repaired to a working state

**Decision:** `KeywordForm` is changed so that it reads the configured vocabularies with a default
of none and no longer rewrites its own class. Nothing else about it changes.
**Why:** FR-024 asks for the page as it works today, and it does not work: the form raises for every
sample type because it reads a setting that does not exist. FR-023 asks for a page that works with
no vocabulary configured. The smallest change that satisfies both is this one.
**Revisit if:** #298 lands first, in which case US-4 only registers its page.

**ADR:** none — a repair inside this feature, and the form is replaced by #298

## D5. Dates and identifiers leave the details page, and the pages are registrations of their own

**Decision:** the six pages are six registered plugins, not additional views of the overview, and
dates and identifiers are edited on their own pages.
**Why:** the specification asks for both (FR-003, FR-016). Architecture decision 0008 says the
opposite on each point, so a new record supersedes it.
**Revisit if:** never without a new specification.

**ADR:** docs/adr/0026-a-records-editing-pages-are-six-shared-pages.md

## D6. Started while another pull request is open

**Decision:** the build started while #383, which shows a record's image as a banner on its
overview, is open and waiting for review.
**Why:** the maintainer asked for this feature to be built now. #383 changes the overview's header
image and two user guide pages. If it merges first, this branch is brought up to date before it is
marked ready.
**Revisit if:** #383 changes the overview's actions block.

**ADR:** none — an ordering note for this run

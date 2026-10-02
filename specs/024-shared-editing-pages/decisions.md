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

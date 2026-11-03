# Documentation standards

These rules cover the documentation a person reads to use what this repository makes: the pages
under `docs/` and the quickstart in the README. `CONSTITUTION.md` makes them binding. Docstrings,
component annotations and comments are covered by
[`code-documentation.md`](code-documentation.md). The sections above **Project additions** are
shared unchanged with our other repositories, so edit this repository's rules in that last
section only.

The rules follow [Diátaxis](https://diataxis.fr/), which sorts documentation by what the reader
needs at the moment they open it.

## 1. What these rules cover

They cover documentation written for the people who use the repository's work:

- for a package, the developer who installs it in their own project,
- for an application, the person who uses the site.

Material written for the people who maintain the repository has a form of its own and is not
covered here:

- the changelog,
- decision records in `docs/adr/`,
- the roadmap,
- specifications in `specs/`,
- contributor guides and standards pages in `docs/contributing/`,
- files that configure tools.

A user page may link to any of these. An explanation, for example, can point to the decision
record behind a design.

## 2. The four types

Every page is one of four types, and only one.

| Type | The reader | Answers |
|---|---|---|
| Tutorial | Is new, and learning by doing | Show me how to get started |
| How-to guide | Already uses it, and has a job to do | How do I do this one thing? |
| Reference | Is working, and needs a fact | What exactly is this setting, component or command? |
| Explanation | Is stepping back to understand | Why does it work this way? |

Two questions tell the types apart:

- **Does the page guide an action, or inform understanding?** Tutorials and how-to guides guide
  action. Reference and explanation inform.
- **Is the reader learning, or working?** Tutorials and explanation serve learning. How-to
  guides and reference serve work.

Material of a second type goes on a second page, and the two link to each other. A how-to guide
that stops to explain a design, or a reference page that walks through a task, has two pages in
it.

## 3. Where pages live

```text
docs/
├── index.md
├── tutorial.md
├── how-to/
├── reference/
└── explanation/
```

- **`index.md`** says in one paragraph what the package is for, then lists the pages under one
  heading for each type, in the order Tutorial, How-to guides, Reference, Explanation. The
  maintainers' material from section 1 follows under headings of its own.
- **A directory is created when its first page arrives.** None of them is set up in advance, and
  none is left empty.
- **A tutorial longer than one page** becomes a `tutorial/` directory, its pages numbered in
  the order they are read.
- **A file is named after its title**, in lowercase words joined by hyphens, with "How to" left
  off: `how-to/add-a-menu-item.md`, `reference/settings.md`,
  `explanation/how-a-theme-is-applied.md`.

**A small package needs no `docs/` directory.** When setting the package up takes no more than
two short examples, the quickstart in the README is its tutorial and the README is its
documentation. A package that needs more than that has a `docs/` directory laid out as above,
and the README's quickstart links to the tutorial there.

**An application's user guide is organised by the application's own sections**, not by type,
because a person looks for help under the name of the screen they are on. Each page is still one
type, and its title follows the rule for that type. Where the guide lives and how its contents are
ordered is set out in **Project additions**.

### Documentation for more than one reader

A repository whose readers do different jobs, such as the developers who build on it, the staff
who run a site built with it and the people who use that site, splits `docs/` by reader first.
It declares its readers in **Project additions** with a table headed **Readers**:

```markdown
### Readers

| Reader | Lives in | Does | Organised by |
|---|---|---|---|
| Portal developer | `developers/` | Builds and deploys a portal | type |
| Portal administrator | `administrators/` | Runs a portal: people, roles, review | type |
| Portal user | `users/` | Adds and edits research data | the site's sections |
```

A repository with no such table has one reader, and the layout above applies as it stands.

```text
docs/
├── index.md
├── explanation/
├── developers/
│   ├── tutorial.md
│   ├── how-to/
│   ├── reference/
│   └── explanation/
├── administrators/
└── users/
```

- **Readers are told apart by what they do, not by what they are allowed to do.** A role gets a
  section of its own only when its tasks differ. A role that only sees one more button gets a
  line on the how-to guide for that task, such as "Only data managers see **Merge**".
- **A reader's section organised by type** has the layout of a single-reader `docs/`, and leaves
  out a type it has no pages for.
- **A reader's section organised by the site's sections** follows the rule for an application's
  user guide above.
- **Explanation that every reader needs is written once**, in `docs/explanation/`. A reader's
  own `explanation/` holds only what that reader needs.
- **`index.md`** says in one paragraph what the repository is for, then gives one entry for each
  reader, in the order of the table, saying who it is for and linking to that reader's section.
  The shared explanation and the maintainers' material follow.

## 4. Tutorials

A tutorial takes someone new from nothing to a working result.

- **Title**: what the reader will have built, such as "Build your first page".
- **Before you start**: what the reader needs, with a link for each.
- **One path.** No options, no alternatives and no "you could also". Choices belong in how-to
  guides.
- **Every step ends with something the reader can see**: a page that loads, a command's output,
  a test that passes.
- **The code is complete.** Each block can be copied as it stands, with its imports. A name the
  reader must change, such as `yourproject`, is called out the first time it appears.
- **It explains almost nothing.** One sentence at most, then a link to the explanation.
- **It ends with the finished result**, and links to the how-to guides a reader is likely to
  want next.

A tutorial is followed from start to finish, in a new project, before a release that changes
anything it relies on.

## 5. How-to guides

A how-to guide takes someone who already uses the package through one task.

- **Title**: "How to", then a verb, then what it acts on: "How to add a menu item", "How to
  restrict a field to part of a vocabulary".
- **Opening paragraph**, with no heading: what the task achieves and when someone would do it,
  in two sentences at most.
- **Before you start**: only when the task has a real precondition. Left out otherwise.
- **Steps**: one numbered list, one action to a step. Code in a step shows only what that step
  changes, with enough around it to show where it goes.
- **The result**: what the reader sees once the task is done, and anything that changed
  elsewhere.

A how-to guide covers one task. A second task gets a guide of its own. It does not teach the
basics, which the tutorial covers, or explain the design, which the explanation covers. Every
setting, component or command it uses links to its reference entry.

**Troubleshooting is a set of how-to guides.** Each entry is headed by the symptom the reader
sees, gives the cause in one sentence, then the fix.

## 6. Reference

A reference page describes the machinery: settings, components, template tags, management
commands, views, models and the Python API.

- **It describes, and does nothing else.** No steps and no argument. A short example is fine
  where it shows the usage faster than the prose can.
- **It is built like the thing it describes.** One page for the settings, one for the
  components, one for the template tags, each in the order the code defines them or in
  alphabetical order.
- **Every entry gives the same facts in the same order**: the name, its type or signature, its
  default, what it does, and what it accepts.
- **It is complete.** Every public setting, component, tag and command has an entry. One that is
  missing is a defect.

**The Python API is generated from docstrings** wherever the repository builds its
documentation, and [`code-documentation.md`](code-documentation.md) makes those docstrings
complete. A docstring is never restated by hand on a reference page. A repository without a docs
build writes reference pages only for what a user sets or calls from outside Python: settings,
components, template tags and management commands.

**An application's reference is a screen guide**: one page for each screen, titled with the
screen's own heading. It says what the screen is for and how to reach it, then has one section
for each part of the screen, saying what the part shows and what it shows when empty. It closes
with what the reader can do from the screen, each action a link to its how-to guide.

## 7. Explanation

An explanation helps a reader understand a subject.

- **Title**: the subject, not a question: "How a theme is applied", "Concepts, schemes and
  collections".
- **Opening paragraph**, with no heading: what the page covers and what it does not.
- **Body**: one idea to a section. Why the design is the way it is, what it was weighed against,
  and where its limits are.
- **Decisions link to their record.** Where a decision has an entry in `docs/adr/`, the
  explanation gives the reasoning in a form a user can follow and links to the record.

An explanation never takes the reader through a task and never lists settings. A sequence that
describes how something works is fine. A list of things to do is a how-to guide.

## 8. Every page

- **It reads on its own.** A reader arrives from search or from a link, so the opening says what
  the page covers.
- **It speaks to the reader as "you".**
- **It links rather than repeats.** A setting is described once, on its reference page, and
  linked from everywhere else.
- **It describes the current release.** What changed, and when, is in the changelog. A page has
  no "new in" notes and no record of how it used to work.

## 9. Enforcement

- Where the repository builds its documentation, the build treats warnings as errors, so a page
  left out of the contents or a broken cross-reference fails it.
- Everything else, including that each page is one type, is checked in review.

## Project additions

### Readers

| Reader | Lives in | Does | Organised by |
|---|---|---|---|
| Portal developer | `developers/` | Builds a research data portal on FairDM and deploys it | type |
| Portal administrator | `administrators/` | Runs a portal: people, roles, content review and configuration checks | type |
| Portal user | `users/` | Adds, edits and publishes research data in a portal | the site's sections |

The portal user's guide follows the sections a portal shows in its navigation: projects,
datasets, samples, measurements and the account pages. Explanation that every reader needs, such
as why FairDM favours configuration over code, lives in `docs/explanation/`.

### Shared reference

Reference that every reader needs, such as the glossary, lives in `docs/reference/`.

---

**Version**: 1.2.0

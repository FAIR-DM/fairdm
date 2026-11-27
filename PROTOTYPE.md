# Prototype: the signed-in dashboard

Branch `prototype-dashboard`, served on the development server at port 8000. Never merged. The
record is the issue at https://github.com/FAIR-DM/fairdm/issues/735.

Seed it with `python manage.py seed_dashboard_prototype` (safe to run again). Every account's
password is `password`:

| Account | What it shows |
|---|---|
| `regular.user@example.com` | A full history: work, tasks waiting, an organization they run, a year of other people using their data |
| `regular.user2@example.com` | A new account holding nothing: the getting-started list and every empty state |
| `data.curator@example.com` | The publication queue |
| `community.manager@example.com` | The people panel |
| `portal.administrator@example.com` | The portal's own setup and its roles |
| `portal.developer@example.com` | API tokens, documentation and table schemas |

## The features

Each entry is a new way for a person to do something. Build order is top to bottom: each needs the
ones above it.

1. **A signed-in person's home page is a dashboard of their own work.** Today `/` shows a signed-in
   person an empty page titled "My Dashboard". On the prototype it greets them in the page's own
   title with a link to their public profile, then shows three ways to start something new, their
   datasets and projects with what they may do with each, their organizations and their tools. Screens: `/` as `regular.user` and
   as `regular.user2`. Models: none. Depends on nothing.
2. **The page tells a person what needs them.** "Needs your attention" lists imports with rows to
   fix or ready to run, requests to join an organization they run, their datasets still missing
   what a reuser needs (by name), and finished datasets that are still private. Each row opens the
   page where the task is done. Screen: `/` as `regular.user`. Models: none. Depends on 1.
3. **A new person is walked from an empty account to a public dataset.** A six-step list (profile,
   project, dataset, data, description, public), each ticked from the database, the next one
   marked. It can be hidden and brought back from Tools. Screen: `/` as `regular.user2`. Model:
   `DashboardState`. Depends on 1.
4. **A person sees how their public data is being used.** Opens and downloads of their public
   datasets by people outside the team, the last 30 days against the 30 before, a weekly chart over
   twelve weeks and the three most opened. Screen: `/` as `regular.user`, panel "Your data in use".
   Model: `RecordUse`, filled by `RecordUseMiddleware`. Depends on 1.
5. **Each portal role gets its own panel of work.** Shown only to people holding the role:
   - Data Curator: public datasets waiting to be published, with readiness, and a full queue page at
     `/dashboard/publication/`.
   - Community Manager: unclaimed profiles, people who may be listed twice, requests to join, new
     accounts this month, each linking to its admin list.
   - Portal Administrator: the portal's own description as a checklist, who holds each role, and
     whether registration is open.
   - Developer: API tokens, the API documentation and every registered type's table schema.

   Screens: `/` as each role account. Models: none. Depends on 1. The four panels are independent of
   each other.
6. **A person sees the community around them.** Separate cards in the side column: Latest news (the
   latest changes to datasets anyone may open, with See all opening `/community/activity/`), This
   month (new datasets, samples added and new members against the month before, and the newest
   members), and the people they work with. Screen: `/` side column, and `/community/activity/`.
   Models: none. Depends on 1.
7. **A person picks up where they left off.** "Pick up where you left off" lists the four projects
   and datasets they last had open, each linking straight back to the page they were on (Samples,
   Descriptions, Imports and so on), with when, and for an unpublished dataset they can edit, what
   it still needs. Screen: `/` as `regular.user`. Model: `RecentRecord`, filled by
   `RecordUseMiddleware`. Depends on 1.

Resolve work, giving nobody a new way:

- The home view's title changes from "My Dashboard" to "Dashboard" and the greeting moves into the
  header band (`fairdm/views/generic.py`, `get_page_title` and `get_page_lead`).

## The shared pieces

| Pattern | Where it occurs | Becomes | Built by |
|---|---|---|---|
| A dataset's readiness checklist | `fairdm/contrib/dashboard/panels.py` `readiness()`, a second copy of `fairdm/core/dataset/plugins.py` `get_readiness` | One function on the dataset, read by the overview plugin and the dashboard | Feature 2 |
| A readiness ring in place of a row's mark | `dashboard/panels/attention.html`, `role_curator.html`, `publication_queue.html` | A Cotton component, `c-overview.ring` | Feature 2, reused by 5 |
| "Still needs X, Y and N more" | `panels.py` `still_needs()` | Part of the readiness function | Feature 2 |
| A count that opens its list (value, label, hint) | `role_community.html`, `role_developer.html` | A Cotton component, `c-dashboard.count` | Feature 5 |
| A record row (mark, title, quiet facts line, figure at the end) | every `dashboard/panels/*.html` row, the overview pages' `ov-rows` | Already the overview's `ov-rows` markup. Make it `c-overview.row` | Feature 1 |
| Portal-wide activity | `panels.py` `PortalActivity`, `views.py` `CommunityActivityView` | `ActivityLines` taking a queryset with no record | Feature 6 |
| Paged list with Http404 past the end | `views.py` both list views, `fairdm/contrib/activity/plugins.py` | Already a pattern. A small mixin | Feature 5 |

## Duplication to remove

- `readiness()` repeats the dataset overview plugin's checklist item by item.
- The three readiness-ring snippets.
- `PortalActivity` overrides `ActivityLines.__init__` only to take a queryset and no record.

## The look

| File | Ported by | Lands in `main` |
|---|---|---|
| `fairdm/templates/fairdm/dashboard.html` | Feature 1 | same path |
| `fairdm/contrib/dashboard/templates/dashboard/panels/start.html`, `work.html`, `organizations.html`, `tools.html` | Feature 1 | same paths |
| `…/panels/attention.html` | Feature 2 | same path |
| `…/panels/getting_started.html` | Feature 3 | same path |
| `…/panels/in_use.html` | Feature 4 | same path |
| `…/panels/role_curator.html`, `role_community.html`, `role_administrator.html`, `role_developer.html`, `…/dashboard/publication_queue.html` | Feature 5 | same paths |
| `…/panels/news.html`, `community.html`, `people.html`, `…/dashboard/community_activity.html` | Feature 6 | same paths |
| `…/panels/pick_up.html` | Feature 7 | same path |
| `fairdm/static/css/fairdm.css`, the block headed "The signed-in dashboard" at the end | Each feature ports its own rules: `.record-portal`, `.dash-start*`, `.dash-stretch`, `.dash-work`, `.dash-tool*` with 1; `.dash-ring`, `.dash-task*` with 2; `.dash-gs*`, `.dash-step*` with 3; `.dash-use*` with 4; `.dash-role*`, `.dash-count*`, `.dash-admin*`, `.dash-dev`, `.dash-schemas*`, `.dash-subhead` with 5; `.dash-pulse*`, `.dash-faces`, `.dash-links` with 6 | same file |

Screens to compare, each at 390 and 1280 wide:

| Screen | Address | Signed in as |
|---|---|---|
| Dashboard, full history | `/` | `regular.user` |
| Dashboard, new account | `/` | `regular.user2` |
| Import dialog | `/`, Import a file | `regular.user` |
| Getting started hidden | `/`, Hide on the list | `regular.user2` |
| Curator panel | `/` | `data.curator` |
| Publication queue | `/dashboard/publication/` | `data.curator` |
| Community Manager panel | `/` | `community.manager` |
| Administrator panel | `/` | `portal.administrator` |
| Developer panel | `/` | `portal.developer` |
| Across the portal | `/community/activity/` | any |

## The data model

| Model | Owned by | Holds |
|---|---|---|
| `dashboard.RecordUse` | Feature 4 | Per record per day: opens and downloads by people outside the record's team |
| `dashboard.DashboardState` | Feature 3 | Per person: whether the getting-started list is hidden |
| `dashboard.RecentRecord` | Feature 7 | Per person per record they hold access to: the last page they had open on it, its address and when |

`RecordUseMiddleware` counts a full-page open of `project:overview` and `dataset:overview`, and a
`?export=` download from the project and dataset sample and measurement tables. Visits by anyone
holding view access on the record are not counted. Those visits instead update the person's
`RecentRecord` for that record, on any of its pages worth going back to.

## Decisions

- No header band. It made the page look like a profile page and like a record's page. The page
  starts with the welcome as its title and "Start something new" under it.
- No Edit profile button on the dashboard. The one profile link reads "Your public profile".
- No card inside a card. Latest news is its own card at the top of the side column, with See all in
  the card's heading. The people the person works with are their own card, not part of This month.
- The portal's figures card is titled "This month", not the portal's name.
- A "Pick up where you left off" panel takes the person back to the page they were last on.

## Decided on my own

- The dashboard reuses the overview page's wide and side columns and its panels, rows and rings,
  so it reads as part of the same portal.
- Pick up sits straight under Start something new, and lists four records. A person who has opened
  none of their records yet gets their most recently changed ones.
- Latest news draws the activity entries straight into its card, because the activity feed
  component wraps itself in a card of its own.
- The wide column runs from what to do next to what has happened. Work before community on a phone.
- Getting started shows only until every step is done, and never to an account that already has
  data unless it still has steps left. It can be hidden and brought back.
- Opens and downloads count only people outside the team, so a person never reads their own visits
  as interest.
- "Needs your attention" holds at most three dataset rows, so imports and requests are never pushed
  off the panel.
- Each row in a record list carries one state mark (published, public or private). What the person
  may do with it is plain text in the facts line.
- Role panels are titled by the work ("Waiting to be published"), with the role named in a chip.
- The Tools panel leaves out a user-guide link: `/docs/` is not served on a development server, and
  the navbar already links the documentation.

## Faked or skipped

| What | Has to be done properly by |
|---|---|
| Opens and downloads are raw counts. No bot filtering, no double-click rule, no unique-visitor counting as COUNTER and Make Data Count require | Feature 4 |
| Counting happens in a middleware on every request, synchronously | Feature 4, as a task or a signal from the views themselves |
| The seeded year of opens and downloads is random | Feature 4 |
| The seed spreads records' `added` and people's `date_joined` over the year | Not ported |
| The readiness checklist is a copy of the overview plugin's | Feature 2 |
| No caching. Every panel is a few counts, unmeasured on a large portal | Feature 1 |
| The "people who may be listed twice" count is an exact first-and-last-name match | Feature 5 |
| The Community Manager's links open the admin's lists, not pages of the portal's own | Feature 5 |
| The import dialog is a plain list with no search, so a person with many datasets scrolls | Feature 1 |

## What it replaces

- `fairdm/templates/fairdm/dashboard.html`, which only extended `page_view.html`. Nothing else uses
  it.
- The greeting in `FairDMHomeView.get_page_lead`. No tables dropped.

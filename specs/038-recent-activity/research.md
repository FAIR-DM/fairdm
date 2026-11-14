# Research: show recent activity on project and dataset pages

## Assumptions checked

Checked on 2026-11-13, before the specification was approved.

- **The project page on `main` carries a "Recent activity" card that says the capability is not
  available yet.** True: `fairdm/core/project/templates/project/project_detail.html:170` places
  `c-card.placeholder` titled "Recent activity". The dataset page on `main` has no such card. The
  person and organization pages carry the same placeholder (`contributors/overview/person.html:176`,
  `organization.html:190`), which this feature leaves in place.
- **django-activity-stream is installed in FairDM.** False. `fairdm/conf/settings/addons.py`
  already defines `ACTSTREAM_SETTINGS`, but `actstream` is in neither the dependencies nor
  `INSTALLED_APPS`: in the running development container, `actstream` and `mvp_community` cannot be
  imported. The feature adds both.
- **The recent-activity component can show a project's activity together with its datasets'.**
  False as published. django-mvp-community 0.1.4's `cotton/mvp_community/activity/recent.html` with
  `object` reads django-activity-stream's `any` stream, which holds only the actions naming that
  object as actor, target or action object (`actstream/managers.py`, `ActionManager.any`).
  Recorded as a dependency on django-mvp-community (decisions.md, D5).
- **The recent-activity component can keep activity from a viewer who may not open its record.**
  False. Every stream it reads goes through `ActionManager.public`, which keeps the actions marked
  public and applies no other rule. Recorded in decisions.md, D4 and D5.
- **The activity extra's following page appears in a project that does not include its URLs.**
  False, as wanted: django-mvp-community's Account Center override places the following card only
  when `mvp_community_activity:following` reverses
  (`mvp_community/templates/mvp/account/overview.html:10`).
- **django-mvp-community's extra draws a list of actions handed to it.** True:
  `cotton/mvp_community/activity/feed.html` takes `actions` already in order, and `recent.html`
  draws through it. The change in D5 is to `recent.html`, which today chooses its own actions.
- **Every record carries when it was added**, so past additions can be shown (FR-014). The
  prototype groups samples, measurements and datasets by their `added` field
  (`overview_proto.py:149` on `prototype-overview-pages`).

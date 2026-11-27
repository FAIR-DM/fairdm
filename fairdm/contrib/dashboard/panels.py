"""Everything the signed-in dashboard draws, gathered for one person.

Each panel has one function, returning a dict or ``None`` when the panel has nothing to show.
``dashboard_context`` calls them in page order. Nothing here is cached: the page is read once a
visit and every figure is a handful of indexed counts.
"""

from datetime import timedelta

from actstream.models import Action
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, Sum
from django.db.models.functions import Lower
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from pyecharts import options as opts
from pyecharts.charts import Bar

from fairdm.contrib.activity.lines import ActivityLines, group_days
from fairdm.contrib.activity.receivers import PUBLISHED
from fairdm.contrib.contributors.choices import ContributionLevel
from fairdm.contrib.contributors.models import Affiliation, Contribution, Person
from fairdm.contrib.dashboard.models import DashboardState, RecentRecord, RecordUse
from fairdm.contrib.identity.models import Authority, Identity
from fairdm.contrib.import_export.models import ImportJob
from fairdm.core.dataset.models import Dataset, DatasetDate, DatasetDescription
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.core.vocabularies import ABSTRACT, CREATOR, DESCRIPTION_TYPES
from fairdm.portal_roles import PortalRoles
from fairdm.registry import registry
from fairdm.utils.choices import Visibility

L = ContributionLevel
METHODS = f"{DESCRIPTION_TYPES}/methods"
WEEKS = 12
ROWS = 5


def url(view, *args, **kwargs):
    """Reverse a URL name, or return an empty string when the portal has no such page."""
    try:
        return reverse(view, args=args or None, kwargs=kwargs or None)
    except NoReverseMatch:
        return ""


# --------------------------------------------------------------------------------- readiness


def readiness(dataset):
    """List what a dataset still needs before it can be published, as the overview page does.

    The same items as the dataset overview's checklist, worked out from the database rather
    than from the page's context. The rebuild gives both one source.

    Returns:
        ``items`` (label, done, required, url), ``done``, ``total``, ``required_missing`` and
        ``percent``.
    """
    described = set(
        DatasetDescription.objects.filter(related=dataset).values_list("type_id", flat=True)
    )
    overview = dataset.get_absolute_url()
    items = [
        (_("An abstract describes the data"), _("an abstract"), ABSTRACT in described, True,
         url("dataset:descriptions", uuid=dataset.uuid)),
        (_("The methods are described"), _("the methods"), METHODS in described, True,
         url("dataset:descriptions", uuid=dataset.uuid)),
        (_("At least one creator is credited"), _("a creator"),
         Contribution.objects.filter(dataset=dataset, roles__uri=CREATOR).exists(), True,
         url("dataset:contribution-list", uuid=dataset.uuid)),
        (_("A licence is chosen"), _("a licence"), dataset.license_id is not None, True,
         url("dataset:edit", uuid=dataset.uuid)),
        (_("It holds samples or measurements"), _("its data"),
         Sample.objects.filter(dataset=dataset).exists()
         or Measurement.objects.filter(dataset=dataset).exists(), True,
         url("dataset:imports", uuid=dataset.uuid)),
        (_("The collection period is recorded"), _("the collection period"),
         DatasetDate.objects.filter(related=dataset, type_id=DatasetDate.START_TYPE).exists(),
         True, url("dataset:key-dates", uuid=dataset.uuid)),
        (_("Keywords make it findable"), _("keywords"), dataset.keywords.exists(), False,
         url("dataset:keywords", uuid=dataset.uuid)),
        (_("The dataset is public"), _("to be public"), dataset.visibility == Visibility.PUBLIC, False,
         url("dataset:edit", uuid=dataset.uuid)),
    ]
    rows = [
        {"label": label, "short": short, "done": done, "required": required, "url": link or overview}
        for label, short, done, required, link in items
    ]
    done = sum(1 for row in rows if row["done"])
    return {
        "items": rows,
        "done": done,
        "total": len(rows),
        "percent": round(100 * done / len(rows)),
        "required_missing": [r for r in rows if r["required"] and not r["done"]],
    }


def still_needs(missing):
    """Name what a dataset still needs, the first two by name and the rest as a count."""
    names = [str(m["short"]) for m in missing]
    if not names:
        return ""
    if len(names) == 1:
        return _("Still needs %(first)s") % {"first": names[0]}
    if len(names) == 2:
        return _("Still needs %(first)s and %(second)s") % {"first": names[0], "second": names[1]}
    return ngettext(
        "Still needs %(first)s, %(second)s and %(n)s more",
        "Still needs %(first)s, %(second)s and %(n)s more",
        len(names) - 2,
    ) % {"first": names[0], "second": names[1], "n": len(names) - 2}


# ------------------------------------------------------------------------------------ scope


class Scope:
    """The records one person holds a level on, worked out once for every panel."""

    def __init__(self, person):
        self.person = person
        self.datasets = Dataset.all_objects.with_level(person, L.VIEW)
        self.editable = Dataset.all_objects.with_level(person, L.EDIT)
        self.managed = Dataset.all_objects.with_level(person, L.MANAGE)
        self.projects = Project.objects.with_level(person, L.VIEW)
        self.samples = Sample.objects.filter(dataset__in=self.datasets)
        self.measurements = Measurement.objects.filter(dataset__in=self.datasets)
        self.public = self.datasets.filter(visibility=Visibility.PUBLIC)


def holds(person, role):
    return PortalRoles.is_held_by(person, role)


# ----------------------------------------------------------------------------------- header


def header(person, scope):
    returning = scope.datasets.exists() or scope.projects.exists()
    name = person.first_name or person.get_full_name() or person.email
    return {
        "title": (_("Welcome back, %(name)s") if returning else _("Welcome, %(name)s")) % {"name": name},
        "profile_url": person.get_absolute_url(),
        "edit_url": url("contributor:overview-update", uuid=person.uuid),
        "returning": returning,
    }


# ------------------------------------------------------------------------------ start new


def start_new(scope):
    editable = list(scope.editable.select_related("project").order_by("-modified")[:12])
    return {
        "editable": [
            {"name": d.name, "project": d.project, "url": url("dataset:imports", uuid=d.uuid)}
            for d in editable
        ],
        "create_project": url("project-create"),
        "create_dataset": url("dataset-create"),
    }


# ------------------------------------------------------------------------- getting started


def getting_started(person, scope):
    state = DashboardState.objects.filter(person=person).first()
    first_dataset = scope.editable.order_by("-modified").first()
    ready_one = any(
        not readiness(d)["required_missing"] for d in scope.managed.order_by("-modified")[:10]
    )
    steps = [
        {
            "label": _("Complete your profile"),
            "hint": _("Add your ORCID iD and the organization you work for, so your credit finds you."),
            "done": bool(person.orcid() and person.primary_affiliation()),
            "url": url("contributor:overview-update", uuid=person.uuid),
        },
        {
            "label": _("Start a project"),
            "hint": _("Optional. A project groups the datasets of one grant or collaboration."),
            "done": scope.projects.exists(),
            "url": url("project-create"),
            "optional": True,
        },
        {
            "label": _("Create a dataset"),
            "hint": _("The body of data you will share and cite."),
            "done": scope.editable.exists(),
            "url": url("dataset-create"),
        },
        {
            "label": _("Add samples and measurements"),
            "hint": _("Import a spreadsheet, or add them one at a time."),
            "done": scope.samples.exists() or scope.measurements.exists(),
            "url": url("dataset:imports", uuid=first_dataset.uuid) if first_dataset else url("dataset-create"),
        },
        {
            "label": _("Describe it for reuse"),
            "hint": _("An abstract, the methods, a licence and who made it."),
            "done": ready_one,
            "url": first_dataset.get_absolute_url() if first_dataset else url("dataset-create"),
        },
        {
            "label": _("Make it public"),
            "hint": _("So others in the community can find it."),
            "done": scope.managed.filter(visibility=Visibility.PUBLIC).exists(),
            "url": url("dataset:edit", uuid=first_dataset.uuid) if first_dataset else url("dataset-create"),
        },
    ]
    done = sum(1 for s in steps if s["done"])
    if done == len(steps):
        return None
    if state and state.getting_started_hidden:
        return {"hidden": True, "done": done, "total": len(steps), "hide_url": url("dashboard:hide-getting-started")}
    current = next((s for s in steps if not s["done"] and not s.get("optional")), None)
    for step in steps:
        step["current"] = step is current
    return {"steps": steps, "done": done, "total": len(steps), "hide_url": url("dashboard:hide-getting-started")}


# --------------------------------------------------------------------------- needs attention


IMPORT_TASKS = {
    ImportJob.Status.PROBLEMS: _("Fix the rows that need changes in %(file)s"),
    ImportJob.Status.CHECKED: _("Import %(file)s, which is checked and ready"),
    ImportJob.Status.FAILED: _("Upload %(file)s again, it could not be read"),
}


def attention(person, scope):
    rows = []
    jobs = (
        ImportJob.objects.filter(created_by=person, status__in=list(IMPORT_TASKS))
        .select_related("dataset")
        .order_by("-created")[:3]
    )
    for job in jobs:
        rows.append({
            "kind": "import",
            "icon": "import" if job.status != ImportJob.Status.FAILED else "warning",
            "label": IMPORT_TASKS[job.status] % {"file": job.filename},
            "sub": job.dataset.name,
            "when": job.created,
            "url": job.get_absolute_url(),
            "tone": "warning" if job.status != ImportJob.Status.CHECKED else "info",
        })
    run = Affiliation.objects.filter(
        person=person,
        type__gte=Affiliation.MembershipType.ADMIN,
        end_date__isnull=True,
    ).values("organization")
    waiting = (
        Affiliation.objects.filter(organization__in=run, type=Affiliation.MembershipType.PENDING)
        .values("organization", "organization__uuid", "organization__name")
        .annotate(n=Count("pk"))
    )
    for org in waiting:
        rows.append({
            "kind": "members",
            "icon": "people",
            "label": ngettext(
                "Answer %(n)s request to join %(org)s",
                "Answer %(n)s requests to join %(org)s",
                org["n"],
            ) % {"n": org["n"], "org": org["organization__name"]},
            "sub": _("You run this organization"),
            "url": url("contributor:organization-members", uuid=org["organization__uuid"]),
            "tone": "info",
        })
    for dataset in scope.managed.filter(published=False).order_by("-modified")[:6]:
        ready = readiness(dataset)
        missing = ready["required_missing"]
        if missing:
            rows.append({
                "kind": "readiness",
                "icon": "dataset",
                "label": _("Finish describing %(name)s") % {"name": dataset.name},
                "sub": still_needs(missing),
                "url": missing[0]["url"],
                "ring": ready,
            })
        elif dataset.visibility == Visibility.PRIVATE:
            rows.append({
                "kind": "public",
                "icon": "unlock",
                "label": _("Make %(name)s public") % {"name": dataset.name},
                "sub": _("Everything a reuser needs is in place"),
                "url": url("dataset:edit", uuid=dataset.uuid),
                "ring": ready,
            })
        if sum(1 for r in rows if r["kind"] in ("readiness", "public")) >= 3:
            break
    return rows


# ------------------------------------------------------------------------------ pick up


PICK_UP = 4


def pick_up(person, scope):
    """The records the person last had open, newest first, each linking to the page they were on.

    A dataset they can edit that is not yet published also says what it still needs. Someone
    who has opened nothing yet gets their most recently changed records instead.
    """
    kinds = {
        ContentType.objects.get_for_model(Dataset).pk: ("dataset", scope.datasets),
        ContentType.objects.get_for_model(Project).pk: ("project", scope.projects),
    }
    recents = list(RecentRecord.objects.filter(person=person).order_by("-seen")[: PICK_UP * 2])
    found = {}
    for ct, (kind, qs) in kinds.items():
        ids = [r.object_id for r in recents if r.content_type_id == ct]
        found.update({(ct, o.pk): o for o in qs.filter(pk__in=ids)})
    rows = []
    for recent in recents:
        record = found.get((recent.content_type_id, recent.object_id))
        if record is None:
            continue
        rows.append({"kind": kinds[recent.content_type_id][0], "record": record,
                     "page": recent.page, "url": recent.path, "seen": recent.seen})
        if len(rows) == PICK_UP:
            break
    if not rows:
        changed = [("dataset", d) for d in scope.editable.order_by("-modified")[:PICK_UP]]
        changed += [("project", p) for p in Project.objects.with_level(person, L.EDIT).order_by("-modified")[:PICK_UP]]
        changed.sort(key=lambda kr: kr[1].modified, reverse=True)
        rows = [{"kind": k, "record": r, "page": "", "url": r.get_absolute_url(), "changed": r.modified}
                for k, r in changed[:PICK_UP]]
    editable = set(scope.editable.values_list("pk", flat=True))
    for row in rows:
        record = row["record"]
        if row["kind"] == "dataset" and not record.published and record.pk in editable:
            row["still_needs"] = still_needs(readiness(record)["required_missing"])
    return rows or None


# ------------------------------------------------------------------------------ your work


def your_work(person, scope):
    datasets = scope.datasets.select_related("project", "license").order_by("-modified")
    projects = scope.projects.order_by("-modified")
    dataset_rows = list(datasets.annotate(
        n_samples=Count("samples", distinct=True),
        n_measurements=Count("measurements", distinct=True),
    )[:ROWS])
    project_rows = list(projects.annotate(n_datasets=Count("datasets", distinct=True))[:ROWS])

    def access(rows, editable, managed):
        can_edit = set(editable.filter(pk__in=[r.pk for r in rows]).values_list("pk", flat=True))
        can_manage = set(managed.filter(pk__in=[r.pk for r in rows]).values_list("pk", flat=True))
        for row in rows:
            row.access = (
                _("You manage it") if row.pk in can_manage
                else _("You can edit it") if row.pk in can_edit
                else _("You can view it")
            )
        return rows

    return {
        "datasets": access(dataset_rows, scope.editable, scope.managed),
        "dataset_count": datasets.count(),
        "projects": access(
            project_rows,
            Project.objects.with_level(person, L.EDIT),
            Project.objects.with_level(person, L.MANAGE),
        ),
        "project_count": projects.count(),
        "datasets_url": url("contributor:contributor-datasets", uuid=person.uuid),
        "projects_url": url("contributor:contributor-projects", uuid=person.uuid),
    }


# -------------------------------------------------------------------------------- in use


def data_in_use(scope):
    """Opens and downloads of the person's public projects and datasets.

    Returns ``None`` when they hold no public dataset: nothing could have been counted.
    """
    if not scope.public.exists():
        return None
    today = timezone.localdate()
    dataset_type = ContentType.objects.get_for_model(Dataset)
    uses = RecordUse.objects.filter(
        content_type=dataset_type, object_id__in=scope.public.values("pk")
    )

    def total(since, until):
        found = uses.filter(day__gt=since, day__lte=until).aggregate(v=Sum("views"), e=Sum("exports"))
        return found["v"] or 0, found["e"] or 0

    views, exports = total(today - timedelta(days=30), today)
    views_before, exports_before = total(today - timedelta(days=60), today - timedelta(days=30))

    def change(now, before):
        if not before:
            return {"change": "", "direction": "flat"}
        moved = round(100 * (now - before) / before)
        return {
            "change": f"{abs(moved)}%",
            "direction": "up" if moved > 0 else "down" if moved < 0 else "flat",
        }

    start = today - timedelta(weeks=WEEKS) + timedelta(days=1)
    weekly_views, weekly_exports, labels = [0] * WEEKS, [0] * WEEKS, []
    for week in range(WEEKS):
        first = start + timedelta(weeks=week)
        labels.append(first.strftime("%-d %b"))
    for row in uses.filter(day__gte=start).values("day").annotate(v=Sum("views"), e=Sum("exports")):
        week = (row["day"] - start).days // 7
        weekly_views[week] += row["v"]
        weekly_exports[week] += row["e"]
    chart = (
        Bar()
        .add_xaxis(labels)
        .add_yaxis(_("Opens"), weekly_views, label_opts=opts.LabelOpts(is_show=False))
        .add_yaxis(_("Downloads"), weekly_exports, label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            legend_opts=opts.LegendOpts(pos_left="left", pos_top="top"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
        )
    )
    chart.options["grid"] = {"left": 8, "right": 8, "top": 40, "bottom": 8, "containLabel": True}
    top = (
        uses.filter(day__gt=today - timedelta(days=30))
        .values("object_id")
        .annotate(v=Sum("views"), e=Sum("exports"))
        .order_by("-v")[:3]
    )
    names = {d.pk: d for d in Dataset.all_objects.filter(pk__in=[t["object_id"] for t in top])}
    most = [
        {"dataset": names[t["object_id"]], "views": t["v"], "exports": t["e"]}
        for t in top
        if t["object_id"] in names
    ]
    return {
        "views": views,
        "exports": exports,
        "views_change": change(views, views_before),
        "exports_change": change(exports, exports_before),
        "chart": chart,
        "chart_text": _(
            "Opens and downloads of your public datasets in each of the last %(n)s weeks: "
            "%(views)s opens and %(exports)s downloads in all."
        ) % {"n": WEEKS, "views": sum(weekly_views), "exports": sum(weekly_exports)},
        "most": most,
        "public_count": scope.public.count(),
    }


# ------------------------------------------------------------------------------- roles


def curator_panel():
    queue = Dataset.all_objects.filter(visibility=Visibility.PUBLIC, published=False)
    since = timezone.now() - timedelta(days=30)
    published = Action.objects.filter(
        verb=PUBLISHED,
        timestamp__gte=since,
        actor_content_type=ContentType.objects.get_for_model(Dataset),
    ).count()
    rows = []
    for dataset in queue.select_related("project").order_by("modified")[:ROWS]:
        rows.append({"dataset": dataset, "ready": readiness(dataset)})
    return {
        "role": PortalRoles.DATA_CURATOR.label,
        "count": queue.count(),
        "published": published,
        "rows": rows,
        "more_url": url("dashboard:publication-queue"),
    }


def duplicate_names():
    return (
        Person.objects.annotate(f=Lower("first_name"), l=Lower("last_name"))
        .exclude(last_name="")
        .values("f", "l")
        .annotate(n=Count("pk"))
        .filter(n__gt=1)
    )


def community_manager_panel():
    since = timezone.now() - timedelta(days=30)
    changelist = url("admin:contributors_person_changelist")
    return {
        "role": PortalRoles.COMMUNITY_MANAGER.label,
        "rows": [
            {
                "value": Person.objects.filter(is_claimed=False).count(),
                "label": _("Profiles nobody can sign in to"),
                "hint": _("Credited people who have not claimed their profile. You keep them up to date."),
                "url": f"{changelist}?is_claimed__exact=0" if changelist else "",
            },
            {
                "value": sum(row["n"] for row in duplicate_names()),
                "label": _("People who may be listed twice"),
                "hint": _("Profiles sharing a first and last name. Merge them when they are one person."),
                "url": changelist,
            },
            {
                "value": Affiliation.objects.filter(type=Affiliation.MembershipType.PENDING).count(),
                "label": _("Requests to join an organization"),
                "hint": _("Waiting for the organization, or for you."),
                "url": (url("admin:contributors_affiliation_changelist") + "?type__exact=0")
                if url("admin:contributors_affiliation_changelist") else "",
            },
            {
                "value": Person.objects.filter(date_joined__gte=since, is_active=True, is_claimed=True).count(),
                "label": _("New accounts this month"),
                "hint": _("Say hello, and point them at a project they could join."),
                "url": url("people-list"),
            },
        ],
    }


def administrator_panel():
    identity = Identity.get_solo()
    authority = Authority.get_solo()
    identity_url = url("admin:identity_identity_changelist")
    authority_url = url("admin:identity_authority_changelist")
    items = [
        {"label": _("The portal has a name"), "done": bool(identity.safe_translation_getter("name")), "url": identity_url, "required": True},
        {"label": _("It says what it is for"), "done": bool(identity.safe_translation_getter("description")), "url": identity_url, "required": True},
        {"label": _("Keywords describe its subject"), "done": identity.keywords.exists(), "url": identity_url, "required": False},
        {"label": _("It has its own logo"), "done": bool(identity.logo_light), "url": identity_url, "required": False},
        {"label": _("Who runs it is named"), "done": bool(authority.safe_translation_getter("name")), "url": authority_url, "required": True},
        {"label": _("Their website is linked"), "done": bool(authority.url), "url": authority_url, "required": False},
        {"label": _("A contact address is given"), "done": bool(authority.contact), "url": authority_url, "required": True},
    ]
    done = sum(1 for i in items if i["done"])
    roles = []
    from django.contrib.auth.models import Group

    groups = {g.name: g for g in Group.objects.filter(name__in=PortalRoles.shipped_names()).annotate(n=Count("user"))}
    for role in PortalRoles.ROLES:
        group = groups.get(role.name)
        roles.append({
            "label": role.label,
            "count": group.n if group else 0,
            "url": url("admin:auth_group_change", group.pk) if group else "",
        })
    return {
        "role": PortalRoles.PORTAL_ADMINISTRATOR.label,
        "setup": {"items": items, "done": done, "total": len(items), "percent": round(100 * done / len(items))},
        "roles": roles,
        "registration": settings.ACCOUNT_ALLOW_REGISTRATION,
        "accounts": Person.objects.filter(is_active=True, is_claimed=True).count(),
    }


def developer_panel(person):
    from knox.models import get_token_model

    tokens = get_token_model().objects.filter(user=person).filter(
        Q(expiry__isnull=True) | Q(expiry__gt=timezone.now())
    )
    types = [
        {"name": model._meta.verbose_name.capitalize(), "kind": _("Sample"), "url": url("table_schema", name=model._meta.model_name)}
        for model in registry.samples
    ] + [
        {"name": model._meta.verbose_name.capitalize(), "kind": _("Measurement"), "url": url("table_schema", name=model._meta.model_name)}
        for model in registry.measurements
    ]
    return {
        "role": PortalRoles.DEVELOPER.label,
        "tokens": tokens.count(),
        "tokens_url": url("account_api_tokens"),
        "docs_url": url("api:api-docs"),
        "types": types,
    }


def role_panels(person):
    panels = []
    if holds(person, PortalRoles.PORTAL_ADMINISTRATOR):
        panels.append(("administrator", administrator_panel()))
    if holds(person, PortalRoles.DATA_CURATOR):
        panels.append(("curator", curator_panel()))
    if holds(person, PortalRoles.COMMUNITY_MANAGER):
        panels.append(("community", community_manager_panel()))
    if holds(person, PortalRoles.DEVELOPER):
        panels.append(("developer", developer_panel(person)))
    return panels


# ---------------------------------------------------------------------------- community


class PortalActivity(ActivityLines):
    """Recent activity across every dataset anyone may open, for the community panel."""

    def __init__(self, datasets, user=None):
        self.record = None
        self.user = user
        self.model = None
        self.datasets = datasets


def everyone_datasets():
    return Dataset.objects.filter(visibility=Visibility.PUBLIC).filter(
        Q(project__isnull=True) | Q(project__visibility=Visibility.PUBLIC)
    )


def community(person, portal_name):
    today = timezone.now()
    month, before = today - timedelta(days=30), today - timedelta(days=60)
    open_datasets = everyone_datasets()

    def moved(qs, field):
        now = qs.filter(**{f"{field}__gte": month}).count()
        earlier = qs.filter(**{f"{field}__gte": before, f"{field}__lt": month}).count()
        if not earlier:
            return now, "", "flat"
        pct = round(100 * (now - earlier) / earlier)
        return now, f"{abs(pct)}%", "up" if pct > 0 else "down" if pct < 0 else "flat"

    figures = []
    for label, qs, field in (
        (_("New datasets"), open_datasets, "added"),
        (_("Samples added"), Sample.objects.filter(dataset__in=open_datasets), "added"),
        (_("New members"), Person.objects.filter(is_active=True, is_claimed=True), "date_joined"),
    ):
        value, change, direction = moved(qs, field)
        figures.append({"label": label, "value": value, "change": change, "direction": direction})
    newcomers = list(
        Person.objects.filter(is_active=True, is_claimed=True, date_joined__gte=month)
        .exclude(pk=person.pk)
        .order_by("-date_joined")[:8]
    )
    collaborators = list(person.get_collaborators(limit=8))
    lines = PortalActivity(open_datasets)[:6]
    return {
        "name": portal_name,
        "figures": figures,
        "newcomers": newcomers,
        "newcomer_count": Person.objects.filter(is_active=True, is_claimed=True, date_joined__gte=month).exclude(pk=person.pk).count(),
        "collaborators": collaborators,
        "days": group_days(lines),
        "activity_url": url("dashboard:community-activity"),
        "people_url": url("people-list"),
        "organizations_url": url("organization-list"),
    }


def organizations(person):
    rows = []
    for affiliation in (
        person.affiliations.filter(end_date__isnull=True)
        .select_related("organization")
        .order_by("-is_primary", "-type")
    ):
        pending = 0
        if affiliation.type >= Affiliation.MembershipType.ADMIN:
            pending = Affiliation.objects.filter(
                organization=affiliation.organization, type=Affiliation.MembershipType.PENDING
            ).count()
        rows.append({
            "organization": affiliation.organization,
            "type": affiliation.get_type_display(),
            "primary": affiliation.is_primary,
            "pending": pending,
            "members_url": url("contributor:organization-members", uuid=affiliation.organization.uuid),
        })
    return rows


def tools(person):
    return {
        "tokens_url": url("account_api_tokens"),
        "docs_url": url("api:api-docs"),
        "control_room_url": url("admin:dj_control_room_djcontrolroomdashboard_changelist") if person.is_superuser else "",
        "account_url": url("account-center"),
    }


# -------------------------------------------------------------------------------- page


def dashboard_context(request, portal_name):
    person = request.user
    scope = Scope(person)
    use = data_in_use(scope)
    return {
        "dash": {
            "header": header(person, scope),
            "pick_up": pick_up(person, scope),
            "start": start_new(scope),
            "getting_started": getting_started(person, scope),
            "attention": attention(person, scope),
            "roles": role_panels(person),
            "work": your_work(person, scope),
            "use": use,
            "community": community(person, portal_name),
            "organizations": organizations(person),
            "tools": tools(person),
        },
        "has_charts": use is not None,
    }

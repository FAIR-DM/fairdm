"""Gather what happened to a project or a dataset into its recent activity lines.

Additions come from the ``added`` time of the records, never from actions: a sample or a
measurement records nothing when it is made. Edits, publishing and contributors joining
come from the not-public actions ``receivers`` records. Everything is grouped in the
database by record and by day, and each source is cut to the part asked for before the
sources are merged.
"""

from dataclasses import dataclass
from datetime import date, datetime
from itertools import chain, groupby

from actstream.models import Action
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import intcomma
from django.db.models import CharField, Count, Max, Q
from django.db.models.functions import Cast, TruncDate
from django.urls import NoReverseMatch
from django.utils import timezone
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import SafeString
from django.utils.translation import gettext, ngettext

from fairdm.contrib.activity.receivers import EDITED, JOINED, PUBLISHED
from fairdm.contrib.contributors.models import Contributor
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.overview import safe_reverse
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample

PANEL_LINES = 8
"""How many lines the panel shows; one more is read to know whether there are others."""


@dataclass(frozen=True)
class Line:
    """One sentence of recent activity.

    Attributes:
        timestamp: The newest event the line covers.
        day: The portal's day the line falls on.
        kind: ``project``, ``dataset``, ``sample`` or ``measurement``: the colour.
        html: The sentence, safe to render, with every name escaped and linked.
    """

    timestamp: datetime
    day: date
    kind: str
    html: SafeString


@dataclass(frozen=True)
class Day:
    """The lines of one day, newest first.

    Attributes:
        day: The portal's day.
        lines: The day's lines.
    """

    day: date
    lines: tuple


@dataclass(frozen=True)
class Row:
    """What one source found, before the records it names are fetched.

    Attributes:
        timestamp: The newest event the row covers.
        day: The portal's day.
        source: Which source found it: ``samples``, ``measurements``, ``datasets``,
            ``project``, ``edited``, ``published`` or ``joined``.
        model: ``project`` or ``dataset``, the record the row is about.
        record_id: The key of that record.
        count: How many records the row adds up.
        contributor_id: The key of the contributor, for ``joined``.
    """

    timestamp: datetime
    day: date
    source: str
    model: str
    record_id: int
    count: int = 1
    contributor_id: int | None = None

    @property
    def kind(self):
        """Return the colour of the line: the record's own, or the data's."""
        return {"samples": "sample", "measurements": "measurement"}.get(
            self.source, self.model
        )


class ActivityLines:
    """The lines of recent activity of a project or a dataset, for one viewer.

    A project covers itself and the datasets the viewer may see. A dataset covers itself
    alone: the page has already decided the viewer may open it. Samples and measurements
    count only when the viewer may see them, as the page's own figures do. It is a
    sequence that is sliced, never indexed, so the panel and a paginator can both read
    it.

    Args:
        record: The project or the dataset whose page asks.
        user: The viewer, or ``None`` for a visitor.
    """

    def __init__(self, record, user):
        self.record = record
        self.user = user
        self.model = record._meta.model_name
        if isinstance(record, Project):
            self.datasets = Dataset.all_objects.visible_to(user).filter(project=record)
        else:
            self.datasets = Dataset.all_objects.filter(pk=record.pk)

    def __len__(self):
        """Return the number of lines, counted in the database."""
        sources = self.sources()
        return sum(queryset.count() for queryset, _ in sources) + len(
            self.project_created()
        )

    def __getitem__(self, key):
        """Return the lines of a slice, newest first.

        Args:
            key: A slice, whose ``stop`` may be ``None`` for every line.

        Returns:
            The lines of the slice.

        Raises:
            TypeError: For anything but a slice.
        """
        if not isinstance(key, slice):
            raise TypeError("Activity lines are sliced, never indexed.")
        stop = key.stop
        rows = sorted(
            chain(
                self.project_created(),
                *(
                    map(convert, queryset[:stop])
                    for queryset, convert in self.sources()
                ),
            ),
            key=lambda row: row.timestamp,
            reverse=True,
        )[key]
        return self.lines(rows)

    def sources(self):
        """Return each grouped source and the way its rows become ``Row``s."""
        return [
            (self.counted(Sample), self.count_row("samples")),
            (self.counted(Measurement), self.count_row("measurements")),
            (self.new_datasets(), self.dataset_row),
            (self.edits(), self.action_row("edited")),
            (self.publications(), self.action_row("published")),
            (self.joinings(), self.action_row("joined")),
        ]

    def counted(self, model):
        """Group the samples or measurements the viewer may see by dataset and day."""
        return (
            model.objects.visible_to(self.user)
            .filter(dataset__in=self.datasets.values("pk"))
            .order_by()
            .annotate(day=TruncDate("added"))
            .values("dataset_id", "day")
            .annotate(count=Count("pk"), newest=Max("added"))
            .order_by("-newest")
        )

    def new_datasets(self):
        """Return the datasets in the scope, newest first."""
        return self.datasets.order_by("-added").values("pk", "added")

    def project_created(self):
        """Return the project's own creation as a row, on a project's page only."""
        if not isinstance(self.record, Project):
            return []
        return [
            Row(
                self.record.added,
                timezone.localtime(self.record.added).date(),
                "project",
                "project",
                self.record.pk,
            )
        ]

    def in_scope(self, side, projects=True):
        """Return the condition for actions whose actor or target is in the scope.

        Args:
            side: ``actor`` or ``target``.
            projects: Whether a project's page counts the project with its datasets.

        Returns:
            A ``Q`` over the action's content type and object id, which is a string.
        """
        keys = self.datasets.annotate(key=Cast("pk", CharField())).values("key")
        condition = Q(
            **{
                f"{side}_content_type": ContentType.objects.get_for_model(Dataset),
                f"{side}_object_id__in": keys,
            }
        )
        if projects and isinstance(self.record, Project):
            condition |= Q(
                **{
                    f"{side}_content_type": ContentType.objects.get_for_model(Project),
                    f"{side}_object_id": str(self.record.pk),
                }
            )
        return condition

    def actions(self, verb, condition):
        """Group the not-public actions of a verb by who did what to whom and by day."""
        return (
            Action.objects.filter(condition, verb=verb, public=False)
            .order_by()
            .annotate(day=TruncDate("timestamp"))
            .values(
                "actor_content_type",
                "actor_object_id",
                "target_content_type",
                "target_object_id",
                "day",
            )
            .annotate(newest=Max("timestamp"))
            .order_by("-newest")
        )

    def edits(self):
        """Return the edits of the project and the datasets, by record and day."""
        return self.actions(EDITED, self.in_scope("actor"))

    def publications(self):
        """Return the publishing of the datasets, by dataset and day."""
        return self.actions(PUBLISHED, self.in_scope("actor", projects=False))

    def joinings(self):
        """Return the contributors joining the project and the datasets."""
        return self.actions(JOINED, self.in_scope("target"))

    def count_row(self, source):
        """Return the conversion of a grouped count into a row."""

        def convert(found):
            return Row(
                found["newest"],
                found["day"],
                source,
                "dataset",
                found["dataset_id"],
                count=found["count"],
            )

        return convert

    def dataset_row(self, found):
        """Turn a dataset's creation into a row."""
        return Row(
            found["added"],
            timezone.localtime(found["added"]).date(),
            "datasets",
            "dataset",
            found["pk"],
        )

    def action_row(self, source):
        """Return the conversion of a grouped action into a row."""
        names = {
            ContentType.objects.get_for_model(Project).pk: "project",
            ContentType.objects.get_for_model(Dataset).pk: "dataset",
        }

        def convert(found):
            about = "target" if source == "joined" else "actor"
            return Row(
                found["newest"],
                found["day"],
                source,
                names[found[f"{about}_content_type"]],
                int(found[f"{about}_object_id"]),
                contributor_id=(
                    int(found["actor_object_id"]) if source == "joined" else None
                ),
            )

        return convert

    def is_own(self, row):
        """Say whether the row is about the record whose page asks."""
        return row.model == self.model and row.record_id == self.record.pk

    def lines(self, rows):
        """Turn rows into lines, fetching each dataset and contributor named once."""
        dataset_ids = {
            row.record_id
            for row in rows
            if row.model == "dataset" and not self.is_own(row)
        }
        datasets = Dataset.all_objects.in_bulk(dataset_ids) if dataset_ids else {}
        contributor_ids = {
            row.contributor_id for row in rows if row.contributor_id is not None
        }
        contributors = (
            Contributor.objects.in_bulk(contributor_ids) if contributor_ids else {}
        )
        lines = []
        for row in rows:
            record = self.record if self.is_own(row) else datasets.get(row.record_id)
            contributor = contributors.get(row.contributor_id)
            if record is None or (row.source == "joined" and contributor is None):
                continue
            lines.append(
                Line(
                    row.timestamp,
                    row.day,
                    row.kind,
                    self.sentence(row, record, contributor),
                )
            )
        return lines

    def sentence(self, row, record, contributor):
        """Write a row's sentence, naming the record unless it is the page's own."""
        own = self.is_own(row)
        name = None if own else self.link(record)
        count = intcomma(row.count)
        if row.source == "samples":
            if own:
                text = ngettext(
                    "{count} sample added", "{count} samples added", row.count
                )
            else:
                text = ngettext(
                    "{count} sample added to {record}",
                    "{count} samples added to {record}",
                    row.count,
                )
        elif row.source == "measurements":
            if own:
                text = ngettext(
                    "{count} measurement added",
                    "{count} measurements added",
                    row.count,
                )
            else:
                text = ngettext(
                    "{count} measurement added to {record}",
                    "{count} measurements added to {record}",
                    row.count,
                )
        elif row.source == "datasets":
            text = gettext("Dataset created" if own else "Dataset created: {record}")
        elif row.source == "project":
            text = gettext("Project created")
        elif row.source == "edited":
            text = gettext("Details edited" if own else "Details edited: {record}")
        elif row.source == "published":
            text = gettext(
                "Dataset published" if own else "Dataset published: {record}"
            )
        else:
            text = gettext(
                "{contributor} joined" if own else "{contributor} joined {record}"
            )
        return format_html(
            text,
            count=count,
            record=name,
            contributor=self.link(contributor) if contributor else "",
        )

    def link(self, record):
        """Return the record's name linked to its page, or alone when it has none."""
        try:
            url = record.get_absolute_url()
        except NoReverseMatch:
            return conditional_escape(str(record))
        return format_html('<a href="{url}">{name}</a>', url=url, name=str(record))


def group_days(lines):
    """Group lines, newest first, into the days they fall on.

    Args:
        lines: Lines in order, so that each day is contiguous.

    Returns:
        A list of ``Day``, in the order of the lines.
    """
    return [
        Day(day, tuple(group))
        for day, group in groupby(lines, key=lambda line: line.day)
    ]


def recent_activity(record, request):
    """Return the context of the recent activity panel of a project or dataset page.

    Args:
        record: The project or dataset.
        request: The request, whose user decides what the viewer may see.

    Returns:
        ``days``, the newest lines grouped by day, and ``more_url``, the address of
        the full list when there are lines beyond the panel's, and an empty string
        otherwise.
    """
    lines = ActivityLines(record, request.user)[: PANEL_LINES + 1]
    more_url = ""
    if len(lines) > PANEL_LINES:
        more_url = (
            safe_reverse(f"{record._meta.model_name}:activity", uuid=record.uuid) or ""
        )
    return {"days": group_days(lines[:PANEL_LINES]), "more_url": more_url}

"""Field summaries and running totals for the Statistics pages.

Prototype code: it works the figures out in Python from the records it is handed, which is
enough to judge the screens and too slow for a large dataset.
"""

from collections import Counter, OrderedDict
from datetime import date, datetime
from statistics import mean, median
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext
from pyecharts import options as opts
from pyecharts.charts import Bar, Line

from fairdm.core.overview import sentence_case


class FieldSummary:
    """Summarises one field of one record type over a set of records.

    Attributes:
        bins: How many bars a numeric distribution has.
        values_shown: How many values of a categorical field are listed before the rest are
            counted together.
    """

    bins = 12
    values_shown = 5

    NUMERIC = (
        models.IntegerField,
        models.FloatField,
        models.DecimalField,
    )

    def __init__(self, model, name: str, values: list[Any]):
        self.model = model
        self.field = model._meta.get_field(name)
        self.values = [value for value in values if value not in (None, "")]
        self.total = len(values)

    def get_kind(self) -> str:
        """Name the kind of summary the field gets: number, date, category or text."""
        field = self.field
        if field.choices or isinstance(
            field, (models.BooleanField, models.ForeignKey, models.ManyToManyField)
        ):
            return "category"
        if isinstance(field, (models.DateField, models.DateTimeField)):
            return "date"
        if isinstance(field, self.NUMERIC) and not isinstance(field, models.AutoField):
            return "number"
        if self.values and hasattr(self.values[0], "magnitude"):
            return "number"
        return "text"

    def as_dict(self) -> dict[str, Any]:
        """Shape the summary for ``c-statistics.field``."""
        kind = self.get_kind()
        recorded = len(self.values)
        result = {
            "label": sentence_case(str(self.field.verbose_name)),
            "help": str(getattr(self.field, "help_text", "") or ""),
            "kind": kind,
            "kind_label": {
                "number": gettext("Number"),
                "date": gettext("Date"),
                "category": gettext("Category"),
                "text": gettext("Text"),
            }[kind],
            "recorded": recorded,
            "total": self.total,
            "missing_percent": round(100 * (self.total - recorded) / self.total)
            if self.total
            else 0,
            "recorded_percent": round(100 * recorded / self.total) if self.total else 0,
        }
        if recorded:
            result.update(getattr(self, f"summarise_{kind}")())
        return result

    def summarise_text(self) -> dict[str, Any]:
        """A free-text field has nothing beyond its count."""
        return {}

    def summarise_number(self) -> dict[str, Any]:
        """Give the range, mean, median and a distribution, in the field's unit."""
        unit = ""
        numbers = []
        for value in self.values:
            if hasattr(value, "magnitude"):
                unit = f"{value.units:~}"
                value = value.magnitude
            numbers.append(float(value))
        low, high = min(numbers), max(numbers)
        result = {
            "unit": unit,
            "min": low,
            "max": high,
            "mean": mean(numbers),
            "median": median(numbers),
        }
        if low == high:
            return result
        width = (high - low) / self.bins
        counts = [0] * self.bins
        for number in numbers:
            counts[min(int((number - low) / width), self.bins - 1)] += 1
        result["histogram"] = self.get_histogram(
            [
                (
                    f"{self.round_edge(low + i * width)} to "
                    f"{self.round_edge(low + (i + 1) * width)}",
                    count,
                )
                for i, count in enumerate(counts)
            ]
        )
        return result

    @staticmethod
    def round_edge(number: float) -> str:
        """Write the edge of a bar to three significant figures, without an exponent."""
        if abs(number) >= 100:
            return f"{number:,.0f}"
        return f"{number:.3g}"

    def summarise_date(self) -> dict[str, Any]:
        """Give the earliest and latest date and how the values spread over the years."""
        days = [v.date() if isinstance(v, datetime) else v for v in self.values]
        first, last = min(days), max(days)
        result = {"earliest": first, "latest": last}
        if first.year != last.year:
            by_year = Counter(day.year for day in days)
            result["histogram"] = self.get_histogram(
                [
                    (str(year), by_year.get(year, 0))
                    for year in range(first.year, last.year + 1)
                ]
            )
        elif (first.year, first.month) != (last.year, last.month):
            by_month = Counter(day.month for day in days)
            result["histogram"] = self.get_histogram(
                [
                    (
                        date_format(date(first.year, month, 1), "YEAR_MONTH_FORMAT"),
                        by_month.get(month, 0),
                    )
                    for month in range(first.month, last.month + 1)
                ]
            )
        return result

    def summarise_category(self) -> dict[str, Any]:
        """Count the records holding each value, most frequent first."""
        choices = dict(self.field.flatchoices) if self.field.choices else {}
        counts = Counter(
            str(choices.get(value, value))
            if not isinstance(value, bool)
            else (gettext("Yes") if value else gettext("No"))
            for value in self.values
        )
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        top = ranked[0][1]
        shown = ranked[: self.values_shown]
        rest = ranked[self.values_shown :]
        return {
            "distinct": len(ranked),
            "values": [
                {"label": label, "count": count, "percent": round(100 * count / top)}
                for label, count in shown
            ],
            "other_values": len(rest),
            "other_count": sum(count for _label, count in rest),
        }

    @staticmethod
    def get_histogram(bars: list[tuple[str, int]]) -> dict[str, Any]:
        """Shape a distribution for ``c-statistics.histogram``.

        Args:
            bars: ``(label, count)`` pairs in axis order.

        Returns:
            The bars with their height as a share of the tallest, and the text alternative.
        """
        tallest = max(count for _label, count in bars) or 1
        return {
            "bars": [
                {
                    "label": label,
                    "count": count,
                    "percent": round(100 * count / tallest),
                }
                for label, count in bars
            ],
            "first": bars[0][0].split(" to ")[0],
            "last": bars[-1][0].split(" to ")[-1],
            "description": "; ".join(f"{label}: {count}" for label, count in bars),
        }


class RecordStatistics:
    """Works out what a dataset's or a project's Statistics page shows from the records given."""

    @classmethod
    def get_statistics_fields(cls, model) -> list[str]:
        """List the fields of a registered type the pages summarise.

        The type's own ``statistics_fields`` when its registration names them, and otherwise
        the fields its table shows.
        """
        from fairdm.registry import registry

        config = registry.get_for_model(model)
        declared = getattr(config, "statistics_fields", None)
        names = declared if declared is not None else config.resolve_fields("table")
        concrete = {field.name for field in model._meta.concrete_fields}
        skipped = {
            "id",
            "uuid",
            "name",
            "dataset",
            "sample",
            "added",
            "modified",
            "image",
            "options",
        }
        return [name for name in names if name in concrete and name not in skipped]

    @classmethod
    def get_type_summaries(cls, queryset, heading: str) -> list[dict[str, Any]]:
        """Summarise a queryset of samples or of measurements, one entry per registered type.

        Args:
            queryset: The records the viewer may see.
            heading: What the records are, for the type's caption.

        Returns:
            One ``{"name", "count", "kind", "fields"}`` entry per type, largest first.
        """
        from fairdm.registry import registry

        rows = (
            queryset.order_by()
            .values("polymorphic_ctype")
            .annotate(n=models.Count("pk"))
            .order_by("-n")
        )
        result = []
        for row in rows:
            model = ContentType.objects.get_for_id(
                row["polymorphic_ctype"]
            ).model_class()
            if model is None:
                continue
            entry = {
                "name": sentence_case(str(model._meta.verbose_name_plural)),
                "slug": model._meta.model_name,
                "count": row["n"],
                "kind": heading,
                "fields": [],
            }
            if registry.is_registered(model):
                names = cls.get_statistics_fields(model)
                records = model.objects.filter(pk__in=queryset.values("pk"))
                columns = list(records.values_list(*names)) if names else []
                for index, name in enumerate(names):
                    values = [record[index] for record in columns]
                    entry["fields"].append(FieldSummary(model, name, values).as_dict())
            result.append(entry)
        return result

    @staticmethod
    def monthly(dates) -> "OrderedDict[date, int]":
        """Count dates by month, oldest month first."""
        counts = Counter(date(d.year, d.month, 1) for d in dates if d)
        return OrderedDict(sorted(counts.items()))

    @classmethod
    def get_running_totals_chart(cls, series: dict[str, Any]) -> dict[str, Any] | None:
        """Draw running totals by month, one line per series, on one count axis.

        Args:
            series: ``{label: dates}``, the dates each thing was added.

        Returns:
            The chart and its text alternative, or ``None`` when everything falls in one month.
        """
        by_month = {label: cls.monthly(dates) for label, dates in series.items()}
        months = sorted({month for counts in by_month.values() for month in counts})
        if len(months) < 2:
            return None
        first, last = months[0], months[-1]
        months, cursor = [], first
        while cursor <= last:
            months.append(cursor)
            cursor = date(cursor.year + cursor.month // 12, cursor.month % 12 + 1, 1)
        chart = Line().add_xaxis(
            [date_format(month, "YEAR_MONTH_FORMAT") for month in months]
        )
        totals = {}
        for label, counts in by_month.items():
            running, values = 0, []
            for month in months:
                running += counts.get(month, 0)
                values.append(running)
            totals[label] = running
            chart.add_yaxis(
                label,
                values,
                is_symbol_show=False,
                linestyle_opts=opts.LineStyleOpts(width=2),
                label_opts=opts.LabelOpts(is_show=False),
            )
        chart.set_global_opts(
            legend_opts=opts.LegendOpts(pos_left="left", pos_top="top"),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            xaxis_opts=opts.AxisOpts(boundary_gap=False),
        )
        chart.options["grid"] = {
            "left": 8,
            "right": 16,
            "top": 40,
            "bottom": 8,
            "containLabel": True,
        }
        return {
            "chart": chart,
            "description": gettext("From %(first)s to %(last)s: %(totals)s.")
            % {
                "first": date_format(months[0], "YEAR_MONTH_FORMAT"),
                "last": date_format(months[-1], "YEAR_MONTH_FORMAT"),
                "totals": ", ".join(f"{label} {n}" for label, n in totals.items()),
            },
        }

    @staticmethod
    def get_yearly_chart(series: dict[str, dict[int, int]]) -> dict[str, Any] | None:
        """Draw counts per year as grouped bars, one group per year.

        Args:
            series: ``{label: {year: count}}``.

        Returns:
            The chart, its text alternative and the same figures as table rows, or ``None``
            when there is nothing to count.
        """
        years = sorted({year for counts in series.values() for year in counts})
        if not years:
            return None
        years = list(range(years[0], years[-1] + 1))
        chart = Bar().add_xaxis([str(year) for year in years])
        for label, counts in series.items():
            chart.add_yaxis(
                label,
                [counts.get(year, 0) for year in years],
                bar_max_width=24,
                label_opts=opts.LabelOpts(is_show=False),
                itemstyle_opts=opts.ItemStyleOpts(border_radius=[4, 4, 0, 0]),
            )
        chart.set_global_opts(
            legend_opts=opts.LegendOpts(
                is_show=len(series) > 1, pos_left="left", pos_top="top"
            ),
            tooltip_opts=opts.TooltipOpts(trigger="axis"),
            yaxis_opts=opts.AxisOpts(min_interval=1),
        )
        chart.options["grid"] = {
            "left": 8,
            "right": 16,
            "top": 40 if len(series) > 1 else 16,
            "bottom": 8,
            "containLabel": True,
        }
        rows = [
            {
                "year": year,
                "counts": [counts.get(year, 0) for counts in series.values()],
            }
            for year in years
        ]
        return {
            "chart": chart,
            "labels": list(series),
            "rows": rows,
            "description": "; ".join(
                f"{row['year']}: "
                + ", ".join(
                    f"{label} {count}"
                    for label, count in zip(series, row["counts"], strict=True)
                )
                for row in rows
            ),
        }

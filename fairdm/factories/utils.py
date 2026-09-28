"""Faker provider and helpers used by the FairDM factories."""

import logging
import random

import faker
from faker.providers import BaseProvider

logger = logging.getLogger(__name__)


def randint(min_value, max_value):
    """Return a callable that yields a random integer in a range.

    Args:
        min_value: The lowest value the callable can return.
        max_value: The highest value the callable can return.

    Returns:
        A zero-argument callable returning an integer from ``min_value`` to
        ``max_value`` inclusive.
    """
    return lambda: random.randint(min_value, max_value)


class FairDMProvider(BaseProvider):
    """Faker provider with generators for FairDM's geographic, text and date fields."""

    def geo_point(self, **kwargs):
        """Generate a random point as a WKT string.

        Args:
            **kwargs: Passed to ``Faker.latlng``.

        Returns:
            A string of the form ``POINT(<latitude> <longitude>)``.
        """
        fake = faker.Faker()
        coords = fake.latlng(**kwargs)
        return "POINT({} {})".format(*coords)

    def html_paragraphs(self, nb=5, **kwargs):
        """Generate paragraphs of text wrapped in ``<p>`` tags.

        Args:
            nb: The number of paragraphs, or a callable returning it.
            **kwargs: Passed to ``Faker.paragraph``.

        Returns:
            The paragraphs as one HTML string.
        """
        if callable(nb):
            nb = nb()
        fake = faker.Faker()
        pg_list = [fake.paragraph(**kwargs) for _ in range(nb)]
        return "<p>" + "</p><p>".join(pg_list) + "</p>"

    def multiline_text(self, nb=5, **kwargs):
        """Generate paragraphs of plain text separated by blank lines.

        Args:
            nb: The number of paragraphs, or a callable returning it.
            **kwargs: Passed to ``Faker.paragraph``.

        Returns:
            The paragraphs as one string.
        """
        if callable(nb):
            nb = nb()
        fake = faker.Faker()
        pg_list = [fake.paragraph(**kwargs) for _ in range(nb)]
        return "\n\n".join(pg_list)

    def partial_date(self, **kwargs):
        """Generate a date at a random precision.

        Args:
            **kwargs: Passed to ``Faker.date_object``.

        Returns:
            The date formatted as a year, a year and month, or a full date.
        """
        fake = faker.Faker()
        date = fake.date_object(**kwargs)
        fmts = ["%Y", "%Y-%m", "%Y-%m-%d"]
        return date.strftime(random.choice(fmts))

    def random_instance(self, model=None, queryset=None):
        """Pick a random existing record.

        Args:
            model: The model to pick from. All its records are candidates.
            queryset: The records to pick from. Takes precedence over ``model``.

        Returns:
            A random instance, or ``None`` when there are no records.

        Raises:
            ValueError: Neither ``model`` nor ``queryset`` is given.
        """
        if not model and not queryset:
            raise ValueError("Must provide either a model or a queryset")
        qs = (
            (queryset if queryset is not None else model.objects.all())
            if model is not None
            else queryset
        )
        if qs is not None:
            return qs.order_by("?").first()
        return None


# Registered on import so every factory can use the provider.
try:
    from factory.faker import Faker

    Faker.add_provider(FairDMProvider)
except ImportError:
    pass

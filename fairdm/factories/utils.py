import logging
import random

import faker
from faker.providers import BaseProvider

logger = logging.getLogger(__name__)


def randint(min_value, max_value):
    return lambda: random.randint(min_value, max_value)


class FairDMProvider(BaseProvider):
    def geo_point(self, **kwargs):
        fake = faker.Faker()
        coords = fake.latlng(**kwargs)
        return "POINT({} {})".format(*coords)

    def html_paragraphs(self, nb=5, **kwargs):
        if callable(nb):
            nb = nb()
        fake = faker.Faker()
        pg_list = [fake.paragraph(**kwargs) for _ in range(nb)]
        return "<p>" + "</p><p>".join(pg_list) + "</p>"

    def multiline_text(self, nb=5, **kwargs):
        """Generate a multi-line string of paragraphs."""
        if callable(nb):
            nb = nb()
        fake = faker.Faker()
        pg_list = [fake.paragraph(**kwargs) for _ in range(nb)]
        return "\n\n".join(pg_list)

    def partial_date(self, **kwargs):
        fake = faker.Faker()
        date = fake.date_object(**kwargs)
        fmts = ["%Y", "%Y-%m", "%Y-%m-%d"]
        return date.strftime(random.choice(fmts))

    def random_instance(self, model=None, queryset=None):
        if not model and not queryset:
            raise ValueError("Must provide either a model or a queryset")
        qs = (queryset if queryset is not None else model.objects.all()) if model is not None else queryset
        if qs is not None:
            return qs.order_by("?").first()
        return None


# Register the custom provider with factory_boy's Faker
# This registration happens when this module is imported
try:
    from factory.faker import Faker

    Faker.add_provider(FairDMProvider)
except ImportError:
    # Fallback if factory_boy is not available
    pass

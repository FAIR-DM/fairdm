import logging
import random

import faker
from faker.providers import BaseProvider

logger = logging.getLogger(__name__)


def randint(min_value, max_value):
    return lambda: random.randint(min_value, max_value)


def apply_optional_image(obj, create, extracted, **image_kwargs):
    """Fill ``obj.image`` per the opt-in convention the core and contributor
    factories use (issue #323): omitted or falsy touches no disk, ``image=True``
    generates a placeholder JPEG sized by ``image_kwargs`` (``width``,
    ``height``, ``color``), and any other value is used as the file directly.

    Called from each factory's own ``image`` ``@factory.post_generation`` hook.
    A declared ``factory.django.ImageField`` can't express "opt-in" on its
    own — a declared field is always evaluated, so ``image=True`` would just
    assign the literal ``True`` to the model field rather than being read as
    a request for a generated one.
    """
    if not create or not extracted:
        return

    if extracted is True:
        from io import BytesIO

        from django.core.files.base import ContentFile
        from PIL import Image

        width = image_kwargs.get("width", 100)
        height = image_kwargs.get("height", width)
        color = image_kwargs.get("color", "blue")
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=color).save(buffer, format="JPEG")
        obj.image.save("placeholder.jpg", ContentFile(buffer.getvalue()), save=True)
    else:
        obj.image = extracted
        obj.save(update_fields=["image"])


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
        qs = (
            (queryset if queryset is not None else model.objects.all())
            if model is not None
            else queryset
        )
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

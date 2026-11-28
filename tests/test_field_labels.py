"""Every model field has a ``verbose_name`` and ``help_text``.

They are translatable everywhere but in the demo app, which is never translated.
"""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.utils.functional import Promise

TESTS_DIRECTORY = Path(settings.BASE_DIR) / "tests"

# Fields a dependency declares and the model inherits, which this repository cannot
# give labels without redeclaring them. Each entry names the dependency. The second
# test fails for an entry that gained both labels, so take it out then.
THIRD_PARTY_FIELDS: dict[tuple[str, str], str] = {
    ("contributors.Contribution", "order"): "django-ordered-model",
    ("contributors.Contributor", "polymorphic_ctype"): "django-polymorphic",
    ("contributors.Person", "date_joined"): "Django's AbstractUser",
    ("contributors.Person", "first_name"): "Django's AbstractUser",
    ("contributors.Person", "last_login"): "Django's AbstractBaseUser",
    ("contributors.Person", "last_name"): "Django's AbstractUser",
    ("contributors.Person", "password"): "Django's AbstractBaseUser",
    ("fairdm.TaggedItem", "content_type"): "django-taggit",
    ("fairdm.TaggedItem", "tag"): "django-taggit",
    ("identity.AuthorityTranslation", "language_code"): "django-parler",
    ("identity.AuthorityTranslation", "master"): "django-parler",
    ("identity.IdentityTranslation", "language_code"): "django-parler",
    ("identity.IdentityTranslation", "master"): "django-parler",
    ("measurement.Measurement", "polymorphic_ctype"): "django-polymorphic",
    ("sample.Sample", "polymorphic_ctype"): "django-polymorphic",
}

DEMO_DIRECTORY = Path(settings.BASE_DIR) / "demo"


def labelled_wrongly():
    """Return the fields missing a label or help text.

    A package field counts when its own declaration gives both ``verbose_name`` and
    ``help_text`` as lazy translations. A field of the demo app counts when it gives
    both as text, because the demo app is never translated. The name Django derives
    from the field name does not count, and neither does an automatic primary key or a
    parent link.

    Returns:
        A dict of model label to the set of field names that lack one or both.
    """
    missing = {}
    for model in apps.get_models():
        directory = Path(model._meta.app_config.path)
        if TESTS_DIRECTORY in directory.parents or "site-packages" in directory.parts:
            continue
        in_demo = directory == DEMO_DIRECTORY
        fields = [*model._meta.local_fields, *model._meta.local_many_to_many]
        for field in fields:
            if field.auto_created:
                continue
            if in_demo:
                labelled = (
                    isinstance(field._verbose_name, str)
                    and bool(field._verbose_name)
                    and isinstance(field.help_text, str)
                    and bool(field.help_text)
                )
            else:
                labelled = isinstance(field._verbose_name, Promise) and isinstance(
                    field.help_text, Promise
                )
            if not labelled:
                missing.setdefault(model._meta.label, set()).add(field.name)
    return missing


class TestFieldLabels:
    def test_every_field_has_a_verbose_name_and_help_text(self):
        new = {
            label: sorted(
                name for name in names if (label, name) not in THIRD_PARTY_FIELDS
            )
            for label, names in labelled_wrongly().items()
            if any((label, name) not in THIRD_PARTY_FIELDS for name in names)
        }

        assert not new, (
            "These fields have no verbose_name or help_text "
            "(gettext_lazy in the package, plain text in the demo app), written on "
            f"the field: {new}"
        )

    def test_a_field_that_gained_its_labels_is_taken_off_the_exclusions(self):
        missing = labelled_wrongly()
        fixed = sorted(
            f"{label}.{name}"
            for label, name in THIRD_PARTY_FIELDS
            if name not in missing.get(label, set())
        )

        assert not fixed, (
            f"Remove these from THIRD_PARTY_FIELDS, they now have both: {fixed}"
        )

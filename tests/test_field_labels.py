"""Every field of every model has a translatable ``verbose_name`` and ``help_text``."""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.utils.functional import Promise

TESTS_DIRECTORY = Path(settings.BASE_DIR) / "tests"

# Fields that were added without a label or a help text, by model label. The list holds what is
# still missing. Adding a field to it hides a defect, so add the label to the field instead and
# take its entry out: the second test fails for an entry that no longer has a gap.
KNOWN_GAPS: dict[str, set[str]] = {
    "contributors.ClaimingAuditLog": {
        "details",
        "failure_reason",
        "ip_address",
        "method",
        "success",
        "timestamp",
    },
    "contributors.Contribution": {
        "order",
    },
    "contributors.Contributor": {
        "polymorphic_ctype",
    },
    "contributors.ContributorIdentifier": {
        "value",
    },
    "contributors.Person": {
        "date_joined",
        "first_name",
        "last_login",
        "last_name",
        "password",
    },
    "dataset.Dataset": {
        "image",
        "name",
        "options",
        "related_literature",
    },
    "dataset.DatasetDate": {
        "related",
        "value",
    },
    "dataset.DatasetDescription": {
        "related",
        "value",
    },
    "dataset.DatasetIdentifier": {
        "related",
        "value",
    },
    "dataset.DatasetLiteratureRelation": {
        "dataset",
        "literature_item",
    },
    "demo.CustomParentSample": {
        "char_field",
    },
    "demo.CustomSample": {
        "big_integer_field",
        "boolean_field",
        "char_field",
        "date_field",
        "date_time_field",
        "decimal_field",
        "float_field",
        "integer_field",
        "positive_integer_field",
        "positive_small_integer_field",
        "small_integer_field",
        "text_field",
        "time_field",
    },
    "demo.ExampleMeasurement": {
        "big_integer_field",
        "boolean_field",
        "char_field",
        "date_field",
        "date_time_field",
        "decimal_field",
        "float_field",
        "integer_field",
        "positive_integer_field",
        "positive_small_integer_field",
        "small_integer_field",
        "text_field",
        "time_field",
    },
    "demo.ICP_MS_Measurement": {
        "analysis_date",
        "concentration_ppb",
        "counts_per_second",
        "dilution_factor",
        "internal_standard",
        "isotope",
        "uncertainty",
        "uncertainty_percent",
        "value",
    },
    "demo.RockSample": {
        "collection_date",
        "hardness_mohs",
        "mineral_content",
        "rock_type",
        "weight_grams",
    },
    "demo.SoilSample": {
        "depth_cm",
        "moisture_content",
        "organic_matter_percent",
        "ph_level",
        "soil_type",
        "texture",
    },
    "demo.WaterSample": {
        "conductivity_us_cm",
        "dissolved_oxygen_mg_l",
        "ph_level",
        "temperature_celsius",
        "turbidity_ntu",
        "water_source",
    },
    "demo.XRFMeasurement": {
        "concentration_ppm",
        "detection_limit_ppm",
        "element",
        "instrument_model",
        "measurement_conditions",
    },
    "fairdm.TaggedItem": {
        "content_type",
        "object_id",
        "tag",
    },
    "identity.AuthorityTranslation": {
        "description",
        "language_code",
        "master",
        "name",
        "short_name",
    },
    "identity.IdentityTranslation": {
        "description",
        "language_code",
        "master",
        "name",
        "short_name",
    },
    "measurement.Measurement": {
        "image",
        "name",
        "options",
        "polymorphic_ctype",
        "uuid",
    },
    "measurement.MeasurementDate": {
        "related",
        "value",
    },
    "measurement.MeasurementDescription": {
        "related",
        "value",
    },
    "measurement.MeasurementIdentifier": {
        "related",
        "value",
    },
    "project.Project": {
        "image",
        "name",
        "options",
        "uuid",
    },
    "project.ProjectDate": {
        "related",
        "value",
    },
    "project.ProjectDescription": {
        "related",
        "value",
    },
    "project.ProjectIdentifier": {
        "related",
        "value",
    },
    "sample.Sample": {
        "image",
        "name",
        "options",
        "polymorphic_ctype",
        "related",
        "uuid",
    },
    "sample.SampleDate": {
        "related",
        "value",
    },
    "sample.SampleDescription": {
        "related",
        "value",
    },
    "sample.SampleIdentifier": {
        "related",
        "value",
    },
    "sample.SampleRelation": {
        "source",
        "target",
        "type",
    },
}


def labelled_wrongly():
    """Return the ``label.field`` of every first-party field missing a lazy label or help text.

    A field counts when its own declaration gives both ``verbose_name`` and ``help_text`` as lazy
    translations. The name Django derives from the field name does not count, and neither does
    an automatic primary key or a parent link.

    Returns:
        A dict of model label to the set of field names that lack one or both.
    """
    missing = {}
    for model in apps.get_models():
        directory = Path(model._meta.app_config.path)
        if TESTS_DIRECTORY in directory.parents or "site-packages" in directory.parts:
            continue
        fields = [*model._meta.local_fields, *model._meta.local_many_to_many]
        for field in fields:
            if field.auto_created:
                continue
            labelled = isinstance(field._verbose_name, Promise) and isinstance(
                field.help_text, Promise
            )
            if not labelled:
                missing.setdefault(model._meta.label, set()).add(field.name)
    return missing


class TestFieldLabels:
    def test_every_field_has_a_lazy_verbose_name_and_help_text(self):
        new = {
            label: sorted(names - KNOWN_GAPS.get(label, set()))
            for label, names in labelled_wrongly().items()
            if names - KNOWN_GAPS.get(label, set())
        }

        assert not new, (
            "These fields have no lazy verbose_name or help_text "
            f"(gettext_lazy, written on the field): {new}"
        )

    def test_a_field_that_gained_its_labels_is_taken_off_the_known_gaps(self):
        missing = labelled_wrongly()
        fixed = {
            label: sorted(names - missing.get(label, set()))
            for label, names in KNOWN_GAPS.items()
            if names - missing.get(label, set())
        }

        assert not fixed, f"Remove these from KNOWN_GAPS, they now have both: {fixed}"

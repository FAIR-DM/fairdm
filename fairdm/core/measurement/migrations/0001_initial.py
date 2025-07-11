# Generated by Django 5.1.6 on 2025-06-20 13:01

import auto_prefetch
import django.db.models.deletion
import django.db.models.manager
import django_bleach.models
import django_lifecycle.mixins
import easy_thumbnails.fields
import fairdm.db.fields
import fairdm.utils.utils
import shortuuid.django_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("dataset", "0001_initial"),
        ("research_vocabs", "0002_alter_concept_unique_together"),
    ]

    operations = [
        migrations.CreateModel(
            name="MeasurementDate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("Created", "Creation date"),
                            ("Destroyed", "Destruction date"),
                            ("Collected", "Collection date"),
                            ("Returned", "Return date"),
                            ("Prepared", "Preparation date"),
                            ("Archival", "Storage date"),
                            ("Restored", "Restoration date"),
                        ],
                        max_length=50,
                    ),
                ),
                ("value", fairdm.db.fields.PartialDateField(verbose_name="date")),
            ],
            options={
                "verbose_name": "date",
                "verbose_name_plural": "dates",
                "ordering": ["value"],
                "abstract": False,
                "default_related_name": "dates",
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="MeasurementDescription",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("SampleCollection", "Collection"),
                            ("SamplePreparation", "Preparation"),
                            ("SampleStorage", "Storage"),
                            ("SampleDestruction", "Destruction"),
                            ("Other", "Other"),
                        ],
                        max_length=50,
                    ),
                ),
                ("value", django_bleach.models.BleachField()),
            ],
            options={
                "verbose_name": "description",
                "verbose_name_plural": "descriptions",
                "abstract": False,
                "default_related_name": "descriptions",
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="MeasurementIdentifier",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("CROSSREF_FUNDER_ID", "Crossref Funder ID"),
                            ("ISNI", "ISNI"),
                            ("ORCID", "ORCID iD"),
                            ("ROR", "ROR"),
                            ("RESEARCHER_ID", "ResearcherID"),
                            ("WIKIDATA", "Wikidata"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "value",
                    models.CharField(
                        db_index=True,
                        max_length=255,
                        unique=True,
                        verbose_name="identifier",
                    ),
                ),
            ],
            options={
                "verbose_name": "identifier",
                "verbose_name_plural": "identifiers",
                "abstract": False,
                "default_related_name": "identifiers",
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name="Measurement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "added",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="The date and time this record was added to the database.",
                        verbose_name="Date added",
                    ),
                ),
                (
                    "modified",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="The date and time this record was last modified.",
                        verbose_name="Last modified",
                    ),
                ),
                (
                    "image",
                    easy_thumbnails.fields.ThumbnailerImageField(
                        blank=True,
                        null=True,
                        upload_to=fairdm.utils.utils.default_image_path,
                        verbose_name="image",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="name")),
                (
                    "options",
                    models.JSONField(blank=True, null=True, verbose_name="options"),
                ),
                (
                    "uuid",
                    shortuuid.django_fields.ShortUUIDField(
                        alphabet=None,
                        editable=False,
                        length=22,
                        max_length=23,
                        prefix="m",
                        unique=True,
                        verbose_name="UUID",
                    ),
                ),
                (
                    "dataset",
                    auto_prefetch.ForeignKey(
                        help_text="The original dataset this measurement first appeared in.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="measurements",
                        to="dataset.dataset",
                        verbose_name="dataset",
                    ),
                ),
                (
                    "keywords",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Controlled keywords for enhanced discoverability",
                        to="research_vocabs.concept",
                        verbose_name="keywords",
                    ),
                ),
                (
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_%(app_label)s.%(class)s_set+",
                        to="contenttypes.contenttype",
                    ),
                ),
            ],
            options={
                "verbose_name": "measurement",
                "verbose_name_plural": "measurements",
                "ordering": ["-modified"],
                "default_related_name": "measurements",
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
            managers=[
                ("objects", django.db.models.manager.Manager()),
                ("prefetch_manager", django.db.models.manager.Manager()),
            ],
        ),
    ]

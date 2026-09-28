"""Manager for loading GIS models from shapefiles."""

import os

from django.contrib.gis.db import models
from django.contrib.gis.utils import LayerMapping

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


class GISManager(models.Manager):
    """Manager that relates GIS records to the sites inside them and loads them from shapefiles."""

    def count_in(self, model, field="geom"):
        """Add every model instance inside each record's polygon to that record's ``sites``.

        Args:
            model: The model whose instances are tested for containment.
            field: The geometry field on ``model``.
        """
        for instance in self.model.objects.all():
            sites = model.objects.filter(**{f"{field}__within": instance.poly})
            print(f"{sites.count()} {model._meta.verbose_name}/s within {instance}")
            instance.sites.add(*sites)

    def load(self, data_dir, verbose=True, strict=True, transform=False):
        """Load the single shapefile in a data directory using the model's ``mapping``.

        Args:
            data_dir: Directory name under this package's ``data`` folder.
            verbose: Print progress while saving.
            strict: Stop at the first error while saving.
            transform: Transform geometries to the model's SRID.

        Raises:
            ValueError: The directory holds no shapefile or more than one.
        """
        data_folder = os.path.join(DATA_DIR, data_dir)
        shp_file = [f for f in os.listdir(data_folder) if f.endswith(".shp")]
        if len(shp_file) == 1:
            lm = LayerMapping(
                self.model,
                os.path.join(data_folder, shp_file[0]),
                self.model.mapping,
                transform=transform,
            )
            lm.save(strict=strict, verbose=verbose)
        elif len(shp_file) > 1:
            raise ValueError("Multiple shapefiles found in directory")
        else:
            raise ValueError("No shapefiles found in directory")

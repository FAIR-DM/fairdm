"""
Collections app for FairDM.

This app provides tabular views for Sample and Measurement sub-types
and plugins that show tabular views related to core objects.
"""

default_app_config = "fairdm.contrib.collections.apps.CollectionsConfig"

# Module-level imports removed to prevent AppRegistryNotReady error
# Import BaseTable, MeasurementTable, SampleTable from .tables where needed

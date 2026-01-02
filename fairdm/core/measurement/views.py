"""Views for the Measurement app."""

from fairdm import plugins

from .models import Measurement

# Get or create the PluggableView for Measurement model
MeasurementDetailView = plugins.registry.get_or_create_view_for_model(Measurement)

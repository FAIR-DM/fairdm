"""Views for the Sample app."""

from fairdm import plugins

from .models import Sample

# Get or create the PluggableView for Sample model
SampleDetailView = plugins.registry.get_or_create_view_for_model(Sample)

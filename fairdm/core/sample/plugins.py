from fairdm.plugins import PluginRegistry

from ..plugins import OverviewPlugin

registry = PluginRegistry(name="sample")


@registry.register()
class Overview(OverviewPlugin):
    fieldsets = []

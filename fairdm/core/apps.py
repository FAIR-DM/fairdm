from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _

from fairdm.config import Authority, Citation


class FairDMCoreConfig(AppConfig):
    name = "fairdm.core"
    label = "fairdm_core"
    verbose_name = _("FairDM")
    authority = Authority(
        name=_("FairDM Core Development"),
        short_name="FairDM",
        website="https://fairdm.org",
    )
    citation = Citation(
        text="FairDM Core Development Team (2021). FairDM: A FAIR Data Management Tool. https://fairdm.org",
        doi="https://doi.org/10.5281/zenodo.123456",
    )
    repository_url = "https://github.com/FAIR-DM/fairdm"

    def register_core_models(self):
        from fairdm.core.models import Measurement, Sample
        from fairdm.registry import registry

        for model in apps.get_models():
            if issubclass(model, Sample | Measurement) and model not in [Sample, Measurement]:
                registry.register(model)

    def register_sample_children(self):
        pass

        # Child models should be registered individually with their own admin classes
        # (either in their app's admin.py or via the registry system)

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from fairdm.registry import Authority, Citation


class FairDMDemoConfig(AppConfig):
    name = "fairdm_demo"
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

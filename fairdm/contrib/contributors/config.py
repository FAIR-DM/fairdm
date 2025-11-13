from django.utils.translation import gettext_lazy as _

from fairdm.registry import Authority, Citation, ModelConfiguration, ModelMetadata

from .filters import ContributorFilter

# Common FairDM metadata for contributor models
fairdm_core_metadata = ModelMetadata(
    authority=Authority(
        name=str(_("FairDM Core Development")),
        short_name="FairDM",
        website="https://fairdm.org",
    ),
    citation=Citation(
        text="FairDM Core Development Team (2021). FairDM: A FAIR Data Management Tool. https://fairdm.org",
        doi="https://doi.org/10.5281/zenodo.123456",
    ),
    repository_url="https://github.com/FAIR-DM/fairdm",
)


# NOTE: Person and Organization are not Sample/Measurement models
# They use the configuration system for other model types


def create_person_config(model):
    """Factory function to create Person configuration."""
    person_metadata = ModelMetadata(
        description=str(
            _(
                "A personal contributor to the creation of a research dataset is an individual who collects, organizes, and curates data for the study. This includes designing data collection methods, gathering information from various sources, and structuring the data for analysis. Their role is crucial in ensuring the dataset is comprehensive, accurate, and aligned with the research objectives."
            )
        ),
        authority=fairdm_core_metadata.authority,
        citation=fairdm_core_metadata.citation,
        repository_url=fairdm_core_metadata.repository_url,
    )
    config = ModelConfiguration(model=model)
    config.metadata = person_metadata
    config.filterset_class = ContributorFilter
    return config


def create_organization_config(model):
    """Factory function to create Organization configuration."""
    org_metadata = ModelMetadata(
        description=str(
            _(
                "An organizational contributor to a research dataset is an entity, such as a research institution, company, or nonprofit, that supports the creation, management, or distribution of the dataset. This can involve providing resources, funding, infrastructure, or access to data sources. Their role is key in facilitating the dataset's development, ensuring its accessibility, and often ensuring compliance with ethical and legal standards."
            )
        ),
        authority=fairdm_core_metadata.authority,
        citation=fairdm_core_metadata.citation,
        repository_url=fairdm_core_metadata.repository_url,
    )
    config = ModelConfiguration(model=model)
    config.metadata = org_metadata
    config.filterset_class = ContributorFilter
    return config

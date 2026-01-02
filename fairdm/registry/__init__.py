"""
FairDM Registry Package - Model registration and configuration system.

This package provides the core registration system for FairDM Sample and Measurement models,
including configuration classes, component factories, and the global registry instance.
"""

from fairdm.registry.config import (
    Authority,
    Citation,
    MeasurementConfig,
    ModelConfiguration,
    ModelMetadata,
    SampleConfig,
)
from fairdm.registry.registry import FairDMRegistry, register, registry

__all__ = [
    "Authority",
    "Citation",
    "FairDMRegistry",
    "MeasurementConfig",
    "ModelConfiguration",
    "ModelMetadata",
    "SampleConfig",
    "register",
    "registry",
]

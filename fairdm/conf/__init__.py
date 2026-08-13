"""
FairDM Configuration Package.

Provides a production-ready Django configuration baseline, layered with
environment overrides selected by the DJANGO_ENV variable, and addon
integration.
"""

from .setup import setup

__all__ = ["setup"]

"""
FairDM Configuration Package.

Provides production-ready Django configuration with profile-based settings
(production, staging, development) and addon integration.
"""

from .setup import setup

__all__ = ["setup"]

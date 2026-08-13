"""
Setup module for conflicting_addon.

Sets ``DEBUG``, a setting FairDM's own ``development.py`` also sets, so a
test can prove this addon's value beats it (layer 3 over layer 2, FR-008).
"""

DEBUG = "addon-value"

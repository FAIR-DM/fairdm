"""
Addon fixture for testing layer precedence (T094, T096).

Its setup module sets ``DEBUG`` — a setting both FairDM's own environment
override (``fairdm/conf/development.py``) and a portal's environment
override commonly set too — so a test can prove the *order* addon settings
apply in, not merely that they land.
"""

__fdm_setup_module__ = "tests.test_conf.conflicting_addon.setup"

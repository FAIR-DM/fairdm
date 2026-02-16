"""
Dummy FairDM addon for testing addon integration.

This package simulates a FairDM addon with a setup module that injects
custom settings into the Django configuration.
"""

# Mark this package as a FairDM addon with a setup module
__fdm_setup_module__ = "tests.test_conf.dummy_addon.setup"

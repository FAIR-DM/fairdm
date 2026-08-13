"""
Addon fixture for testing partial-failure handling (T101, T102).

Its setup module exists and is found by ``find_spec`` — so it passes the
same validation an addon's setup module normally does — but raises partway
through execution, after having already written a setting. Used to prove
such an addon is treated as unloadable rather than left half-applied.
"""

__fdm_setup_module__ = "tests.test_conf.broken_execution_addon.setup"

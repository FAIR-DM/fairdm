"""
Addon fixture for testing the non-production warn-and-skip path (T099, T100).

Names a setup module that does not exist, so ``validate_addon_module``
cannot find it — the same "cannot be loaded" case as ``broken_prod_addon``
in ``test_addons.py``, but as an importable package under this test
package rather than one built dynamically under ``tmp_path``.
"""

__fdm_setup_module__ = "tests.test_conf.unloadable_addon.nonexistent"

"""Setup module for mutating_broken_addon — appends to INSTALLED_APPS in
place, then raises (T113)."""

INSTALLED_APPS += ["tests.test_conf.mutating_broken_addon"]

raise RuntimeError("mutating_broken_addon always raises after mutating in place")

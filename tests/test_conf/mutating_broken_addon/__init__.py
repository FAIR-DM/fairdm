"""Addon fixture whose setup module mutates a container in place, then
raises (T113).

``broken_execution_addon`` rebinds a name before raising, which a shallow
scratch copy would already contain. This one appends to the composed
scope's own ``INSTALLED_APPS``, which a shallow copy shares by reference —
so it proves the scratch scope copies the container rather than the
binding.
"""

__fdm_setup_module__ = "tests.test_conf.mutating_broken_addon.setup"

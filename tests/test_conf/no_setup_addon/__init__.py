"""Addon fixture for an addon that contributes no settings at all (T112).

It defines no ``__fdm_setup_module__``, which is legitimate — an addon may
ship only apps or URLs — so it is warned about and skipped in every
environment rather than treated as unloadable.
"""

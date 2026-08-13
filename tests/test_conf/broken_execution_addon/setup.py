"""
Setup module for broken_execution_addon.

Writes a setting, then raises — simulating an addon whose settings module
imports cleanly but fails partway through execution (edge case, FR-022).
"""

BROKEN_EXECUTION_ADDON_PARTIAL = "partial-write"

raise RuntimeError("broken_execution_addon always raises partway through setup")

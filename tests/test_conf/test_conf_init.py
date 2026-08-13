"""
Tests asserting ``fairdm.conf`` exposes no second configuration-validation
entry point alongside Django's check framework (FR-018).
"""


class TestNoSecondValidationPath:
    """``fairdm.conf``'s public API is ``setup()`` alone (FR-018, research R7)."""

    def test_setup_is_the_only_public_export(self):
        import fairdm.conf

        assert fairdm.conf.__all__ == ["setup"]

    def test_no_validate_services_function_remains(self):
        """The deleted second validation path (D5) does not resurface anywhere
        importable under ``fairdm.conf``."""
        import fairdm.conf.checks

        assert not hasattr(fairdm.conf.checks, "validate_services")

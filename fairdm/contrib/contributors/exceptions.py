"""Exceptions raised by the contributors services."""


class ClaimingError(Exception):
    """Signal an expected, user-facing claiming failure.

    Raised for an inactive person, an already claimed person, or a tampered or
    expired token. Unexpected programmer errors raise ``ValueError`` instead.
    """

class ClaimingError(Exception):
    """Raised by claiming service functions for expected, user-facing failure conditions.

    Distinguishes anticipated claiming failures (banned person, already claimed,
    invalid/expired token) from unexpected programmer errors (which raise ValueError).

    Examples of conditions that raise ClaimingError:
    - person.is_active=False  (target Person is Banned — FR-017)
    - person.is_claimed=True  (Person already claimed)
    - Token HMAC invalid or tampered
    - Token expired (exceeds CLAIM_TOKEN_MAX_AGE)
    """

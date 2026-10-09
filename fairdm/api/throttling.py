"""The limits on how often a caller may use the API.

Each kind of caller has two limits, one over a short window to stop a burst and one over a
day. Every rate is read from ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`` under the scope
named on its class.
"""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class AnonBurstThrottle(AnonRateThrottle):
    """Limit an anonymous caller over a short window."""

    scope = "anon_burst"


class AnonDailyThrottle(AnonRateThrottle):
    """Limit an anonymous caller over a day."""

    scope = "anon_day"


class SignedInThrottle(UserRateThrottle):
    """Count only callers who are signed in, by who they are.

    Django REST framework's own class also counts an anonymous caller, by address. The
    anonymous throttles count those callers, so counting them here would stop them at the
    signed-in rate whenever it is the lower one.
    """

    def get_cache_key(self, request, view):
        """Return the caller's key, or none for an anonymous caller.

        Args:
            request: The request being answered.
            view: The view answering it.

        Returns:
            The cache key counting this person's requests, or ``None`` when the caller
            is not signed in.
        """
        if not (request.user and request.user.is_authenticated):
            return None
        return super().get_cache_key(request, view)


class UserBurstThrottle(SignedInThrottle):
    """Limit a signed-in caller over a short window."""

    scope = "user_burst"


class UserDailyThrottle(SignedInThrottle):
    """Limit a signed-in caller over a day."""

    scope = "user_day"

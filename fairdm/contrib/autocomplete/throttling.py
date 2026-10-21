"""The limits on how often one caller may use the autocomplete addresses.

They count callers the way the API's limits do, and each has a scope of its own, so a person
typing into a search box does not use up an API allowance. Every rate is read from
``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]`` under the scope named on its class. A portal that
replaced that dictionary without these scopes is limited at the class's ``default_rate``.
"""

from django.core.exceptions import ImproperlyConfigured

from fairdm.api.throttling import (
    AnonBurstThrottle,
    AnonDailyThrottle,
    UserBurstThrottle,
    UserDailyThrottle,
)


class DefaultRateMixin:
    """Fall back to the class's ``default_rate`` when the settings lack its scope.

    Attributes:
        default_rate: The rate used when the settings do not give one for the scope.
    """

    default_rate = ""

    def get_rate(self):
        """Return the configured rate, or the default when the scope is not configured.

        Returns:
            The rate as ``"number/period"``.
        """
        try:
            return super().get_rate()
        except ImproperlyConfigured:
            return self.default_rate


class AutocompleteAnonBurstThrottle(DefaultRateMixin, AnonBurstThrottle):
    """Limit a visitor over a short window."""

    scope = "autocomplete_anon_burst"
    default_rate = "60/minute"


class AutocompleteAnonDailyThrottle(DefaultRateMixin, AnonDailyThrottle):
    """Limit a visitor over a day."""

    scope = "autocomplete_anon_day"
    default_rate = "5000/day"


class AutocompleteUserBurstThrottle(DefaultRateMixin, UserBurstThrottle):
    """Limit a signed-in caller over a short window."""

    scope = "autocomplete_user_burst"
    default_rate = "240/minute"


class AutocompleteUserDailyThrottle(DefaultRateMixin, UserDailyThrottle):
    """Limit a signed-in caller over a day."""

    scope = "autocomplete_user_day"
    default_rate = "50000/day"

"""Tests for the request limits of the FairDM API (Feature 011 US6)."""

import pytest
from django.core.cache.backends.locmem import LocMemCache
from django.urls import reverse
from fairdm.api.throttling import (
    AnonBurstThrottle,
    AnonDailyThrottle,
    UserBurstThrottle,
    UserDailyThrottle,
)
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

SCOPES = ("anon_burst", "anon_day", "user_burst", "user_day")

#: A rate nothing in these tests reaches, so a case can set only the rate it is about.
OUT_OF_REACH = {
    "anon_burst": "1000/minute",
    "anon_day": "1000/day",
    "user_burst": "1000/minute",
    "user_day": "1000/day",
}


@pytest.fixture(autouse=True)
def counting_cache(monkeypatch):
    """Give the throttles a cache that stores counts: the test settings use one that stores none."""
    cache = LocMemCache("throttle-test", {})
    cache.clear()
    monkeypatch.setattr(SimpleRateThrottle, "cache", cache)
    yield cache
    cache.clear()


@pytest.fixture
def set_rates(settings, monkeypatch):
    """Return a function that changes the rates in the settings for one test.

    Rates not named stay out of reach, so a case sees only the limit it sets.
    """

    def set_rates(**rates):
        configured = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        for scope, rate in {**OUT_OF_REACH, **rates}.items():
            monkeypatch.setitem(configured, scope, rate)

    return set_rates


@pytest.fixture
def url():
    return reverse("api:project-list")


def passes(client, url, times):
    """Send requests until one is refused, or the number is reached; return the answers."""
    answers = []
    for _ in range(times):
        answers.append(client.get(url).status_code)
        if answers[-1] != 200:
            break
    return answers


@pytest.mark.django_db
class TestLimits:
    def test_an_anonymous_caller_past_the_short_rate_is_refused(
        self, api_client, url, set_rates
    ):
        set_rates(anon_burst="3/minute")

        answers = passes(api_client, url, 5)

        assert answers == [200, 200, 200, 429]

    def test_an_anonymous_caller_past_the_daily_rate_is_refused(
        self, api_client, url, set_rates
    ):
        set_rates(anon_day="3/day")

        answers = passes(api_client, url, 5)

        assert answers == [200, 200, 200, 429]

    @pytest.mark.parametrize("scope", ["anon_burst", "anon_day"])
    def test_a_refusal_says_when_to_try_again(self, api_client, url, set_rates, scope):
        set_rates(**{scope: "1/minute" if scope == "anon_burst" else "1/day"})
        api_client.get(url)

        response = api_client.get(url)

        assert response.status_code == 429
        assert int(response["Retry-After"]) > 0

    def test_a_token_caller_is_not_stopped_at_the_anonymous_rate(
        self, authenticated_client, url, set_rates
    ):
        set_rates(anon_burst="2/minute", user_burst="5/minute")

        answers = passes(authenticated_client, url, 5)

        assert answers == [200] * 5

    def test_a_token_caller_past_the_short_rate_is_refused(
        self, authenticated_client, url, set_rates
    ):
        set_rates(anon_burst="2/minute", user_burst="4/minute")

        answers = passes(authenticated_client, url, 6)

        assert answers == [200, 200, 200, 200, 429]
        assert int(authenticated_client.get(url)["Retry-After"]) > 0

    def test_a_token_caller_past_the_daily_rate_is_refused(
        self, authenticated_client, url, set_rates
    ):
        set_rates(user_day="3/day")

        answers = passes(authenticated_client, url, 5)

        assert answers == [200, 200, 200, 429]

    def test_an_anonymous_caller_is_counted_by_the_anonymous_rates_alone(
        self, api_client, url, set_rates
    ):
        # A signed-in rate below the anonymous one would stop the caller early if it counted
        # anonymous requests by address.
        set_rates(anon_burst="5/minute", user_burst="2/minute", user_day="2/day")

        answers = passes(api_client, url, 7)

        assert answers == [200] * 5 + [429]

    def test_a_signed_in_caller_is_not_counted_by_the_anonymous_rates(
        self, api_client, authenticated_client, url, set_rates
    ):
        set_rates(anon_burst="2/minute", anon_day="2/day")
        passes(authenticated_client, url, 4)

        answers = passes(api_client, url, 3)

        assert answers == [200, 200, 429]

    def test_one_callers_requests_do_not_count_against_another(
        self, authenticated_client, make_token, other_user, url, set_rates
    ):
        _record, value = make_token(other_user)
        other_client = APIClient()
        other_client.credentials(HTTP_AUTHORIZATION=f"Token {value}")
        set_rates(user_burst="2/minute")
        passes(authenticated_client, url, 3)

        answers = passes(other_client, url, 3)

        assert answers == [200, 200, 429]


@pytest.mark.django_db
class TestLimitsAreSettings:
    @pytest.mark.parametrize("scope", SCOPES)
    def test_each_throttle_takes_its_rate_from_the_settings(
        self, settings, set_rates, scope
    ):
        throttle = {
            "anon_burst": AnonBurstThrottle,
            "anon_day": AnonDailyThrottle,
            "user_burst": UserBurstThrottle,
            "user_day": UserDailyThrottle,
        }[scope]
        set_rates(**{scope: "7/hour"})

        assert throttle.scope == scope
        assert throttle().rate == "7/hour"
        assert (
            settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"][scope] == throttle().rate
        )

    def test_the_four_throttles_are_the_ones_the_api_applies(self, settings):
        from rest_framework.settings import api_settings

        applied = {cls.__name__ for cls in api_settings.DEFAULT_THROTTLE_CLASSES}

        assert applied == {
            "AnonBurstThrottle",
            "AnonDailyThrottle",
            "UserBurstThrottle",
            "UserDailyThrottle",
        }
        assert set(settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]) == set(SCOPES)

    @pytest.mark.parametrize(
        ("scope", "rate", "caller", "allowed"),
        [
            ("anon_burst", "4/minute", "anonymous", 4),
            ("anon_day", "5/day", "anonymous", 5),
            ("user_burst", "6/minute", "token", 6),
            ("user_day", "7/day", "token", 7),
        ],
    )
    def test_a_caller_is_stopped_at_the_changed_figure(
        self,
        api_client,
        authenticated_client,
        url,
        set_rates,
        scope,
        rate,
        caller,
        allowed,
    ):
        client = api_client if caller == "anonymous" else authenticated_client
        set_rates(**{scope: rate})

        answers = passes(client, url, allowed + 2)

        assert answers == [200] * allowed + [429]

    def test_the_settings_the_throttles_read_are_the_portals_own(self, settings):
        # The throttles read their rates from the dict the portal's settings hold, so a portal
        # that assigns REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] in its settings changes them.
        assert (
            SimpleRateThrottle.THROTTLE_RATES
            is settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        )

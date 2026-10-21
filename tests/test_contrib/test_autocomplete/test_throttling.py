"""Tests for the request limits on the autocomplete addresses."""

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.cache.backends.locmem import LocMemCache
from django.urls import resolve, reverse
from rest_framework.throttling import SimpleRateThrottle

from fairdm.factories import UserFactory

SCOPES = (
    "autocomplete_anon_burst",
    "autocomplete_anon_day",
    "autocomplete_user_burst",
    "autocomplete_user_day",
)

#: A rate nothing in these tests reaches, so a case can set only the rate it is about.
OUT_OF_REACH = {
    "autocomplete_anon_burst": "1000/minute",
    "autocomplete_anon_day": "1000/day",
    "autocomplete_user_burst": "1000/minute",
    "autocomplete_user_day": "1000/day",
}


def every_address():
    """Return the name of each record address the app registers."""
    from fairdm.contrib.autocomplete import urls

    return [
        f"autocomplete:{kind}-{scope}"
        for kind in urls.RECORD_VIEWS
        for scope in urls.SCOPES
    ]


@pytest.fixture(autouse=True)
def counting_cache(monkeypatch):
    """Give the throttles a cache that stores counts: the test settings use one that stores none."""
    cache = LocMemCache("autocomplete-throttle-test", {})
    cache.clear()
    monkeypatch.setattr(SimpleRateThrottle, "cache", cache)
    yield cache
    cache.clear()


@pytest.fixture
def set_rates(settings, monkeypatch):
    """Return a function that changes the autocomplete rates for one test."""

    def set_rates(**rates):
        configured = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        for scope, rate in {**OUT_OF_REACH, **rates}.items():
            monkeypatch.setitem(configured, scope, rate)

    return set_rates


def statuses(client, url, times, **headers):
    """Send requests until one is refused or the number is reached; return the answers."""
    answers = []
    for _ in range(times):
        answers.append(client.get(url, **headers).status_code)
        if answers[-1] != 200:
            break
    return answers


@pytest.mark.django_db
@pytest.mark.parametrize("address", every_address())
class TestAutocompleteThrottles:
    def test_a_visitor_over_the_burst_rate_is_refused_with_a_retry_time(
        self, client, set_rates, address
    ):
        set_rates(autocomplete_anon_burst="3/minute")
        url = reverse(address)

        answers = statuses(client, url, 6)
        refused = client.get(url)

        assert answers == [200, 200, 200, 429]
        assert refused.status_code == 429
        assert int(refused["Retry-After"]) > 0
        assert refused.json()["results"] == []

    def test_a_visitor_over_the_daily_rate_is_refused(self, client, set_rates, address):
        set_rates(autocomplete_anon_day="2/day")

        assert statuses(client, reverse(address), 5) == [200, 200, 429]

    def test_no_query_runs_once_a_visitor_is_over_the_rate(
        self, rf, set_rates, django_assert_num_queries, address
    ):
        # The view is called directly: the test client wraps the request in a transaction, whose
        # savepoints would count as queries of their own.
        set_rates(autocomplete_anon_burst="1/minute")
        view = resolve(reverse(address)).func
        request = rf.get(reverse(address))
        request.user = AnonymousUser()
        view(request)

        with django_assert_num_queries(0):
            response = view(request)

        assert response.status_code == 429

    def test_signed_in_callers_are_counted_by_account(self, client, set_rates, address):
        set_rates(
            autocomplete_user_burst="2/minute", autocomplete_anon_burst="1/minute"
        )
        url = reverse(address)
        first, second = UserFactory(), UserFactory()

        client.force_login(first)
        first_answers = statuses(client, url, 5, REMOTE_ADDR="10.0.0.9")
        client.force_login(second)
        second_answers = statuses(client, url, 5, REMOTE_ADDR="10.0.0.9")

        assert first_answers == [200, 200, 429]
        assert second_answers == [200, 200, 429]

    def test_a_signed_in_caller_is_not_stopped_at_the_visitor_rate(
        self, client, set_rates, address
    ):
        set_rates(
            autocomplete_anon_burst="1/minute", autocomplete_user_burst="5/minute"
        )
        client.force_login(UserFactory())

        assert statuses(client, reverse(address), 5) == [200] * 5

    def test_another_caller_is_answered_while_one_is_over_the_rate(
        self, client, set_rates, address
    ):
        set_rates(autocomplete_anon_burst="2/minute")
        url = reverse(address)
        assert statuses(client, url, 4, REMOTE_ADDR="10.0.0.1") == [200, 200, 429]

        other = client.get(url, REMOTE_ADDR="10.0.0.2")

        assert other.status_code == 200

    def test_a_portal_without_the_rates_still_limits_the_fields(
        self, client, settings, monkeypatch, address
    ):
        from fairdm.contrib.autocomplete.throttling import AutocompleteAnonBurstThrottle

        rates = settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
        for scope in SCOPES:
            monkeypatch.delitem(rates, scope, raising=False)
        monkeypatch.setattr(AutocompleteAnonBurstThrottle, "default_rate", "2/minute")

        assert statuses(client, reverse(address), 5) == [200, 200, 429]

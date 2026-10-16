"""Behaviour of ``docker/entrypoint.sh``, the start sequence of the base images."""

WEB_STEPS = [
    "python manage.py migrate --noinput",
    "python manage.py collectstatic --noinput",
    "python manage.py compress",
]


class TestWebStart:
    def test_web_runs_the_steps_in_order_then_serves(self, run_entrypoint):
        process, calls = run_entrypoint("web")

        assert process.returncode == 0
        assert calls == [*WEB_STEPS, "gunicorn config.wsgi:application"]

    def test_no_argument_starts_the_web_sequence(self, run_entrypoint):
        process, calls = run_entrypoint()

        assert process.returncode == 0
        assert calls == [*WEB_STEPS, "gunicorn config.wsgi:application"]

    def test_wsgi_app_sets_the_application_gunicorn_serves(self, run_entrypoint):
        process, calls = run_entrypoint("web", WSGI_APP="portal.wsgi:app")

        assert process.returncode == 0
        assert calls[-1] == "gunicorn portal.wsgi:app"

    def test_a_failing_migrate_stops_the_start_and_the_server_never_runs(self, run_entrypoint):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[0], status=3)

        assert process.returncode == 3
        assert calls == [WEB_STEPS[0]]

    def test_a_failing_collectstatic_stops_the_start_before_compress(self, run_entrypoint):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[1], status=4)

        assert process.returncode == 4
        assert calls == WEB_STEPS[:2]

    def test_a_failing_compress_stops_the_start_before_the_server(self, run_entrypoint):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[2], status=5)

        assert process.returncode == 5
        assert calls == WEB_STEPS


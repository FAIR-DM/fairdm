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

    def test_a_failing_migrate_stops_the_start_and_the_server_never_runs(
        self, run_entrypoint
    ):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[0], status=3)

        assert process.returncode == 3
        assert calls == [WEB_STEPS[0]]

    def test_a_failing_collectstatic_stops_the_start_before_compress(
        self, run_entrypoint
    ):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[1], status=4)

        assert process.returncode == 4
        assert calls == WEB_STEPS[:2]

    def test_a_failing_compress_stops_the_start_before_the_server(self, run_entrypoint):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[2], status=5)

        assert process.returncode == 5
        assert calls == WEB_STEPS


class TestWorkerAndPassThrough:
    def test_worker_runs_celery_and_none_of_the_web_steps(self, run_entrypoint):
        process, calls = run_entrypoint("worker")

        assert process.returncode == 0
        assert calls == ["celery --app config worker"]

    def test_celery_app_sets_the_application_the_worker_runs(self, run_entrypoint):
        process, calls = run_entrypoint("worker", CELERY_APP="portal.celery")

        assert process.returncode == 0
        assert calls == ["celery --app portal.celery worker"]

    def test_extra_arguments_reach_celery(self, run_entrypoint):
        process, calls = run_entrypoint(
            "worker", "--loglevel", "INFO", "--concurrency", "2"
        )

        assert process.returncode == 0
        assert calls == ["celery --app config worker --loglevel INFO --concurrency 2"]

    def test_any_other_command_runs_as_given_with_its_arguments(self, run_entrypoint):
        process, calls = run_entrypoint("tool", "shell", "--no-startup")

        assert process.returncode == 0
        assert calls == ["tool shell --no-startup"]

    def test_any_other_command_keeps_its_exit_status(self, run_entrypoint):
        process, calls = run_entrypoint("tool", "check", fail_on="tool check", status=7)

        assert process.returncode == 7
        assert calls == ["tool check"]

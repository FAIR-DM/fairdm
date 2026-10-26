"""Behaviour of ``docker/entrypoint.sh``, the start sequence of the base images."""

import pytest

WEB_STEPS = [
    "python manage.py migrate --noinput",
    "python manage.py collectstatic --noinput",
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

    def test_a_failing_collectstatic_stops_the_start_before_the_server(
        self, run_entrypoint
    ):
        process, calls = run_entrypoint("web", fail_on=WEB_STEPS[1], status=4)

        assert process.returncode == 4
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


class TestBeat:
    def test_beat_runs_celery_beat_and_none_of_the_web_steps(self, run_entrypoint):
        process, calls = run_entrypoint("beat")

        assert process.returncode == 0
        assert calls == ["celery --app config beat"]

    def test_celery_app_sets_the_application_beat_runs(self, run_entrypoint):
        process, calls = run_entrypoint("beat", CELERY_APP="portal.celery")

        assert process.returncode == 0
        assert calls == ["celery --app portal.celery beat"]

    def test_extra_arguments_reach_celery_beat(self, run_entrypoint):
        process, calls = run_entrypoint("beat", "--loglevel", "INFO")

        assert process.returncode == 0
        assert calls == ["celery --app config beat --loglevel INFO"]

    def test_beat_runs_no_start_steps(self, run_entrypoint, tmp_path):
        step = tmp_path / "10-first"
        step.write_text('#!/bin/sh\necho "step 10-first" >> "$STAND_IN_LOG"\n')
        step.chmod(0o755)

        process, calls = run_entrypoint("beat", FAIRDM_START_DIR=str(tmp_path))

        assert process.returncode == 0
        assert calls == ["celery --app config beat"]


class TestStartSteps:
    @pytest.fixture
    def start_dir(self, tmp_path):
        """An empty directory for start steps, named by FAIRDM_START_DIR."""
        directory = tmp_path / "start-steps"
        directory.mkdir()
        return directory

    @pytest.fixture
    def add_step(self, start_dir):
        """Write a step that logs its own name, exiting with ``status``."""

        def add(name, *, executable=True, status=0):
            step = start_dir / name
            step.write_text(
                f'#!/bin/sh\necho "step {name}" >> "$STAND_IN_LOG"\nexit {status}\n'
            )
            step.chmod(0o755 if executable else 0o644)
            return step

        return add

    def test_steps_run_after_collectstatic_and_before_the_server(
        self, run_entrypoint, add_step, start_dir
    ):
        add_step("10-first")

        process, calls = run_entrypoint("web", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 0
        assert calls == [
            *WEB_STEPS,
            "step 10-first",
            "gunicorn config.wsgi:application",
        ]

    def test_steps_run_in_name_order(self, run_entrypoint, add_step, start_dir):
        add_step("30-third")
        add_step("10-first")
        add_step("20-second")

        process, calls = run_entrypoint("web", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 0
        assert calls[2:5] == ["step 10-first", "step 20-second", "step 30-third"]

    def test_a_failing_step_stops_the_start_before_the_server(
        self, run_entrypoint, add_step, start_dir
    ):
        add_step("10-fails", status=9)
        add_step("20-never-runs")

        process, calls = run_entrypoint("web", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 9
        assert calls == [*WEB_STEPS, "step 10-fails"]

    def test_a_step_that_is_not_executable_is_skipped_and_named_on_stderr(
        self, run_entrypoint, add_step, start_dir
    ):
        skipped = add_step("10-no-chmod", executable=False)
        add_step("20-runs")

        process, calls = run_entrypoint("web", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 0
        assert calls == [*WEB_STEPS, "step 20-runs", "gunicorn config.wsgi:application"]
        assert str(skipped) in process.stderr

    def test_an_empty_directory_runs_the_default_sequence_alone(
        self, run_entrypoint, start_dir
    ):
        process, calls = run_entrypoint("web", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 0
        assert calls == [*WEB_STEPS, "gunicorn config.wsgi:application"]

    def test_a_missing_directory_runs_the_default_sequence_alone(
        self, run_entrypoint, start_dir
    ):
        process, calls = run_entrypoint(
            "web", FAIRDM_START_DIR=str(start_dir / "does-not-exist")
        )

        assert process.returncode == 0
        assert calls == [*WEB_STEPS, "gunicorn config.wsgi:application"]

    def test_the_worker_runs_no_steps(self, run_entrypoint, add_step, start_dir):
        add_step("10-first")

        process, calls = run_entrypoint("worker", FAIRDM_START_DIR=str(start_dir))

        assert process.returncode == 0
        assert calls == ["celery --app config worker"]

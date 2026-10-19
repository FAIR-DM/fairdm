"""Behaviour of ``docker/publish.sh``, which publishes the base images of a release."""

import subprocess
from pathlib import Path

import pytest

PUBLISH = Path(__file__).resolve().parents[2] / "docker" / "publish.sh"

REPOSITORY = "registry.example/fairdm"

# A stand-in for the docker command. ``buildx imagetools inspect REF`` answers like a registry:
# found when REF is listed in FAKE_PRESENT, not found when it is not, and a connection error for
# every REF when FAKE_UNREACHABLE is set or for the one named by FAKE_BROKEN_REF. Every call is
# appended to FAKE_LOG, and a push of FAKE_PUSH_FAILS exits 1.
FAKE_DOCKER = """#!/bin/sh
echo "$*" >> "$FAKE_LOG"
if [ "$1 $2 $3" = "buildx imagetools inspect" ]; then
    ref=$4
    if [ -n "${FAKE_UNREACHABLE:-}" ] || [ "$ref" = "${FAKE_BROKEN_REF:-}" ]; then
        echo "ERROR: failed to do request: Head \\"https://$ref\\": connection refused" >&2
        exit 1
    fi
    case " ${FAKE_PRESENT:-} " in
        *" $ref "*) echo "Name: $ref"; exit 0 ;;
    esac
    echo "ERROR: $ref: not found" >&2
    exit 1
fi
if [ "$1" = "push" ] && [ "$2" = "${FAKE_PUSH_FAILS:-}" ]; then
    exit 1
fi
"""


@pytest.fixture
def run_publish(tmp_path):
    """Run ``publish.sh`` with ``docker`` replaced by a stand-in.

    Returns the completed process and the docker commands the script ran, in order. Keyword
    arguments become the stand-in's environment: ``FAKE_PRESENT`` lists the references the
    registry already has.
    """
    fake = tmp_path / "docker"
    fake.write_text(FAKE_DOCKER)
    fake.chmod(0o755)
    log = tmp_path / "docker.log"

    def run(*args, **env):
        process = subprocess.run(  # noqa: S603
            ["/bin/sh", str(PUBLISH), *args],
            cwd=tmp_path,
            env={
                "PATH": "/usr/bin:/bin",
                "DOCKER": str(fake),
                "FAKE_LOG": str(log),
                **env,
            },
            capture_output=True,
            text=True,
            check=False,
        )
        calls = log.read_text().splitlines() if log.exists() else []
        return process, calls

    return run


def pushes(calls):
    return [call for call in calls if call.startswith("push ")]


class TestPublishing:
    def test_pushes_both_tags_when_neither_exists(self, run_publish):
        process, calls = run_publish("1.2.3", REPOSITORY)

        assert process.returncode == 0
        assert pushes(calls) == [
            f"push {REPOSITORY}:1.2.3",
            f"push {REPOSITORY}:1.2.3-dev",
        ]

    def test_each_tag_is_pushed_from_its_own_local_image(self, run_publish):
        process, calls = run_publish(
            "1.2.3",
            REPOSITORY,
            RUNTIME_IMAGE="local-runtime",
            DEVELOPMENT_IMAGE="local-development",
        )

        assert process.returncode == 0
        assert f"tag local-runtime {REPOSITORY}:1.2.3" in calls
        assert f"tag local-development {REPOSITORY}:1.2.3-dev" in calls

    def test_the_repository_defaults_to_the_fairdm_package(self, run_publish):
        process, calls = run_publish("1.2.3")

        assert process.returncode == 0
        assert pushes(calls) == [
            "push ghcr.io/fair-dm/fairdm:1.2.3",
            "push ghcr.io/fair-dm/fairdm:1.2.3-dev",
        ]

    def test_pushes_nothing_when_both_tags_exist(self, run_publish):
        present = f"{REPOSITORY}:1.2.3 {REPOSITORY}:1.2.3-dev"

        process, calls = run_publish("1.2.3", REPOSITORY, FAKE_PRESENT=present)

        assert process.returncode == 0
        assert pushes(calls) == []

    def test_pushes_only_the_development_tag_when_the_release_tag_exists(
        self, run_publish
    ):
        process, calls = run_publish(
            "1.2.3", REPOSITORY, FAKE_PRESENT=f"{REPOSITORY}:1.2.3"
        )

        assert process.returncode == 0
        assert pushes(calls) == [f"push {REPOSITORY}:1.2.3-dev"]

    def test_pushes_only_the_release_tag_when_the_development_tag_exists(
        self, run_publish
    ):
        process, calls = run_publish(
            "1.2.3", REPOSITORY, FAKE_PRESENT=f"{REPOSITORY}:1.2.3-dev"
        )

        assert process.returncode == 0
        assert pushes(calls) == [f"push {REPOSITORY}:1.2.3"]


class TestWhenTheRegistryCannotBeAsked:
    def test_an_unreachable_registry_stops_the_script_before_any_push(
        self, run_publish
    ):
        process, calls = run_publish("1.2.3", REPOSITORY, FAKE_UNREACHABLE="1")

        assert process.returncode != 0
        assert pushes(calls) == []

    def test_an_error_on_the_second_tag_stops_the_script_before_the_first_is_pushed(
        self, run_publish
    ):
        process, calls = run_publish(
            "1.2.3", REPOSITORY, FAKE_BROKEN_REF=f"{REPOSITORY}:1.2.3-dev"
        )

        assert process.returncode != 0
        assert pushes(calls) == []

    def test_a_failing_push_fails_the_script(self, run_publish):
        process, _ = run_publish(
            "1.2.3", REPOSITORY, FAKE_PUSH_FAILS=f"{REPOSITORY}:1.2.3"
        )

        assert process.returncode != 0


class TestArguments:
    def test_a_missing_version_is_refused_without_calling_docker(self, run_publish):
        process, calls = run_publish()

        assert process.returncode == 2
        assert calls == []

"""Behaviour of ``docker/next-version.sh``, which works out the version of an image release."""

import subprocess
from pathlib import Path

import pytest

NEXT_VERSION = Path(__file__).resolve().parents[2] / "docker" / "next-version.sh"


@pytest.fixture
def repository(tmp_path):
    """A git repository with one commit, tagged with whatever tags a test names."""

    def git(*args):
        subprocess.run(  # noqa: S603
            ["git", *args],  # noqa: S607
            cwd=tmp_path,
            check=True,
            capture_output=True,
            env={
                "PATH": "/usr/bin:/bin",
                "GIT_AUTHOR_NAME": "test",
                "GIT_AUTHOR_EMAIL": "test@example.org",
                "GIT_COMMITTER_NAME": "test",
                "GIT_COMMITTER_EMAIL": "test@example.org",
                "HOME": str(tmp_path),
            },
        )

    git("init", "-q")
    git("commit", "-q", "--allow-empty", "-m", "first")

    def tag(*names):
        for name in names:
            git("tag", name)
        return tmp_path

    return tag


def run(directory, bump):
    return subprocess.run(  # noqa: S603
        ["/bin/sh", str(NEXT_VERSION), bump],
        cwd=directory,
        env={"PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )


class TestNextVersion:
    @pytest.mark.parametrize(
        ("bump", "expected"),
        [("patch", "1.10.1"), ("minor", "1.11.0"), ("major", "2.0.0")],
    )
    def test_a_bump_counts_on_from_the_newest_image_release(
        self, repository, bump, expected
    ):
        directory = repository("image-v1.2.3", "image-v1.10.0", "image-v1.9.9")

        result = run(directory, bump)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected

    def test_fairdm_release_tags_are_ignored(self, repository):
        directory = repository("v3.0.0", "image-v1.0.0")

        result = run(directory, "patch")

        assert result.stdout.strip() == "1.0.1"

    def test_with_no_image_release_a_bump_counts_from_zero(self, repository):
        directory = repository("v0.1.0")

        result = run(directory, "patch")

        assert result.stdout.strip() == "0.0.1"

    def test_an_explicit_version_above_the_newest_is_taken_as_given(self, repository):
        directory = repository("image-v1.2.3")

        result = run(directory, "2.0.0")

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "2.0.0"

    @pytest.mark.parametrize("bump", ["1.2.3", "1.0.0"])
    def test_an_explicit_version_not_above_the_newest_is_refused(
        self, repository, bump
    ):
        directory = repository("image-v1.2.3")

        result = run(directory, bump)

        assert result.returncode != 0
        assert result.stdout == ""

    @pytest.mark.parametrize("bump", ["", "huge", "1.2", "v1.2.4", "1.2.3-rc1"])
    def test_anything_else_is_refused(self, repository, bump):
        directory = repository("image-v1.2.3")

        result = run(directory, bump)

        assert result.returncode != 0
        assert result.stdout == ""

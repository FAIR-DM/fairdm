"""Fixtures for running ``docker/entrypoint.sh`` against stand-in programs."""

import os
import subprocess
from pathlib import Path

import pytest

ENTRYPOINT = Path(__file__).resolve().parents[2] / "docker" / "entrypoint.sh"

STAND_IN = """#!/bin/sh
echo "{name} $*" >> "$STAND_IN_LOG"
if [ "$*" = "${{STAND_IN_FAIL_ON:-}}" ]; then
    exit "${{STAND_IN_STATUS:-1}}"
fi
"""


@pytest.fixture
def stand_in_log(tmp_path):
    """The file every stand-in program appends its command line to."""
    return tmp_path / "calls.log"


@pytest.fixture
def run_entrypoint(tmp_path, stand_in_log):
    """Run the entrypoint with ``python``, ``gunicorn``, ``celery`` and ``tool`` replaced by stand-ins.

    Each stand-in appends its command line to the log and exits 0, unless the line equals
    ``fail_on``, in which case it exits with ``status``. Returns the completed process and the
    lines the stand-ins logged, in order.
    """
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("python", "gunicorn", "celery", "tool"):
        stand_in = bin_dir / name
        stand_in.write_text(STAND_IN.format(name=name))
        stand_in.chmod(0o755)

    def run(*args, fail_on="", status=1, **env):
        process = subprocess.run(
            ["/bin/sh", str(ENTRYPOINT), *args],
            cwd=tmp_path,
            env={
                "PATH": f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin",
                "STAND_IN_LOG": str(stand_in_log),
                "STAND_IN_FAIL_ON": fail_on,
                "STAND_IN_STATUS": str(status),
                **env,
            },
            capture_output=True,
            text=True,
            check=False,
        )
        calls = stand_in_log.read_text().splitlines() if stand_in_log.exists() else []
        return process, calls

    return run

"""Tests for repository README trust signals."""

import re
import subprocess
import sys
from pathlib import Path


def test_readme_test_count_matches_pytest_collection() -> None:
    """README trust signal should match the collected test count."""
    readme = Path("README.md").read_text(encoding="utf-8")
    match = re.search(r"\* (?P<count>\d+) automated tests passing", readme)

    assert match is not None
    assert int(match.group("count")) == _collected_test_count()


def _collected_test_count() -> int:
    """Return the number of tests collected by pytest."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        check=True,
        capture_output=True,
        text=True,
    )
    for line in reversed(result.stdout.splitlines()):
        match = re.fullmatch(r"(?P<count>\d+) tests collected in .+", line)
        if match is not None:
            return int(match.group("count"))

    raise AssertionError("Could not determine pytest collection count.")

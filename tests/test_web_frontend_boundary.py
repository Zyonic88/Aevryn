from __future__ import annotations

import re
from pathlib import Path

WEB_SOURCE_ROOT = Path("web/src")
API_SOURCE_ROOT = WEB_SOURCE_ROOT / "api"
API_CLIENT_PATH = API_SOURCE_ROOT / "client.ts"
FORBIDDEN_IMPORT_MARKERS = (
    "src/aevryn",
    "../src",
    "../../src",
    "from aevryn",
    "import aevryn",
)
ENDPOINT_LITERAL_PATTERN = re.compile(r"[\"'](/v2(?:/[^\"']*)?)[\"']")


def _typescript_sources() -> list[Path]:
    assert WEB_SOURCE_ROOT.exists()
    return sorted(
        source_path
        for source_path in WEB_SOURCE_ROOT.rglob("*")
        if source_path.suffix in {".ts", ".tsx"}
    )


def test_web_frontend_does_not_import_engine_code_directly() -> None:
    """The browser app must use the API contract instead of importing engine modules."""

    violations: list[str] = []
    for source_path in _typescript_sources():
        source = source_path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_IMPORT_MARKERS:
            if marker in source:
                violations.append(f"{source_path}: {marker}")

    assert violations == []


def test_web_components_do_not_call_fetch_directly() -> None:
    """Network access must stay behind the frontend API client boundary."""

    violations: list[str] = []
    for source_path in _typescript_sources():
        if source_path == API_CLIENT_PATH:
            continue
        source = source_path.read_text(encoding="utf-8")
        if "fetch(" in source:
            violations.append(str(source_path))

    assert violations == []


def test_web_endpoint_paths_stay_inside_api_layer() -> None:
    """Components should not know concrete API endpoint paths."""

    violations: list[str] = []
    for source_path in _typescript_sources():
        if API_SOURCE_ROOT in source_path.parents:
            continue
        source = source_path.read_text(encoding="utf-8")
        if ENDPOINT_LITERAL_PATTERN.search(source):
            violations.append(str(source_path))

    assert violations == []

"""Tests for the checked-in validation corpus metadata."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = ROOT / "validation"
CASE_DIR = VALIDATION_ROOT / "cases"
VALIDATION_README = VALIDATION_ROOT / "README.md"
V1_READINESS = ROOT / "docs" / "AEVRYN_V1_READINESS.md"
EXPECTED_CASE_COUNT = 8


def test_validation_cases_store_only_metadata_and_hashes() -> None:
    """Validation case JSON must not store raw source or prompt text."""
    forbidden_keys = {
        "anchor_quote",
        "chapter_text",
        "evidence_quote",
        "prompt",
        "prompt_text",
        "quote",
        "raw_text",
        "scene_text",
        "source_text",
        "text",
    }
    for case_path in sorted(CASE_DIR.glob("*.json")):
        payload = json.loads(case_path.read_text(encoding="utf-8"))
        leaked_keys = _find_forbidden_keys(payload, forbidden_keys)

        assert leaked_keys == []


def test_validation_cases_are_canonical_json() -> None:
    """Validation case files should stay mechanically formatted."""
    for case_path in sorted(CASE_DIR.glob("*.json")):
        payload = json.loads(case_path.read_text(encoding="utf-8"))
        expected_text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

        assert case_path.read_text(encoding="utf-8") == expected_text


def test_validation_cases_have_unique_identity_and_sources() -> None:
    """Validation case IDs, genres, and source folders should not drift."""
    cases = [
        json.loads(case_path.read_text(encoding="utf-8"))
        for case_path in sorted(CASE_DIR.glob("*.json"))
    ]

    assert len(cases) == EXPECTED_CASE_COUNT
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert len({case["genre"] for case in cases}) == len(cases)
    assert len({case["source_directory"] for case in cases}) == len(cases)
    for case_path, case in zip(sorted(CASE_DIR.glob("*.json")), cases, strict=True):
        assert case_path.stem == case["case_id"]
        assert re.fullmatch(r"[a-z0-9_]+", case["case_id"])
        assert case["chapter_glob"] == "*.txt"


def test_validation_case_metrics_are_consistent() -> None:
    """Validation case metrics should agree internally."""
    digest_pattern = re.compile(r"[0-9a-f]{64}")
    for case_path in sorted(CASE_DIR.glob("*.json")):
        payload = json.loads(case_path.read_text(encoding="utf-8"))
        expected_import = payload["expected_import"]
        expected_extraction = payload["expected_extraction"]

        assert expected_import["chapter_files"] == 10
        assert expected_import["chapters"] == expected_import["chapter_files"]
        assert expected_import["scenes"] == expected_import["chapters"]
        assert expected_import["sentences"] == expected_import["evidence_anchors"]
        assert expected_extraction["scene_inputs"] == expected_import["scenes"]
        assert (
            expected_extraction["evidence_anchors"]
            == expected_import["evidence_anchors"]
        )
        for digest_key in (
            "source_manifest_digest",
            "import_digest",
        ):
            assert digest_pattern.fullmatch(expected_import[digest_key]), case_path
        for digest_key in (
            "extraction_input_digest",
            "extraction_prompt_digest",
        ):
            assert digest_pattern.fullmatch(expected_extraction[digest_key]), case_path


def test_validation_fingerprint_docs_match_checked_in_cases() -> None:
    """Validation docs should stay synchronized with checked-in case metrics."""
    cases = _load_cases()
    totals_line = _validation_totals_line(cases)
    suite_digest = _validation_suite_digest(cases)
    readme = VALIDATION_README.read_text(encoding="utf-8")
    readiness = V1_READINESS.read_text(encoding="utf-8")

    assert totals_line in readme
    assert suite_digest in readme
    assert _validation_readiness_totals_text(cases) in readiness
    assert f"digest={suite_digest}" in readiness


def test_validation_directory_does_not_store_known_source_phrases() -> None:
    """Validation metadata must not include known local source chapter phrases."""
    known_source_phrases = (
        "Mark found a brass key.",
        "Mark opened the archive.",
        "Scene Text:",
        "Evidence Anchors:",
    )
    validation_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in VALIDATION_ROOT.rglob("*")
        if path.is_file()
    )

    for phrase in known_source_phrases:
        assert phrase not in validation_text


def _find_forbidden_keys(
    value: object,
    forbidden_keys: set[str],
    path: str = "",
) -> list[str]:
    """Return paths to forbidden keys in a JSON-like value."""
    if isinstance(value, dict):
        findings: list[str] = []
        for key, item in value.items():
            item_path = f"{path}.{key}" if path else key
            if key in forbidden_keys:
                findings.append(item_path)
            findings.extend(_find_forbidden_keys(item, forbidden_keys, item_path))
        return findings

    if isinstance(value, list):
        findings = []
        for index, item in enumerate(value):
            findings.extend(_find_forbidden_keys(item, forbidden_keys, f"{path}[{index}]"))
        return findings

    return []


def _load_cases() -> list[dict[str, object]]:
    """Return checked-in validation case payloads."""
    return [
        json.loads(case_path.read_text(encoding="utf-8"))
        for case_path in sorted(CASE_DIR.glob("*.json"))
    ]


def _validation_totals_line(cases: list[dict[str, object]]) -> str:
    """Return expected validation totals text for checked-in cases."""
    expected_imports = [
        case["expected_import"]
        for case in cases
        if isinstance(case["expected_import"], dict)
    ]
    expected_extractions = [
        case["expected_extraction"]
        for case in cases
        if isinstance(case["expected_extraction"], dict)
    ]
    return (
        f"cases={len(cases)} "
        f"passed={len(cases)} "
        "failed=0 "
        f"files={sum(int(item['chapter_files']) for item in expected_imports)} "
        f"chapters={sum(int(item['chapters']) for item in expected_imports)} "
        f"scenes={sum(int(item['scenes']) for item in expected_imports)} "
        f"paragraphs={sum(int(item['paragraphs']) for item in expected_imports)} "
        f"sentences={sum(int(item['sentences']) for item in expected_imports)} "
        f"anchors={sum(int(item['evidence_anchors']) for item in expected_imports)} "
        f"extraction_inputs={sum(int(item['scene_inputs']) for item in expected_extractions)} "
        "extraction_anchors="
        f"{sum(int(item['evidence_anchors']) for item in expected_extractions)}"
    )


def _validation_suite_digest(cases: list[dict[str, object]]) -> str:
    """Return expected validation suite digest for checked-in passing cases."""
    payload = []
    for case in sorted(cases, key=lambda item: str(item["case_id"])):
        expected_import = case["expected_import"]
        expected_extraction = case["expected_extraction"]
        if not isinstance(expected_import, dict) or not isinstance(
            expected_extraction,
            dict,
        ):
            raise AssertionError("Validation cases should have object metric sections.")
        payload.append(
            {
                "case_id": case["case_id"],
                "genre": case["genre"],
                "passed": True,
                "source_manifest_digest": expected_import["source_manifest_digest"],
                "import_digest": expected_import["import_digest"],
                "errors": [],
                "extraction_input_digest": expected_extraction[
                    "extraction_input_digest"
                ],
                "extraction_prompt_digest": expected_extraction[
                    "extraction_prompt_digest"
                ],
            }
        )
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _validation_readiness_totals_text(cases: list[dict[str, object]]) -> str:
    """Return expected validation totals text as formatted in V1 readiness."""
    totals_line = _validation_totals_line(cases)
    prefix, suffix = totals_line.split(" extraction_inputs=", maxsplit=1)
    return f"{prefix}\nextraction_inputs={suffix}"

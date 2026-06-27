"""Tests for Aevryn's machine-readable V1 acceptance audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "docs" / "AEVRYN_V1_ACCEPTANCE_AUDIT.json"

EXPECTED_IMPLEMENTED_SYSTEMS = {
    "Story Import",
    "Entity Extraction",
    "Canon Updating",
    "Canon Engine",
    "Timeline Engine",
    "Character Engine",
    "World Engine",
    "Scene Engine",
    "Scene Analyzer",
    "Prompt Engine",
    "Presentation Engine",
    "Export Engine",
    "Project Manager",
    "CLI Proof Workflow",
}


def load_audit() -> dict[str, Any]:
    """Load the V1 acceptance audit document."""
    with AUDIT_PATH.open(encoding="utf-8") as audit_file:
        audit = json.load(audit_file)

    assert isinstance(audit, dict)
    return audit


def test_v1_acceptance_audit_is_utf8_without_bom() -> None:
    """Machine-readable audit JSON must not include a UTF-8 BOM."""
    assert not AUDIT_PATH.read_bytes().startswith(b"\xef\xbb\xbf")


def test_v1_acceptance_audit_uses_canonical_json_formatting() -> None:
    """Machine-readable audit JSON should stay mechanically formatted."""
    audit = load_audit()
    expected_text = json.dumps(audit, indent=2, ensure_ascii=False) + "\n"

    assert AUDIT_PATH.read_text(encoding="utf-8") == expected_text


def test_v1_acceptance_audit_covers_all_implemented_systems() -> None:
    """Every implemented V1 system must have an acceptance audit entry."""
    audit = load_audit()

    audited_system_names = [system["name"] for system in audit["implemented_systems"]]
    audited_systems = set(audited_system_names)

    assert len(audited_system_names) == len(audited_systems)
    assert audited_systems == EXPECTED_IMPLEMENTED_SYSTEMS


def test_v1_acceptance_audit_boundary_systems_are_unique() -> None:
    """Documented boundary systems should not be duplicated in the audit."""
    audit = load_audit()
    boundary_system_names = [
        system["name"] for system in audit["boundary_systems"]
    ]

    assert len(boundary_system_names) == len(set(boundary_system_names))


def test_v1_acceptance_audit_covers_every_universal_criterion() -> None:
    """Every implemented system must explicitly assess every universal criterion."""
    audit = load_audit()
    universal_criteria = set(audit["universal_criteria"])
    accepted_values = set(audit["accepted_criterion_values"])

    for system in audit["implemented_systems"]:
        criteria = system["criteria"]

        assert set(criteria) == universal_criteria
        assert set(criteria.values()).issubset(accepted_values)


def test_v1_acceptance_audit_evidence_paths_exist() -> None:
    """Audit evidence must point at real documentation, source, and tests."""
    audit = load_audit()

    for system in audit["implemented_systems"]:
        evidence = system["evidence"]

        for evidence_group in ("documentation", "source", "tests"):
            assert evidence[evidence_group], system["name"]
            assert len(evidence[evidence_group]) == len(set(evidence[evidence_group]))
            for relative_path in evidence[evidence_group]:
                assert (ROOT / relative_path).exists(), relative_path

    for boundary_system in audit["boundary_systems"]:
        assert len(boundary_system["documentation"]) == len(
            set(boundary_system["documentation"])
        )
        for relative_path in boundary_system["documentation"]:
            assert (ROOT / relative_path).exists(), relative_path


def test_cli_proof_workflow_audit_includes_validation_evidence() -> None:
    """CLI proof workflow acceptance must include validation runner evidence."""
    audit = load_audit()
    cli_system = next(
        system
        for system in audit["implemented_systems"]
        if system["name"] == "CLI Proof Workflow"
    )
    evidence = cli_system["evidence"]

    assert "src/aevryn/validation/runner.py" in evidence["source"]
    assert "tests/test_validation_runner.py" in evidence["tests"]
    assert "tests/test_validation_corpus.py" in evidence["tests"]


def test_remaining_acceptance_blockers_are_product_level() -> None:
    """Implemented systems should have no blockers after RC snapshot comparison."""
    audit = load_audit()
    global_blockers = set(audit["global_blockers"])

    assert global_blockers == set()

    for system in audit["implemented_systems"]:
        open_criteria = {
            criterion
            for criterion, value in system["criteria"].items()
            if value != "pass"
        }
        remaining_blockers = set(system["remaining_blockers"])

        assert open_criteria == set()
        assert remaining_blockers == global_blockers


def test_implemented_acceptance_statuses_match_remaining_blockers() -> None:
    """Implemented system status should match the completed RC state."""
    audit = load_audit()
    expected_status = "v1_complete_rc1"

    for system in audit["implemented_systems"]:
        assert system["status"] == expected_status, system["name"]
        assert system["remaining_blockers"] == []


def test_v1_acceptance_audit_records_rc1_snapshot_comparison() -> None:
    """RC1 audit should record the completed deterministic snapshot comparison."""
    audit = load_audit()
    comparison = audit["rc1_snapshot_comparison"]

    assert audit["audit_status"] == "rc1_ready"
    assert comparison["status"] == "pass"
    assert comparison["suite_digest"] == (
        "b911bda5279c30ead1830f58efa640d83bc66e41f3a50e96846804b428dec9d1"
    )
    assert comparison["compared_files"] == [
        "README.md",
        "validation_result.json",
    ]


def test_v1_source_and_tests_have_no_todo_placeholders() -> None:
    """V1 code and tests should not carry unfinished-work markers."""
    scanned_paths = tuple((ROOT / "src").rglob("*.py")) + tuple(
        (ROOT / "tests").rglob("*.py")
    )
    placeholder = "TO" + "DO"

    offenders = [
        str(path.relative_to(ROOT))
        for path in scanned_paths
        if placeholder in path.read_text(encoding="utf-8")
    ]

    assert offenders == []

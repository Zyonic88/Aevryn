"""Tests for SceneSmith's machine-readable V1 acceptance audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "docs" / "SCENESMITH_V1_ACCEPTANCE_AUDIT.json"

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


def test_v1_acceptance_audit_covers_all_implemented_systems() -> None:
    """Every implemented V1 system must have an acceptance audit entry."""
    audit = load_audit()

    audited_systems = {system["name"] for system in audit["implemented_systems"]}

    assert audited_systems == EXPECTED_IMPLEMENTED_SYSTEMS


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
            for relative_path in evidence[evidence_group]:
                assert (ROOT / relative_path).exists(), relative_path

    for boundary_system in audit["boundary_systems"]:
        for relative_path in boundary_system["documentation"]:
            assert (ROOT / relative_path).exists(), relative_path


def test_remaining_acceptance_blockers_are_product_level() -> None:
    """Implemented systems should only be blocked by the real multi-chapter Canon Test."""
    audit = load_audit()
    global_blockers = set(audit["global_blockers"])

    assert global_blockers == {"real_chapter_1_to_chapter_4_canon_test_not_run"}

    for system in audit["implemented_systems"]:
        open_criteria = {
            criterion
            for criterion, value in system["criteria"].items()
            if value != "pass"
        }
        remaining_blockers = set(system["remaining_blockers"])

        assert open_criteria == set()
        assert remaining_blockers == global_blockers

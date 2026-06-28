"""Tests for Phase 10 internal alpha planning contracts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_phase10_internal_alpha_docs_define_private_readiness_boundary() -> None:
    """Phase 10 docs should define private alpha scope before implementation."""
    alpha_doc = (ROOT / "docs" / "AEVRYN_INTERNAL_ALPHA.md").read_text(
        encoding="utf-8"
    )
    acceptance_doc = (
        ROOT / "docs" / "AEVRYN_V2_PHASE_10_ACCEPTANCE.md"
    ).read_text(encoding="utf-8")

    assert "Use it." in alpha_doc
    assert "Do not launch it publicly." in alpha_doc
    assert "Register\n-> Create Project\n-> Upload Story" in alpha_doc
    assert "backend owns workflow state" in alpha_doc
    assert "performance metadata stays outside canon" in alpha_doc
    assert "Phase 10 is accepted when:" in acceptance_doc
    assert "Aevryn validation passes." in acceptance_doc
    assert "public launch" in acceptance_doc


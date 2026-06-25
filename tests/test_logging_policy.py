"""Tests for SceneSmith's V1 logging policy."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_SUBSYSTEM_MODULES = (
    "src/scenesmith/importing/engine.py",
    "src/scenesmith/extraction/ai.py",
    "src/scenesmith/extraction/engine.py",
    "src/scenesmith/canon/updating.py",
    "src/scenesmith/canon/database.py",
    "src/scenesmith/canon/engine.py",
    "src/scenesmith/timeline/engine.py",
    "src/scenesmith/characters/cards.py",
    "src/scenesmith/characters/engine.py",
    "src/scenesmith/world/engine.py",
    "src/scenesmith/scenes/context.py",
    "src/scenesmith/scenes/engine.py",
    "src/scenesmith/scenes/analyzer.py",
    "src/scenesmith/prompts/builder.py",
    "src/scenesmith/prompts/engine.py",
    "src/scenesmith/presentation/engine.py",
    "src/scenesmith/export/engine.py",
    "src/scenesmith/projects/runner.py",
)


def test_logging_policy_document_exists() -> None:
    """The V1 logging policy must be documented."""
    assert (ROOT / "docs" / "SCENESMITH_LOGGING_POLICY.md").exists()


def test_package_installs_null_handler() -> None:
    """SceneSmith must not leak library logs unless an app configures logging."""
    source_text = (ROOT / "src" / "scenesmith" / "__init__.py").read_text(
        encoding="utf-8"
    )

    assert "logging.getLogger(__name__).addHandler(logging.NullHandler())" in source_text


def test_core_subsystem_modules_define_module_loggers() -> None:
    """Implemented core subsystem modules must define module-level loggers."""
    for relative_path in CORE_SUBSYSTEM_MODULES:
        source_text = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "import logging" in source_text, relative_path
        assert "logger = logging.getLogger(__name__)" in source_text, relative_path


def test_core_subsystems_do_not_print_user_output() -> None:
    """Core subsystems must keep presentation output out of subsystem code."""
    source_root = ROOT / "src" / "scenesmith"

    for path in source_root.rglob("*.py"):
        if path.name == "cli.py":
            continue

        source_text = path.read_text(encoding="utf-8")
        assert "print(" not in source_text, str(path.relative_to(ROOT))

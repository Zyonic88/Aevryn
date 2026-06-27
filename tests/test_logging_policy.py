"""Tests for Aevryn's V1 logging policy."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORE_SUBSYSTEM_MODULES = (
    "src/aevryn/importing/engine.py",
    "src/aevryn/extraction/ai.py",
    "src/aevryn/extraction/engine.py",
    "src/aevryn/canon/updating.py",
    "src/aevryn/canon/database.py",
    "src/aevryn/canon/engine.py",
    "src/aevryn/timeline/engine.py",
    "src/aevryn/characters/cards.py",
    "src/aevryn/characters/engine.py",
    "src/aevryn/world/engine.py",
    "src/aevryn/scenes/context.py",
    "src/aevryn/scenes/engine.py",
    "src/aevryn/scenes/analyzer.py",
    "src/aevryn/prompts/builder.py",
    "src/aevryn/prompts/engine.py",
    "src/aevryn/presentation/engine.py",
    "src/aevryn/export/engine.py",
    "src/aevryn/projects/runner.py",
    "src/aevryn/persistence/json_file.py",
    "src/aevryn/persistence/memory.py",
    "src/aevryn/persistence/schema.py",
    "src/aevryn/validation/runner.py",
)


def test_logging_policy_document_exists() -> None:
    """The V1 logging policy must be documented."""
    assert (ROOT / "docs" / "AEVRYN_LOGGING_POLICY.md").exists()


def test_repository_line_endings_are_normalized() -> None:
    """The repository must declare stable text line endings."""
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")

    assert "*.py text eol=lf" in attributes
    assert "*.md text eol=lf" in attributes
    assert "*.json text eol=lf" in attributes


def test_repository_ignores_generated_reference_outputs() -> None:
    """Generated outputs and local snapshots should not be committed accidentally."""
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "generated/" in gitignore
    assert "runtime/" in gitignore
    assert "output/" in gitignore
    assert "exports/" in gitignore
    assert "snapshots/*" in gitignore
    assert "!snapshots/README.md" in gitignore


def test_package_installs_null_handler() -> None:
    """Aevryn must not leak library logs unless an app configures logging."""
    source_text = (ROOT / "src" / "aevryn" / "__init__.py").read_text(
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
    source_root = ROOT / "src" / "aevryn"

    for path in source_root.rglob("*.py"):
        if path.name == "cli.py":
            continue

        source_text = path.read_text(encoding="utf-8")
        assert "print(" not in source_text, str(path.relative_to(ROOT))

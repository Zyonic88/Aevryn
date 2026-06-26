"""Tests for the validation corpus regression runner."""

import json
import logging
import re
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture

from scenesmith.importing import ImportedSource, StoryImporter
from scenesmith.validation import ValidationRunner
from scenesmith.validation.runner import (
    _extraction_input_digest,
    _extraction_prompt_digest,
    _source_manifest_digest,
    _structure_digest,
)


def test_validation_runner_passes_matching_import_metrics() -> None:
    """Validation passes when local chapter structure matches expected metrics."""
    source_root = Path("build") / "test_validation_runner" / "passing" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "passing" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case")

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is True
    assert result.score == 100
    assert result.totals.cases == 1
    assert result.totals.passed == 1
    assert result.totals.failed == 0
    assert result.totals.chapter_files == 2
    assert result.totals.sentences == 2
    assert result.totals.extraction_inputs == 2
    assert result.totals.extraction_anchors == 2
    assert re.fullmatch(r"[0-9a-f]{64}", result.suite_digest)
    assert result.results[0].actual_import is not None
    assert result.results[0].actual_extraction is not None
    assert result.results[0].actual_import.chapters == 2
    assert result.results[0].actual_import.evidence_anchors == 2
    assert result.results[0].actual_extraction.scene_inputs == 2


def test_validation_runner_reports_metric_mismatches() -> None:
    """Validation reports expected metric drift without raising."""
    source_root = Path("build") / "test_validation_runner" / "mismatch" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "mismatch" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case", evidence_anchors=999)

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.score == 0
    assert result.totals.cases == 1
    assert result.totals.passed == 0
    assert result.totals.failed == 1
    assert result.totals.evidence_anchors == 2
    assert result.totals.extraction_inputs == 2
    assert result.results[0].errors == ("import.evidence_anchors: expected 999, got 2",)


def test_validation_runner_logs_failed_cases(caplog: LogCaptureFixture) -> None:
    """Validation logs case failures for production diagnostics."""
    source_root = Path("build") / "test_validation_runner" / "logging" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "logging" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case", evidence_anchors=999)

    with caplog.at_level(logging.WARNING, logger="scenesmith.validation.runner"):
        result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert any(
        record.message == "validation_case_failed"
        and record.__dict__.get("case_id") == "demo_validation_case"
        and record.__dict__.get("error_count") == 1
        for record in caplog.records
    )


def test_validation_runner_logs_suite_elapsed_time(caplog: LogCaptureFixture) -> None:
    """Validation logs elapsed time without adding it to deterministic output."""
    source_root = Path("build") / "test_validation_runner" / "elapsed" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "elapsed" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case")

    with caplog.at_level(logging.INFO, logger="scenesmith.validation.runner"):
        result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    completed_records = [
        record
        for record in caplog.records
        if record.message == "validation_suite_completed"
    ]
    assert result.passed is True
    assert len(completed_records) == 1
    elapsed_ms = completed_records[0].__dict__.get("elapsed_ms")
    assert isinstance(elapsed_ms, float)
    assert elapsed_ms >= 0.0


def test_validation_runner_reports_import_digest_mismatches() -> None:
    """Validation catches parsing drift even when broad counts still match."""
    source_root = Path("build") / "test_validation_runner" / "digest" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "digest" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        import_digest="0" * 64,
    )

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.score == 0
    assert len(result.results[0].errors) == 1
    assert result.results[0].errors[0].startswith(
        "import.import_digest: expected 000000000000000000000000000000000000000000000000"
        "0000000000000000, got "
    )


def test_validation_runner_reports_extraction_digest_mismatches() -> None:
    """Validation catches extraction-readiness drift."""
    source_root = Path("build") / "test_validation_runner" / "extract_digest" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "extract_digest" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        extraction_input_digest="0" * 64,
    )

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.score == 0
    assert len(result.results[0].errors) == 1
    assert result.results[0].errors[0].startswith(
        "extraction.extraction_input_digest: expected "
        "0000000000000000000000000000000000000000000000000000000000000000, got "
    )


def test_validation_runner_reports_extraction_prompt_digest_mismatches() -> None:
    """Validation catches extraction prompt builder drift."""
    source_root = Path("build") / "test_validation_runner" / "prompt_digest" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "prompt_digest" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        extraction_prompt_digest="0" * 64,
    )

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.score == 0
    assert len(result.results[0].errors) == 1
    assert result.results[0].errors[0].startswith(
        "extraction.extraction_prompt_digest: expected "
        "0000000000000000000000000000000000000000000000000000000000000000, got "
    )


def test_validation_runner_can_filter_cases_by_id() -> None:
    """Validation runner can run a selected case subset."""
    source_root = Path("build") / "test_validation_runner" / "filter" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "filter" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case")

    result = ValidationRunner(
        case_dir=case_dir,
        source_root=source_root,
        case_ids=("demo_validation_case",),
    ).run()

    assert result.passed is True
    assert result.totals.cases == 1
    assert result.results[0].case_id == "demo_validation_case"


def test_validation_runner_rejects_unknown_selected_cases() -> None:
    """Validation runner rejects selected case IDs that do not exist."""
    source_root = Path("build") / "test_validation_runner" / "unknown_case" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "unknown_case" / "cases"
    _write_validation_source(source_root)
    _write_case(case_dir, case_id="demo_validation_case")

    with pytest.raises(ValueError, match="Unknown validation case IDs"):
        ValidationRunner(
            case_dir=case_dir,
            source_root=source_root,
            case_ids=("missing_case",),
        ).run()


def test_validation_runner_rejects_case_directory_file_paths() -> None:
    """Validation case directory must be a real directory."""
    source_root = Path("build") / "test_validation_runner" / "case_file" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "case_file" / "cases.json"
    _write_validation_source(source_root)
    case_dir.parent.mkdir(parents=True, exist_ok=True)
    case_dir.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="case path is not a directory"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_non_file_case_matches() -> None:
    """Validation case globs must resolve to JSON files."""
    source_root = Path("build") / "test_validation_runner" / "case_non_file" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "case_non_file" / "cases"
    _write_validation_source(source_root)
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "demo_validation_case.json").mkdir(exist_ok=True)

    with pytest.raises(ValueError, match="case path is not a file"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_duplicate_case_json_keys() -> None:
    """Validation case JSON cannot rely on last-key-wins parsing."""
    source_root = Path("build") / "test_validation_runner" / "duplicate_key" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "duplicate_key" / "cases"
    _write_validation_source(source_root)
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "demo_validation_case.json").write_text(
        (
            '{"case_id": "demo_validation_case", '
            '"case_id": "other_case", '
            '"title": "Demo", '
            '"genre": "Demo", '
            '"source_directory": "Demo Genre", '
            '"chapter_glob": "*.txt", '
            '"expected_import": {}, '
            '"expected_extraction": {}}'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate key"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_non_object_case_json() -> None:
    """Validation case JSON root must be an object."""
    source_root = Path("build") / "test_validation_runner" / "non_object" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "non_object" / "cases"
    _write_validation_source(source_root)
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "demo_validation_case.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError, match="must be a JSON object"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_extra_case_fields() -> None:
    """Validation case files reject unsupported top-level fields."""
    source_root = Path("build") / "test_validation_runner" / "extra_case" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "extra_case" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        extra_case_fields={"unexpected": True},
    )

    with pytest.raises(ValueError, match="Unsupported validation case fields"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_extra_expected_import_fields() -> None:
    """Validation expected_import files reject unsupported metric fields."""
    source_root = Path("build") / "test_validation_runner" / "extra_import" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "extra_import" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        extra_expected_import_fields={"unexpected_metric": 1},
    )

    with pytest.raises(ValueError, match="Unsupported validation expected_import fields"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_non_object_expected_import() -> None:
    """Validation expected_import must be an object."""
    source_root = Path("build") / "test_validation_runner" / "bad_import" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "bad_import" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        expected_import_override=[],
    )

    with pytest.raises(ValueError, match="requires object field: expected_import"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_non_object_expected_extraction() -> None:
    """Validation expected_extraction must be an object."""
    source_root = Path("build") / "test_validation_runner" / "bad_extract" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "bad_extract" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        expected_extraction_override=[],
    )

    with pytest.raises(ValueError, match="requires object field: expected_extraction"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_boolean_metric_values() -> None:
    """Validation metric integers cannot be booleans."""
    source_root = Path("build") / "test_validation_runner" / "bool_metric" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "bool_metric" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        extra_expected_import_fields={"chapters": True},
    )

    with pytest.raises(ValueError, match="requires integer field: chapters"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_filename_case_id_mismatches() -> None:
    """Validation case filenames must match their case IDs."""
    source_root = Path("build") / "test_validation_runner" / "filename" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "filename" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        filename="different_name.json",
        allow_filename_mismatch=True,
    )

    with pytest.raises(ValueError, match="filename must match case_id"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_nested_chapter_globs() -> None:
    """Validation chapter globs must not escape the source directory."""
    source_root = Path("build") / "test_validation_runner" / "glob" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "glob" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        chapter_glob="../*.txt",
    )

    with pytest.raises(ValueError, match="filename-only glob"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_parent_source_directories() -> None:
    """Validation source directories must not escape the source root."""
    source_root = Path("build") / "test_validation_runner" / "parent_source" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "parent_source" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        source_directory="../Demo Genre",
    )

    with pytest.raises(ValueError, match="relative to the validation root"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_rejects_absolute_source_directories() -> None:
    """Validation source directories must be relative corpus paths."""
    source_root = Path("build") / "test_validation_runner" / "absolute_source" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "absolute_source" / "cases"
    _write_validation_source(source_root)
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        source_directory=str((source_root / "Demo Genre").resolve()),
    )

    with pytest.raises(ValueError, match="relative to the validation root"):
        ValidationRunner(case_dir=case_dir, source_root=source_root).run()


def test_validation_runner_reports_source_directory_file_paths() -> None:
    """Validation source directory must be a real directory."""
    source_root = Path("build") / "test_validation_runner" / "source_file" / "sources"
    case_dir = Path("build") / "test_validation_runner" / "source_file" / "cases"
    source_root.mkdir(parents=True, exist_ok=True)
    (source_root / "Demo Genre").write_text("not a directory", encoding="utf-8")
    _write_case(case_dir, case_id="demo_validation_case")

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.results[0].actual_import is None
    assert result.results[0].errors[0].startswith(
        "Validation source path is not a directory:"
    )


def test_validation_runner_uses_natural_chapter_file_order() -> None:
    """Validation imports Chapter 10 after Chapter 2, not between 1 and 2."""
    source_root = Path("build") / "test_validation_runner" / "natural_order" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_validation_runner" / "natural_order" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 10.txt").write_text(
        "Chapter 10\nMark sealed the archive.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )
    imported = StoryImporter().import_text(
        source_id="demo_validation_case",
        title="Demo",
        text="\n\n".join(
            (
                "Chapter 1\nMark found a brass key.",
                "Chapter 2\nMark opened the archive.",
                "Chapter 10\nMark sealed the archive.",
            )
        ),
    )
    _write_case(
        case_dir,
        case_id="demo_validation_case",
        chapter_files=(
            source_dir / "Demo Chapter 1.txt",
            source_dir / "Demo Chapter 2.txt",
            source_dir / "Demo Chapter 10.txt",
        ),
        imported=imported,
    )

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is True
    assert result.results[0].actual_import is not None
    assert result.results[0].actual_import.chapter_files == 3
    assert result.results[0].actual_import.chapters == 3


def test_validation_runner_reports_empty_chapter_files() -> None:
    """Validation corpus chapter files cannot be blank."""
    source_root = Path("build") / "test_validation_runner" / "empty_file" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_validation_runner" / "empty_file" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text("   \n", encoding="utf-8")
    _write_case(case_dir, case_id="demo_validation_case")

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.results[0].actual_import is None
    assert result.results[0].errors[0].startswith("Validation chapter file is empty:")
    assert "Demo Chapter 2.txt" in result.results[0].errors[0]


def test_validation_runner_reports_non_file_chapter_matches() -> None:
    """Validation chapter globs must resolve to files."""
    source_root = Path("build") / "test_validation_runner" / "non_file" / "sources"
    source_dir = source_root / "Demo Genre"
    case_dir = Path("build") / "test_validation_runner" / "non_file" / "cases"
    source_dir.mkdir(parents=True, exist_ok=True)
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").mkdir(exist_ok=True)
    _write_case(case_dir, case_id="demo_validation_case")

    result = ValidationRunner(case_dir=case_dir, source_root=source_root).run()

    assert result.passed is False
    assert result.results[0].actual_import is None
    assert result.results[0].errors[0].startswith(
        "Validation chapter path is not a file:"
    )
    assert "Demo Chapter 2.txt" in result.results[0].errors[0]


def _write_validation_source(source_root: Path) -> None:
    """Write a tiny local validation source."""
    source_dir = source_root / "Demo Genre"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "Demo Chapter 1.txt").write_text(
        "Chapter 1\nMark found a brass key.",
        encoding="utf-8",
    )
    (source_dir / "Demo Chapter 2.txt").write_text(
        "Chapter 2\nMark opened the archive.",
        encoding="utf-8",
    )


def _write_case(
    case_dir: Path,
    *,
    case_id: str,
    filename: str = "demo.json",
    evidence_anchors: int | None = None,
    import_digest: str | None = None,
    extraction_input_digest: str | None = None,
    extraction_prompt_digest: str | None = None,
    source_directory: str = "Demo Genre",
    chapter_glob: str = "*.txt",
    chapter_files: tuple[Path, ...] | None = None,
    imported: ImportedSource | None = None,
    allow_filename_mismatch: bool = False,
    extra_case_fields: dict[str, object] | None = None,
    extra_expected_import_fields: dict[str, object] | None = None,
    expected_import_override: object | None = None,
    expected_extraction_override: object | None = None,
) -> None:
    """Write a validation case definition."""
    case_dir.mkdir(parents=True, exist_ok=True)
    for existing_case in case_dir.glob("*.json"):
        existing_case.unlink()
    expected = _expected_import_metrics(chapter_files=chapter_files, imported=imported)
    expected_import: dict[str, object] = {
        "chapter_files": expected["chapter_files"],
        "source_manifest_digest": expected["source_manifest_digest"],
        "chapters": expected["chapters"],
        "scenes": expected["scenes"],
        "paragraphs": expected["paragraphs"],
        "sentences": expected["sentences"],
        "evidence_anchors": evidence_anchors or expected["evidence_anchors"],
        "import_digest": import_digest or expected["import_digest"],
    }
    expected_extraction: dict[str, object] = {
        "scene_inputs": expected["extraction_scene_inputs"],
        "evidence_anchors": expected["extraction_evidence_anchors"],
        "extraction_input_digest": (
            extraction_input_digest or expected["extraction_input_digest"]
        ),
        "extraction_prompt_digest": (
            extraction_prompt_digest or expected["extraction_prompt_digest"]
        ),
    }
    if extra_expected_import_fields is not None:
        expected_import.update(extra_expected_import_fields)
    case_payload: dict[str, object] = {
        "case_id": case_id,
        "title": "Demo",
        "genre": "Demo",
        "source_directory": source_directory,
        "chapter_glob": chapter_glob,
        "expected_import": (
            expected_import if expected_import_override is None else expected_import_override
        ),
        "expected_extraction": (
            expected_extraction
            if expected_extraction_override is None
            else expected_extraction_override
        ),
    }
    if extra_case_fields is not None:
        case_payload.update(extra_case_fields)
    output_filename = filename
    if filename == "demo.json" and not allow_filename_mismatch:
        output_filename = f"{case_id}.json"
    (case_dir / output_filename).write_text(
        json.dumps(case_payload),
        encoding="utf-8",
    )


def _expected_import_metrics(
    *,
    chapter_files: tuple[Path, ...] | None = None,
    imported: ImportedSource | None = None,
) -> dict[str, int | str]:
    """Return expected metrics for the tiny validation source."""
    if chapter_files is None:
        chapter_file_root = (
            Path("build")
            / "test_validation_runner"
            / "expected"
            / "sources"
            / "Demo Genre"
        )
        _write_validation_source(chapter_file_root.parent)
        chapter_files = tuple(sorted(chapter_file_root.glob("*.txt")))
    if imported is None:
        imported = StoryImporter().import_text(
            source_id="demo_validation_case",
            title="Demo",
            text="\n\n".join(
                (
                    "Chapter 1\nMark found a brass key.",
                    "Chapter 2\nMark opened the archive.",
                )
            ),
        )
    return {
        "chapter_files": len(chapter_files),
        "source_manifest_digest": _source_manifest_digest(chapter_files),
        "chapters": len(imported.story.chapters),
        "scenes": sum(len(chapter.scenes) for chapter in imported.story.chapters),
        "paragraphs": len(imported.paragraphs),
        "sentences": sum(len(paragraph.sentences) for paragraph in imported.paragraphs),
        "evidence_anchors": len(imported.anchors),
        "import_digest": _structure_digest(imported),
        "extraction_scene_inputs": sum(
            len(chapter.scenes) for chapter in imported.story.chapters
        ),
        "extraction_evidence_anchors": len(imported.anchors),
        "extraction_input_digest": _extraction_input_digest(imported),
        "extraction_prompt_digest": _extraction_prompt_digest(imported),
    }

"""Validation corpus regression runner."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scenesmith.extraction import (
    EvidenceBoundedAIExtractor,
    SceneEvidenceAnchor,
    SceneExtractionInput,
    StaticAIExtractionClient,
)
from scenesmith.importing import EvidenceAnchor, ImportedSource, StoryImporter
from scenesmith.json_utils import loads_json_without_duplicate_keys

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExpectedImportMetrics:
    """Expected Story Import metrics for one validation case."""

    chapter_files: int
    source_manifest_digest: str
    chapters: int
    scenes: int
    paragraphs: int
    sentences: int
    evidence_anchors: int
    import_digest: str

    def __post_init__(self) -> None:
        """Validate expected metric values."""
        for field_name, value in (
            ("chapter files", self.chapter_files),
            ("chapters", self.chapters),
            ("scenes", self.scenes),
            ("paragraphs", self.paragraphs),
            ("sentences", self.sentences),
            ("evidence anchors", self.evidence_anchors),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"Expected {field_name} must be a positive integer.")
        for digest_field_name, digest_value in (
            ("source manifest digest", self.source_manifest_digest),
            ("import digest", self.import_digest),
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", digest_value):
                raise ValueError(
                    f"Expected {digest_field_name} must be a SHA-256 hex digest."
                )


@dataclass(frozen=True, slots=True)
class ExpectedExtractionMetrics:
    """Expected Entity Extraction input-readiness metrics for one case."""

    scene_inputs: int
    evidence_anchors: int
    extraction_input_digest: str
    extraction_prompt_digest: str

    def __post_init__(self) -> None:
        """Validate expected extraction readiness metrics."""
        for field_name, value in (
            ("scene inputs", self.scene_inputs),
            ("evidence anchors", self.evidence_anchors),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"Expected {field_name} must be a positive integer.")
        for digest_field_name, digest_value in (
            ("extraction input digest", self.extraction_input_digest),
            ("extraction prompt digest", self.extraction_prompt_digest),
        ):
            if not re.fullmatch(r"[0-9a-f]{64}", digest_value):
                raise ValueError(
                    f"Expected {digest_field_name} must be a SHA-256 hex digest."
                )


@dataclass(frozen=True, slots=True)
class ValidationCase:
    """One local validation corpus case."""

    case_id: str
    title: str
    genre: str
    source_directory: str
    chapter_glob: str
    expected_import: ExpectedImportMetrics
    expected_extraction: ExpectedExtractionMetrics

    def __post_init__(self) -> None:
        """Validate validation case metadata."""
        _require_machine_token(self.case_id, "Validation case ID")
        _require_text(self.title, "Validation case title")
        _require_text(self.genre, "Validation case genre")
        _require_relative_path(self.source_directory, "Validation source directory")
        _require_filename_glob(self.chapter_glob, "Validation chapter glob")


@dataclass(frozen=True, slots=True)
class ValidationCaseResult:
    """Result for one validation case."""

    case_id: str
    title: str
    genre: str
    passed: bool
    actual_import: ExpectedImportMetrics | None
    actual_extraction: ExpectedExtractionMetrics | None
    errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate validation result fields."""
        _require_machine_token(self.case_id, "Validation result case ID")
        _require_text(self.title, "Validation result title")
        _require_text(self.genre, "Validation result genre")
        if not isinstance(self.passed, bool):
            raise ValueError("Validation result passed flag must be boolean.")
        for error in self.errors:
            _require_text(error, "Validation result error")


@dataclass(frozen=True, slots=True)
class ValidationTotals:
    """Aggregate validation metrics for all cases that produced metrics."""

    cases: int
    passed: int
    failed: int
    chapter_files: int
    chapters: int
    scenes: int
    paragraphs: int
    sentences: int
    evidence_anchors: int
    extraction_inputs: int
    extraction_anchors: int

    def __post_init__(self) -> None:
        """Validate aggregate validation metrics."""
        for field_name, value in (
            ("cases", self.cases),
            ("passed", self.passed),
            ("failed", self.failed),
            ("chapter files", self.chapter_files),
            ("chapters", self.chapters),
            ("scenes", self.scenes),
            ("paragraphs", self.paragraphs),
            ("sentences", self.sentences),
            ("evidence anchors", self.evidence_anchors),
            ("extraction inputs", self.extraction_inputs),
            ("extraction anchors", self.extraction_anchors),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"Validation total {field_name} cannot be negative.")


@dataclass(frozen=True, slots=True)
class ValidationSuiteResult:
    """Result for an entire validation corpus run."""

    results: tuple[ValidationCaseResult, ...]

    @property
    def passed(self) -> bool:
        """Return whether every validation case passed."""
        return all(result.passed for result in self.results)

    @property
    def score(self) -> int:
        """Return whole-number validation score."""
        if not self.results:
            return 0

        passed_count = sum(1 for result in self.results if result.passed)
        return round((passed_count / len(self.results)) * 100)

    @property
    def totals(self) -> ValidationTotals:
        """Return aggregate metrics for this validation suite result."""
        metrics = tuple(
            result.actual_import
            for result in self.results
            if result.actual_import is not None
        )
        extraction_metrics = tuple(
            result.actual_extraction
            for result in self.results
            if result.actual_extraction is not None
        )
        return ValidationTotals(
            cases=len(self.results),
            passed=sum(1 for result in self.results if result.passed),
            failed=sum(1 for result in self.results if not result.passed),
            chapter_files=sum(metric.chapter_files for metric in metrics),
            chapters=sum(metric.chapters for metric in metrics),
            scenes=sum(metric.scenes for metric in metrics),
            paragraphs=sum(metric.paragraphs for metric in metrics),
            sentences=sum(metric.sentences for metric in metrics),
            evidence_anchors=sum(metric.evidence_anchors for metric in metrics),
            extraction_inputs=sum(
                metric.scene_inputs for metric in extraction_metrics
            ),
            extraction_anchors=sum(
                metric.evidence_anchors for metric in extraction_metrics
            ),
        )

    @property
    def suite_digest(self) -> str:
        """Return a deterministic fingerprint for the full validation result."""
        payload = [
            {
                "case_id": result.case_id,
                "genre": result.genre,
                "passed": result.passed,
                "source_manifest_digest": (
                    None
                    if result.actual_import is None
                    else result.actual_import.source_manifest_digest
                ),
                "import_digest": (
                    None
                    if result.actual_import is None
                    else result.actual_import.import_digest
                ),
                "errors": list(result.errors),
                "extraction_input_digest": (
                    None
                    if result.actual_extraction is None
                    else result.actual_extraction.extraction_input_digest
                ),
                "extraction_prompt_digest": (
                    None
                    if result.actual_extraction is None
                    else result.actual_extraction.extraction_prompt_digest
                ),
            }
            for result in sorted(self.results, key=lambda item: item.case_id)
        ]
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ValidationRunner:
    """Run local validation corpus cases without storing source chapters."""

    def __init__(
        self,
        case_dir: Path,
        source_root: Path,
        case_ids: Sequence[str] = (),
    ) -> None:
        """Create a validation runner.

        Parameters:
            case_dir: Directory containing JSON validation case definitions.
            source_root: Local root containing chapter folders.
            case_ids: Optional validation case IDs to run.
        """
        self._case_dir = case_dir
        self._source_root = source_root
        self._case_ids = tuple(case_ids)
        for case_id in self._case_ids:
            _require_machine_token(case_id, "Validation selected case ID")

    def run(self) -> ValidationSuiteResult:
        """Run every validation case."""
        cases = self._load_cases()
        started_at = time.perf_counter()
        logger.info(
            "validation_suite_started",
            extra={"case_count": len(cases), "source_root": str(self._source_root)},
        )
        result = ValidationSuiteResult(
            results=tuple(self._run_case(case) for case in cases)
        )
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 3)
        logger.info(
            "validation_suite_completed",
            extra={
                "case_count": result.totals.cases,
                "passed": result.totals.passed,
                "failed": result.totals.failed,
                "suite_digest": result.suite_digest,
                "elapsed_ms": elapsed_ms,
            },
        )
        return result

    def list_cases(self) -> tuple[ValidationCase, ...]:
        """Return available validation cases without importing chapter files."""
        return self._load_cases()

    def _run_case(self, case: ValidationCase) -> ValidationCaseResult:
        """Run one validation case."""
        try:
            chapter_files = self._chapter_files(case)
            imported = self._import_case(case=case, chapter_files=chapter_files)
            repeated_import = self._import_case(case=case, chapter_files=chapter_files)
            actual_import = _import_metrics(
                imported=imported,
                chapter_files=chapter_files,
            )
            actual_extraction = _extraction_metrics(imported)
            errors = tuple(
                self._metric_errors(
                    case=case,
                    actual_import=actual_import,
                    actual_extraction=actual_extraction,
                    imported=imported,
                    repeated_import=repeated_import,
                )
            )
            if errors:
                logger.warning(
                    "validation_case_failed",
                    extra={"case_id": case.case_id, "error_count": len(errors)},
                )
            else:
                logger.debug(
                    "validation_case_passed",
                    extra={"case_id": case.case_id},
                )
            return ValidationCaseResult(
                case_id=case.case_id,
                title=case.title,
                genre=case.genre,
                passed=not errors,
                actual_import=actual_import,
                actual_extraction=actual_extraction,
                errors=errors,
            )
        except (OSError, ValueError) as error:
            logger.warning(
                "validation_case_failed",
                extra={"case_id": case.case_id, "error_count": 1},
            )
            return ValidationCaseResult(
                case_id=case.case_id,
                title=case.title,
                genre=case.genre,
                passed=False,
                actual_import=None,
                actual_extraction=None,
                errors=(str(error),),
            )

    def _load_cases(self) -> tuple[ValidationCase, ...]:
        """Load validation case definitions from disk."""
        if not self._case_dir.exists():
            raise ValueError(f"Validation case directory not found: {self._case_dir}")
        if not self._case_dir.is_dir():
            raise ValueError(f"Validation case path is not a directory: {self._case_dir}")

        cases = tuple(
            self._load_case(path)
            for path in sorted(self._case_dir.glob("*.json"), key=lambda path: path.name)
        )
        if not cases:
            raise ValueError(f"No validation cases found in: {self._case_dir}")

        case_ids = [case.case_id for case in cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Validation cases cannot contain duplicate case IDs.")

        if not self._case_ids:
            return cases

        requested_case_ids = set(self._case_ids)
        available_case_ids = set(case_ids)
        unknown_case_ids = requested_case_ids - available_case_ids
        if unknown_case_ids:
            unknown = ", ".join(sorted(unknown_case_ids))
            raise ValueError(f"Unknown validation case IDs: {unknown}")

        return tuple(case for case in cases if case.case_id in requested_case_ids)

    def _load_case(self, path: Path) -> ValidationCase:
        """Load one validation case definition."""
        if not path.is_file():
            raise ValueError(f"Validation case path is not a file: {path}")
        payload = loads_json_without_duplicate_keys(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Validation case must be a JSON object: {path}")

        _reject_extra_keys(
            payload=payload,
            allowed_keys={
                "case_id",
                "title",
                "genre",
                "source_directory",
                "chapter_glob",
                "expected_import",
                "expected_extraction",
            },
            path=path,
            context="validation case",
        )
        expected = _required_mapping(payload, "expected_import", path)
        _reject_extra_keys(
            payload=expected,
            allowed_keys={
                "chapter_files",
                "source_manifest_digest",
                "chapters",
                "scenes",
                "paragraphs",
                "sentences",
                "evidence_anchors",
                "import_digest",
            },
            path=path,
            context="validation expected_import",
        )
        expected_extraction = _required_mapping(payload, "expected_extraction", path)
        _reject_extra_keys(
            payload=expected_extraction,
            allowed_keys={
                "scene_inputs",
                "evidence_anchors",
                "extraction_input_digest",
                "extraction_prompt_digest",
            },
            path=path,
            context="validation expected_extraction",
        )
        case_id = _required_str(payload, "case_id", path)
        if path.stem != case_id:
            raise ValueError(
                "Validation case filename must match case_id: "
                f"{path.name} != {case_id}.json"
            )
        return ValidationCase(
            case_id=case_id,
            title=_required_str(payload, "title", path),
            genre=_required_str(payload, "genre", path),
            source_directory=_required_str(payload, "source_directory", path),
            chapter_glob=_required_str(payload, "chapter_glob", path),
            expected_import=ExpectedImportMetrics(
                chapter_files=_required_int(expected, "chapter_files", path),
                source_manifest_digest=_required_str(
                    expected,
                    "source_manifest_digest",
                    path,
                ),
                chapters=_required_int(expected, "chapters", path),
                scenes=_required_int(expected, "scenes", path),
                paragraphs=_required_int(expected, "paragraphs", path),
                sentences=_required_int(expected, "sentences", path),
                evidence_anchors=_required_int(expected, "evidence_anchors", path),
                import_digest=_required_str(expected, "import_digest", path),
            ),
            expected_extraction=ExpectedExtractionMetrics(
                scene_inputs=_required_int(expected_extraction, "scene_inputs", path),
                evidence_anchors=_required_int(
                    expected_extraction,
                    "evidence_anchors",
                    path,
                ),
                extraction_input_digest=_required_str(
                    expected_extraction,
                    "extraction_input_digest",
                    path,
                ),
                extraction_prompt_digest=_required_str(
                    expected_extraction,
                    "extraction_prompt_digest",
                    path,
                ),
            ),
        )

    def _chapter_files(self, case: ValidationCase) -> tuple[Path, ...]:
        """Return chapter files in natural chapter order."""
        source_dir = self._source_root / case.source_directory
        if not source_dir.exists():
            raise ValueError(f"Validation source directory not found: {source_dir}")
        if not source_dir.is_dir():
            raise ValueError(f"Validation source path is not a directory: {source_dir}")

        chapter_files = tuple(
            sorted(source_dir.glob(case.chapter_glob), key=lambda path: _natural_key(path.name))
        )
        if not chapter_files:
            raise ValueError(f"No chapter files found for validation case: {case.case_id}")
        for chapter_file in chapter_files:
            if not chapter_file.is_file():
                raise ValueError(f"Validation chapter path is not a file: {chapter_file}")
            if not chapter_file.read_text(encoding="utf-8").strip():
                raise ValueError(f"Validation chapter file is empty: {chapter_file}")

        return chapter_files

    @staticmethod
    def _import_case(
        case: ValidationCase,
        chapter_files: Sequence[Path],
    ) -> ImportedSource:
        """Import a case from local chapter files."""
        combined_text = "\n\n".join(
            path.read_text(encoding="utf-8").strip() for path in chapter_files
        )
        return StoryImporter().import_text(
            source_id=case.case_id,
            title=case.title,
            text=combined_text,
        )

    @staticmethod
    def _metric_errors(
        case: ValidationCase,
        actual_import: ExpectedImportMetrics,
        actual_extraction: ExpectedExtractionMetrics,
        imported: ImportedSource,
        repeated_import: ImportedSource,
    ) -> list[str]:
        """Return validation errors for one import result."""
        errors: list[str] = []
        expected = case.expected_import
        for field_name, expected_value, actual_value in (
            (
                "import.chapter_files",
                expected.chapter_files,
                actual_import.chapter_files,
            ),
            (
                "import.source_manifest_digest",
                expected.source_manifest_digest,
                actual_import.source_manifest_digest,
            ),
            ("import.chapters", expected.chapters, actual_import.chapters),
            ("import.scenes", expected.scenes, actual_import.scenes),
            ("import.paragraphs", expected.paragraphs, actual_import.paragraphs),
            ("import.sentences", expected.sentences, actual_import.sentences),
            (
                "import.evidence_anchors",
                expected.evidence_anchors,
                actual_import.evidence_anchors,
            ),
            ("import.import_digest", expected.import_digest, actual_import.import_digest),
        ):
            if expected_value != actual_value:
                errors.append(
                    f"{field_name}: expected {expected_value}, got {actual_value}"
                )

        if _structure_digest(imported) != _structure_digest(repeated_import):
            errors.append(
                "determinism.import_structure_digest: changed between repeated runs"
            )

        expected_extraction = case.expected_extraction
        for field_name, expected_value, actual_value in (
            (
                "extraction.scene_inputs",
                expected_extraction.scene_inputs,
                actual_extraction.scene_inputs,
            ),
            (
                "extraction.evidence_anchors",
                expected_extraction.evidence_anchors,
                actual_extraction.evidence_anchors,
            ),
            (
                "extraction.extraction_input_digest",
                expected_extraction.extraction_input_digest,
                actual_extraction.extraction_input_digest,
            ),
            (
                "extraction.extraction_prompt_digest",
                expected_extraction.extraction_prompt_digest,
                actual_extraction.extraction_prompt_digest,
            ),
        ):
            if expected_value != actual_value:
                errors.append(
                    f"{field_name}: expected {expected_value}, got {actual_value}"
                )

        errors.extend(_integrity_errors(imported))

        return errors


def _import_metrics(
    imported: ImportedSource,
    chapter_files: Sequence[Path],
) -> ExpectedImportMetrics:
    """Return Story Import metrics for an imported source."""
    return ExpectedImportMetrics(
        chapter_files=len(chapter_files),
        source_manifest_digest=_source_manifest_digest(chapter_files),
        chapters=len(imported.story.chapters),
        scenes=sum(len(chapter.scenes) for chapter in imported.story.chapters),
        paragraphs=len(imported.paragraphs),
        sentences=sum(len(paragraph.sentences) for paragraph in imported.paragraphs),
        evidence_anchors=len(imported.anchors),
        import_digest=_structure_digest(imported),
    )


def _structure_digest(imported: ImportedSource) -> str:
    """Return deterministic digest for imported structure and evidence IDs."""
    payload = {
        "source_id": imported.source_id,
        "chapters": [
            {
                "chapter_id": chapter.chapter_id,
                "chapter_index": chapter.chapter_index,
                "scene_ids": [scene.scene_id for scene in chapter.scenes],
            }
            for chapter in imported.story.chapters
        ],
        "paragraphs": [paragraph.paragraph_id for paragraph in imported.paragraphs],
        "sentences": [
            {
                "sentence_id": sentence.sentence_id,
                "text_hash": _text_digest(sentence.text),
            }
            for paragraph in imported.paragraphs
            for sentence in paragraph.sentences
        ],
        "anchors": [
            {
                "anchor_id": anchor.anchor_id,
                "quote_hash": _text_digest(anchor.quote),
            }
            for anchor in imported.anchors
        ],
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _extraction_metrics(imported: ImportedSource) -> ExpectedExtractionMetrics:
    """Return deterministic extraction-input readiness metrics."""
    return ExpectedExtractionMetrics(
        scene_inputs=sum(len(chapter.scenes) for chapter in imported.story.chapters),
        evidence_anchors=len(imported.anchors),
        extraction_input_digest=_extraction_input_digest(imported),
        extraction_prompt_digest=_extraction_prompt_digest(imported),
    )


def _extraction_input_digest(imported: ImportedSource) -> str:
    """Return digest for evidence-bounded scene extraction inputs."""
    anchors_by_scene: dict[str, list[dict[str, str]]] = {}
    for anchor in imported.anchors:
        anchors_by_scene.setdefault(anchor.scene_id, []).append(
            {
                "anchor_id": anchor.anchor_id,
                "quote_hash": _text_digest(anchor.quote),
            }
        )
    payload = [
        {
            "scene_id": scene.scene_id,
            "text_hash": _text_digest("\n\n".join(scene.paragraphs)),
            "evidence_anchors": anchors_by_scene.get(scene.scene_id, []),
        }
        for chapter in imported.story.chapters
        for scene in chapter.scenes
    ]
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _extraction_prompt_digest(imported: ImportedSource) -> str:
    """Return digest for evidence-bounded extraction prompts."""
    extractor = EvidenceBoundedAIExtractor(StaticAIExtractionClient("{}"))
    prompts = [
        {
            "scene_id": scene_input.scene_id,
            "prompt_hash": _text_digest(extractor.build_prompt(scene_input)),
        }
        for scene_input in _scene_extraction_inputs(imported)
    ]
    serialized = json.dumps(prompts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _scene_extraction_inputs(imported: ImportedSource) -> tuple[SceneExtractionInput, ...]:
    """Return extraction inputs in story order."""
    anchors_by_scene = _anchors_by_scene(imported)
    return tuple(
        SceneExtractionInput(
            scene_id=scene.scene_id,
            text="\n\n".join(scene.paragraphs),
            evidence_anchor_ids=tuple(
                anchor.anchor_id for anchor in anchors_by_scene.get(scene.scene_id, ())
            ),
            evidence_anchors=tuple(
                SceneEvidenceAnchor(
                    anchor_id=anchor.anchor_id,
                    quote=anchor.quote,
                )
                for anchor in anchors_by_scene.get(scene.scene_id, ())
            ),
        )
        for chapter in imported.story.chapters
        for scene in chapter.scenes
    )


def _anchors_by_scene(imported: ImportedSource) -> dict[str, tuple[EvidenceAnchor, ...]]:
    """Return evidence anchors grouped by scene ID."""
    grouped: dict[str, list[EvidenceAnchor]] = {}
    for anchor in imported.anchors:
        grouped.setdefault(anchor.scene_id, []).append(anchor)
    return {
        scene_id: tuple(scene_anchors)
        for scene_id, scene_anchors in grouped.items()
    }


def _text_digest(value: str) -> str:
    """Return a deterministic digest for imported text without storing the text."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _source_manifest_digest(chapter_files: Sequence[Path]) -> str:
    """Return a digest for ordered local source files without storing their text."""
    payload = [
        {
            "name": path.name,
            "content_hash": _text_digest(path.read_text(encoding="utf-8")),
        }
        for path in chapter_files
    ]
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _integrity_errors(imported: ImportedSource) -> list[str]:
    """Return source integrity errors that would block V1 pipeline readiness."""
    errors: list[str] = []
    paragraphs_by_id = {paragraph.paragraph_id: paragraph for paragraph in imported.paragraphs}
    sentences_by_id = {
        sentence.sentence_id: sentence
        for paragraph in imported.paragraphs
        for sentence in paragraph.sentences
    }
    anchors_by_scene: dict[str, list[str]] = {}
    sentences_by_scene: dict[str, list[str]] = {}

    for paragraph in imported.paragraphs:
        expected_sentence_indexes = tuple(range(1, len(paragraph.sentences) + 1))
        actual_sentence_indexes = tuple(
            sentence.sentence_index for sentence in paragraph.sentences
        )
        if actual_sentence_indexes != expected_sentence_indexes:
            errors.append(
                "paragraph sentence indexes are not contiguous: "
                f"{paragraph.paragraph_id}"
            )
        sentences_by_scene.setdefault(paragraph.scene_id, []).extend(
            sentence.sentence_id for sentence in paragraph.sentences
        )

    for anchor in imported.anchors:
        anchors_by_scene.setdefault(anchor.scene_id, []).append(anchor.anchor_id)
        anchor_paragraph = paragraphs_by_id.get(anchor.paragraph_id)
        anchor_sentence = sentences_by_id.get(anchor.sentence_id)
        if (
            anchor_paragraph is not None
            and anchor.paragraph_index != anchor_paragraph.paragraph_index
        ):
            errors.append(f"anchor paragraph index drifted: {anchor.anchor_id}")
        if (
            anchor_sentence is not None
            and anchor.sentence_index != anchor_sentence.sentence_index
        ):
            errors.append(f"anchor sentence index drifted: {anchor.anchor_id}")

    for chapter in imported.story.chapters:
        expected_scene_indexes = tuple(range(1, len(chapter.scenes) + 1))
        actual_scene_indexes = tuple(scene.scene_index for scene in chapter.scenes)
        if actual_scene_indexes != expected_scene_indexes:
            errors.append(
                f"chapter scene indexes are not contiguous: {chapter.chapter_id}"
            )
        for scene in chapter.scenes:
            scene_anchors = anchors_by_scene.get(scene.scene_id, [])
            scene_sentences = sentences_by_scene.get(scene.scene_id, [])
            if not scene_anchors:
                errors.append(f"scene has no evidence anchors: {scene.scene_id}")
            if len(scene_anchors) != len(scene_sentences):
                errors.append(
                    "scene anchor coverage mismatch: "
                    f"{scene.scene_id} has {len(scene_anchors)} anchors "
                    f"for {len(scene_sentences)} sentences"
                )

    if len(imported.anchors) != len(sentences_by_id):
        errors.append(
            "import anchor coverage mismatch: "
            f"{len(imported.anchors)} anchors for {len(sentences_by_id)} sentences"
        )

    return errors


def _natural_key(value: str) -> tuple[object, ...]:
    """Return a natural-sort key for chapter filenames."""
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", value)
    )


def _required_mapping(payload: dict[str, Any], key: str, path: Path) -> dict[str, Any]:
    """Read a required object field from a validation case."""
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Validation case {path} requires object field: {key}")
    return value


def _required_str(payload: dict[str, Any], key: str, path: Path) -> str:
    """Read a required string field from a validation case."""
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Validation case {path} requires string field: {key}")
    return value


def _required_int(payload: dict[str, Any], key: str, path: Path) -> int:
    """Read a required positive integer field from a validation case."""
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Validation case {path} requires integer field: {key}")
    return value


def _reject_extra_keys(
    payload: dict[str, Any],
    allowed_keys: set[str],
    path: Path,
    context: str,
) -> None:
    """Reject unsupported validation case fields."""
    extra_keys = set(payload) - allowed_keys
    if extra_keys:
        extra = ", ".join(sorted(extra_keys))
        raise ValueError(f"Unsupported {context} fields in {path}: {extra}")


def _require_text(value: str, field_name: str) -> None:
    """Validate required text."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_machine_token(value: str, field_name: str) -> None:
    """Validate required machine token."""
    _require_text(value, field_name)
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} cannot contain whitespace.")


def _require_relative_path(value: str, field_name: str) -> None:
    """Validate a case-relative local path."""
    _require_text(value, field_name)
    if Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError(f"{field_name} must be relative to the validation root.")


def _require_filename_glob(value: str, field_name: str) -> None:
    """Validate a filename-only glob pattern."""
    _require_text(value, field_name)
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        raise ValueError(f"{field_name} must be a filename-only glob.")

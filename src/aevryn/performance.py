"""Performance budgets and metadata-only snapshot helpers."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, TypedDict, TypeVar, cast

BenchmarkName = Literal[
    "import_inspect",
    "import_save",
    "project_status",
    "snapshot_creation",
    "workspace_load",
    "export_preview",
    "validation_suite",
    "worker_processing",
]
BudgetStatus = Literal["target", "acceptable", "warning", "critical", "measured"]
RegressionStatus = Literal["warning", "critical"]
_ResultT = TypeVar("_ResultT")
PERFORMANCE_BASELINE_ARTIFACT_KIND = "aevryn_phase9_performance_baseline"
PERFORMANCE_SCHEMA_VERSION = 1
BENCHMARK_NAMES: tuple[BenchmarkName, ...] = (
    "import_inspect",
    "import_save",
    "project_status",
    "snapshot_creation",
    "workspace_load",
    "export_preview",
    "validation_suite",
    "worker_processing",
)


class PerformanceMeasurementPayload(TypedDict):
    """Serialized metadata for one performance measurement."""

    benchmark: BenchmarkName
    elapsed_ms: float
    status: BudgetStatus


class PerformanceSnapshotPayload(TypedDict):
    """Serialized metadata-only performance snapshot."""

    schema_version: int
    measurements: list[PerformanceMeasurementPayload]


class PerformanceRegressionPayload(TypedDict):
    """Serialized metadata for one performance regression."""

    benchmark: BenchmarkName
    previous_ms: float
    current_ms: float
    delta_ms: float
    ratio: float
    status: RegressionStatus


class PerformanceBaselineArtifactPayload(TypedDict):
    """Serialized metadata-only performance baseline artifact."""

    artifact_kind: str
    schema_version: int
    snapshot: PerformanceSnapshotPayload


@dataclass(frozen=True)
class PerformanceBudget:
    """Latency budget for one measured Phase 9 benchmark."""

    benchmark: BenchmarkName
    target_ms: float | None
    warning_ms: float | None
    critical_ms: float | None

    def classify(self, elapsed_ms: float) -> BudgetStatus:
        """Return the budget status for an elapsed millisecond value."""
        if elapsed_ms < 0:
            raise ValueError("Elapsed milliseconds must not be negative.")
        if (
            self.target_ms is None
            or self.warning_ms is None
            or self.critical_ms is None
        ):
            return "measured"
        if elapsed_ms < self.target_ms:
            return "target"
        if elapsed_ms < self.warning_ms:
            return "acceptable"
        if elapsed_ms < self.critical_ms:
            return "warning"
        return "critical"


@dataclass(frozen=True)
class PerformanceMeasurement:
    """One metadata-only performance measurement."""

    benchmark: BenchmarkName
    elapsed_ms: float


PERFORMANCE_BUDGETS: dict[BenchmarkName, PerformanceBudget] = {
    "import_inspect": PerformanceBudget(
        benchmark="import_inspect",
        target_ms=250.0,
        warning_ms=500.0,
        critical_ms=1000.0,
    ),
    "import_save": PerformanceBudget(
        benchmark="import_save",
        target_ms=100.0,
        warning_ms=250.0,
        critical_ms=500.0,
    ),
    "project_status": PerformanceBudget(
        benchmark="project_status",
        target_ms=100.0,
        warning_ms=250.0,
        critical_ms=500.0,
    ),
    "snapshot_creation": PerformanceBudget(
        benchmark="snapshot_creation",
        target_ms=None,
        warning_ms=None,
        critical_ms=None,
    ),
    "workspace_load": PerformanceBudget(
        benchmark="workspace_load",
        target_ms=1000.0,
        warning_ms=2000.0,
        critical_ms=4000.0,
    ),
    "export_preview": PerformanceBudget(
        benchmark="export_preview",
        target_ms=500.0,
        warning_ms=1000.0,
        critical_ms=2000.0,
    ),
    "validation_suite": PerformanceBudget(
        benchmark="validation_suite",
        target_ms=None,
        warning_ms=None,
        critical_ms=None,
    ),
    "worker_processing": PerformanceBudget(
        benchmark="worker_processing",
        target_ms=None,
        warning_ms=None,
        critical_ms=None,
    ),
}


def measure_operation(
    benchmark: BenchmarkName,
    operation: Callable[[], _ResultT],
    timer: Callable[[], float] = time.perf_counter,
) -> tuple[_ResultT, PerformanceMeasurement]:
    """Run an operation and return its value plus elapsed metadata."""
    started_at = timer()
    value = operation()
    elapsed_ms = (timer() - started_at) * 1000
    return value, PerformanceMeasurement(
        benchmark=benchmark,
        elapsed_ms=round(elapsed_ms, 3),
    )


def run_performance_baseline(
    operations: Mapping[BenchmarkName, Callable[[], object]],
    timer: Callable[[], float] = time.perf_counter,
) -> PerformanceSnapshotPayload:
    """Run benchmark operations and return a metadata-only baseline snapshot."""
    measurements: list[PerformanceMeasurement] = []
    for benchmark, operation in operations.items():
        _value, measurement = measure_operation(
            benchmark=benchmark,
            operation=operation,
            timer=timer,
        )
        measurements.append(measurement)
    return build_performance_snapshot(measurements)


def build_performance_snapshot(
    measurements: list[PerformanceMeasurement],
) -> PerformanceSnapshotPayload:
    """Build a stable metadata-only performance snapshot payload."""
    payload_measurements: list[PerformanceMeasurementPayload] = []
    seen: set[BenchmarkName] = set()
    for measurement in sorted(measurements, key=lambda item: item.benchmark):
        if measurement.benchmark in seen:
            raise ValueError("Performance measurement benchmarks must be unique.")
        seen.add(measurement.benchmark)
        budget = PERFORMANCE_BUDGETS[measurement.benchmark]
        elapsed_ms = round(measurement.elapsed_ms, 3)
        payload_measurements.append(
            {
                "benchmark": measurement.benchmark,
                "elapsed_ms": elapsed_ms,
                "status": budget.classify(elapsed_ms),
            }
        )
    return {
        "schema_version": PERFORMANCE_SCHEMA_VERSION,
        "measurements": payload_measurements,
    }


def build_performance_baseline_artifact(
    snapshot: PerformanceSnapshotPayload,
) -> PerformanceBaselineArtifactPayload:
    """Wrap a performance snapshot in a stable baseline artifact envelope."""
    _validate_performance_snapshot(snapshot)
    return {
        "artifact_kind": PERFORMANCE_BASELINE_ARTIFACT_KIND,
        "schema_version": PERFORMANCE_SCHEMA_VERSION,
        "snapshot": snapshot,
    }


def performance_baseline_json(snapshot: PerformanceSnapshotPayload) -> str:
    """Return stable JSON text for a metadata-only performance baseline."""
    artifact = build_performance_baseline_artifact(snapshot)
    return json.dumps(artifact, indent=2, sort_keys=True) + "\n"


def load_performance_baseline_json(text: str) -> PerformanceSnapshotPayload:
    """Load and validate metadata-only performance baseline JSON text."""
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Performance baseline artifact must be an object.")
    if payload.get("artifact_kind") != PERFORMANCE_BASELINE_ARTIFACT_KIND:
        raise ValueError("Performance baseline artifact kind is unsupported.")
    if payload.get("schema_version") != PERFORMANCE_SCHEMA_VERSION:
        raise ValueError("Performance baseline schema version is unsupported.")
    snapshot = payload.get("snapshot")
    _validate_performance_snapshot(snapshot)
    return cast(PerformanceSnapshotPayload, snapshot)


def compare_performance_snapshots(
    previous: PerformanceSnapshotPayload,
    current: PerformanceSnapshotPayload,
) -> list[PerformanceRegressionPayload]:
    """Return major latency regressions between two metadata-only snapshots."""
    _validate_performance_snapshot(previous)
    _validate_performance_snapshot(current)
    previous_measurements = {
        measurement["benchmark"]: measurement for measurement in previous["measurements"]
    }
    regressions: list[PerformanceRegressionPayload] = []
    for measurement in current["measurements"]:
        benchmark = measurement["benchmark"]
        if benchmark not in previous_measurements:
            continue
        previous_ms = previous_measurements[benchmark]["elapsed_ms"]
        current_ms = measurement["elapsed_ms"]
        delta_ms = round(current_ms - previous_ms, 3)
        if delta_ms < 100.0 or previous_ms <= 0:
            continue
        ratio = round(current_ms / previous_ms, 3)
        status = _regression_status(delta_ms=delta_ms, ratio=ratio)
        if status is None:
            continue
        regressions.append(
            {
                "benchmark": benchmark,
                "previous_ms": previous_ms,
                "current_ms": current_ms,
                "delta_ms": delta_ms,
                "ratio": ratio,
                "status": status,
            }
        )
    return sorted(regressions, key=lambda item: item["benchmark"])


def _regression_status(delta_ms: float, ratio: float) -> RegressionStatus | None:
    """Return regression severity for a latency change."""
    if ratio >= 4.0 and delta_ms >= 250.0:
        return "critical"
    if ratio >= 2.0:
        return "warning"
    return None


def _validate_performance_snapshot(payload: object) -> None:
    """Validate a metadata-only performance snapshot payload."""
    if not isinstance(payload, dict):
        raise ValueError("Performance snapshot must be an object.")
    if payload.get("schema_version") != PERFORMANCE_SCHEMA_VERSION:
        raise ValueError("Performance snapshot schema version is unsupported.")
    measurements = payload.get("measurements")
    if not isinstance(measurements, list):
        raise ValueError("Performance snapshot measurements must be a list.")
    seen: set[str] = set()
    for measurement in measurements:
        if not isinstance(measurement, dict):
            raise ValueError("Performance measurement must be an object.")
        benchmark = measurement.get("benchmark")
        if benchmark not in BENCHMARK_NAMES:
            raise ValueError("Performance measurement benchmark is unsupported.")
        if benchmark in seen:
            raise ValueError("Performance measurement benchmarks must be unique.")
        seen.add(str(benchmark))
        elapsed_ms = measurement.get("elapsed_ms")
        if not isinstance(elapsed_ms, int | float) or elapsed_ms < 0:
            raise ValueError("Performance measurement elapsed_ms must be non-negative.")
        status = measurement.get("status")
        expected_status = PERFORMANCE_BUDGETS[cast(BenchmarkName, benchmark)].classify(
            float(elapsed_ms)
        )
        if status != expected_status:
            raise ValueError("Performance measurement status does not match budget.")

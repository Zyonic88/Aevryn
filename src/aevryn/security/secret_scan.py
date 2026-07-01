"""Repository secret scanning for tracked release files."""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

MAX_SCANNED_BYTES = 2_000_000


@dataclass(frozen=True)
class SecretRule:
    id: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class SecretScanFinding:
    path: str
    line_number: int
    rule_id: str
    snippet: str


SECRET_RULES: tuple[SecretRule, ...] = (
    SecretRule(
        id="openai_api_key",
        pattern=re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{19,}\b"),
    ),
    SecretRule(
        id="aws_access_key_id",
        pattern=re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    SecretRule(
        id="private_key_block",
        pattern=re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    SecretRule(
        id="assigned_secret",
        pattern=re.compile(
            r"(?i)^\s*(?:export\s+)?[A-Z0-9_-]*(?:api[_-]?key|secret|token|password)"
            r"[A-Z0-9_-]*\s*[:=]\s*[\"']?([A-Za-z0-9][A-Za-z0-9_.\-/+=]{15,})[\"']?"
        ),
    ),
)


ALLOWED_PLACEHOLDER_MARKERS = (
    "...",
    "<",
    ">",
    "example",
    "placeholder",
    "redacted",
    "test",
    "fake",
    "dummy",
    "sample",
    "local-dev-key",
    "production-api-key",
    "secret-provider-key",
    "secret-key",
    "another-key",
    "do-not-log",
)


def tracked_files(root: Path) -> tuple[Path, ...]:
    """Return git-tracked files under root."""

    # Fixed git command, no shell, repository root only.
    result = subprocess.run(  # nosec B603 B607
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
        text=False,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return tuple(root / path for path in paths if path)


def scan_paths(paths: Iterable[Path], *, root: Path) -> tuple[SecretScanFinding, ...]:
    findings: list[SecretScanFinding] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if len(raw) > MAX_SCANNED_BYTES or b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        display_path = _relative_path(path, root)
        findings.extend(scan_text(display_path, text))
    return tuple(findings)


def scan_text(path: str, text: str) -> tuple[SecretScanFinding, ...]:
    findings: list[SecretScanFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _is_allowed_placeholder(line):
            continue
        matched_spans: list[tuple[int, int]] = []
        for rule in SECRET_RULES:
            for match in rule.pattern.finditer(line):
                secret = match.group(1) if rule.id == "assigned_secret" else match.group(0)
                if _is_allowed_placeholder(secret) or (
                    rule.id == "assigned_secret" and _is_runtime_reference(secret)
                ):
                    continue
                secret_start, secret_end = (
                    match.span(1) if rule.id == "assigned_secret" else match.span(0)
                )
                if _overlaps_existing_span(secret_start, secret_end, matched_spans):
                    continue
                matched_spans.append((secret_start, secret_end))
                findings.append(
                    SecretScanFinding(
                        path=path,
                        line_number=line_number,
                        rule_id=rule.id,
                        snippet=_redact_line(line, secret_start, secret_end),
                    )
                )
    return tuple(findings)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan tracked repository files for secrets.")
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Optional files or directories to scan instead of git-tracked files.",
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    paths = _expanded_paths(args.paths, root) if args.paths else tracked_files(root)
    findings = scan_paths(paths, root=root)

    return 1 if findings else 0


def _expanded_paths(paths: Sequence[Path], root: Path) -> tuple[Path, ...]:
    expanded: list[Path] = []
    for input_path in paths:
        path = input_path if input_path.is_absolute() else root / input_path
        if path.is_dir():
            expanded.extend(child for child in path.rglob("*") if child.is_file())
        else:
            expanded.append(path)
    return tuple(expanded)


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_allowed_placeholder(value: str) -> bool:
    normalized = value.lower()
    return any(marker in normalized for marker in ALLOWED_PLACEHOLDER_MARKERS)


def _is_runtime_reference(value: str) -> bool:
    normalized = value.lower()
    return (
        normalized.startswith(
            (
                "payload.",
                "request.",
                "reset.",
                "result.",
                "session.",
                "self.",
                "config.",
                "settings.",
                "token_factory.",
                "os.",
            )
        )
        or value.upper() == value
    )


def _overlaps_existing_span(
    start: int, end: int, existing_spans: Iterable[tuple[int, int]]
) -> bool:
    return any(
        start < existing_end and end > existing_start
        for existing_start, existing_end in existing_spans
    )


def _redact_line(line: str, start: int, end: int) -> str:
    redacted = f"{line[:start]}<redacted>{line[end:]}"
    return redacted.strip()[:160]


if __name__ == "__main__":
    raise SystemExit(main())

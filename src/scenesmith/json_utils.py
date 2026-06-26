"""Shared JSON parsing helpers for strict SceneSmith inputs."""

from __future__ import annotations

import json
from typing import Any, NoReturn


def loads_json_without_duplicate_keys(raw_json: str) -> Any:
    """Parse JSON text and reject duplicate object keys.

    Parameters:
        raw_json: JSON text to parse. A UTF-8 BOM is tolerated.

    Returns:
        Parsed JSON value.

    Raises:
        ValueError: If the input is not text.
        ValueError: If any JSON object contains duplicate keys.
        json.JSONDecodeError: If the input is not valid JSON.
    """
    if not isinstance(raw_json, str):
        raise ValueError("JSON input must be text.")

    return json.loads(
        raw_json.lstrip("\ufeff"),
        object_pairs_hook=_object_without_duplicate_keys,
        parse_constant=_reject_non_standard_json_constant,
    )


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting duplicate keys."""
    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError(f"JSON object contains duplicate key: {key}")
        parsed[key] = value

    return parsed


def _reject_non_standard_json_constant(value: str) -> NoReturn:
    """Reject JSON constants that are accepted by Python but not strict JSON."""
    raise ValueError(f"JSON input contains non-standard constant: {value}")

"""Shared JSON parsing helpers for strict SceneSmith inputs."""

from __future__ import annotations

import json
from typing import Any


def loads_json_without_duplicate_keys(raw_json: str) -> Any:
    """Parse JSON text and reject duplicate object keys.

    Parameters:
        raw_json: JSON text to parse. A UTF-8 BOM is tolerated.

    Returns:
        Parsed JSON value.

    Raises:
        ValueError: If any JSON object contains duplicate keys.
        json.JSONDecodeError: If the input is not valid JSON.
    """
    return json.loads(
        raw_json.lstrip("\ufeff"),
        object_pairs_hook=_object_without_duplicate_keys,
    )


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting duplicate keys."""
    parsed: dict[str, Any] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError(f"JSON object contains duplicate key: {key}")
        parsed[key] = value

    return parsed

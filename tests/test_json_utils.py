"""Tests for strict JSON parsing helpers."""

from typing import Any, cast

import pytest

from scenesmith.json_utils import loads_json_without_duplicate_keys


def test_strict_json_parser_accepts_utf8_bom_text() -> None:
    """Strict JSON parsing accepts text files saved with a UTF-8 BOM."""
    parsed = loads_json_without_duplicate_keys('\ufeff{"value": 1}')

    assert parsed == {"value": 1}


def test_strict_json_parser_rejects_nested_duplicate_keys() -> None:
    """Duplicate JSON keys are rejected at every object level."""
    with pytest.raises(ValueError, match="duplicate key: value"):
        loads_json_without_duplicate_keys('{"outer": {"value": 1, "value": 2}}')


def test_strict_json_parser_rejects_non_standard_constants() -> None:
    """Strict JSON parsing rejects NaN and Infinity constants."""
    with pytest.raises(ValueError, match="non-standard constant: NaN"):
        loads_json_without_duplicate_keys('{"confidence": NaN}')


def test_strict_json_parser_rejects_non_text_input() -> None:
    """Strict JSON parsing requires decoded text input."""
    with pytest.raises(ValueError, match="JSON input must be text"):
        loads_json_without_duplicate_keys(cast(Any, b'{"value": 1}'))

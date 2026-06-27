"""Tests for the Aevryn public package API."""

import aevryn


def test_public_api_exports_are_unique_and_resolvable() -> None:
    """Top-level exports should not drift away from available V1 symbols."""
    exported_names = aevryn.__all__

    assert len(exported_names) == len(set(exported_names))
    for exported_name in exported_names:
        assert hasattr(aevryn, exported_name), exported_name

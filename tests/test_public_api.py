"""Tests for the SceneSmith public package API."""

import scenesmith


def test_public_api_exports_are_unique_and_resolvable() -> None:
    """Top-level exports should not drift away from available V1 symbols."""
    exported_names = scenesmith.__all__

    assert len(exported_names) == len(set(exported_names))
    for exported_name in exported_names:
        assert hasattr(scenesmith, exported_name), exported_name

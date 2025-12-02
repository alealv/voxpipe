"""Tests for our own API exposition."""

from __future__ import annotations

import voxpipe


def test_version_exists() -> None:
    """Version is accessible."""
    assert hasattr(voxpipe, "__version__")
    assert isinstance(voxpipe.__version__, str)


def test_app_exists() -> None:
    """App is accessible."""
    assert hasattr(voxpipe, "app")
    assert "app" in voxpipe.__all__

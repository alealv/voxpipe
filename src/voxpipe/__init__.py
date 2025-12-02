"""voxpipe package.

Audio pipeline for videos.
"""

from __future__ import annotations

from voxpipe._internal.cli import app
from voxpipe._internal.debug import _get_version

__version__ = _get_version()
__all__: list[str] = ["app"]

"""JSON I/O utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path | str) -> dict[str, Any]:
    """Read JSON file and return parsed data.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed JSON data as dictionary.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path | str, data: dict[str, Any], indent: int = 2) -> None:
    """Write data to JSON file.

    Args:
        path: Path to output file.
        data: Data to serialize.
        indent: JSON indentation level.
    """
    Path(path).write_text(
        json.dumps(data, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )

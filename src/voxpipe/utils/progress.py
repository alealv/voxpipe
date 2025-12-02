"""Progress display utilities."""

from __future__ import annotations

import sys
from typing import Any


def print_progress(current: int, total: int, message: str = "Processing") -> None:
    """Print progress indicator to stderr.

    Args:
        current: Current item number (1-indexed).
        total: Total number of items.
        message: Action description.
    """
    percentage = int((current / total) * 100) if total > 0 else 0
    print(
        f"\r[{current}/{total}] {message}... ({percentage}%)",
        end="",
        flush=True,
        file=sys.stderr,
    )


def print_done(message: str = "Done") -> None:
    """Print completion message.

    Args:
        message: Completion message.
    """
    print(f"\n{message}", file=sys.stderr)


def progress_hook(*args: Any, **kwargs: Any) -> None:
    """Progress hook compatible with pyannote callbacks.

    Args:
        args: Positional arguments (expects completed, total as first two).
        kwargs: Ignored keyword arguments.
    """
    if (
        len(args) >= 2
        and isinstance(args[0], (int, float))
        and isinstance(args[1], (int, float))
    ):
        completed, total = args[0], args[1]
        if total > 0:
            percentage = int((completed / total) * 100)
            print(
                f"\rProcessing: {completed}/{total} ({percentage}%)", end="", flush=True
            )

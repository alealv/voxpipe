"""Audio transcription using whisper-cli."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from voxpipe.config import config


def transcribe(
    audio_path: Path | str,
    output_path: Path | str,
    whisper_bin: Path | None = None,
    whisper_model: Path | None = None,
) -> Path:
    """Transcribe audio file using whisper-cli.

    Args:
        audio_path: Path to input audio file.
        output_path: Path to output JSON file (without extension).
        whisper_bin: Path to whisper-cli binary (default from config).
        whisper_model: Path to whisper model (default from config).

    Returns:
        Path to the transcript JSON file.

    Raises:
        subprocess.CalledProcessError: If whisper-cli fails.
        FileNotFoundError: If whisper-cli is not found.
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    whisper_bin = whisper_bin or config.whisper_bin
    whisper_model = whisper_model or config.whisper_model

    # Remove .json extension if provided (whisper adds it)
    if output_path.suffix == ".json":
        output_path = output_path.with_suffix("")

    cmd = [
        str(whisper_bin),
        "-m",
        str(whisper_model),
        "-f",
        str(audio_path),
        "-oj",  # Output JSON
        "-of",
        str(output_path),
    ]

    print(f"Transcribing: {audio_path}", file=sys.stderr)
    subprocess.run(cmd, check=True)

    result_path = Path(f"{output_path}.json")
    print(f"Transcript saved to: {result_path}", file=sys.stderr)

    return result_path

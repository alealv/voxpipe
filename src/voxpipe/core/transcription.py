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
    language: str | None = None,
    max_len: int = 0,
    no_context: bool = False,
    entropy_threshold: float = 2.4,
    logprob_threshold: float = -1.0,
    no_timestamps: bool = False,
) -> Path:
    """Transcribe audio file using whisper-cli.

    Args:
        audio_path: Path to input audio file.
        output_path: Path to output JSON file (without extension).
        whisper_bin: Path to whisper-cli binary (default from config).
        whisper_model: Path to whisper model (default from config).
        language: Language code (e.g., 'en', 'de'). Auto-detect if None.
        max_len: Maximum segment length in characters (0 = no limit).
        no_context: Disable previous context to prevent hallucination loops.
        entropy_threshold: Entropy threshold for decoder fail (default 2.4).
        logprob_threshold: Log probability threshold for decoder fail (default -1.0).
        no_timestamps: Disable timestamp output.

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
        # Anti-hallucination parameters
        "-et",
        str(entropy_threshold),
        "-lpt",
        str(logprob_threshold),
    ]

    if language:
        cmd.extend(["-l", language])

    if max_len > 0:
        cmd.extend(["-ml", str(max_len)])

    if no_context:
        cmd.append("-nc")

    if no_timestamps:
        cmd.append("-nt")

    print(f"Transcribing: {audio_path}", file=sys.stderr)
    subprocess.run(cmd, check=True)

    result_path = Path(f"{output_path}.json")
    print(f"Transcript saved to: {result_path}", file=sys.stderr)

    return result_path

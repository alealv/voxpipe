"""Audio extraction from video files."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def extract_audio(
    video_path: Path | str,
    output_path: Path | str,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Extract audio from video file using ffmpeg.

    Args:
        video_path: Path to input video file.
        output_path: Path to output WAV file.
        sample_rate: Audio sample rate (default 16kHz for whisper).
        channels: Number of audio channels (default 1 for mono).

    Returns:
        Path to the extracted audio file.

    Raises:
        subprocess.CalledProcessError: If ffmpeg fails.
        FileNotFoundError: If ffmpeg is not installed.
    """
    video_path = Path(video_path)
    output_path = Path(output_path)

    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",  # No video
        "-acodec",
        "pcm_s16le",  # PCM 16-bit
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        str(output_path),
        "-y",  # Overwrite
    ]

    print(f"Extracting audio from: {video_path}", file=sys.stderr)
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"Audio saved to: {output_path}", file=sys.stderr)

    return output_path

"""Speaker diarization using pyannote.audio."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pyannote.audio import Pipeline

from voxpipe.config import config
from voxpipe.utils.device import device_name, get_best_device
from voxpipe.utils.io import write_json
from voxpipe.utils.progress import progress_hook


def run_diarization(
    audio_path: Path | str,
    output_path: Path | str,
    num_speakers: int | None = None,
    hf_token: str | None = None,
) -> dict[str, Any]:
    """Run speaker diarization on audio file.

    Args:
        audio_path: Path to input audio file.
        output_path: Path to output JSON file.
        num_speakers: Number of speakers (auto-detect if None).
        hf_token: Hugging Face token (default from config/env).

    Returns:
        Diarization result dictionary.

    Raises:
        ValueError: If HF_TOKEN is not set.
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    hf_token = hf_token or config.hf_token

    if not hf_token:
        msg = "HF_TOKEN environment variable not set"
        raise ValueError(msg)

    # Load pipeline
    print("Loading pyannote speaker diarization pipeline...", file=sys.stderr)
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token,
    )
    if pipeline is None:
        msg = "Failed to load pyannote pipeline"
        raise RuntimeError(msg)

    # Setup device
    device = get_best_device()
    print(f"Using device: {device_name(device)}", file=sys.stderr)
    pipeline.to(device)

    # Run diarization
    print(f"Processing: {audio_path}", file=sys.stderr)
    print("This may take several minutes...\n", file=sys.stderr)

    diarization_kwargs: dict[str, Any] = {"hook": progress_hook}
    if num_speakers:
        diarization_kwargs["num_speakers"] = num_speakers

    diarization = pipeline(str(audio_path), **diarization_kwargs)  # type: ignore[misc]
    print("\n\nDiarization complete!", file=sys.stderr)

    # Convert to structured JSON format
    segments = []
    speakers: set[str] = set()

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append(
            {
                "start": round(turn.start, 3),
                "end": round(turn.end, 3),
                "speaker": speaker,
            }
        )
        speakers.add(speaker)

    result = {
        "audio_file": str(audio_path),
        "num_speakers": len(speakers),
        "speakers": sorted(speakers),
        "segments": segments,
    }

    # Save results
    write_json(output_path, result)
    print(f"Output saved to: {output_path}", file=sys.stderr)
    print(
        f"Detected {len(speakers)} speakers: {', '.join(sorted(speakers))}",
        file=sys.stderr,
    )

    return result

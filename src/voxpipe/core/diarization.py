"""Speaker diarization using pyannote.audio."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from pyannote.audio import Pipeline

from voxpipe.config import config
from voxpipe.utils.device import device_name, get_best_device
from voxpipe.utils.io import write_json
from voxpipe.utils.progress import progress_hook

PIPELINE_MODEL = "pyannote/speaker-diarization-3.1"


def load_pipeline(hf_token: str | None = None) -> Pipeline:
    """Load the pyannote speaker diarization pipeline.

    Tries to load from local cache first. If not available and a token
    is provided, downloads from Hugging Face Hub.

    Args:
        hf_token: Hugging Face token for downloading models.

    Returns:
        Loaded Pipeline instance.

    Raises:
        RuntimeError: If pipeline cannot be loaded.
    """
    # Try loading from cache first (offline mode)
    try:
        print("Loading pyannote pipeline from cache...", file=sys.stderr)
        pipeline = Pipeline.from_pretrained(
            PIPELINE_MODEL,
            local_files_only=True,
        )
        if pipeline is not None:
            return pipeline
    except Exception:
        pass  # Cache miss, try downloading

    # Try downloading with token
    if hf_token:
        print("Downloading pyannote pipeline from Hugging Face...", file=sys.stderr)
        pipeline = Pipeline.from_pretrained(
            PIPELINE_MODEL,
            use_auth_token=hf_token,
        )
        if pipeline is not None:
            return pipeline

    msg = (
        "Failed to load pyannote pipeline. "
        "Either download models first with HF_TOKEN set, "
        "or ensure models are cached in ~/.cache/torch/pyannote/"
    )
    raise RuntimeError(msg)


def run_diarization(
    audio_path: Path | str,
    output_path: Path | str,
    num_speakers: int | None = None,
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    hf_token: str | None = None,
) -> dict[str, Any]:
    """Run speaker diarization on audio file.

    Args:
        audio_path: Path to input audio file.
        output_path: Path to output JSON file.
        num_speakers: Exact number of speakers (auto-detect if None).
        min_speakers: Minimum number of speakers (for auto-detection).
        max_speakers: Maximum number of speakers (for auto-detection).
        hf_token: Hugging Face token for downloading models (optional if cached).

    Returns:
        Diarization result dictionary.
    """
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    hf_token = hf_token or config.hf_token or os.environ.get("HF_TOKEN")

    # Load pipeline (tries cache first, then downloads if token available)
    pipeline = load_pipeline(hf_token)

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
    if min_speakers:
        diarization_kwargs["min_speakers"] = min_speakers
    if max_speakers:
        diarization_kwargs["max_speakers"] = max_speakers

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

"""Merge whisper transcript with speaker diarization."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from voxpipe.utils.io import read_json, write_json


def calculate_overlap(
    seg_start: float,
    seg_end: float,
    diar_start: float,
    diar_end: float,
) -> float:
    """Calculate overlap duration between two time ranges.

    Args:
        seg_start: Segment start time.
        seg_end: Segment end time.
        diar_start: Diarization segment start.
        diar_end: Diarization segment end.

    Returns:
        Overlap duration in seconds.
    """
    overlap_start = max(seg_start, diar_start)
    overlap_end = min(seg_end, diar_end)
    return max(0, overlap_end - overlap_start)


def find_dominant_speaker(
    seg_start: float,
    seg_end: float,
    diarization_segments: list[dict[str, Any]],
) -> str:
    """Find speaker with most overlap for a given segment.

    Args:
        seg_start: Segment start time.
        seg_end: Segment end time.
        diarization_segments: List of diarization segments.

    Returns:
        Speaker ID with most overlap, or "UNKNOWN".
    """
    speaker_overlaps: dict[str, float] = {}

    for diar in diarization_segments:
        overlap = calculate_overlap(seg_start, seg_end, diar["start"], diar["end"])
        if overlap > 0:
            speaker = diar["speaker"]
            speaker_overlaps[speaker] = speaker_overlaps.get(speaker, 0) + overlap

    if not speaker_overlaps:
        return "UNKNOWN"

    return max(speaker_overlaps, key=lambda k: speaker_overlaps[k])


def merge_transcript(
    transcript_path: Path | str,
    diarization_path: Path | str,
    output_path: Path | str,
) -> dict[str, Any]:
    """Merge transcript with speaker diarization.

    Args:
        transcript_path: Path to whisper transcript JSON.
        diarization_path: Path to diarization JSON.
        output_path: Path to output merged JSON.

    Returns:
        Merged result dictionary.
    """
    transcript_path = Path(transcript_path)
    diarization_path = Path(diarization_path)
    output_path = Path(output_path)

    # Load data
    transcript_data = read_json(transcript_path)
    diarization_data = read_json(diarization_path)
    diar_segments = diarization_data["segments"]

    # Process transcript segments
    merged_segments = []

    # Handle whisper.cpp JSON output format
    if "transcription" in transcript_data:
        for seg in transcript_data["transcription"]:
            start_ms = seg.get("offsets", {}).get("from", 0)
            end_ms = seg.get("offsets", {}).get("to", 0)
            start = start_ms / 1000.0
            end = end_ms / 1000.0
            text = seg.get("text", "").strip()

            if text:
                speaker = find_dominant_speaker(start, end, diar_segments)
                merged_segments.append(
                    {
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "speaker": speaker,
                        "text": text,
                    }
                )
    # Handle standard whisper JSON format
    elif "segments" in transcript_data:
        for seg in transcript_data["segments"]:
            start = seg.get("start", 0)
            end = seg.get("end", 0)
            text = seg.get("text", "").strip()

            if text:
                speaker = find_dominant_speaker(start, end, diar_segments)
                merged_segments.append(
                    {
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "speaker": speaker,
                        "text": text,
                    }
                )

    # Consolidate consecutive segments from same speaker
    consolidated: list[dict[str, Any]] = []
    for seg in merged_segments:
        if consolidated and consolidated[-1]["speaker"] == seg["speaker"]:
            consolidated[-1]["end"] = seg["end"]
            consolidated[-1]["text"] += " " + seg["text"]
        else:
            consolidated.append(seg.copy())

    result = {
        "source_transcript": str(transcript_path),
        "source_diarization": str(diarization_path),
        "speakers": diarization_data.get("speakers", []),
        "segments": consolidated,
    }

    # Save output
    write_json(output_path, result)
    print(f"Merged transcript saved to: {output_path}", file=sys.stderr)
    print(f"Total segments: {len(consolidated)}", file=sys.stderr)

    return result

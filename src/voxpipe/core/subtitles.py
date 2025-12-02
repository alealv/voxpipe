"""Subtitle export functionality."""

from __future__ import annotations

import sys
from pathlib import Path

from voxpipe.utils.io import read_json
from voxpipe.utils.timestamps import seconds_to_srt, seconds_to_vtt


def export_srt(
    input_path: Path | str,
    output_path: Path | str,
    include_speaker: bool = True,
) -> None:
    """Export transcript to SRT subtitle format.

    Args:
        input_path: Path to input transcript JSON.
        output_path: Path to output SRT file.
        include_speaker: Whether to include speaker labels.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    data = read_json(input_path)
    segments = data.get("segments", [])

    srt_lines = []
    for i, seg in enumerate(segments, 1):
        start = seconds_to_srt(seg.get("start", 0))
        end = seconds_to_srt(seg.get("end", 0))
        text = seg.get("text", "").strip()
        speaker = seg.get("speaker", "")

        if include_speaker and speaker:
            text = f"[{speaker}] {text}"

        srt_lines.append(str(i))
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between entries

    srt_content = "\n".join(srt_lines)
    output_path.write_text(srt_content, encoding="utf-8")

    print(f"SRT saved to: {output_path}", file=sys.stderr)
    print(f"Total subtitles: {len(segments)}", file=sys.stderr)


def export_vtt(
    input_path: Path | str,
    output_path: Path | str,
    include_speaker: bool = True,
) -> None:
    """Export transcript to WebVTT subtitle format.

    Args:
        input_path: Path to input transcript JSON.
        output_path: Path to output VTT file.
        include_speaker: Whether to include speaker labels.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    data = read_json(input_path)
    segments = data.get("segments", [])

    vtt_lines = ["WEBVTT", ""]
    for i, seg in enumerate(segments, 1):
        start = seconds_to_vtt(seg.get("start", 0))
        end = seconds_to_vtt(seg.get("end", 0))
        text = seg.get("text", "").strip()
        speaker = seg.get("speaker", "")

        if include_speaker and speaker:
            text = f"<v {speaker}>{text}"

        vtt_lines.append(str(i))
        vtt_lines.append(f"{start} --> {end}")
        vtt_lines.append(text)
        vtt_lines.append("")

    vtt_content = "\n".join(vtt_lines)
    output_path.write_text(vtt_content, encoding="utf-8")

    print(f"VTT saved to: {output_path}", file=sys.stderr)
    print(f"Total subtitles: {len(segments)}", file=sys.stderr)

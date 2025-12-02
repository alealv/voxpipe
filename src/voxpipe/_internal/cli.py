"""Command-line interface for voxpipe."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from voxpipe._internal import debug

PIPELINE_DIAGRAM = """\
┌─────────────────────────────────────────────────────────────┐
│                      Pipeline Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────┐   ┌─────────┐   ┌───────┐   ┌───────────┐       │
│  │ Video │──▶│ Extract │──▶│ Audio │──▶│Transcribe │       │
│  └───────┘   └─────────┘   └───────┘   └─────┬─────┘       │
│                                              │              │
│                                              ▼              │
│  ┌─────────┐   ┌───────┐   ┌─────────┐   ┌─────────┐       │
│  │ Diarize │──▶│ Merge │──▶│ Correct │──▶│Translate│       │
│  └─────────┘   └───────┘   └─────────┘   └────┬────┘       │
│                                               │             │
│                                               ▼             │
│                            ┌────────┐   ┌─────────┐        │
│                            │ Export │──▶│ SRT/VTT │        │
│                            └────────┘   └─────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘"""

console = Console()


def show_help_with_diagram(ctx: typer.Context, param: typer.CallbackParam, value: bool) -> None:
    """Show help with pipeline diagram."""
    if value:
        # Print standard help
        typer.echo(ctx.get_help())
        # Print diagram
        console.print()
        console.print(PIPELINE_DIAGRAM, highlight=False)
        raise typer.Exit()


app = typer.Typer(
    name="voxpipe",
    help="Video/audio processing pipeline with transcription, diarization, and translation.",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"voxpipe {debug._get_version()}")
        raise typer.Exit()


def debug_callback(value: bool) -> None:
    """Print debug info and exit."""
    if value:
        debug._print_debug_info()
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version.",
        ),
    ] = False,
    debug_info: Annotated[
        bool,
        typer.Option(
            "--debug-info",
            callback=debug_callback,
            is_eager=True,
            help="Print debug information.",
        ),
    ] = False,
    help_flag: Annotated[
        bool,
        typer.Option(
            "--help",
            "-h",
            callback=show_help_with_diagram,
            is_eager=True,
            help="Show this message and exit.",
        ),
    ] = False,
) -> None:
    """Voxpipe - Video/audio processing pipeline."""
    if ctx.invoked_subcommand is None:
        # No command given, show help with diagram
        typer.echo(ctx.get_help())
        console.print()
        console.print(PIPELINE_DIAGRAM, highlight=False)
        raise typer.Exit()


# --- Extract Command ---
@app.command()
def extract(
    video: Annotated[Path, typer.Argument(help="Input video file")],
    output: Annotated[Path, typer.Argument(help="Output WAV file")],
    sample_rate: Annotated[
        int, typer.Option("--rate", "-r", help="Sample rate")
    ] = 16000,
    channels: Annotated[
        int, typer.Option("--channels", "-c", help="Number of channels")
    ] = 1,
) -> None:
    """Extract audio from video file."""
    from voxpipe.core.audio import extract_audio

    extract_audio(video, output, sample_rate, channels)
    typer.echo(f"Audio extracted to: {output}")


# --- Transcribe Command ---
@app.command()
def transcribe(
    audio: Annotated[Path, typer.Argument(help="Input audio file")],
    output: Annotated[Path, typer.Argument(help="Output JSON file")],
    whisper_bin: Annotated[
        Optional[Path], typer.Option("--bin", help="Whisper binary path")
    ] = None,
    whisper_model: Annotated[
        Optional[Path], typer.Option("--model", "-m", help="Whisper model path")
    ] = None,
    language: Annotated[
        Optional[str], typer.Option("--lang", "-l", help="Language code (e.g., 'en', 'de')")
    ] = None,
    max_len: Annotated[
        int, typer.Option("--max-len", help="Max segment length in chars (0=unlimited)")
    ] = 0,
    no_context: Annotated[
        bool, typer.Option("--no-context", help="Disable context to prevent hallucination loops")
    ] = False,
) -> None:
    """Transcribe audio with Whisper."""
    from voxpipe.core.transcription import transcribe as do_transcribe

    result = do_transcribe(
        audio,
        output,
        whisper_bin,
        whisper_model,
        language=language,
        max_len=max_len,
        no_context=no_context,
    )
    typer.echo(f"Transcript saved to: {result}")


# --- Diarize Command ---
@app.command()
def diarize(
    audio: Annotated[Path, typer.Argument(help="Input audio file")],
    output: Annotated[Path, typer.Argument(help="Output JSON file")],
    speakers: Annotated[
        Optional[int], typer.Option("--speakers", "-s", help="Exact number of speakers")
    ] = None,
    min_speakers: Annotated[
        Optional[int], typer.Option("--min", help="Minimum number of speakers")
    ] = None,
    max_speakers: Annotated[
        Optional[int], typer.Option("--max", help="Maximum number of speakers")
    ] = None,
) -> None:
    """Run speaker diarization on audio file."""
    from voxpipe.core.diarization import run_diarization

    run_diarization(audio, output, speakers, min_speakers, max_speakers)
    typer.echo(f"Diarization saved to: {output}")


# --- Merge Command ---
@app.command()
def merge(
    transcript: Annotated[Path, typer.Argument(help="Whisper transcript JSON")],
    diarization: Annotated[Path, typer.Argument(help="Diarization JSON")],
    output: Annotated[Path, typer.Argument(help="Output merged JSON")],
) -> None:
    """Merge transcript with speaker diarization."""
    from voxpipe.core.merger import merge_transcript

    merge_transcript(transcript, diarization, output)
    typer.echo(f"Merged transcript saved to: {output}")


# --- Correct Command ---
@app.command()
def correct(
    input_file: Annotated[Path, typer.Argument(help="Input transcript JSON")],
    output: Annotated[Path, typer.Argument(help="Output corrected JSON")],
    model: Annotated[
        Optional[str], typer.Option("--model", "-m", help="Ollama model")
    ] = None,
    base_url: Annotated[
        Optional[str], typer.Option("--url", help="Ollama base URL")
    ] = None,
) -> None:
    """Correct transcript grammar and ASR errors."""
    from voxpipe.core.llm import correct_transcript

    correct_transcript(input_file, output, model, base_url)
    typer.echo(f"Corrected transcript saved to: {output}")


# --- Translate Command ---
@app.command()
def translate(
    input_file: Annotated[Path, typer.Argument(help="Input transcript JSON")],
    output: Annotated[Path, typer.Argument(help="Output translated JSON")],
    lang: Annotated[
        str, typer.Option("--lang", "-l", help="Target language")
    ] = "Spanish",
    model: Annotated[
        Optional[str], typer.Option("--model", "-m", help="Ollama model")
    ] = None,
    base_url: Annotated[
        Optional[str], typer.Option("--url", help="Ollama base URL")
    ] = None,
) -> None:
    """Translate transcript to another language."""
    from voxpipe.core.llm import translate_transcript

    translate_transcript(input_file, output, lang, model, base_url)
    typer.echo(f"Translated transcript saved to: {output}")


# --- Export Command ---
export_app = typer.Typer(help="Export transcript to subtitle formats.")
app.add_typer(export_app, name="export")


@export_app.command("srt")
def export_srt(
    input_file: Annotated[Path, typer.Argument(help="Input transcript JSON")],
    output: Annotated[Path, typer.Argument(help="Output SRT file")],
    no_speaker: Annotated[
        bool, typer.Option("--no-speaker", help="Exclude speaker labels")
    ] = False,
) -> None:
    """Export transcript to SRT format."""
    from voxpipe.core.subtitles import export_srt as do_export_srt

    do_export_srt(input_file, output, include_speaker=not no_speaker)
    typer.echo(f"SRT saved to: {output}")


@export_app.command("vtt")
def export_vtt(
    input_file: Annotated[Path, typer.Argument(help="Input transcript JSON")],
    output: Annotated[Path, typer.Argument(help="Output VTT file")],
    no_speaker: Annotated[
        bool, typer.Option("--no-speaker", help="Exclude speaker labels")
    ] = False,
) -> None:
    """Export transcript to WebVTT format."""
    from voxpipe.core.subtitles import export_vtt as do_export_vtt

    do_export_vtt(input_file, output, include_speaker=not no_speaker)
    typer.echo(f"VTT saved to: {output}")


# --- Pipeline Command ---
pipeline_app = typer.Typer(
    help="Run complete processing pipelines.",
)
app.add_typer(pipeline_app, name="pipeline")


@pipeline_app.command("run")
def pipeline_run(
    video: Annotated[Path, typer.Argument(help="Input video file")],
    output_dir: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("."),
    lang: Annotated[
        str, typer.Option("--lang", "-l", help="Target language for translation")
    ] = "Spanish",
    speakers: Annotated[
        Optional[int], typer.Option("--speakers", "-s", help="Number of speakers")
    ] = None,
    model: Annotated[
        Optional[str], typer.Option("--model", "-m", help="Ollama model")
    ] = None,
) -> None:
    """Run full pipeline: video -> translated transcript."""
    from voxpipe.core.audio import extract_audio
    from voxpipe.core.diarization import run_diarization
    from voxpipe.core.llm import correct_transcript, translate_transcript
    from voxpipe.core.merger import merge_transcript
    from voxpipe.core.subtitles import export_srt
    from voxpipe.core.transcription import transcribe

    basename = video.stem
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"=== Processing: {video} ===\n")

    # Step 1: Extract audio
    typer.echo("Step 1: Extracting audio...")
    audio_path = output_dir / f"{basename}_audio.wav"
    extract_audio(video, audio_path)

    # Step 2: Transcribe
    typer.echo("\nStep 2: Transcribing with Whisper...")
    transcript_path = output_dir / f"{basename}_transcript"
    transcribe(audio_path, transcript_path)
    transcript_path = transcript_path.with_suffix(".json")

    # Step 3: Diarize
    typer.echo("\nStep 3: Running speaker diarization...")
    diarization_path = output_dir / f"{basename}_diarization.json"
    run_diarization(audio_path, diarization_path, speakers)

    # Step 4: Merge
    typer.echo("\nStep 4: Merging transcript with speakers...")
    merged_path = output_dir / f"{basename}_merged.json"
    merge_transcript(transcript_path, diarization_path, merged_path)

    # Step 5: Correct
    typer.echo("\nStep 5: Correcting transcript...")
    corrected_path = output_dir / f"{basename}_corrected.json"
    correct_transcript(merged_path, corrected_path, model)

    # Step 6: Translate
    typer.echo(f"\nStep 6: Translating to {lang}...")
    translated_path = output_dir / f"{basename}_{lang.lower()}.json"
    translate_transcript(corrected_path, translated_path, lang, model)

    # Step 7: Export SRT
    typer.echo("\nStep 7: Exporting subtitles...")
    srt_path = output_dir / f"{basename}_{lang.lower()}.srt"
    export_srt(translated_path, srt_path)

    typer.echo(f"\n=== Done! Output in {output_dir} ===")


@pipeline_app.command("quick")
def pipeline_quick(
    video: Annotated[Path, typer.Argument(help="Input video file")],
    output_dir: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("."),
) -> None:
    """Quick transcription only (no diarization or translation)."""
    from voxpipe.core.audio import extract_audio
    from voxpipe.core.transcription import transcribe

    basename = video.stem
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"=== Quick transcribe: {video} ===\n")

    # Extract audio
    audio_path = output_dir / f"{basename}_audio.wav"
    extract_audio(video, audio_path)

    # Transcribe
    transcript_path = output_dir / f"{basename}_transcript"
    result = transcribe(audio_path, transcript_path)

    typer.echo(f"\n=== Done! Transcript: {result} ===")


if __name__ == "__main__":
    app()

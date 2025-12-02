"""Command-line interface for voxpipe."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from voxpipe._internal import debug

PIPELINE_DIAGRAM = """
Pipeline Flow:

  ┌─────────┐    ┌─────────────┐    ┌──────────┐    ┌─────────┐
  │  Video  │───▶│   Extract   │───▶│  Audio   │───▶│Transcribe│
  └─────────┘    └─────────────┘    └──────────┘    └────┬────┘
                                                         │
                      ┌──────────────────────────────────┘
                      │
                      ▼
  ┌──────────┐    ┌────────┐    ┌─────────┐    ┌───────────┐
  │ Diarize  │───▶│ Merge  │───▶│ Correct │───▶│ Translate │
  └──────────┘    └────────┘    └─────────┘    └─────┬─────┘
                                                      │
                      ┌───────────────────────────────┘
                      │
                      ▼
               ┌────────────┐    ┌─────────┐
               │   Export   │───▶│ SRT/VTT │
               └────────────┘    └─────────┘

Commands:
  extract      Extract audio from video (FFmpeg)
  transcribe   Speech-to-text (whisper-cli)
  diarize      Speaker identification (pyannote)
  merge        Combine transcript + speakers
  correct      Fix ASR errors (Ollama)
  translate    Translate to target language (Ollama)
  export       Generate SRT/VTT subtitles

  pipeline run    Run full pipeline (all steps)
  pipeline quick  Quick transcription only
"""


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="voxpipe",
        description="Video/audio processing pipeline with transcription, diarization, and translation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=PIPELINE_DIAGRAM,
    )

    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Show version and exit",
    )
    parser.add_argument(
        "--debug-info",
        action="store_true",
        help="Print debug information and exit",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- Extract Command ---
    extract_parser = subparsers.add_parser(
        "extract",
        help="Extract audio from video file",
        description="Extract audio from video file using FFmpeg.",
    )
    extract_parser.add_argument("video", type=Path, help="Input video file")
    extract_parser.add_argument("output", type=Path, help="Output WAV file")
    extract_parser.add_argument("-r", "--rate", type=int, default=16000, help="Sample rate (default: 16000)")
    extract_parser.add_argument("-c", "--channels", type=int, default=1, help="Number of channels (default: 1)")

    # --- Transcribe Command ---
    transcribe_parser = subparsers.add_parser(
        "transcribe",
        help="Transcribe audio with Whisper",
        description="Transcribe audio to text using whisper-cli.",
    )
    transcribe_parser.add_argument("audio", type=Path, help="Input audio file")
    transcribe_parser.add_argument("output", type=Path, help="Output JSON file")
    transcribe_parser.add_argument("--bin", type=Path, dest="whisper_bin", help="Whisper binary path")
    transcribe_parser.add_argument("-m", "--model", type=Path, dest="whisper_model", help="Whisper model path")
    transcribe_parser.add_argument("-l", "--lang", dest="language", help="Language code (e.g., 'en', 'de')")
    transcribe_parser.add_argument("--max-len", type=int, default=0, help="Max segment length in chars (0=unlimited)")
    transcribe_parser.add_argument("--no-context", action="store_true", help="Disable context to prevent hallucination loops")

    # --- Diarize Command ---
    diarize_parser = subparsers.add_parser(
        "diarize",
        help="Run speaker diarization",
        description="Identify speakers in audio using pyannote.",
    )
    diarize_parser.add_argument("audio", type=Path, help="Input audio file")
    diarize_parser.add_argument("output", type=Path, help="Output JSON file")
    diarize_parser.add_argument("-s", "--speakers", type=int, help="Exact number of speakers")
    diarize_parser.add_argument("--min", type=int, dest="min_speakers", help="Minimum number of speakers")
    diarize_parser.add_argument("--max", type=int, dest="max_speakers", help="Maximum number of speakers")

    # --- Merge Command ---
    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge transcript with speaker diarization",
        description="Combine Whisper transcript with pyannote speaker labels.",
    )
    merge_parser.add_argument("transcript", type=Path, help="Whisper transcript JSON")
    merge_parser.add_argument("diarization", type=Path, help="Diarization JSON")
    merge_parser.add_argument("output", type=Path, help="Output merged JSON")

    # --- Correct Command ---
    correct_parser = subparsers.add_parser(
        "correct",
        help="Correct transcript grammar and ASR errors",
        description="Fix transcription errors using Ollama LLM.",
    )
    correct_parser.add_argument("input", type=Path, help="Input transcript JSON")
    correct_parser.add_argument("output", type=Path, help="Output corrected JSON")
    correct_parser.add_argument("-m", "--model", help="Ollama model name")
    correct_parser.add_argument("--url", dest="base_url", help="Ollama base URL")

    # --- Translate Command ---
    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate transcript to another language",
        description="Translate transcript using Ollama LLM.",
    )
    translate_parser.add_argument("input", type=Path, help="Input transcript JSON")
    translate_parser.add_argument("output", type=Path, help="Output translated JSON")
    translate_parser.add_argument("-l", "--lang", default="Spanish", help="Target language (default: Spanish)")
    translate_parser.add_argument("-m", "--model", help="Ollama model name")
    translate_parser.add_argument("--url", dest="base_url", help="Ollama base URL")

    # --- Export Command ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export transcript to subtitle formats",
        description="Export transcript to SRT or VTT subtitle format.",
    )
    export_subparsers = export_parser.add_subparsers(dest="format", metavar="FORMAT")

    # Export SRT
    srt_parser = export_subparsers.add_parser("srt", help="Export to SRT format")
    srt_parser.add_argument("input", type=Path, help="Input transcript JSON")
    srt_parser.add_argument("output", type=Path, help="Output SRT file")
    srt_parser.add_argument("--no-speaker", action="store_true", help="Exclude speaker labels")

    # Export VTT
    vtt_parser = export_subparsers.add_parser("vtt", help="Export to WebVTT format")
    vtt_parser.add_argument("input", type=Path, help="Input transcript JSON")
    vtt_parser.add_argument("output", type=Path, help="Output VTT file")
    vtt_parser.add_argument("--no-speaker", action="store_true", help="Exclude speaker labels")

    # --- Pipeline Command ---
    pipeline_parser = subparsers.add_parser(
        "pipeline",
        help="Run complete processing pipelines",
        description="Run complete video processing pipelines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=PIPELINE_DIAGRAM,
    )
    pipeline_subparsers = pipeline_parser.add_subparsers(dest="pipeline_cmd", metavar="PIPELINE")

    # Pipeline run
    run_parser = pipeline_subparsers.add_parser(
        "run",
        help="Run full pipeline: video -> translated subtitles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=PIPELINE_DIAGRAM,
    )
    run_parser.add_argument("video", type=Path, help="Input video file")
    run_parser.add_argument("-o", "--output", type=Path, default=Path("."), dest="output_dir", help="Output directory")
    run_parser.add_argument("-l", "--lang", default="Spanish", help="Target language for translation")
    run_parser.add_argument("-s", "--speakers", type=int, help="Number of speakers")
    run_parser.add_argument("-m", "--model", help="Ollama model name")

    # Pipeline quick
    quick_parser = pipeline_subparsers.add_parser(
        "quick",
        help="Quick transcription only (no diarization/translation)",
    )
    quick_parser.add_argument("video", type=Path, help="Input video file")
    quick_parser.add_argument("-o", "--output", type=Path, default=Path("."), dest="output_dir", help="Output directory")

    return parser


def cmd_extract(args: argparse.Namespace) -> None:
    """Handle extract command."""
    from voxpipe.core.audio import extract_audio

    extract_audio(args.video, args.output, args.rate, args.channels)
    print(f"Audio extracted to: {args.output}")


def cmd_transcribe(args: argparse.Namespace) -> None:
    """Handle transcribe command."""
    from voxpipe.core.transcription import transcribe

    result = transcribe(
        args.audio,
        args.output,
        args.whisper_bin,
        args.whisper_model,
        language=args.language,
        max_len=args.max_len,
        no_context=args.no_context,
    )
    print(f"Transcript saved to: {result}")


def cmd_diarize(args: argparse.Namespace) -> None:
    """Handle diarize command."""
    from voxpipe.core.diarization import run_diarization

    run_diarization(
        args.audio,
        args.output,
        args.speakers,
        args.min_speakers,
        args.max_speakers,
    )
    print(f"Diarization saved to: {args.output}")


def cmd_merge(args: argparse.Namespace) -> None:
    """Handle merge command."""
    from voxpipe.core.merger import merge_transcript

    merge_transcript(args.transcript, args.diarization, args.output)
    print(f"Merged transcript saved to: {args.output}")


def cmd_correct(args: argparse.Namespace) -> None:
    """Handle correct command."""
    from voxpipe.core.llm import correct_transcript

    correct_transcript(args.input, args.output, args.model, args.base_url)
    print(f"Corrected transcript saved to: {args.output}")


def cmd_translate(args: argparse.Namespace) -> None:
    """Handle translate command."""
    from voxpipe.core.llm import translate_transcript

    translate_transcript(args.input, args.output, args.lang, args.model, args.base_url)
    print(f"Translated transcript saved to: {args.output}")


def cmd_export_srt(args: argparse.Namespace) -> None:
    """Handle export srt command."""
    from voxpipe.core.subtitles import export_srt

    export_srt(args.input, args.output, include_speaker=not args.no_speaker)
    print(f"SRT saved to: {args.output}")


def cmd_export_vtt(args: argparse.Namespace) -> None:
    """Handle export vtt command."""
    from voxpipe.core.subtitles import export_vtt

    export_vtt(args.input, args.output, include_speaker=not args.no_speaker)
    print(f"VTT saved to: {args.output}")


def cmd_pipeline_run(args: argparse.Namespace) -> None:
    """Handle pipeline run command."""
    from voxpipe.core.audio import extract_audio
    from voxpipe.core.diarization import run_diarization
    from voxpipe.core.llm import correct_transcript, translate_transcript
    from voxpipe.core.merger import merge_transcript
    from voxpipe.core.subtitles import export_srt
    from voxpipe.core.transcription import transcribe

    video = args.video
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = video.stem

    print(f"=== Processing: {video} ===\n")

    # Step 1: Extract audio
    print("Step 1: Extracting audio...")
    audio_path = output_dir / f"{basename}_audio.wav"
    extract_audio(video, audio_path)

    # Step 2: Transcribe
    print("\nStep 2: Transcribing with Whisper...")
    transcript_path = output_dir / f"{basename}_transcript"
    transcribe(audio_path, transcript_path)
    transcript_path = transcript_path.with_suffix(".json")

    # Step 3: Diarize
    print("\nStep 3: Running speaker diarization...")
    diarization_path = output_dir / f"{basename}_diarization.json"
    run_diarization(audio_path, diarization_path, args.speakers)

    # Step 4: Merge
    print("\nStep 4: Merging transcript with speakers...")
    merged_path = output_dir / f"{basename}_merged.json"
    merge_transcript(transcript_path, diarization_path, merged_path)

    # Step 5: Correct
    print("\nStep 5: Correcting transcript...")
    corrected_path = output_dir / f"{basename}_corrected.json"
    correct_transcript(merged_path, corrected_path, args.model)

    # Step 6: Translate
    print(f"\nStep 6: Translating to {args.lang}...")
    translated_path = output_dir / f"{basename}_{args.lang.lower()}.json"
    translate_transcript(corrected_path, translated_path, args.lang, args.model)

    # Step 7: Export SRT
    print("\nStep 7: Exporting subtitles...")
    srt_path = output_dir / f"{basename}_{args.lang.lower()}.srt"
    export_srt(translated_path, srt_path)

    print(f"\n=== Done! Output in {output_dir} ===")


def cmd_pipeline_quick(args: argparse.Namespace) -> None:
    """Handle pipeline quick command."""
    from voxpipe.core.audio import extract_audio
    from voxpipe.core.transcription import transcribe

    video = args.video
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = video.stem

    print(f"=== Quick transcribe: {video} ===\n")

    # Extract audio
    audio_path = output_dir / f"{basename}_audio.wav"
    extract_audio(video, audio_path)

    # Transcribe
    transcript_path = output_dir / f"{basename}_transcript"
    result = transcribe(audio_path, transcript_path)

    print(f"\n=== Done! Transcript: {result} ===")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Handle top-level options
    if args.version:
        print(f"voxpipe {debug._get_version()}")
        return 0

    if args.debug_info:
        debug._print_debug_info()
        return 0

    # No command given
    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handlers
    try:
        if args.command == "extract":
            cmd_extract(args)
        elif args.command == "transcribe":
            cmd_transcribe(args)
        elif args.command == "diarize":
            cmd_diarize(args)
        elif args.command == "merge":
            cmd_merge(args)
        elif args.command == "correct":
            cmd_correct(args)
        elif args.command == "translate":
            cmd_translate(args)
        elif args.command == "export":
            if args.format == "srt":
                cmd_export_srt(args)
            elif args.format == "vtt":
                cmd_export_vtt(args)
            else:
                parser.parse_args([args.command, "--help"])
        elif args.command == "pipeline":
            if args.pipeline_cmd == "run":
                cmd_pipeline_run(args)
            elif args.pipeline_cmd == "quick":
                cmd_pipeline_quick(args)
            else:
                parser.parse_args([args.command, "--help"])
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def app() -> None:
    """Entry point for the CLI."""
    sys.exit(main())


if __name__ == "__main__":
    app()

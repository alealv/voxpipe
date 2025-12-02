# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Voxpipe is an audio pipeline for videos that provides transcription, speaker diarization, grammar correction, translation, and subtitle export. It uses whisper-cli for transcription, pyannote.audio for speaker diarization, and Ollama for LLM-based text processing.

## Development Commands

All commands use `python scripts/make` (or just `make` with direnv enabled):

```bash
make setup              # Install dependencies in .venv and .venvs/3.x for all Python versions
make test               # Run tests with pytest (parallel, all Python versions)
make check              # Run all checks (quality, types, deps, docs, API)
make check-quality      # Lint with ruff
make check-types        # Type check with ty
make check-deps         # Check dependency issues with deptry
make check-docs         # Build documentation
make format             # Auto-fix and format code with ruff
make docs               # Serve documentation locally (localhost:8000)
make coverage           # Generate coverage report
make clean              # Remove build artifacts and caches
```

Run a single test file:
```bash
python scripts/make run pytest tests/test_cli.py -v
```

Run tests for a specific Python version:
```bash
python scripts/make 3.12 duty test
```

## Architecture

```
src/voxpipe/
├── __init__.py           # Package entry, exports CLI app
├── config.py             # Environment-based configuration (HF_TOKEN, whisper paths, Ollama)
├── _internal/
│   ├── cli.py            # Typer CLI with all commands
│   └── debug.py          # Version and debug info
├── core/
│   ├── audio.py          # FFmpeg audio extraction
│   ├── transcription.py  # whisper-cli transcription
│   ├── diarization.py    # pyannote speaker diarization
│   ├── merger.py         # Merge transcripts with speaker labels
│   ├── llm.py            # Ollama client for correction/translation
│   └── subtitles.py      # SRT/VTT export
└── utils/
    ├── io.py             # JSON read/write helpers
    ├── device.py         # PyTorch device detection
    ├── timestamps.py     # Time formatting
    └── progress.py       # Progress display
```

### Pipeline Flow

The full pipeline (`voxpipe pipeline run`) executes:
1. **Extract** - FFmpeg extracts audio from video to WAV
2. **Transcribe** - whisper-cli generates timestamped transcript
3. **Diarize** - pyannote identifies speaker segments
4. **Merge** - Assigns speakers to transcript segments by overlap
5. **Correct** - Ollama fixes ASR errors and grammar
6. **Translate** - Ollama translates to target language
7. **Export** - Generates SRT/VTT subtitles

### Configuration

Environment variables (loaded in `config.py`):
- `HF_TOKEN` - Hugging Face token for pyannote models (required for diarization)
- `WHISPER_BIN` - Path to whisper-cli binary
- `WHISPER_MODEL` - Path to whisper GGML model
- `OLLAMA_BASE_URL` - Ollama API URL (default: localhost:11434)
- `OLLAMA_MODEL` - Default LLM model (default: qwen3:4b)

## Code Quality

- **Linting**: ruff with config in `config/ruff.toml`
- **Type checking**: ty (Red Knot type checker)
- **Dependency checking**: deptry for detecting missing/unused dependencies
- **Testing**: pytest with coverage (Codecov integration), config in `config/pytest.ini`
- **Docstrings**: Google style convention

## Key Dependencies

- `typer` - CLI framework
- `pyannote-audio` - Speaker diarization (requires HF token and model acceptance)
- `torch` - PyTorch for ML inference
- `httpx` - Ollama API client

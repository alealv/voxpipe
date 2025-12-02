# voxpipe

[![CI](https://github.com/alealv/voxpipe/actions/workflows/ci.yml/badge.svg)](https://github.com/alealv/voxpipe/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/alealv/voxpipe/branch/main/graph/badge.svg)](https://codecov.io/gh/alealv/voxpipe)
[![PyPI version](https://img.shields.io/pypi/v/voxpipe.svg)](https://pypi.org/project/voxpipe/)
[![Python versions](https://img.shields.io/pypi/pyversions/voxpipe.svg)](https://pypi.org/project/voxpipe/)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-708FCC.svg?style=flat)](https://alealv.github.io/voxpipe/)
[![License](https://img.shields.io/pypi/l/voxpipe.svg)](https://github.com/alealv/voxpipe/blob/main/LICENSE)

Audio pipeline for videos with transcription, speaker diarization, correction, translation, and subtitle export.

## Features

- **Audio extraction** - Extract audio from video files using FFmpeg
- **Transcription** - Speech-to-text using whisper-cli
- **Speaker diarization** - Identify who speaks when using pyannote.audio
- **Transcript merging** - Combine transcription with speaker labels
- **Grammar correction** - Fix ASR errors using Ollama LLMs
- **Translation** - Translate transcripts to any language
- **Subtitle export** - Generate SRT and WebVTT files

## Installation

```bash
pip install voxpipe
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv tool install voxpipe
```

### Prerequisites

- **FFmpeg** - For audio extraction
- **whisper-cli** - For transcription ([whisper.cpp](https://github.com/ggerganov/whisper.cpp))
- **Ollama** - For correction/translation (optional)
- **Hugging Face token** - For pyannote speaker diarization

## Quick Start

### Environment Setup

```bash
# Required for speaker diarization
export HF_TOKEN="your_huggingface_token"

# Optional: customize paths
export WHISPER_BIN="~/.local/bin/whisper-cli"
export WHISPER_MODEL="~/.local/share/whisper/ggml-base.bin"
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_MODEL="qwen3:4b"
```

### Full Pipeline

Process a video from start to translated subtitles:

```bash
voxpipe pipeline run video.mp4 --output ./output --lang Spanish --speakers 2
```

This runs: extract → transcribe → diarize → merge → correct → translate → export SRT

### Quick Transcription

For fast transcription without diarization or translation:

```bash
voxpipe pipeline quick video.mp4 --output ./output
```

## Usage Examples

### Individual Commands

**Extract audio from video:**
```bash
voxpipe extract video.mp4 audio.wav --rate 16000 --channels 1
```

**Transcribe audio:**
```bash
voxpipe transcribe audio.wav transcript.json
```

**Run speaker diarization:**
```bash
voxpipe diarize audio.wav diarization.json --speakers 3
```

**Merge transcript with speakers:**
```bash
voxpipe merge transcript.json diarization.json merged.json
```

**Correct grammar/ASR errors:**
```bash
voxpipe correct merged.json corrected.json --model llama3
```

**Translate to another language:**
```bash
voxpipe translate corrected.json spanish.json --lang Spanish
```

**Export to subtitles:**
```bash
voxpipe export srt spanish.json output.srt
voxpipe export vtt spanish.json output.vtt
```

### Help

```bash
voxpipe --help
voxpipe transcribe --help
voxpipe pipeline --help
```

## Output Formats

### Merged Transcript JSON

```json
{
  "speakers": ["SPEAKER_00", "SPEAKER_01"],
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "speaker": "SPEAKER_00",
      "text": "Hello, welcome to the meeting."
    },
    {
      "start": 3.8,
      "end": 7.2,
      "speaker": "SPEAKER_01",
      "text": "Thanks for having me."
    }
  ]
}
```

### SRT Output

```
1
00:00:00,000 --> 00:00:03,500
[SPEAKER_00] Hello, welcome to the meeting.

2
00:00:03,800 --> 00:00:07,200
[SPEAKER_01] Thanks for having me.
```

## Development

```bash
# Clone and setup
git clone https://github.com/alealv/voxpipe.git
cd voxpipe
make setup

# Run tests
make test

# Run all checks (lint, types, deps, docs)
make check

# Format code
make format

# Serve documentation locally
make docs
```

## License

LGPL-3.0 - see [LICENSE](LICENSE) for details.

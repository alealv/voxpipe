"""Configuration management for voxpipe."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""

    hf_token: str | None
    """Hugging Face token for pyannote models."""

    whisper_bin: Path
    """Path to whisper-cli binary."""

    whisper_model: Path
    """Path to whisper GGML model file."""

    ollama_base_url: str
    """Ollama API base URL."""

    ollama_model: str
    """Default Ollama model for correction/translation."""

    @classmethod
    def from_env(cls) -> Config:
        """Load configuration from environment variables.

        Returns:
            Config instance with values from environment.
        """
        return cls(
            hf_token=os.getenv("HF_TOKEN"),
            whisper_bin=Path(
                os.getenv(
                    "WHISPER_BIN",
                    "~/.voicemode/services/whisper/build/bin/whisper-cli",
                )
            ).expanduser(),
            whisper_model=Path(
                os.getenv(
                    "WHISPER_MODEL",
                    "~/.voicemode/services/whisper/models/ggml-base.bin",
                )
            ).expanduser(),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:4b"),
        )


# Global config instance
config = Config.from_env()

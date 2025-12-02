"""Ollama LLM client for text correction and translation."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import httpx

from voxpipe.config import config
from voxpipe.utils.io import read_json, write_json
from voxpipe.utils.progress import print_progress

CORRECTION_PROMPT = """You are a transcript correction assistant. Your task is to fix errors in speech-to-text transcription while preserving the original meaning.

Fix the following issues:
- Grammar and punctuation errors
- Obvious ASR mistakes (words that sound similar but are wrong)
- Missing punctuation and capitalization
- Run-on sentences (add proper breaks)

Do NOT:
- Change the meaning or content
- Add information not present in the original
- Translate to another language
- Add commentary or explanations

Return ONLY the corrected text, nothing else.

Text to correct:
{text}"""

TRANSLATION_PROMPT = """You are a professional translator. Translate the following text to {language}.

Requirements:
- Maintain the original meaning and tone
- Preserve any technical terms or proper nouns appropriately
- Use natural, fluent {language}
- Do not add explanations or commentary

Return ONLY the translation, nothing else.

Text to translate:
{text}"""


class OllamaClient:
    """Client for Ollama API interactions."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        """Initialize Ollama client.

        Args:
            base_url: Ollama API base URL.
            model: Model name to use.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or config.ollama_base_url
        self.model = model or config.ollama_model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> str:
        """Generate text from Ollama.

        Args:
            prompt: Input prompt.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text.
        """
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    **({"num_predict": max_tokens} if max_tokens else {}),
                },
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = response.json().get("response", "").strip()
        return self._clean_thinking_tags(result)

    def correct(self, text: str) -> str:
        """Correct grammar and ASR errors in text.

        Args:
            text: Text to correct.

        Returns:
            Corrected text.
        """
        prompt = CORRECTION_PROMPT.format(text=text)
        return self.generate(prompt, max_tokens=len(text) * 2) or text

    def translate(self, text: str, target_language: str) -> str:
        """Translate text to target language.

        Args:
            text: Text to translate.
            target_language: Target language name.

        Returns:
            Translated text.
        """
        prompt = TRANSLATION_PROMPT.format(language=target_language, text=text)
        return self.generate(prompt, max_tokens=len(text) * 3) or text

    @staticmethod
    def _clean_thinking_tags(text: str) -> str:
        """Remove <think> tags from model output.

        Args:
            text: Text with potential thinking tags.

        Returns:
            Cleaned text.
        """
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def correct_transcript(
    input_path: Path | str,
    output_path: Path | str,
    model: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Correct all segments in a transcript.

    Args:
        input_path: Path to input transcript JSON.
        output_path: Path to output corrected JSON.
        model: Ollama model to use.
        base_url: Ollama API base URL.

    Returns:
        Corrected transcript data.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    data = read_json(input_path)
    segments = data.get("segments", [])
    client = OllamaClient(base_url=base_url, model=model)

    print(
        f"Correcting {len(segments)} segments using {client.model}...", file=sys.stderr
    )

    corrected_segments = []
    for i, seg in enumerate(segments, 1):
        original_text = seg.get("text", "")

        if original_text.strip():
            print_progress(i, len(segments), "Correcting")
            corrected_text = client.correct(original_text)
        else:
            corrected_text = original_text

        new_seg = {**seg, "text": corrected_text}
        if corrected_text != original_text:
            new_seg["original_text"] = original_text
        corrected_segments.append(new_seg)

    print("\nCorrection complete!", file=sys.stderr)

    result = {
        **data,
        "segments": corrected_segments,
        "correction_model": client.model,
    }

    write_json(output_path, result)
    print(f"Corrected transcript saved to: {output_path}", file=sys.stderr)

    return result


def translate_transcript(
    input_path: Path | str,
    output_path: Path | str,
    target_language: str = "Spanish",
    model: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Translate all segments in a transcript.

    Args:
        input_path: Path to input transcript JSON.
        output_path: Path to output translated JSON.
        target_language: Target language for translation.
        model: Ollama model to use.
        base_url: Ollama API base URL.

    Returns:
        Translated transcript data.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    data = read_json(input_path)
    segments = data.get("segments", [])
    client = OllamaClient(base_url=base_url, model=model)

    print(
        f"Translating {len(segments)} segments to {target_language} using {client.model}...",
        file=sys.stderr,
    )

    translated_segments = []
    for i, seg in enumerate(segments, 1):
        original_text = seg.get("text", "")

        if original_text.strip():
            print_progress(i, len(segments), "Translating")
            translated_text = client.translate(original_text, target_language)
        else:
            translated_text = original_text

        translated_segments.append(
            {
                **seg,
                "text": translated_text,
                "original_text": original_text,
            }
        )

    print("\nTranslation complete!", file=sys.stderr)

    result = {
        **data,
        "segments": translated_segments,
        "target_language": target_language,
        "translation_model": client.model,
    }

    write_json(output_path, result)
    print(f"Translated transcript saved to: {output_path}", file=sys.stderr)

    return result

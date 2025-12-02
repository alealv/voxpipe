"""Transcript cleaning utilities for detecting and removing hallucinations."""

from __future__ import annotations

import re
import sys
from typing import Any


def detect_repetition(text: str, min_phrase_len: int = 20, min_repeats: int = 3) -> str | None:
    """Detect if text contains repeated phrases (hallucination loop).

    Args:
        text: Text to check for repetitions.
        min_phrase_len: Minimum phrase length to consider.
        min_repeats: Minimum number of repeats to flag as hallucination.

    Returns:
        The repeated phrase if found, None otherwise.
    """
    # Normalize whitespace
    text = " ".join(text.split())

    # Try different phrase lengths
    for phrase_len in range(min_phrase_len, len(text) // min_repeats):
        # Slide through text looking for repeating patterns
        for start in range(len(text) - phrase_len * min_repeats):
            phrase = text[start : start + phrase_len]
            if not phrase.strip():
                continue

            # Count occurrences
            count = 0
            pos = 0
            while True:
                pos = text.find(phrase, pos)
                if pos == -1:
                    break
                count += 1
                pos += 1

            if count >= min_repeats:
                return phrase

    return None


def remove_repeated_segments(
    segments: list[dict[str, Any]],
    similarity_threshold: float = 0.9,
    max_consecutive_similar: int = 3,
) -> list[dict[str, Any]]:
    """Remove segments that are repetitive (hallucination loops).

    Args:
        segments: List of transcript segments with 'text' field.
        similarity_threshold: Threshold for considering texts similar (0-1).
        max_consecutive_similar: Max allowed consecutive similar segments.

    Returns:
        Cleaned list of segments with repetitions removed.
    """
    if not segments:
        return segments

    cleaned = []
    consecutive_similar = 0
    last_text = ""

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        # Check similarity with last segment
        similarity = _text_similarity(text, last_text)

        if similarity >= similarity_threshold:
            consecutive_similar += 1
            if consecutive_similar >= max_consecutive_similar:
                # Skip this segment - it's part of a hallucination loop
                print(
                    f"Removing hallucinated segment at {seg.get('start', '?')}s: {text[:50]}...",
                    file=sys.stderr,
                )
                continue
        else:
            consecutive_similar = 0

        cleaned.append(seg)
        last_text = text

    removed = len(segments) - len(cleaned)
    if removed > 0:
        print(f"Removed {removed} hallucinated segments", file=sys.stderr)

    return cleaned


def clean_transcript_text(text: str) -> str:
    """Clean transcript text by removing obvious hallucination patterns.

    Args:
        text: Text to clean.

    Returns:
        Cleaned text.
    """
    # Remove repeated phrases at the end
    text = re.sub(r"(.{20,}?)\1{2,}$", r"\1", text)

    # Remove multiple consecutive identical sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    cleaned_sentences = []
    last_sentence = ""
    repeat_count = 0

    for sentence in sentences:
        if sentence.strip() == last_sentence.strip():
            repeat_count += 1
            if repeat_count >= 2:
                continue  # Skip repeated sentences
        else:
            repeat_count = 0

        cleaned_sentences.append(sentence)
        last_sentence = sentence

    return " ".join(cleaned_sentences)


def _text_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity ratio.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity ratio between 0 and 1.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize
    t1 = text1.lower().split()
    t2 = text2.lower().split()

    if not t1 or not t2:
        return 0.0

    # Jaccard similarity
    set1 = set(t1)
    set2 = set(t2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0

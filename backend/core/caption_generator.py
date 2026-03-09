"""
Caption generator using OpenAI Whisper.
Transcribes speech from video/audio and returns timed caption segments.
"""

import whisper
import logging
from typing import List, Dict, Optional

from config import settings

logger = logging.getLogger("reel-generator.caption_generator")

# Lazy-load model (heavy, only load once)
_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info(f"Loading Whisper model: {settings.WHISPER_MODEL}")
        _model = whisper.load_model(settings.WHISPER_MODEL)
    return _model


def generate_captions(
    media_path: str,
    language: Optional[str] = None,
    max_words_per_segment: int = 8,
) -> List[Dict]:
    """
    Transcribe audio from a video/audio file and return caption segments.

    Args:
        media_path:             Path to video or audio file.
        language:               Force language (None = auto-detect).
        max_words_per_segment:  Split long segments for readability.

    Returns:
        List of dicts: [{"start": 0.0, "end": 2.5, "text": "Hello world"}, ...]
    """
    model = _get_model()

    options = {"task": "transcribe"}
    if language:
        options["language"] = language

    logger.info(f"Transcribing: {media_path}")
    result = model.transcribe(media_path, **options)

    captions = []
    for seg in result.get("segments", []):
        text = seg["text"].strip()
        if not text:
            continue

        words = text.split()
        # Split long segments into smaller chunks for TikTok/Reels style
        if len(words) > max_words_per_segment:
            duration = seg["end"] - seg["start"]
            words_per_sec = len(words) / duration if duration > 0 else len(words)

            chunk_start = seg["start"]
            for i in range(0, len(words), max_words_per_segment):
                chunk_words = words[i:i + max_words_per_segment]
                chunk_text = " ".join(chunk_words)
                chunk_dur = len(chunk_words) / words_per_sec if words_per_sec > 0 else 1.0
                chunk_end = min(chunk_start + chunk_dur, seg["end"])

                captions.append({
                    "start": round(chunk_start, 3),
                    "end": round(chunk_end, 3),
                    "text": chunk_text,
                })
                chunk_start = chunk_end
        else:
            captions.append({
                "start": round(seg["start"], 3),
                "end": round(seg["end"], 3),
                "text": text,
            })

    logger.info(f"Generated {len(captions)} caption segments")
    return captions


def captions_to_srt(captions: List[Dict], output_path: str):
    """Export captions as an SRT subtitle file."""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, cap in enumerate(captions, 1):
            start = _seconds_to_srt_time(cap["start"])
            end = _seconds_to_srt_time(cap["end"])
            f.write(f"{i}\n{start} --> {end}\n{cap['text']}\n\n")
    logger.info(f"SRT saved: {output_path}")


def _seconds_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

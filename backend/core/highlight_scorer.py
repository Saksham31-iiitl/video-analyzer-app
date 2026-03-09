"""
Highlight Scorer — ranks scenes by "interestingness" using multiple signals.

Scoring signals:
  1. Motion       — optical flow magnitude (OpenCV)
  2. Sharpness    — Laplacian variance
  3. CLIP         — semantic relevance to text prompts
  4. Audio energy — RMS loudness of scene audio
  5. Face         — face presence / emotion detection

All scores are normalised to 0.0 – 1.0, then combined with configurable weights.
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from config import settings
from ai.motion_analyzer import compute_motion_score
from ai.quality_checker import compute_sharpness_score
from ai.clip_scorer import compute_clip_score
from ai.face_detector import compute_face_score
from utils.ffmpeg_utils import extract_audio_segment
from utils.video_utils import extract_frames

logger = logging.getLogger("reel-generator.highlight_scorer")


def _audio_energy_score(video_path: str, start: float, end: float) -> float:
    """Compute normalised RMS audio energy for a scene segment."""
    try:
        import librosa
        audio_path = extract_audio_segment(video_path, start, end)
        if audio_path is None:
            return 0.0
        y, sr = librosa.load(audio_path, sr=22050)
        if len(y) == 0:
            return 0.0
        rms = np.sqrt(np.mean(y ** 2))
        # Normalise: typical speech RMS ≈ 0.02–0.1, music ≈ 0.05–0.3
        score = float(np.clip(rms / 0.2, 0.0, 1.0))
        return round(score, 4)
    except Exception as e:
        logger.warning(f"Audio energy failed: {e}")
        return 0.0


def score_single_scene(
    video_path: str,
    scene: Dict,
    prompts: List[str],
) -> Dict:
    """Score one scene across all signals and return enriched dict."""
    start = scene["start_time"]
    end = scene["end_time"]

    # Extract sampled frames for this scene
    frames = extract_frames(
        video_path, start, end,
        sample_fps=settings.FRAME_SAMPLE_FPS,
    )

    if not frames:
        logger.warning(f"No frames extracted for scene {start:.1f}–{end:.1f}")
        return {**scene, "score": 0, "motion_score": 0, "sharpness_score": 0,
                "clip_score": 0, "audio_score": 0, "face_score": 0}

    # ── Compute individual scores ────────────────────────────────────
    motion = compute_motion_score(frames)
    sharpness = compute_sharpness_score(frames)
    clip_rel = compute_clip_score(frames, prompts)
    audio = _audio_energy_score(video_path, start, end)
    face = compute_face_score(frames)

    # ── Weighted combination ─────────────────────────────────────────
    combined = (
        settings.WEIGHT_MOTION * motion
        + settings.WEIGHT_SHARPNESS * sharpness
        + settings.WEIGHT_CLIP * clip_rel
        + settings.WEIGHT_AUDIO * audio
        + settings.WEIGHT_FACE * face
    )

    return {
        **scene,
        "score": round(combined, 4),
        "motion_score": round(motion, 4),
        "sharpness_score": round(sharpness, 4),
        "clip_score": round(clip_rel, 4),
        "audio_score": round(audio, 4),
        "face_score": round(face, 4),
    }


def score_scenes(
    video_path: str,
    scenes: List[Dict],
    prompts: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Score all scenes in a video.
    Uses thread pool for parallel frame extraction.
    """
    if prompts is None:
        prompts = ["an exciting interesting moment"]

    logger.info(f"Scoring {len(scenes)} scenes from {video_path}…")

    scored = []
    # Process scenes sequentially for GPU models (CLIP),
    # but frame extraction within each scene uses threads
    for scene in scenes:
        result = score_single_scene(video_path, scene, prompts)
        scored.append(result)
        logger.debug(f"  Scene {scene['start_time']:.1f}–{scene['end_time']:.1f}  "
                      f"→ score={result['score']:.3f}")

    return scored

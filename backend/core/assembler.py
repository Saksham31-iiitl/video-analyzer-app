"""
Assembler — selects top scenes, trims to beat boundaries, and concatenates
them into a single intermediate video file (before final rendering).
"""

from moviepy.editor import (
    VideoFileClip,
    concatenate_videoclips,
    CompositeVideoClip,
)
import os
import logging
from typing import List, Dict, Optional

from config import settings

logger = logging.getLogger("reel-generator.assembler")


def _trim_scene_to_beats(
    scene: Dict,
    beat_times: Optional[List[float]],
    target_clip_dur: float,
) -> Dict:
    """
    Adjust a scene's start/end to align with the nearest beat boundaries.
    If no beats are provided, just center-trim to target_clip_dur.
    """
    start = scene["start_time"]
    end = scene["end_time"]
    dur = end - start

    if beat_times and len(beat_times) >= 2:
        # Find the beat closest to the scene start
        closest_start = min(beat_times, key=lambda b: abs(b - start))
        # Find the next beat that gives us ≈ target_clip_dur
        candidates = [b for b in beat_times if b > closest_start]
        if candidates:
            # Pick the beat closest to (closest_start + target_clip_dur)
            ideal_end = closest_start + target_clip_dur
            closest_end = min(candidates, key=lambda b: abs(b - ideal_end))
            return {**scene, "trim_start": closest_start, "trim_end": closest_end}

    # Fallback: center-trim
    if dur > target_clip_dur:
        mid = (start + end) / 2
        half = target_clip_dur / 2
        return {**scene, "trim_start": max(0, mid - half), "trim_end": mid + half}

    return {**scene, "trim_start": start, "trim_end": end}


def assemble_reel(
    scenes: List[Dict],
    beat_times: Optional[List[float]] = None,
    target_duration: int = 30,
    transition_type: str = "cut",
) -> Dict:
    """
    Assemble selected scenes into a single video.

    Args:
        scenes:           List of dicts with video_path, start_time, end_time, score.
        beat_times:        Beat timestamps from beat_analyzer (or None).
        target_duration:   Target reel duration in seconds.
        transition_type:   'cut' | 'crossfade' | 'zoom'

    Returns:
        Dict with temp_video_path (path to assembled intermediate file).
    """
    if not scenes:
        raise ValueError("No scenes provided to assemble.")

    # ── Sort by score and select enough to fill target_duration ───────
    scenes_sorted = sorted(scenes, key=lambda s: s.get("score", 0), reverse=True)

    selected = []
    total_dur = 0.0
    n_scenes = len(scenes_sorted)
    avg_clip_dur = target_duration / max(n_scenes, 1)
    avg_clip_dur = max(1.0, min(avg_clip_dur, 5.0))  # clamp between 1–5 sec

    for sc in scenes_sorted:
        if total_dur >= target_duration:
            break
        trimmed = _trim_scene_to_beats(sc, beat_times, avg_clip_dur)
        clip_dur = trimmed["trim_end"] - trimmed["trim_start"]
        if clip_dur < 0.3:
            continue
        selected.append(trimmed)
        total_dur += clip_dur

    if not selected:
        raise ValueError("Could not select any valid scenes.")

    logger.info(f"Selected {len(selected)} scenes, total ≈ {total_dur:.1f}s "
                f"(target {target_duration}s)")

    # ── Load and trim MoviePy clips ──────────────────────────────────
    clips = []
    for sc in selected:
        try:
            clip = VideoFileClip(sc["video_path"]).subclip(sc["trim_start"], sc["trim_end"])
            clips.append(clip)
        except Exception as e:
            logger.warning(f"Failed to load scene: {e}")
            continue

    if not clips:
        raise ValueError("All clips failed to load.")

    # ── Concatenate with transitions ─────────────────────────────────
    if transition_type == "crossfade" and len(clips) > 1:
        # Crossfade: overlap by 0.3 seconds
        padding = -0.3
        final = concatenate_videoclips(clips, method="compose", padding=padding)
    else:
        # Hard cut (default)
        final = concatenate_videoclips(clips, method="compose")

    # ── Write intermediate file ──────────────────────────────────────
    temp_path = os.path.join(settings.TEMP_DIR, f"assembled_{os.getpid()}.mp4")
    final.write_videofile(
        temp_path,
        codec="libx264",
        audio_codec="aac",
        fps=settings.DEFAULT_FPS,
        preset="ultrafast",   # fast intermediate encode
        logger=None,
    )

    # Clean up MoviePy clips
    for c in clips:
        c.close()
    final.close()

    logger.info(f"Assembled video saved: {temp_path}")
    return {
        "temp_video_path": temp_path,
        "duration": total_dur,
        "num_scenes": len(selected),
    }

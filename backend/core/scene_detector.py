"""
Scene detection using PySceneDetect.
Splits a video into individual scenes based on content changes.

If no hard cuts are found (e.g. a single continuous nature/mountain shot),
the video is split into equal-length segments so the pipeline always has
something to score and assemble.
"""

import cv2
from scenedetect import open_video, SceneManager, ContentDetector
from typing import List, Dict
import logging

logger = logging.getLogger("reel-generator.scene_detector")


def _get_video_duration(video_path: str) -> float:
    """Fast duration read via OpenCV (no PySceneDetect overhead)."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frames / fps if fps > 0 else 0.0


def _split_into_segments(
    video_path: str,
    segment_duration: float = 3.0,
    min_scene_len: float = 0.5,
) -> List[Dict]:
    """
    Fallback: split a video into equal-length segments when no scene cuts are found.
    Used for long continuous shots (nature, timelapses, vlogs, etc.)
    """
    total = _get_video_duration(video_path)
    if total <= 0:
        return []

    segments = []
    start = 0.0
    while start < total:
        end = min(start + segment_duration, total)
        duration = end - start
        if duration >= min_scene_len:
            segments.append({
                "start_time": round(start, 3),
                "end_time": round(end, 3),
                "duration": round(duration, 3),
            })
        start = end

    logger.info(f"Fallback: split into {len(segments)} x {segment_duration}s segments")
    return segments


def detect_scenes_in_video(
    video_path: str,
    threshold: float = 27.0,
    min_scene_len: float = 0.5,
    fallback_segment_duration: float = 3.0,
) -> List[Dict]:
    """
    Detect scene boundaries in a video file.

    Args:
        video_path:               Path to the video file.
        threshold:                Sensitivity for content change detection.
                                  Lower = more scenes detected.
                                  27.0 works well for nature/gradual videos.
                                  20.0 is very sensitive.
                                  40.0 only catches hard cuts.
        min_scene_len:            Ignore scenes shorter than this (seconds).
        fallback_segment_duration: If no scenes found, split video into
                                  segments of this length (seconds).

    Returns:
        List of dicts with keys: start_time, end_time, duration (all in seconds).
    """
    video = open_video(video_path)
    scene_manager = SceneManager()

    scene_manager.add_detector(
        ContentDetector(
            threshold=threshold,
            min_scene_len=int(min_scene_len * video.frame_rate),
        )
    )

    logger.info(f"Running scene detection on {video_path} (threshold={threshold})…")
    scene_manager.detect_scenes(video)
    scene_list = scene_manager.get_scene_list()

    scenes = []
    for start, end in scene_list:
        start_sec = start.get_seconds()
        end_sec = end.get_seconds()
        duration = end_sec - start_sec

        if duration < min_scene_len:
            continue

        scenes.append({
            "start_time": round(start_sec, 3),
            "end_time": round(end_sec, 3),
            "duration": round(duration, 3),
        })

    logger.info(f"Detected {len(scenes)} scenes in {video_path}")

    # ── Fallback: no hard cuts found → split into equal segments ─────
    if not scenes:
        logger.info(
            f"No scene cuts detected — video is likely a single continuous shot. "
            f"Splitting into {fallback_segment_duration}s segments…"
        )
        scenes = _split_into_segments(
            video_path,
            segment_duration=fallback_segment_duration,
            min_scene_len=min_scene_len,
        )

    return scenes

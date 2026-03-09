"""
Video utilities — frame extraction, sampling, and manipulation.
"""

import cv2
import numpy as np
import logging
from typing import List

logger = logging.getLogger("reel-generator.video_utils")


def extract_frames(
    video_path: str,
    start_time: float = 0.0,
    end_time: float = None,
    sample_fps: int = 2,
    max_frames: int = 50,
    resize_height: int = 360,
) -> List[np.ndarray]:
    """
    Extract sampled frames from a video segment.

    Args:
        video_path:     Path to video file.
        start_time:     Start time in seconds.
        end_time:       End time in seconds (None = end of video).
        sample_fps:     Frames per second to sample (e.g., 2 = every 0.5s).
        max_frames:     Maximum number of frames to return.
        resize_height:  Resize frames for faster processing (0 = no resize).

    Returns:
        List of BGR numpy arrays (OpenCV format).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return []

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration = total_frames / fps

    if end_time is None:
        end_time = total_duration

    # Calculate which frames to extract
    sample_interval = max(1, int(fps / sample_fps))
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)

    frames = []
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    frame_idx = start_frame
    while frame_idx < end_frame and len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if (frame_idx - start_frame) % sample_interval == 0:
            # Resize for faster processing
            if resize_height > 0 and frame.shape[0] > resize_height:
                scale = resize_height / frame.shape[0]
                new_width = int(frame.shape[1] * scale)
                frame = cv2.resize(frame, (new_width, resize_height))

            frames.append(frame)

        frame_idx += 1

    cap.release()

    logger.debug(f"Extracted {len(frames)} frames from {video_path} "
                 f"({start_time:.1f}s – {end_time:.1f}s)")
    return frames


def get_frame_at_time(video_path: str, timestamp: float) -> np.ndarray:
    """Extract a single frame at a specific timestamp."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_num = int(timestamp * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

    ret, frame = cap.read()
    cap.release()

    return frame if ret else None

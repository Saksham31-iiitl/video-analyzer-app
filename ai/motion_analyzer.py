"""
Motion analyser — computes an optical-flow-based motion score for a set of frames.
High motion = action, dancing, sports → higher highlight score.
"""

import cv2
import numpy as np
import logging
from typing import List

logger = logging.getLogger("reel-generator.motion_analyzer")


def compute_motion_score(frames: List[np.ndarray]) -> float:
    """
    Compute average motion intensity across a sequence of frames
    using Farneback dense optical flow.

    Args:
        frames: List of BGR frames (numpy arrays from OpenCV).

    Returns:
        Normalised motion score 0.0 – 1.0.
    """
    if len(frames) < 2:
        return 0.0

    flow_magnitudes = []

    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)

    for frame in frames[1:]:
        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Farneback dense optical flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray,
            flow=None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )

        # Magnitude of flow vectors
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        avg_mag = float(np.mean(mag))
        flow_magnitudes.append(avg_mag)

        prev_gray = curr_gray

    if not flow_magnitudes:
        return 0.0

    mean_flow = np.mean(flow_magnitudes)

    # Normalise: typical values range from 0 (static) to ~20 (fast motion)
    # Map to 0–1 with a soft ceiling at ~15
    score = float(np.clip(mean_flow / 15.0, 0.0, 1.0))

    logger.debug(f"Motion: mean_flow={mean_flow:.2f} → score={score:.3f}")
    return score

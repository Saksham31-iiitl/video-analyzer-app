"""
Quality checker — image sharpness and exposure scoring.
Blurry or poorly exposed frames score lower.
"""

import cv2
import numpy as np
import logging
from typing import List

logger = logging.getLogger("reel-generator.quality_checker")


def _laplacian_variance(frame: np.ndarray) -> float:
    """Laplacian variance — higher = sharper image."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    return float(lap.var())


def _exposure_score(frame: np.ndarray) -> float:
    """
    Score exposure quality based on histogram distribution.
    Well-exposed images have a spread-out histogram; over/underexposed don't.
    Returns 0.0 – 1.0.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist.flatten() / hist.sum()

    # Standard deviation of brightness distribution
    mean_brightness = np.sum(np.arange(256) * hist)
    std_brightness = np.sqrt(np.sum(((np.arange(256) - mean_brightness) ** 2) * hist))

    # Ideal std is around 50–70 for well-exposed images
    # Too low = flat/dark, too high = overblown contrast
    score = float(np.clip(std_brightness / 70.0, 0.0, 1.0))
    return score


def compute_sharpness_score(frames: List[np.ndarray]) -> float:
    """
    Average sharpness score across sampled frames.

    Args:
        frames: List of BGR frames.

    Returns:
        Normalised score 0.0 – 1.0.
    """
    if not frames:
        return 0.0

    sharpness_values = []
    exposure_values = []

    for frame in frames:
        sharpness_values.append(_laplacian_variance(frame))
        exposure_values.append(_exposure_score(frame))

    mean_sharpness = np.mean(sharpness_values)
    mean_exposure = np.mean(exposure_values)

    # Normalise sharpness: typical range 0–2000, map to 0–1 with ceiling at 500
    sharp_norm = float(np.clip(mean_sharpness / 500.0, 0.0, 1.0))

    # Combine 70% sharpness + 30% exposure
    combined = 0.7 * sharp_norm + 0.3 * mean_exposure

    logger.debug(f"Quality: sharpness={mean_sharpness:.0f} exposure={mean_exposure:.2f} "
                 f"→ score={combined:.3f}")
    return float(np.clip(combined, 0.0, 1.0))

"""
Face detector — detects faces (MediaPipe) and optionally analyses emotions (DeepFace).
Scenes with faces (especially expressive ones) score higher for vlogs/reels.
"""

import cv2
import numpy as np
import logging
from typing import List

logger = logging.getLogger("reel-generator.face_detector")

# Lazy-load face cascade
_face_cascade = None


def _get_face_detector():
    """Load OpenCV Haar cascade face detector once."""
    global _face_cascade
    if _face_cascade is None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _face_cascade = cv2.CascadeClassifier(cascade_path)
        if _face_cascade.empty():
            logger.warning("Failed to load Haar cascade. Face detection will return 0.")
            _face_cascade = None
        else:
            logger.info("OpenCV face detection loaded ✓")
    return _face_cascade


def _detect_faces_in_frame(frame: np.ndarray) -> int:
    """Return number of faces detected in a single frame."""
    detector = _get_face_detector()
    if detector is None:
        return 0

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )
    return len(faces) if len(faces) > 0 else 0


def _emotion_bonus(frame: np.ndarray) -> float:
    """
    Use DeepFace to detect emotions. Strong emotions (happy, surprise) get a bonus.
    Returns 0.0 – 0.5 bonus.
    """
    try:
        from deepface import DeepFace

        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )

        if isinstance(result, list):
            result = result[0]

        emotions = result.get("emotion", {})
        dominant = result.get("dominant_emotion", "neutral")

        # Bonus for engaging emotions
        bonus_map = {
            "happy": 0.5,
            "surprise": 0.4,
            "angry": 0.2,     # can be dramatic / engaging
            "sad": 0.1,
            "fear": 0.2,
            "neutral": 0.0,
            "disgust": 0.05,
        }

        return bonus_map.get(dominant, 0.0)

    except Exception as e:
        logger.debug(f"DeepFace emotion failed (non-critical): {e}")
        return 0.0


def compute_face_score(
    frames: List[np.ndarray],
    check_emotions: bool = True,
    sample_count: int = 3,
) -> float:
    """
    Compute a face-presence + emotion score across sampled frames.

    Args:
        frames:          List of BGR frames.
        check_emotions:  Whether to run DeepFace emotion analysis.
        sample_count:    Max frames to check (DeepFace is slow).

    Returns:
        Normalised score 0.0 – 1.0.
    """
    if not frames:
        return 0.0

    # Sample frames evenly
    if len(frames) > sample_count:
        indices = np.linspace(0, len(frames) - 1, sample_count, dtype=int)
        sampled = [frames[i] for i in indices]
    else:
        sampled = frames

    face_counts = []
    emotion_bonuses = []

    for frame in sampled:
        n_faces = _detect_faces_in_frame(frame)
        face_counts.append(n_faces)

        if check_emotions and n_faces > 0:
            bonus = _emotion_bonus(frame)
            emotion_bonuses.append(bonus)

    # Face presence: any face detected → base score
    has_face = any(c > 0 for c in face_counts)
    if not has_face:
        return 0.0

    # Score based on consistency of face presence
    face_ratio = sum(1 for c in face_counts if c > 0) / len(face_counts)
    base_score = face_ratio * 0.6  # up to 0.6 for consistent face presence

    # Add emotion bonus (up to 0.4)
    avg_emotion = float(np.mean(emotion_bonuses)) if emotion_bonuses else 0.0
    emotion_contribution = min(avg_emotion, 0.4)

    score = base_score + emotion_contribution
    score = float(np.clip(score, 0.0, 1.0))

    logger.debug(f"Face score: presence={face_ratio:.2f} emotion_bonus={avg_emotion:.2f} "
                 f"→ score={score:.3f}")
    return score

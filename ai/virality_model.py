"""
Virality Score Predictor — scikit-learn model that estimates how "viral"
a reel is likely to be based on editing features.

Features used:
  1. avg_clip_duration       — shorter clips tend to perform better
  2. avg_motion_score        — high motion = engagement
  3. num_scene_changes       — more cuts = dynamic feel
  4. speech_presence_ratio   — speech helps retention
  5. beat_alignment_ratio    — how many cuts land on a beat
  6. face_presence_ratio     — face clips = emotional connection
  7. avg_sharpness_score     — quality signal
  8. total_duration          — reels 15–30s score highest

Training data is synthetic by default (100 samples).
Replace with real engagement data (views, shares, likes) when available.

Usage:
    from ai.virality_model import predict_virality, train_default_model
    model = train_default_model()         # or load saved model
    score = predict_virality(model, features_dict)
"""

import numpy as np
import logging
import os
import pickle
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("reel-generator.virality_model")

# ── Feature names (must match the order in _features_to_vector) ──────────────
FEATURE_NAMES = [
    "avg_clip_duration",         # seconds
    "avg_motion_score",          # 0–1
    "num_scene_changes",         # count
    "speech_presence_ratio",     # 0–1 (fraction of clips with speech)
    "beat_alignment_ratio",      # 0–1 (fraction of cuts aligned to beats)
    "face_presence_ratio",       # 0–1
    "avg_sharpness_score",       # 0–1
    "total_duration",            # seconds
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "cache", "virality_model.pkl")


# ── Feature Extraction ────────────────────────────────────────────────────────

def extract_features(
    scenes: List[Dict],
    beat_times: Optional[List[float]] = None,
    target_duration: float = 30.0,
) -> Dict[str, float]:
    """
    Compute virality features from a list of scored scenes.

    Args:
        scenes:          List of scene dicts (with score, motion_score, etc.)
        beat_times:      Beat timestamps in seconds (from beat_analyzer).
        target_duration: Total reel duration in seconds.

    Returns:
        Dict mapping feature names to float values.
    """
    if not scenes:
        return {name: 0.0 for name in FEATURE_NAMES}

    durations = [sc.get("duration", sc.get("end_time", 0) - sc.get("start_time", 0))
                 for sc in scenes]
    avg_clip_dur = float(np.mean(durations)) if durations else 0.0

    motion_scores = [sc.get("motion_score", 0.0) for sc in scenes]
    avg_motion = float(np.mean(motion_scores))

    num_cuts = len(scenes)

    # Speech presence: proxy = audio_score > 0.1 means speech likely present
    audio_scores = [sc.get("audio_score", 0.0) for sc in scenes]
    speech_ratio = float(np.mean([1.0 if a > 0.1 else 0.0 for a in audio_scores]))

    # Beat alignment: for each scene's start_time, check if a beat is within 0.15s
    beat_aligned = 0
    if beat_times and len(beat_times) > 0:
        for sc in scenes:
            start = sc.get("start_time", 0.0)
            min_dist = min(abs(bt - start) for bt in beat_times)
            if min_dist <= 0.15:
                beat_aligned += 1
        beat_alignment_ratio = beat_aligned / num_cuts
    else:
        beat_alignment_ratio = 0.0

    face_scores = [sc.get("face_score", 0.0) for sc in scenes]
    face_ratio = float(np.mean([1.0 if f > 0.1 else 0.0 for f in face_scores]))

    sharpness_scores = [sc.get("sharpness_score", 0.0) for sc in scenes]
    avg_sharpness = float(np.mean(sharpness_scores))

    return {
        "avg_clip_duration": round(avg_clip_dur, 3),
        "avg_motion_score": round(avg_motion, 3),
        "num_scene_changes": num_cuts,
        "speech_presence_ratio": round(speech_ratio, 3),
        "beat_alignment_ratio": round(beat_alignment_ratio, 3),
        "face_presence_ratio": round(face_ratio, 3),
        "avg_sharpness_score": round(avg_sharpness, 3),
        "total_duration": round(target_duration, 3),
    }


def _features_to_vector(features: Dict[str, float]) -> np.ndarray:
    """Convert features dict to numpy vector in correct order."""
    return np.array([features.get(name, 0.0) for name in FEATURE_NAMES], dtype=np.float32)


# ── Model Training ────────────────────────────────────────────────────────────

def _generate_training_data(n_samples: int = 200) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate synthetic training data based on domain knowledge.

    In production, replace this with real engagement metrics:
        X[i] = feature vector for reel i
        y[i] = normalised engagement score (views/1000, likes, shares combined)

    The synthetic rules encode known best practices:
      - Short clips (1–3s) → higher virality
      - High motion → higher virality
      - Beat-aligned cuts → higher virality
      - Face presence → higher virality
      - Optimal duration 15–30s → higher virality
      - Bad sharpness → lower virality
    """
    rng = np.random.default_rng(42)
    X = []
    y = []

    for _ in range(n_samples):
        avg_clip_dur = rng.uniform(0.5, 8.0)
        avg_motion = rng.uniform(0.0, 1.0)
        num_cuts = rng.integers(3, 30)
        speech_ratio = rng.uniform(0.0, 1.0)
        beat_align = rng.uniform(0.0, 1.0)
        face_ratio = rng.uniform(0.0, 1.0)
        sharpness = rng.uniform(0.0, 1.0)
        total_dur = rng.uniform(5.0, 60.0)

        # Virality scoring rules (domain knowledge)
        score = 0.0

        # Short clips are more engaging (sweet spot 1–3s)
        if 1.0 <= avg_clip_dur <= 3.0:
            score += 0.25
        elif avg_clip_dur < 1.0:
            score += 0.10    # too fast = disorienting
        else:
            score += max(0, 0.25 - (avg_clip_dur - 3.0) * 0.05)

        # High motion boosts engagement
        score += avg_motion * 0.20

        # Beat alignment is a strong positive signal
        score += beat_align * 0.20

        # Face presence → emotional connection
        score += face_ratio * 0.15

        # Speech presence → retention
        score += speech_ratio * 0.10

        # Quality matters
        score += sharpness * 0.10

        # Optimal reel duration: 15–30s
        if 15 <= total_dur <= 30:
            score += 0.10
        elif total_dur < 15:
            score += 0.05
        else:
            score += max(0, 0.10 - (total_dur - 30) * 0.003)

        # Clip count sweet spot: 8–20 cuts
        if 8 <= num_cuts <= 20:
            score += 0.05

        # Add noise
        score += rng.normal(0, 0.05)
        score = float(np.clip(score, 0.0, 1.0))

        X.append([avg_clip_dur, avg_motion, num_cuts, speech_ratio,
                  beat_align, face_ratio, sharpness, total_dur])
        y.append(score)

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


def train_default_model(save: bool = True):
    """
    Train a GradientBoostingRegressor on synthetic data.
    Saves the model to cache/virality_model.pkl.

    Returns:
        Trained sklearn Pipeline (StandardScaler + GBR).
    """
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
        from sklearn.model_selection import cross_val_score
    except ImportError:
        logger.error("scikit-learn not installed. Run: pip install scikit-learn")
        return None

    logger.info("Training virality model on synthetic data…")
    X, y = _generate_training_data(n_samples=300)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr", GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42,
        )),
    ])
    model.fit(X, y)

    # Quick cross-val check
    scores = cross_val_score(model, X, y, cv=5, scoring="r2")
    logger.info(f"Cross-val R² = {scores.mean():.3f} ± {scores.std():.3f}")

    if save:
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        logger.info(f"Model saved → {MODEL_PATH}")

    return model


def load_model():
    """Load saved model, or train a new one if not found."""
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        logger.info("Virality model loaded from cache")
        return model
    logger.info("No saved model found. Training default model…")
    return train_default_model(save=True)


# ── Prediction ────────────────────────────────────────────────────────────────

def predict_virality(
    scenes: List[Dict],
    beat_times: Optional[List[float]] = None,
    target_duration: float = 30.0,
    model=None,
) -> Dict:
    """
    Predict the virality score for a reel given its scenes.

    Args:
        scenes:          Scored scene list (from highlight_scorer).
        beat_times:      Beat timestamps (from beat_analyzer).
        target_duration: Intended reel duration in seconds.
        model:           Trained sklearn model (loaded automatically if None).

    Returns:
        Dict with:
          - virality_score: float 0.0–1.0
          - virality_label: "Low" | "Medium" | "High" | "Viral"
          - features:       the extracted feature values
          - tips:           list of improvement suggestions
    """
    if model is None:
        model = load_model()

    if model is None:
        return {"virality_score": 0.0, "virality_label": "Unknown",
                "features": {}, "tips": ["Install scikit-learn"]}

    features = extract_features(scenes, beat_times, target_duration)
    X = _features_to_vector(features).reshape(1, -1)

    score = float(np.clip(model.predict(X)[0], 0.0, 1.0))

    # Label
    if score >= 0.75:
        label = "Viral"
    elif score >= 0.55:
        label = "High"
    elif score >= 0.35:
        label = "Medium"
    else:
        label = "Low"

    tips = _generate_tips(features, score)

    logger.info(f"Virality: score={score:.3f} label={label}")
    return {
        "virality_score": round(score, 3),
        "virality_label": label,
        "features": features,
        "tips": tips,
    }


def _generate_tips(features: Dict[str, float], score: float) -> List[str]:
    """Generate human-readable improvement suggestions."""
    tips = []

    if features["avg_clip_duration"] > 4.0:
        tips.append("Cut clips shorter (1–3s each) to increase energy.")
    if features["beat_alignment_ratio"] < 0.5:
        tips.append("Sync more cuts to music beats for a more satisfying rhythm.")
    if features["face_presence_ratio"] < 0.3:
        tips.append("Include more face shots — they drive emotional engagement.")
    if features["avg_motion_score"] < 0.3:
        tips.append("Add higher-motion clips — static scenes reduce engagement.")
    if features["avg_sharpness_score"] < 0.4:
        tips.append("Some clips appear blurry or low quality — consider removing them.")
    if not (15 <= features["total_duration"] <= 30):
        tips.append("Aim for 15–30s reel duration for best platform performance.")
    if features["speech_presence_ratio"] < 0.3:
        tips.append("Adding a voiceover or speech-heavy clips can increase retention.")
    if features["num_scene_changes"] < 6:
        tips.append("Add more scene variety — monotone reels lose viewers quickly.")

    if not tips:
        tips.append("Reel looks well-optimised. Consider A/B testing with a different music track.")

    return tips

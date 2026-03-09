"""
CLIP scorer — uses OpenAI CLIP to score frames against text prompts.
Measures semantic relevance: "how well does this frame match 'exciting travel moment'?"
"""

import numpy as np
import logging
from typing import List, Optional
from PIL import Image

logger = logging.getLogger("reel-generator.clip_scorer")

# Lazy-load CLIP (heavy model)
_clip_model = None
_clip_preprocess = None
_clip_device = None


def _load_clip():
    """Load CLIP model once and cache it."""
    global _clip_model, _clip_preprocess, _clip_device

    if _clip_model is not None:
        return

    try:
        import torch
        import clip

        _clip_device = "cuda" if torch.cuda.is_available() else "cpu"
        from config import settings
        logger.info(f"Loading CLIP {settings.CLIP_MODEL} on {_clip_device}…")
        _clip_model, _clip_preprocess = clip.load(settings.CLIP_MODEL, device=_clip_device)
        logger.info("CLIP loaded ✓")
    except ImportError:
        logger.warning("CLIP not installed. Install with: pip install git+https://github.com/openai/CLIP.git")
        logger.warning("CLIP scoring will return 0.0 for all frames.")
    except Exception as e:
        logger.warning(f"Failed to load CLIP: {e}")


def compute_clip_score(
    frames: List[np.ndarray],
    prompts: List[str],
    sample_count: int = 3,
) -> float:
    """
    Score frames against text prompts using CLIP.

    Args:
        frames:        List of BGR frames (numpy arrays).
        prompts:       Text descriptions of "interesting" content.
        sample_count:  Max frames to score (CLIP is slow on CPU).

    Returns:
        Normalised relevance score 0.0 – 1.0.
    """
    _load_clip()

    if _clip_model is None:
        return 0.0  # CLIP not available, skip gracefully

    import torch
    import clip
    import cv2

    # Sample evenly from the frame list
    if len(frames) > sample_count:
        indices = np.linspace(0, len(frames) - 1, sample_count, dtype=int)
        sampled = [frames[i] for i in indices]
    else:
        sampled = frames

    if not sampled:
        return 0.0

    # Also include a "negative" prompt to create contrast
    all_prompts = prompts + ["boring empty footage", "blurry dark unusable clip"]
    text_tokens = clip.tokenize(all_prompts).to(_clip_device)

    scores = []
    with torch.no_grad():
        text_features = _clip_model.encode_text(text_tokens)
        text_features /= text_features.norm(dim=-1, keepdim=True)

        for frame in sampled:
            # Convert BGR → RGB → PIL
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
            image_input = _clip_preprocess(pil_img).unsqueeze(0).to(_clip_device)

            image_features = _clip_model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)

            # Cosine similarity with each prompt
            similarity = (image_features @ text_features.T).squeeze(0)
            sim_probs = similarity.softmax(dim=-1).cpu().numpy()

            # Score = average similarity to positive prompts minus negative prompts
            n_positive = len(prompts)
            positive_score = float(np.mean(sim_probs[:n_positive]))
            negative_score = float(np.mean(sim_probs[n_positive:]))

            # Normalize: positive proportion of total
            if positive_score + negative_score > 0:
                frame_score = positive_score / (positive_score + negative_score)
            else:
                frame_score = 0.5

            scores.append(frame_score)

    final_score = float(np.mean(scores)) if scores else 0.0
    logger.debug(f"CLIP score: {final_score:.3f} (from {len(sampled)} frames)")
    return float(np.clip(final_score, 0.0, 1.0))

"""
/api/analyze — Run scene detection and highlight scoring on uploaded clips.
Returns scored scenes with thumbnails.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import logging

from config import settings
from core.scene_detector import detect_scenes_in_video
from core.highlight_scorer import score_scenes
from utils.ffmpeg_utils import generate_thumbnail
from ai.virality_model import predict_virality

router = APIRouter()
logger = logging.getLogger("reel-generator.analyze")


class AnalyzeRequest(BaseModel):
    project_id: str
    clip_prompts: Optional[List[str]] = None   # CLIP text prompts for relevance scoring
    scene_threshold: Optional[float] = None     # override default threshold


class SceneResult(BaseModel):
    clip_file: str
    scene_index: int
    start_time: float
    end_time: float
    duration: float
    score: float
    motion_score: float
    sharpness_score: float
    clip_score: float
    audio_score: float
    face_score: float
    thumbnail_url: Optional[str] = None


@router.post("/analyze", response_model=dict)
async def analyze_project(req: AnalyzeRequest):
    """
    Detect scenes in all clips and score them.
    Returns a list of scored scenes sorted by highlight score (descending).
    """
    project_dir = os.path.join(settings.UPLOAD_DIR, req.project_id)
    videos_dir = os.path.join(project_dir, "videos")

    if not os.path.isdir(videos_dir):
        raise HTTPException(404, f"Project '{req.project_id}' not found.")

    video_files = sorted([
        f for f in os.listdir(videos_dir)
        if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv", ".webm"))
    ])

    if not video_files:
        raise HTTPException(400, "No video files found in project.")

    threshold = req.scene_threshold or settings.SCENE_THRESHOLD
    prompts = req.clip_prompts or [
        "an exciting interesting moment",
        "beautiful scenery or landscape",
        "a person showing emotion",
        "dramatic action or movement",
    ]

    # ── Detect & score scenes across all clips ───────────────────────
    all_scenes: List[dict] = []
    thumbs_dir = os.path.join(project_dir, "thumbnails")
    os.makedirs(thumbs_dir, exist_ok=True)

    for vfile in video_files:
        vpath = os.path.join(videos_dir, vfile)
        logger.info(f"[{req.project_id}] Detecting scenes in {vfile}…")

        # Step 1 — scene boundaries
        scenes = detect_scenes_in_video(vpath, threshold=threshold)
        logger.info(f"  → Found {len(scenes)} scenes")

        # Step 2 — score each scene
        scored = score_scenes(vpath, scenes, prompts=prompts)

        for idx, sc in enumerate(scored):
            # Generate thumbnail at midpoint
            mid = (sc["start_time"] + sc["end_time"]) / 2
            thumb_name = f"{vfile}_{idx:03d}.jpg"
            thumb_path = os.path.join(thumbs_dir, thumb_name)
            generate_thumbnail(vpath, mid, thumb_path)

            sc["clip_file"] = vfile
            sc["scene_index"] = idx
            sc["thumbnail_url"] = f"/output/{req.project_id}/thumbnails/{thumb_name}"
            all_scenes.append(sc)

    # Sort by score descending
    all_scenes.sort(key=lambda s: s["score"], reverse=True)

    logger.info(f"[{req.project_id}] Total scenes: {len(all_scenes)}, "
                f"top score: {all_scenes[0]['score']:.2f}" if all_scenes else "no scenes")

    # Compute a quick virality preview on top-N scenes
    top_scenes = all_scenes[:20]
    virality_preview = predict_virality(scenes=top_scenes)

    return {
        "project_id": req.project_id,
        "total_scenes": len(all_scenes),
        "scenes": all_scenes,
        "virality_preview": virality_preview,
    }

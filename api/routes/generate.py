"""
/api/generate — Assemble the final reel from scored scenes.
Trims clips to beat boundaries, adds transitions, music, captions, and exports.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import logging

from config import settings
from core.beat_analyzer import detect_beats
from core.assembler import assemble_reel
from core.renderer import render_final
from core.caption_generator import generate_captions
from core.style_engine import get_style, list_styles, apply_style_to_scenes, build_color_grade_filter
from ai.virality_model import predict_virality

router = APIRouter()
logger = logging.getLogger("reel-generator.generate")

# ── In-memory job tracker (use Redis/Celery for production) ──────────
jobs: dict = {}


class SceneSelection(BaseModel):
    clip_file: str
    start_time: float
    end_time: float
    score: float = 0.0
    motion_score: float = 0.0
    face_score: float = 0.0
    audio_score: float = 0.0
    sharpness_score: float = 0.0


class GenerateRequest(BaseModel):
    project_id: str
    selected_scenes: List[SceneSelection]
    target_duration: Optional[int] = 30           # seconds
    style: Optional[str] = "fast_cuts"            # fast_cuts | cinematic | vlog_energy | meme_style | minimal
    add_captions: Optional[bool] = False
    music_volume: Optional[float] = None          # None = use style default


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str
    virality: Optional[dict] = None


@router.get("/styles")
async def get_styles():
    """Return all available editing styles."""
    return {"styles": list_styles()}


@router.post("/generate", response_model=GenerateResponse)
async def generate_reel(req: GenerateRequest):
    """
    Take selected scenes, apply style, sync to music beats, assemble, and render the reel.
    Returns a job_id to poll for progress and an immediate virality prediction.
    """
    project_dir = os.path.join(settings.UPLOAD_DIR, req.project_id)
    videos_dir = os.path.join(project_dir, "videos")

    if not os.path.isdir(videos_dir):
        raise HTTPException(404, f"Project '{req.project_id}' not found.")

    if not req.selected_scenes:
        raise HTTPException(400, "Select at least one scene.")

    # ── Resolve style ─────────────────────────────────────────────────
    style = get_style(req.style or "fast_cuts")

    # ── Pre-compute virality score (fast, before heavy processing) ────
    scenes_dicts = [sc.model_dump() for sc in req.selected_scenes]
    virality = predict_virality(
        scenes=scenes_dicts,
        target_duration=req.target_duration,
    )

    # ── Create a job ─────────────────────────────────────────────────
    job_id = str(uuid.uuid4())[:10]
    jobs[job_id] = {"status": "processing", "progress": 0, "output": None, "error": None}

    # NOTE: In production, delegate to Celery task (see tasks/celery_tasks.py).
    # For the MVP we run synchronously (blocking).
    try:
        _run_generation(job_id, req, project_dir, videos_dir, style)
    except Exception as e:
        logger.exception(f"[{job_id}] Generation failed")
        jobs[job_id] = {"status": "failed", "progress": 0, "output": None, "error": str(e)}
        raise HTTPException(500, f"Reel generation failed: {e}")

    return GenerateResponse(
        job_id=job_id,
        status=jobs[job_id]["status"],
        message="Reel generated successfully!" if jobs[job_id]["status"] == "done" else "Processing…",
        virality=virality,
    )


def _run_generation(job_id: str, req: GenerateRequest, project_dir: str, videos_dir: str, style):
    """Synchronous generation pipeline (would be async Celery task in prod)."""

    # ── Step 1: Beat detection ───────────────────────────────────────
    jobs[job_id]["progress"] = 10
    music_dir = os.path.join(project_dir, "music")
    music_path = None
    beat_times = None

    if os.path.isdir(music_dir):
        music_files = os.listdir(music_dir)
        if music_files:
            music_path = os.path.join(music_dir, music_files[0])
            logger.info(f"[{job_id}] Detecting beats in {music_files[0]}…")
            beat_times = detect_beats(music_path)
            logger.info(f"[{job_id}] Found {len(beat_times)} beats")

    # ── Step 2: Apply style — re-rank scenes by style preferences ────
    jobs[job_id]["progress"] = 20
    scenes_data = []
    for sc in req.selected_scenes:
        scenes_data.append({
            "video_path": os.path.join(videos_dir, sc.clip_file),
            "start_time": sc.start_time,
            "end_time": sc.end_time,
            "score": sc.score,
            "motion_score": sc.motion_score,
            "face_score": sc.face_score,
            "audio_score": sc.audio_score,
            "sharpness_score": sc.sharpness_score,
        })

    # Re-rank by style preference (face/motion boosts)
    scenes_data = apply_style_to_scenes(scenes_data, style)

    # ── Step 3: Assemble clips to beat boundaries ────────────────────
    jobs[job_id]["progress"] = 35
    logger.info(f"[{job_id}] Style={style.name} | Assembling {len(scenes_data)} scenes…")

    assembled = assemble_reel(
        scenes=scenes_data,
        beat_times=beat_times,
        target_duration=req.target_duration,
        transition_type=style.transition_type,   # ← comes from style, not request
    )

    # ── Step 4: Captions ─────────────────────────────────────────────
    jobs[job_id]["progress"] = 60
    captions = None
    if req.add_captions and style.caption_style != "none":
        logger.info(f"[{job_id}] Generating captions (style={style.caption_style})…")
        captions = generate_captions(assembled["temp_video_path"])

    # ── Step 5: Build color grade FFmpeg filter ───────────────────────
    color_grade_filter = build_color_grade_filter(style.color_grade)

    # ── Step 6: Final render ─────────────────────────────────────────
    jobs[job_id]["progress"] = 80
    output_filename = f"reel_{req.project_id}_{job_id}.mp4"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

    music_vol = req.music_volume if req.music_volume is not None else style.music_volume

    logger.info(f"[{job_id}] Rendering final reel → {output_filename} (grade={style.color_grade})")
    render_final(
        assembled_video_path=assembled["temp_video_path"],
        output_path=output_path,
        music_path=music_path,
        music_volume=music_vol,
        captions=captions,
        color_grade_filter=color_grade_filter,
        caption_style=style.caption_style,
        width=settings.DEFAULT_WIDTH,
        height=settings.DEFAULT_HEIGHT,
    )

    # ── Done ─────────────────────────────────────────────────────────
    jobs[job_id] = {
        "status": "done",
        "progress": 100,
        "output": f"/output/{output_filename}",
        "error": None,
    }
    logger.info(f"[{job_id}] ✓ Reel ready: {output_path}")


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll job progress."""
    if job_id not in jobs:
        raise HTTPException(404, "Job not found.")
    return jobs[job_id]

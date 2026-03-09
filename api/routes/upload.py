"""
/api/upload — Accept video clips and a music file.
Returns a project_id that ties all files together.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import os
import shutil
import logging

from config import settings
from utils.ffmpeg_utils import get_video_metadata

router = APIRouter()
logger = logging.getLogger("reel-generator.upload")


@router.post("/upload")
async def upload_files(
    videos: List[UploadFile] = File(..., description="Raw video clips (2-10 files)"),
    music: UploadFile = File(None, description="Background music track (optional)"),
):
    """
    Upload raw video clips (and optionally a music track).
    Returns a project_id and metadata for each file.
    """
    # ── Validate ─────────────────────────────────────────────────────
    if len(videos) < 1:
        raise HTTPException(400, "Upload at least 1 video clip.")
    if len(videos) > 10:
        raise HTTPException(400, "Maximum 10 clips allowed.")

    for v in videos:
        if not v.content_type or not v.content_type.startswith("video/"):
            raise HTTPException(400, f"'{v.filename}' is not a video file.")

    # ── Create project folder ────────────────────────────────────────
    project_id = str(uuid.uuid4())[:12]
    project_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    videos_dir = os.path.join(project_dir, "videos")
    os.makedirs(videos_dir, exist_ok=True)

    # ── Save video files ─────────────────────────────────────────────
    video_info = []
    for idx, v in enumerate(videos):
        ext = os.path.splitext(v.filename)[1] or ".mp4"
        filename = f"clip_{idx:02d}{ext}"
        filepath = os.path.join(videos_dir, filename)

        with open(filepath, "wb") as f:
            shutil.copyfileobj(v.file, f)

        # Extract metadata
        meta = get_video_metadata(filepath)
        meta["original_name"] = v.filename
        meta["saved_as"] = filename
        video_info.append(meta)
        logger.info(f"[{project_id}] Saved {v.filename} → {filename}  ({meta.get('duration', '?')}s)")

    # ── Save music file (optional) ───────────────────────────────────
    music_info = None
    if music and music.filename:
        music_dir = os.path.join(project_dir, "music")
        os.makedirs(music_dir, exist_ok=True)
        ext = os.path.splitext(music.filename)[1] or ".mp3"
        music_path = os.path.join(music_dir, f"track{ext}")
        with open(music_path, "wb") as f:
            shutil.copyfileobj(music.file, f)
        music_info = {
            "original_name": music.filename,
            "saved_as": f"track{ext}",
            "path": music_path,
        }
        logger.info(f"[{project_id}] Saved music: {music.filename}")

    return {
        "project_id": project_id,
        "videos": video_info,
        "music": music_info,
        "message": f"Uploaded {len(videos)} clips successfully.",
    }


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Return file listing for an existing project."""
    project_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    if not os.path.isdir(project_dir):
        raise HTTPException(404, "Project not found.")

    videos_dir = os.path.join(project_dir, "videos")
    video_files = sorted(os.listdir(videos_dir)) if os.path.isdir(videos_dir) else []

    music_dir = os.path.join(project_dir, "music")
    music_files = os.listdir(music_dir) if os.path.isdir(music_dir) else []

    return {
        "project_id": project_id,
        "videos": video_files,
        "music": music_files[0] if music_files else None,
    }

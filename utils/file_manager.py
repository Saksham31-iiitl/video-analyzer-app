"""
File manager — handles temp file cleanup, directory management, and safe file paths.
"""

import os
import shutil
import time
import logging

from config import settings

logger = logging.getLogger("reel-generator.file_manager")


def cleanup_temp(max_age_hours: float = 2.0):
    """Remove temp files older than max_age_hours."""
    temp_dir = settings.TEMP_DIR
    if not os.path.isdir(temp_dir):
        return

    cutoff = time.time() - (max_age_hours * 3600)
    removed = 0

    for f in os.listdir(temp_dir):
        fpath = os.path.join(temp_dir, f)
        try:
            if os.path.getmtime(fpath) < cutoff:
                if os.path.isfile(fpath):
                    os.remove(fpath)
                elif os.path.isdir(fpath):
                    shutil.rmtree(fpath)
                removed += 1
        except OSError:
            pass

    if removed:
        logger.info(f"Cleaned up {removed} temp files")


def cleanup_project(project_id: str):
    """Remove all files for a project (uploads + thumbnails)."""
    project_dir = os.path.join(settings.UPLOAD_DIR, project_id)
    if os.path.isdir(project_dir):
        shutil.rmtree(project_dir)
        logger.info(f"Removed project: {project_id}")


def get_project_path(project_id: str) -> str:
    """Get the upload directory for a project."""
    return os.path.join(settings.UPLOAD_DIR, project_id)


def ensure_dir(path: str):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

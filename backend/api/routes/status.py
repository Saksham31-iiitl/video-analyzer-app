"""
/api/status — Lightweight status & job polling endpoints.
"""

from fastapi import APIRouter
from api.routes.generate import jobs

router = APIRouter()


@router.get("/status/{job_id}")
async def poll_status(job_id: str):
    """Return current progress of a generation job."""
    job = jobs.get(job_id)
    if not job:
        return {"status": "not_found", "progress": 0, "output": None, "error": "Job ID not found."}
    return job

"""
Celery task definitions for background video processing.

SETUP (optional — the MVP runs synchronously without Celery):
    1. Install Redis: sudo apt install redis-server
    2. pip install celery redis
    3. Start worker: celery -A tasks.celery_tasks worker --loglevel=info
    4. Switch generate.py to use .delay() calls instead of synchronous _run_generation()
"""

# ── Uncomment below when you're ready to add background task support ──

# from celery import Celery
# import os
#
# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
#
# celery_app = Celery(
#     "auto_reel_generator",
#     broker=REDIS_URL,
#     backend=REDIS_URL,
# )
#
# celery_app.conf.update(
#     task_serializer="json",
#     result_serializer="json",
#     accept_content=["json"],
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_time_limit=600,  # 10 minute timeout
# )
#
#
# @celery_app.task(bind=True)
# def generate_reel_task(self, project_id, scenes, music_path, options):
#     """Background reel generation task."""
#     self.update_state(state="PROGRESS", meta={"progress": 10})
#     # ... call the same pipeline as generate.py _run_generation()
#     pass

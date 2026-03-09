"""
Centralised settings for the Auto Reel Generator backend.
Override any value via environment variables or a .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    # ── Directories ──────────────────────────────────────────────────
    UPLOAD_DIR: str = str(BASE_DIR / "uploads")
    TEMP_DIR: str = str(BASE_DIR / "temp")
    OUTPUT_DIR: str = str(BASE_DIR / "output")
    CACHE_DIR: str = str(BASE_DIR / "cache")
    MUSIC_DIR: str = str(BASE_DIR / "music")

    # ── CORS ─────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",   # CRA / Next
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # ── Video defaults ───────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 500
    PROXY_HEIGHT: int = 360           # height for low-res proxy
    DEFAULT_REEL_DURATION: int = 30   # seconds
    DEFAULT_FPS: int = 30
    DEFAULT_WIDTH: int = 1080         # 9:16 vertical
    DEFAULT_HEIGHT: int = 1920

    # ── AI Models ────────────────────────────────────────────────────
    CLIP_MODEL: str = "ViT-B/32"
    WHISPER_MODEL: str = "base"       # tiny | base | small | medium
    SCENE_THRESHOLD: float = 30.0     # PySceneDetect content threshold

    # ── Scoring weights ──────────────────────────────────────────────
    WEIGHT_MOTION: float = 0.25
    WEIGHT_SHARPNESS: float = 0.20
    WEIGHT_CLIP: float = 0.30
    WEIGHT_AUDIO: float = 0.15
    WEIGHT_FACE: float = 0.10

    # ── Processing ───────────────────────────────────────────────────
    FRAME_SAMPLE_FPS: int = 2         # frames per second to analyse
    MAX_WORKERS: int = 4              # parallel processing workers

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

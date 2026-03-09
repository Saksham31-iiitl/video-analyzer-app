"""
Auto Reel Generator — FastAPI entry point
"""

import os
import logging

# ── Ensure ffmpeg is on PATH for whisper and other tools ─────────────────────
_WINGET_FFMPEG_BIN = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.0.1-full_build\bin"
)
if os.path.isdir(_WINGET_FFMPEG_BIN) and _WINGET_FFMPEG_BIN not in os.environ.get("PATH", ""):
    os.environ["PATH"] = _WINGET_FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from api.routes import upload, analyze, generate, status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Auto Reel Generator",
    description="AI-powered short reel generator from raw video clips.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(generate.router, prefix="/api", tags=["generate"])
app.include_router(status.router, prefix="/api", tags=["status"])

import os
os.makedirs("output", exist_ok=True)
app.mount("/output", StaticFiles(directory="output"), name="output")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Auto Reel Generator API is running."}

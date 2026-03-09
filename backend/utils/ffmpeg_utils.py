"""
FFmpeg & FFprobe utility wrappers.
Handles metadata extraction, thumbnail generation, audio extraction, proxy creation.
"""

import subprocess
import json
import os
import logging
from typing import Dict, Optional

from config import settings

logger = logging.getLogger("reel-generator.ffmpeg_utils")

# Use imageio-ffmpeg's bundled binary so FFmpeg doesn't need to be on PATH
try:
    import imageio_ffmpeg
    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    logger.info(f"Using bundled ffmpeg: {_FFMPEG}")
except Exception:
    _FFMPEG = "ffmpeg"

# ffprobe: check known winget install path, then fall back to PATH
_WINGET_FFPROBE = os.path.expandvars(
    r"%LOCALAPPDATA%\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-8.0.1-full_build\bin\ffprobe.exe"
)
_FFPROBE = _WINGET_FFPROBE if os.path.isfile(_WINGET_FFPROBE) else "ffprobe"


def get_video_metadata(video_path: str) -> Dict:
    """
    Extract metadata from a video file using FFprobe.

    Returns dict with: duration, width, height, fps, codec, has_audio, file_size_mb.
    """
    cmd = [
        _FFPROBE,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
    except Exception as e:
        logger.warning(f"FFprobe failed for {video_path}: {e}")
        return {"path": video_path, "error": str(e)}

    # Find video stream
    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream["codec_type"] == "video" and video_stream is None:
            video_stream = stream
        elif stream["codec_type"] == "audio" and audio_stream is None:
            audio_stream = stream

    fmt = data.get("format", {})

    # Parse FPS from r_frame_rate (e.g., "30/1" or "30000/1001")
    fps = 30.0
    if video_stream and "r_frame_rate" in video_stream:
        try:
            num, den = video_stream["r_frame_rate"].split("/")
            fps = round(int(num) / int(den), 2)
        except (ValueError, ZeroDivisionError):
            pass

    duration = float(fmt.get("duration", 0))
    file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB

    return {
        "path": video_path,
        "duration": round(duration, 2),
        "width": int(video_stream.get("width", 0)) if video_stream else 0,
        "height": int(video_stream.get("height", 0)) if video_stream else 0,
        "fps": fps,
        "codec": video_stream.get("codec_name", "unknown") if video_stream else "unknown",
        "has_audio": audio_stream is not None,
        "file_size_mb": round(file_size, 2),
    }


def generate_thumbnail(video_path: str, timestamp: float, output_path: str, width: int = 320):
    """
    Extract a single frame as a JPEG thumbnail.

    Args:
        video_path:   Source video file.
        timestamp:    Time in seconds to extract the frame.
        output_path:  Output JPEG path.
        width:        Thumbnail width (height auto-scaled).
    """
    cmd = [
        _FFMPEG, "-y",
        "-ss", str(timestamp),
        "-i", video_path,
        "-vframes", "1",
        "-vf", f"scale={width}:-1",
        "-q:v", "5",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        logger.warning(f"Thumbnail failed at {timestamp}s: {result.stderr[:200]}")


def create_proxy(video_path: str, output_path: str, height: int = 360):
    """
    Create a low-resolution proxy for fast analysis.

    Args:
        video_path:   Original high-res video.
        output_path:  Proxy output path.
        height:       Proxy height in pixels (width auto-scaled).
    """
    cmd = [
        _FFMPEG, "-y",
        "-i", video_path,
        "-vf", f"scale=-2:{height}",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "28",
        "-c:a", "copy",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.warning(f"Proxy creation failed: {result.stderr[:200]}")
    else:
        logger.info(f"Proxy created: {output_path}")


def extract_audio_segment(
    video_path: str,
    start: float,
    end: float,
) -> Optional[str]:
    """
    Extract an audio segment from a video as a temporary WAV file.

    Returns:
        Path to the extracted audio file, or None if extraction fails.
    """
    output_path = os.path.join(
        settings.TEMP_DIR,
        f"audio_{os.getpid()}_{start:.1f}_{end:.1f}.wav"
    )

    duration = end - start
    cmd = [
        _FFMPEG, "-y",
        "-ss", str(start),
        "-i", video_path,
        "-t", str(duration),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "22050",
        "-ac", "1",
        output_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        logger.debug(f"Audio extraction failed (may have no audio): {result.stderr[:200]}")
        return None

    # Check if the file has content
    if os.path.exists(output_path) and os.path.getsize(output_path) > 44:  # WAV header = 44 bytes
        return output_path

    return None

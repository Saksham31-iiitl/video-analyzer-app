"""
Renderer — applies final post-processing:
  • 9:16 aspect ratio (vertical crop/pad)
  • Background music overlay
  • Caption burn-in
  • H.264 encoding optimised for social media
"""

import subprocess
import os
import logging
from typing import Optional, List, Dict

from config import settings

logger = logging.getLogger("reel-generator.renderer")


def render_final(
    assembled_video_path: str,
    output_path: str,
    music_path: Optional[str] = None,
    music_volume: float = 0.7,
    captions: Optional[List[Dict]] = None,
    color_grade_filter: str = "",
    caption_style: str = "bottom",
    width: int = 1080,
    height: int = 1920,
):
    """
    Render the final reel with all post-processing.

    Approach: build a single FFmpeg command with filter chains for
    maximum speed (no intermediate files).

    Args:
        assembled_video_path: Intermediate assembled video.
        output_path:          Final output MP4 path.
        music_path:           Background music file (optional).
        music_volume:         Music volume 0.0–1.0.
        captions:             List of {start, end, text} dicts (optional).
        color_grade_filter:   FFmpeg filter string for color grade (from style_engine).
        caption_style:        Caption rendering style: bottom | meme | karaoke | none.
        width:                Output width (default 1080).
        height:               Output height (default 1920).
    """
    filters = []
    inputs = ["-i", assembled_video_path]
    audio_filter = []

    # ── 1. Scale + pad to 9:16 ───────────────────────────────────────
    scale_pad = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        f"setsar=1"
    )
    filters.append(scale_pad)

    # ── 2. Color grade ───────────────────────────────────────────────
    if color_grade_filter:
        filters.append(color_grade_filter)

    # ── 3. Caption burn-in ───────────────────────────────────────────
    if captions and caption_style != "none":
        for cap in captions:
            text = cap["text"].replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")
            start = cap["start"]
            end = cap["end"]
            enable = f"between(t,{start},{end})"

            if caption_style == "meme":
                drawtext = (
                    f"drawtext=text='{text}':fontsize=56:fontcolor=white"
                    f":borderw=5:bordercolor=black"
                    f":x=(w-text_w)/2:y=h-h/5-text_h:enable='{enable}'"
                )
            elif caption_style == "karaoke":
                drawtext = (
                    f"drawtext=text='{text}':fontsize=48:fontcolor=yellow"
                    f":shadowcolor=black@0.8:shadowx=2:shadowy=2"
                    f":x=(w-text_w)/2:y=h-h/5-text_h:enable='{enable}'"
                )
            else:  # bottom (default)
                drawtext = (
                    f"drawtext=text='{text}':fontsize=42:fontcolor=white"
                    f":borderw=3:bordercolor=black"
                    f":x=(w-text_w)/2:y=h-h/4:enable='{enable}'"
                )
            filters.append(drawtext)

    # ── 3. Build video filter chain ──────────────────────────────────
    vf = ",".join(filters) if filters else None

    # ── 4. Audio mixing ──────────────────────────────────────────────
    if music_path and os.path.exists(music_path):
        inputs.extend(["-i", music_path])
        # Mix original audio (if any) with music
        # [0:a] = video audio, [1:a] = music
        audio_filter = [
            "-filter_complex",
            (
                f"[0:a]volume=0.3[va];"
                f"[1:a]volume={music_volume}[ma];"
                f"[va][ma]amix=inputs=2:duration=shortest[aout]"
            ),
            "-map", "0:v",
            "-map", "[aout]",
        ]
    else:
        audio_filter = ["-map", "0:v", "-map", "0:a?"]

    # ── 5. Assemble FFmpeg command ───────────────────────────────────
    cmd = ["ffmpeg", "-y"]
    cmd.extend(inputs)

    if vf:
        cmd.extend(["-vf", vf])

    cmd.extend(audio_filter)

    cmd.extend([
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",   # web-optimised MP4
        output_path,
    ])

    logger.info(f"FFmpeg command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        logger.error(f"FFmpeg failed:\n{result.stderr}")
        raise RuntimeError(f"FFmpeg render failed: {result.stderr[-500:]}")

    # ── Clean up intermediate file ───────────────────────────────────
    if os.path.exists(assembled_video_path):
        os.remove(assembled_video_path)

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"✓ Final reel: {output_path} ({file_size:.1f} MB)")

"""
Style Engine — applies predefined editing styles to the reel pipeline.

Each style is a dataclass that controls:
  - clip_duration_range   : (min, max) seconds per clip
  - beat_multiplier       : snap to every N-th beat (1=every beat, 2=every other)
  - transition_type       : cut | crossfade | zoom
  - caption_style         : none | bottom | meme | karaoke
  - color_grade           : none | warm | cold | hdr | bw
  - audio_duck            : whether to duck music under speech
  - prefer_face_clips     : boost face-detected scenes to top
  - prefer_motion_clips   : boost high-motion scenes to top

Adding a new style = adding one entry to STYLES dict.
"""

from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Dict
import logging

logger = logging.getLogger("reel-generator.style_engine")


@dataclass
class EditingStyle:
    name: str
    display_name: str
    description: str

    # Clip selection
    clip_duration_range: Tuple[float, float] = (1.5, 4.0)   # (min_sec, max_sec)
    beat_multiplier: int = 1                                  # snap to every N beats
    prefer_face_clips: bool = False
    prefer_motion_clips: bool = False

    # Visual
    transition_type: str = "cut"                              # cut | crossfade | zoom
    color_grade: str = "none"                                 # none | warm | cold | hdr | bw

    # Text / captions
    caption_style: str = "bottom"                             # none | bottom | meme | karaoke
    caption_font_size: int = 42
    caption_color: str = "white"
    caption_position: str = "bottom"                          # bottom | center | top

    # Audio
    audio_duck: bool = True                                   # duck music under speech
    music_volume: float = 0.7

    # Score weight overrides (None = use settings defaults)
    weight_motion_override: Optional[float] = None
    weight_face_override: Optional[float] = None


# ── Predefined Styles ────────────────────────────────────────────────────────

STYLES: Dict[str, EditingStyle] = {

    "fast_cuts": EditingStyle(
        name="fast_cuts",
        display_name="Fast Cuts",
        description="Rapid-fire cuts synced to every beat. High energy, TikTok/Reels style.",
        clip_duration_range=(0.5, 2.5),
        beat_multiplier=1,           # cut on every single beat
        prefer_motion_clips=True,
        transition_type="cut",
        color_grade="hdr",
        caption_style="karaoke",
        caption_font_size=48,
        caption_color="yellow",
        audio_duck=False,
        music_volume=0.85,
        weight_motion_override=0.45,  # prioritise high-motion scenes
    ),

    "cinematic": EditingStyle(
        name="cinematic",
        display_name="Cinematic",
        description="Slow, deliberate cuts every 2–3 beats. Film-like color grade. Suits travel/landscape.",
        clip_duration_range=(3.0, 6.0),
        beat_multiplier=2,            # cut every 2nd beat
        prefer_face_clips=True,
        transition_type="crossfade",
        color_grade="cold",
        caption_style="bottom",
        caption_font_size=36,
        caption_color="white",
        audio_duck=True,
        music_volume=0.6,
        weight_face_override=0.25,
    ),

    "vlog_energy": EditingStyle(
        name="vlog_energy",
        display_name="Vlog Energy",
        description="Casual vlog pacing. Prefers face shots. Warm grade. Natural feel.",
        clip_duration_range=(2.0, 5.0),
        beat_multiplier=2,
        prefer_face_clips=True,
        transition_type="cut",
        color_grade="warm",
        caption_style="bottom",
        caption_font_size=40,
        caption_color="white",
        audio_duck=True,
        music_volume=0.5,
        weight_face_override=0.30,
    ),

    "meme_style": EditingStyle(
        name="meme_style",
        display_name="Meme Style",
        description="Short clips, impact-font captions, reaction zooms. Viral meme energy.",
        clip_duration_range=(0.5, 3.0),
        beat_multiplier=1,
        prefer_face_clips=True,
        prefer_motion_clips=True,
        transition_type="zoom",
        color_grade="none",
        caption_style="meme",
        caption_font_size=56,
        caption_color="white",
        audio_duck=False,
        music_volume=0.75,
        weight_face_override=0.35,
        weight_motion_override=0.35,
    ),

    "minimal": EditingStyle(
        name="minimal",
        display_name="Minimal",
        description="Long, clean clips. No captions. Subtle cold grade. For aesthetic/portfolio content.",
        clip_duration_range=(4.0, 8.0),
        beat_multiplier=4,
        prefer_face_clips=False,
        prefer_motion_clips=False,
        transition_type="crossfade",
        color_grade="cold",
        caption_style="none",
        caption_font_size=32,
        caption_color="white",
        audio_duck=False,
        music_volume=0.8,
    ),
}


def get_style(name: str) -> EditingStyle:
    """Return an EditingStyle by name. Falls back to 'fast_cuts'."""
    style = STYLES.get(name)
    if style is None:
        logger.warning(f"Unknown style '{name}', falling back to 'fast_cuts'")
        style = STYLES["fast_cuts"]
    return style


def list_styles() -> List[Dict]:
    """Return all styles as JSON-serialisable dicts (for the API)."""
    return [
        {
            "name": s.name,
            "display_name": s.display_name,
            "description": s.description,
            "transition_type": s.transition_type,
            "caption_style": s.caption_style,
            "color_grade": s.color_grade,
        }
        for s in STYLES.values()
    ]


def apply_style_to_scenes(
    scenes: List[Dict],
    style: EditingStyle,
) -> List[Dict]:
    """
    Re-rank scenes based on style preferences.

    - If prefer_face_clips: multiply face_score weight
    - If prefer_motion_clips: multiply motion_score weight
    Returns re-sorted scenes.
    """
    scored = []
    for sc in scenes:
        raw = sc.get("score", 0.0)

        # Apply style-specific boosts on top of existing scores
        boost = 0.0
        if style.prefer_face_clips:
            boost += sc.get("face_score", 0.0) * 0.2
        if style.prefer_motion_clips:
            boost += sc.get("motion_score", 0.0) * 0.2

        scored.append({**sc, "_style_score": raw + boost})

    scored.sort(key=lambda s: s["_style_score"], reverse=True)
    return scored


def build_color_grade_filter(grade: str) -> str:
    """
    Return an FFmpeg video filter string for the chosen color grade.
    Empty string = no grade.

    These are lightweight FFmpeg filters — no external LUT files needed.
    """
    grades = {
        "warm": "curves=r='0/0 0.5/0.6 1/1':g='0/0 0.5/0.5 1/1':b='0/0 0.5/0.4 1/0.9'",
        "cold": "curves=r='0/0 0.5/0.4 1/0.9':g='0/0 0.5/0.5 1/1':b='0/0 0.5/0.6 1/1'",
        "hdr":  "eq=contrast=1.15:brightness=0.02:saturation=1.4",
        "bw":   "hue=s=0,eq=contrast=1.2",
        "none": "",
    }
    return grades.get(grade, "")


def build_caption_drawtext(
    caption: Dict,
    style: EditingStyle,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Build a single FFmpeg drawtext filter string for one caption segment.

    Handles:
      - bottom: standard subtitle style
      - meme:   large impact-style text at top AND bottom
      - karaoke: centered, highlighted word-by-word (approximated)
      - none:   returns empty string
    """
    if style.caption_style == "none":
        return ""

    text = caption["text"].replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")
    start = caption["start"]
    end = caption["end"]
    enable = f"between(t,{start},{end})"
    font_size = style.caption_font_size

    # Position presets
    if style.caption_position == "top":
        y_expr = f"h/8"
    elif style.caption_position == "center":
        y_expr = "(h-text_h)/2"
    else:  # bottom (default)
        y_expr = "h-h/5-text_h"

    if style.caption_style == "meme":
        # Impact-style: white text, thick black border
        return (
            f"drawtext=text='{text}'"
            f":fontsize={font_size}"
            f":fontcolor=white"
            f":borderw=5"
            f":bordercolor=black"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='{enable}'"
        )
    elif style.caption_style == "karaoke":
        # Karaoke: yellow text with shadow
        return (
            f"drawtext=text='{text}'"
            f":fontsize={font_size}"
            f":fontcolor=yellow"
            f":shadowcolor=black@0.8"
            f":shadowx=2:shadowy=2"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='{enable}'"
        )
    else:
        # Standard bottom caption
        return (
            f"drawtext=text='{text}'"
            f":fontsize={font_size}"
            f":fontcolor={style.caption_color}"
            f":borderw=3"
            f":bordercolor=black"
            f":x=(w-text_w)/2"
            f":y={y_expr}"
            f":enable='{enable}'"
        )

"""
Beat & onset detection for music synchronisation.
Uses librosa to find beat timestamps in an audio track.
"""

import librosa
import numpy as np
import logging
from typing import List, Optional

logger = logging.getLogger("reel-generator.beat_analyzer")


def detect_beats(
    audio_path: str,
    start_time: float = 0.0,
    duration: Optional[float] = None,
) -> List[float]:
    """
    Detect beat timestamps in an audio file.

    Args:
        audio_path:  Path to audio file (mp3, wav, etc.)
        start_time:  Start offset in seconds.
        duration:    Max duration to analyse (None = entire file).

    Returns:
        Sorted list of beat timestamps in seconds.
    """
    logger.info(f"Loading audio: {audio_path}")
    y, sr = librosa.load(audio_path, sr=22050, offset=start_time, duration=duration)

    # Beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # Add start_time offset back
    beat_times = [round(t + start_time, 3) for t in beat_times]

    # librosa >= 0.10 returns tempo as a numpy array; extract scalar
    tempo_val = float(np.atleast_1d(tempo)[0])
    logger.info(f"Detected tempo ≈ {tempo_val:.1f} BPM, {len(beat_times)} beats")
    return beat_times


def detect_onsets(
    audio_path: str,
    start_time: float = 0.0,
    duration: Optional[float] = None,
) -> List[float]:
    """
    Detect onset (transient) timestamps — more granular than beats.
    Useful for syncing to cymbal hits, bass drops, etc.
    """
    y, sr = librosa.load(audio_path, sr=22050, offset=start_time, duration=duration)
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="frames")
    onset_times = librosa.frames_to_time(onset_frames, sr=sr).tolist()
    onset_times = [round(t + start_time, 3) for t in onset_times]

    logger.info(f"Detected {len(onset_times)} onsets")
    return onset_times


def get_beat_intervals(beat_times: List[float]) -> List[tuple]:
    """
    Convert beat timestamps to intervals.
    Returns list of (start, end) tuples.
    """
    intervals = []
    for i in range(len(beat_times) - 1):
        intervals.append((beat_times[i], beat_times[i + 1]))
    return intervals

"""
Tests for scene detection module.
Run with:  python -m pytest tests/ -v
"""

import os
import pytest


class TestSceneDetector:
    """Basic tests for scene detection (require a sample video)."""

    SAMPLE_VIDEO = os.path.join(os.path.dirname(__file__), "..", "test_data", "sample.mp4")

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "test_data", "sample.mp4")),
        reason="No sample video available"
    )
    def test_detect_scenes(self):
        from core.scene_detector import detect_scenes_in_video

        scenes = detect_scenes_in_video(self.SAMPLE_VIDEO, threshold=30.0)
        assert isinstance(scenes, list)
        assert len(scenes) >= 1

        for scene in scenes:
            assert "start_time" in scene
            assert "end_time" in scene
            assert "duration" in scene
            assert scene["end_time"] > scene["start_time"]
            assert scene["duration"] > 0

    def test_empty_path_raises(self):
        from core.scene_detector import detect_scenes_in_video

        with pytest.raises(Exception):
            detect_scenes_in_video("/nonexistent/video.mp4")


class TestFFmpegUtils:
    """Test FFmpeg utility functions."""

    def test_metadata_invalid_file(self):
        from utils.ffmpeg_utils import get_video_metadata

        result = get_video_metadata("/nonexistent/video.mp4")
        assert "error" in result or result.get("duration", 0) == 0


class TestBeatAnalyzer:
    """Test beat detection (requires a sample audio file)."""

    SAMPLE_AUDIO = os.path.join(os.path.dirname(__file__), "..", "test_data", "sample.mp3")

    @pytest.mark.skipif(
        not os.path.exists(os.path.join(os.path.dirname(__file__), "..", "test_data", "sample.mp3")),
        reason="No sample audio available"
    )
    def test_detect_beats(self):
        from core.beat_analyzer import detect_beats

        beats = detect_beats(self.SAMPLE_AUDIO)
        assert isinstance(beats, list)
        assert len(beats) > 0
        # Beats should be in ascending order
        for i in range(1, len(beats)):
            assert beats[i] > beats[i - 1]

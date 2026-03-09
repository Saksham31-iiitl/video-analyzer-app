# Auto Reel Generator — Backend

AI-powered short reel generator from raw video clips.

## Quick Start

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** installed and on your PATH
  - Windows: Download from https://ffmpeg.org/download.html and add to PATH
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Setup

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install CLIP (separate step — it's from GitHub)
pip install git+https://github.com/openai/CLIP.git

# Copy environment file
cp .env.example .env
```

### 3. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Test the API

```bash
# Upload videos
curl -X POST http://localhost:8000/api/upload \
  -F "videos=@clip1.mp4" \
  -F "videos=@clip2.mp4" \
  -F "music=@track.mp3"

# Analyse scenes (use project_id from upload response)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"project_id": "abc123"}'

# Generate reel (use scenes from analyse response)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc123",
    "selected_scenes": [...],
    "target_duration": 30,
    "style": "fast_cuts"
  }'
```

## Project Structure

```
backend/
├── main.py                 # FastAPI entry point
├── config.py               # Settings
├── api/routes/             # API endpoints
│   ├── upload.py           # POST /api/upload
│   ├── analyze.py          # POST /api/analyze
│   ├── generate.py         # POST /api/generate
│   └── status.py           # GET  /api/status/{job_id}
├── core/                   # Processing pipeline
│   ├── scene_detector.py   # PySceneDetect
│   ├── highlight_scorer.py # Multi-signal scoring
│   ├── beat_analyzer.py    # librosa beats
│   ├── assembler.py        # Clip selection + trimming
│   ├── renderer.py         # FFmpeg final render
│   └── caption_generator.py# Whisper captions
├── ai/                     # AI models
│   ├── clip_scorer.py      # CLIP semantic scoring
│   ├── motion_analyzer.py  # Optical flow
│   ├── face_detector.py    # MediaPipe + DeepFace
│   └── quality_checker.py  # Sharpness + exposure
├── utils/                  # Helpers
│   ├── ffmpeg_utils.py     # FFmpeg wrappers
│   ├── video_utils.py      # Frame extraction
│   ├── cache.py            # Result caching
│   └── file_manager.py     # File operations
├── presets/                # Style configurations
│   ├── styles.json
│   └── transitions.json
└── tests/                  # Test suite
```

## GPU Support

The pipeline works on CPU but is much faster on GPU:

- **CLIP**: ~20x faster on GPU
- **Whisper**: ~6x faster on GPU
- **MediaPipe**: CPU-only (already fast)

If you have an NVIDIA GPU, install PyTorch with CUDA:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

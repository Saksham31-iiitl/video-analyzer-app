# Auto Reel Generator

AI-powered short reel generator from raw video clips — FastAPI backend + React frontend.

---

## Backend (FastAPI)

### Prerequisites
- **Python 3.10+**
- **FFmpeg** installed and on your PATH
  - Windows: Download from https://ffmpeg.org/download.html and add to PATH
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Setup

```bash
cd backend

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

### Run the Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Frontend (React + Vite)

### Prerequisites
- **Node.js 18+** — https://nodejs.org
- **Backend running** at http://localhost:8000

### Setup

```bash
cd frontend
npm install
npm run dev
```

The app opens at **http://localhost:5173**.

---

## Project Structure

```
├── frontend/                # React + Vite frontend
│   ├── index.html           # HTML entry point
│   ├── package.json         # Node.js dependencies
│   ├── vite.config.js       # Vite build config
│   ├── tailwind.config.js   # Tailwind CSS config
│   └── src/
│       ├── App.jsx          # Main React component
│       ├── api/             # API client
│       ├── pages/           # Page components
│       ├── components/      # Reusable components
│       └── hooks/           # Custom React hooks
│
├── backend/                 # FastAPI backend
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings
│   ├── requirements.txt     # Python dependencies
│   ├── api/routes/          # API endpoints
│   ├── core/                # Processing pipeline
│   ├── ai/                  # AI models
│   ├── utils/               # Helpers
│   ├── presets/             # Style configurations
│   └── tests/               # Test suite
```

## GPU Support

If you have an NVIDIA GPU, install PyTorch with CUDA:
```bash
cd backend
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

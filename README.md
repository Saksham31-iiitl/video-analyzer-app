# Auto Reel Generator — Frontend

React + Vite + Tailwind CSS interface for the Auto Reel Generator.

## Quick Start

### Prerequisites
- **Node.js 18+** — https://nodejs.org
- **Backend running** at http://localhost:8000

### Setup

```bash
# Install dependencies
npm install

# Start dev server
npm run dev
```

The app opens at **http://localhost:5173**.

Vite's proxy config forwards `/api` requests to the backend at `:8000` automatically.

### Build for Production

```bash
npm run build
npm run preview   # preview the production build
```

## Pages

1. **Upload** — Drag & drop video clips + optional music
2. **Analyze** — Auto scene detection + AI highlight scoring
3. **Configure** — Pick scenes, editing style, duration, transitions
4. **Export** — Real-time progress → download final reel

## Tech Stack

- React 18 + Vite
- Tailwind CSS
- Framer Motion (animations)
- React Dropzone (file upload)
- Axios (API calls)
- Lucide React (icons)

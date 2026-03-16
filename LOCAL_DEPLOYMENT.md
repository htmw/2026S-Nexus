# MindMirror Local Deployment Manual

This guide helps any teammate run the full project locally (frontend + backend + model via Git LFS).

## 1) Prerequisites

- macOS/Linux/Windows
- Git
- Git LFS
- Python 3.10+ and `pip`
- Node.js 18+ and `npm`
- MongoDB running locally on port `27017`

## 2) Clone the repository and pull LFS model files

```bash
git lfs install
git clone https://github.com/htmw/2026S-Nexus.git
cd 2026S-Nexus
git checkout feature/model
git lfs pull
```

Verify model file exists:

```bash
ls -lh backend/models/mood_regression_model/model.safetensors
```

## 3) Backend setup (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Start backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check in another terminal:

```bash
curl http://localhost:8000/
```

Expected response includes:

```json
{"message":"MindMirror API is running"}
```

## 4) Frontend setup (Vite + React)

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend should run at:

- `http://localhost:5173`

The frontend already points to backend API:

- `frontend/src/services/api.js` → `http://localhost:8000/api`

## 5) Run both services together

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

## 6) Common issues and fixes

### A) Model not loading / fallback feedback

Check that these files exist in `backend/models/mood_regression_model/`:

- `config.json`
- `tokenizer.json`
- `tokenizer_config.json`
- `model.safetensors`

If missing, run from repo root:

```bash
git lfs pull
```

### B) `working copy must not be dirty` during LFS migration

Your repo has uncommitted changes. Save work first:

```bash
git add -A
git commit -m "save local changes"
# or
git stash push -u -m "temp"
```

### C) MongoDB connection fails

Make sure MongoDB is running and `.env` has:

```dotenv
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=mindmirror
MOOD_MODEL_DIR=models/mood_regression_model
```

### D) Port already in use

- Change backend port: `--port 8001`
- If backend port changes, also update `frontend/src/services/api.js`

## 7) Optional production-style checks

Frontend production build:

```bash
cd frontend
npm run build
npm run preview
```

Backend without auto-reload:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 8) Quick onboarding checklist for teammates

1. Install Git LFS once: `git lfs install`
2. Clone repo and run `git lfs pull`
3. Start MongoDB
4. Start backend on `8000`
5. Start frontend on `5173`

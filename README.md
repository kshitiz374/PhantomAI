# PHANTOM — The Ghost in Your Machine

**PHANTOM** is an offline-first, privacy-first interactive investigation app. You import fictional digital artifacts (logs, notes, emails), build an evidence graph and timeline, and converse with a local AI persona — or explore everything in **Demonstration Mode** without downloading a model.

> All horror scenarios are **fictional entertainment**. The app does not detect real ghosts, deceased persons, or supernatural entities.

## Features

- **Haunted Terminal** — command parser (`scan`, `memories`, `inspect`, `question`, …)
- **Digital Archaeology** — explicit file import (TXT, MD, JSON, CSV, LOG)
- **Memory Engine** — mock or Ollama-backed analysis with evidence vs inference labeling
- **Investigation Board** — React Flow evidence graph
- **Timeline** — dated and unknown-date events
- **Final Reconstruction** — export Markdown / JSON

## Quick start

### Prerequisites

- Python 3.11–3.12 (recommended; 3.14 may lack prebuilt wheels for some deps)
- Node.js 20+
- (Optional) [Ollama](https://ollama.com) for local models

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 — choose **Sample: THE LAST PROCESS** (no model required).

### Environment (optional)

```bash
# backend/.env
PHANTOM_MODEL_PROVIDER=mock
PHANTOM_OLLAMA_BASE_URL=http://127.0.0.1:11434
PHANTOM_DEFAULT_CHAT_MODEL=qwen2.5:3b
```

Frontend API URL:

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Local models (Ollama)

1. Install Ollama (requires internet for install and `ollama pull`).
2. Pull a small instruct model, e.g. `ollama pull qwen2.5:3b` or `ollama pull gemma2:2b`.
3. In **Settings**, switch provider to **Ollama**.

Verify license terms for each model (Qwen, Gemma, etc.) separately from this MIT-licensed application code.

| Model (example) | Approx. download | RAM hint |
|-----------------|------------------|----------|
| qwen2.5:3b      | ~2 GB            | 8 GB+    |
| gemma2:2b       | ~1.5 GB          | 8 GB+    |
| nomic-embed-text| ~300 MB          | optional embeddings |

## Tests

```bash
cd backend && pytest
cd frontend && npm test
```

Integration with a real Ollama instance is optional; default tests use the mock provider.

## Project layout

```
backend/          FastAPI + SQLite + providers (mock, ollama)
frontend/         Next.js UI
sample_data/      Reference copies of fictional sample artifacts
```

## Privacy

- Artifacts are only read when **you** select files.
- No telemetry or silent cloud upload in this codebase.
- SQLite database: `backend/data/phantom.db` (gitignored).
- OS backups and other tools may still copy files outside PHANTOM's control.

See [SECURITY.md](SECURITY.md) for threat model notes.

## Troubleshooting

| Issue | Action |
|-------|--------|
| CORS errors | Ensure backend on :8000 and `NEXT_PUBLIC_API_URL` matches |
| Ollama unavailable | App falls back to mock; check `ollama serve` |
| Empty graph | Run `scan` in terminal after import |
| Large file rejected | Default limit 2 MB — adjust `PHANTOM_MAX_ARTIFACT_BYTES` |

## License

Application source: [MIT](LICENSE). Third-party models and dependencies carry their own licenses.

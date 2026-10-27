# Contributing to PHANTOM

1. Fork and branch from `main`.
2. Backend: `cd backend && pip install -r requirements.txt && pytest`
3. Frontend: `cd frontend && npm install && npm run lint && npm test`
4. Keep fictional sample content clearly labeled.
5. Do not commit `backend/data/`, `.env`, or user artifacts.

PRs should describe privacy implications when touching ingestion or AI providers.

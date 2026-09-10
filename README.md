# EmployIQ — Phase 1 Foundation

EmployIQ is a hackathon-ready student employability platform. It includes institution-scoped JWT access, profile and assessment capture, a trained placement-readiness prediction API, deterministic career gaps and roadmaps, a grounded career copilot, and TPO dashboard endpoints.

## Prerequisites

- Python 3.12+ (3.14 is supported by the declared Django range)
- Node.js 20+
- PostgreSQL 16+ for local database use, or Docker Desktop for the complete stack

## Environment

Copy the root example to `.env` and replace development-safe values as needed:

```powershell
Copy-Item .env.example .env
Copy-Item frontend/.env.example frontend/.env
```

The backend reads the root `.env`; the frontend reads `frontend/.env`. The frontend uses `VITE_API_BASE_URL`, which defaults to `http://localhost:8000/api`.

## Run locally

Start PostgreSQL first, using the values in `.env`, then run each application independently.

```powershell
# Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
python manage.py seed_careers
python manage.py seed_knowledge
# Train or refresh the local ML artifact (uses the deterministic demo dataset by default):
..\.venv\Scripts\python -m ml.training.train
# Optional: train from a compatible campus-placement archive instead:
# ..\.venv\Scripts\python -m ml.training.train --source-zip "C:\path\to\placement-dataset.zip"
python manage.py runserver
```

```powershell
# Frontend (a second terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The shell requests `GET http://localhost:8000/api/health/` and displays the connection state.

## Run with Docker

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Services are available on PostgreSQL `5432`, API `8000`, and frontend `5173`. The backend waits for PostgreSQL health, migrates, and seeds the curated career/knowledge data. Train the local ML artifact before using `POST /api/v1/predictions/`.

## Demo APIs

- Student: `/api/v1/students/me/profile/`, `/api/v1/assessments/`, `/api/v1/predictions/`, `/api/v1/careers/roles/`, `/api/v1/roadmaps/`, `/api/v1/copilot/ask/`.
- TPO/Admin: `/api/v1/analytics/overview/` and `/api/v1/analytics/interventions/`.
- Copilot responses are grounded in ten seeded curated documents and include citations. A Gemini provider can be added later without changing this API contract.

## Structure

- `backend/config/settings/`: separated base, development, and production Django settings.
- `backend/apps/`: phase-ready Django app boundaries (`accounts`, `students`, `assessments`, `predictions`, `careers`, `rag`, `roadmaps`, `analytics`).
- `frontend/src/app/`: React Router and TanStack Query providers.
- `frontend/src/lib/api.ts`: configured Axios client and health endpoint.
- `frontend/src/components/ui/`: shadcn-compatible reusable UI components.
- `infrastructure/docker/`: lean application images used by `docker-compose.yml`.

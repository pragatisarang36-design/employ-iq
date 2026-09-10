# EmployIQ Project Structure

This is the target structure for a clean implementation. Existing folders are not an instruction to migrate code during the architecture phase.

```text
employiq/
├─ frontend/
│  ├─ src/
│  │  ├─ app/                 # router, providers, query client
│  │  ├─ features/            # accounts, profile, assessment, readiness, copilot, tpo
│  │  ├─ components/          # shadcn/ui-derived shared components
│  │  ├─ lib/                 # axios client, formatting, schemas
│  │  ├─ hooks/
│  │  └─ types/               # API DTOs only; avoid duplicating domain logic
│  ├─ public/
│  └─ tests/
├─ backend/
│  ├─ config/                 # Django settings, urls, ASGI/WSGI, Celery config
│  ├─ apps/
│  │  ├─ accounts/
│  │  ├─ students/
│  │  ├─ assessments/
│  │  ├─ predictions/
│  │  ├─ careers/
│  │  ├─ rag/
│  │  ├─ roadmaps/
│  │  └─ analytics/
│  ├─ ml/
│  │  ├─ training/            # notebooks/scripts excluded from web runtime
│  │  ├─ artifacts/           # ignored locally; fetched/versioned at deploy
│  │  ├─ feature_schema.py
│  │  └─ inference.py
│  ├─ knowledge_base/         # 10–15 reviewed source documents + manifest
│  ├─ manage.py
│  └─ requirements/
├─ infrastructure/
│  ├─ docker/
│  ├─ docker-compose.yml
│  └─ env.example
├─ docs/
│  └─ adr/                    # short architecture decision records
├─ SYSTEM_ARCHITECTURE.md
├─ PROJECT_STRUCTURE.md
├─ API_SPECIFICATION.md
├─ DATABASE_SCHEMA.md
├─ ML_ARCHITECTURE.md
├─ RAG_ARCHITECTURE.md
└─ DEVELOPMENT_PLAN.md
```

## Backend conventions

Each Django app contains `models.py`, `serializers.py`, `services.py`, `selectors.py`, `permissions.py`, `urls.py`, `views.py`, `tasks.py` when needed, `tests/`, and `migrations/`. Views remain thin; writes go through services, read composition through selectors, and cross-app imports use public service interfaces rather than model internals.

`predictions` may depend on normalized feature data from `students` and `assessments`. `rag` may read a minimal student-context DTO, but neither `rag` nor `roadmaps` writes prediction results. `analytics` reads approved reporting views/selectors and never bypasses institution filtering.

## Frontend conventions

Organize by feature rather than page type. A feature owns its routes, query hooks, view components, and form schemas. TanStack Query is the server-state authority; local state is only for UI state. Axios has one configured client with token refresh and normalized error handling. Recharts charts consume API aggregates, never raw full-cohort data fetched to the browser.

## Configuration and artifacts

`.env` files are local-only. Maintain `.env.example` with names and no values. Production model artifacts and documents carry IDs/checksums in a manifest; they are not committed as opaque ad-hoc binaries. Docker images use pinned dependency locks and non-root processes.

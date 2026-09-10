# EmployIQ System Architecture

## Scope and principles

EmployIQ is an institutional employability intelligence platform. Its operating loop is **predict → explain → identify gaps → guide → improve**. It is not a job board, ATS, application portal, recruitment platform, or scraping service.

The core rule is intentional separation: the trained ML model owns placement-readiness probability; the RAG service owns grounded guidance. An LLM never invents or overrides the probability.

## Logical architecture

```text
React SPA (Vite, TypeScript)
  ├─ Student workspace: profile, assessment, readiness, gaps, roadmap, copilot
  └─ TPO workspace: cohort metrics, intervention queue, aggregate trends
             │ HTTPS / JWT
             ▼
Django REST API
  ├─ accounts       authentication, roles and permissions
  ├─ students       student profile and evidence
  ├─ assessments    skill/aptitude observations
  ├─ predictions    model inference and SHAP explanations
  ├─ careers        role definitions and gap calculation
  ├─ rag            ingestion, retrieval and copilot orchestration
  ├─ roadmaps       personalized, reviewable learning plans
  └─ analytics      institution-scoped aggregates
             │
     PostgreSQL + pgvector       ML artifact store       Gemini APIs
     transactional data/vectors  joblib model/version    embeddings + LLM
```

## Runtime boundaries

| Boundary | Responsibility | Must not do |
|---|---|---|
| Frontend | Render workflows, collect validated input, display results/citations | Calculate readiness or expose provider secrets |
| Django API | Authorization, persistence, orchestration, audit trails, stable API | Embed business logic in views or trust client role claims |
| ML service/module | Feature validation, deterministic inference, model metrics, SHAP | Call an LLM to estimate probability |
| RAG service/module | Retrieve curated context, construct grounded prompts, cite sources | Make core readiness decisions |
| PostgreSQL/pgvector | Source of truth, role-scoped data, document vectors | Store raw credentials or unbounded chat telemetry |
| Gemini | Embeddings and grounded response generation | Receive data beyond the minimum needed context |

For the hackathon, ML inference runs in-process through a versioned Python service module inside Django. Promote it to a separate container only when prediction traffic, model memory, or independent release cadence justifies it.

## Primary flows

1. A student updates profile or completes an assessment. Django validates and persists a normalized feature snapshot.
2. The prediction service loads the approved, versioned artifact; it returns a probability, readiness band, feature schema version, and SHAP contributions where supported.
3. Careers compares the snapshot against selected-role benchmarks and returns prioritized gaps.
4. Roadmaps combines deterministic gaps with curated learning content. The LLM may phrase or sequence guidance but the underlying gap facts remain explicit.
5. For a copilot question, RAG filters documents by role/topic, retrieves vector matches, adds approved student context, calls Gemini, and returns response plus citations.
6. TPO analytics queries institution-scoped, privacy-aware aggregates and an intervention queue for scores below 60%.

## Security and privacy

- JWT access/refresh tokens with rotation/blacklisting; short-lived access tokens and HTTPS only.
- RBAC: `student`, `tpo`, and `admin`; every student object is institution-scoped and ownership-checked.
- Treat assessment and prediction data as sensitive educational data: minimize fields, encrypt backups, redact logs, and retain only needed chat history.
- Store secrets only in environment/configuration management; never return Gemini keys, model paths, internal prompts, or raw SHAP background data.
- Rate-limit authentication and copilot endpoints; validate request sizes and use server-side timeouts/retries for external calls.
- Audit TPO exports, prediction access, model version changes, and knowledge-base publication.

## Scalability and maintainability

- Begin with a modular monolith and a single PostgreSQL instance. This reduces deployment risk while preserving clean app boundaries.
- Add indexes for institution, student, timestamps, and vector retrieval; paginate all cohort views.
- Cache immutable career definitions and model metadata; do not cache personalized responses without a privacy review.
- Use background jobs for document embedding, bulk prediction refresh, and heavy analytics—never inside a request lifecycle.
- Version APIs (`/api/v1`), models, feature schemas, prompts, and knowledge documents. Write contract and role-permission tests at boundaries.

## Hackathon decisions

- Fully support Full-Stack Developer and Data Analyst first; define Cloud/DevOps and QA role content but defer deep role workflows.
- Keep the curated knowledge base to 10–15 reviewed documents and use one embedding model.
- Deploy frontend, Django API, PostgreSQL/pgvector, and a worker as Docker services. Use managed Gemini credentials configured per environment.

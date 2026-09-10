# EmployIQ API Specification

Base URL: `/api/v1`. JSON request/response bodies use `snake_case`; TypeScript maps them consistently. All authenticated endpoints require `Authorization: Bearer <access_token>`. Errors follow `{ "code", "message", "details"? }`.

## Identity

| Method / path | Access | Purpose |
|---|---|---|
| `POST /auth/token/` | Public | Obtain access and refresh JWTs |
| `POST /auth/token/refresh/` | Public | Rotate access token |
| `POST /auth/logout/` | Authenticated | Blacklist refresh token |
| `GET /me/` | Authenticated | Current user and institution role |

## Student and assessment

| Method / path | Access | Purpose |
|---|---|---|
| `GET, PATCH /students/me/profile/` | Student | Retrieve/update own academic, technical, experience, aptitude, communication, extracurricular profile |
| `GET /students/me/feature-snapshot/` | Student | Validated model-ready features with schema version (no internal transforms) |
| `POST /assessments/` | Student | Save a submitted assessment observation |
| `GET /assessments/` | Student | Paginated own assessment history |
| `GET /students/{student_id}/profile/` | TPO/Admin, scoped | View an authorized student profile |

`PATCH /students/me/profile/` accepts only declared profile fields. Lists such as languages/certifications are arrays of normalized labels or object IDs; numeric fields have server-side ranges. The API rejects unknown model-affecting fields until a feature schema is approved.

## Predictions and careers

| Method / path | Access | Purpose |
|---|---|---|
| `POST /predictions/` | Student | Generate prediction from latest valid snapshot |
| `GET /predictions/latest/` | Student | Latest result and explanation summary |
| `GET /predictions/{id}/` | Owner or scoped TPO | Immutable result details |
| `GET /careers/roles/` | Authenticated | Available roles and support level |
| `GET /careers/roles/{slug}/gap-analysis/` | Student | Own role-specific benchmark comparison |

`POST /predictions/` response: `{id, probability_percent, readiness, intervention_required, model_version, feature_schema_version, generated_at, explanation}`. `readiness` is `ready`, `near_ready`, or `needs_training`; mapping thresholds are configuration/version metadata, not embedded magic values. `intervention_required` is true below 60%. `explanation` contains ranked positive/negative feature contributions and a plain-language disclaimer.

## Roadmaps and copilot

| Method / path | Access | Purpose |
|---|---|---|
| `POST /roadmaps/` | Student | Create/recompute a roadmap for selected role using current gaps |
| `GET /roadmaps/current/` | Student | Current roadmap and milestones |
| `PATCH /roadmaps/{id}/items/{item_id}/` | Student | Update completion status only |
| `POST /copilot/ask/` | Student | Ask grounded career question |
| `GET /copilot/conversations/` | Student | Paginated own conversation metadata/history |

`POST /copilot/ask/` body is `{question, role_slug?, conversation_id?}`. Response is `{answer, citations: [{document_id, title, section?, relevance}], conversation_id, safety_note?}`. If retrieval finds no qualifying source, return a constrained response that says the curated knowledge base lacks coverage, rather than presenting unsupported advice.

## TPO analytics

| Method / path | Access | Purpose |
|---|---|---|
| `GET /analytics/overview/` | TPO/Admin | Institution aggregate readiness and trends |
| `GET /analytics/interventions/` | TPO/Admin | Paginated students below 60%, filterable by cohort/role |
| `GET /analytics/skills/` | TPO/Admin | Aggregate role/skill gaps; minimum cohort threshold applied |
| `GET /analytics/students/{id}/readiness/` | TPO/Admin, scoped | Authorized student’s summary |

Never provide a cross-institution identifier filter. Exports, if introduced, are asynchronous, permission-audited, and short-lived downloads.

## Operational behavior

All lists paginate (`page`, `page_size`) and cap `page_size`. Use `201` for created snapshots/roadmaps, `202` for queued long-running work, `400` validation errors, `401/403` authentication/authorization failures, `404` scoped missing objects, `409` stale-version conflicts, and `429` rate limits. Document the OpenAPI schema from DRF and contract-test it in CI.

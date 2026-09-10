# EmployIQ Development Plan

## Milestones

| Milestone | Outcome | Exit criteria |
|---|---|---|
| 0. Architecture approval | Scope, data contract, role/RBAC decisions locked | These seven documents reviewed; no feature code implied |
| 1. Foundations | Docker, Django project/apps, React shell, PostgreSQL/pgvector, JWT/RBAC | Local stack starts; student/TPO isolation tests pass |
| 2. Profile and assessment | Validated student inputs and feature snapshot | All specified fields persisted; contract tests and audit events work |
| 3. ML intelligence | Reproducible comparison, selected model, prediction and SHAP API | Three model metrics recorded; approved artifact predicts from golden input |
| 4. Careers and roadmap | Two complete role tracks, deterministic gaps, milestone roadmap | Full-Stack and Data Analyst flows usable end-to-end |
| 5. RAG copilot | Curated corpus, ingestion, citations, Gemini response | 10–15 documents, cited answers, retrieval evaluation set passes |
| 6. TPO analytics and hardening | Scoped dashboards, intervention queue, demo readiness | Below-60% queue, pagination, security checks, seeded demo |

## Suggested hackathon sequencing

Days 1–2: approve data fields/label source, set up foundation, write OpenAPI contracts, curate the first role documents, and prepare a representative ML dataset. Days 3–4: finish profile/assessment storage and ML comparison; freeze the active model and explanations. Days 5–6: implement careers/roadmaps and RAG retrieval before UI polish. Day 7: TPO analytics, security verification, accessibility, demo script, and contingency fixes.

Build vertical slices, not isolated screens: profile → prediction → explanation → chosen-role gaps → roadmap → cited copilot answer. Add TPO reporting after the student signal pipeline is reliable.

## Work streams and ownership

| Stream | Deliverables | Dependencies |
|---|---|---|
| Product/data | feature dictionary, consent copy, role benchmarks, labels | None |
| Backend | apps, APIs, RBAC, migrations, services | product contracts |
| ML | dataset checks, comparison report, artifact, SHAP | feature dictionary/labels |
| RAG/content | corpus, manifest, ingestion, eval questions | role benchmarks/Gemini config |
| Frontend | student/TPO workflows, charts, error states | API contracts |
| QA/DevOps | Docker, fixtures, tests, CI, demo environment | all streams |

## Quality gates

- Security: authenticated routes, object-level institution checks, token lifecycle, CORS allowlist, secret scan, rate-limit tests.
- ML: no leakage, reproducible run, metrics for all three candidates, feature parity, selected-model approval, explanation sanity checks.
- RAG: only published docs retrieved, every factual answer cites retrieved material, safe no-context fallback, evaluation questions reviewed.
- API/UI: OpenAPI contract tests, empty/loading/error states, keyboard-accessible core workflows, mobile-safe layouts, no raw cohort data in client charts.
- Data: migrations reversible in development, backup/restore rehearsal, seed data explicitly synthetic, retention policy documented.

## Risks and controls

| Risk | Control |
|---|---|
| Weak or biased placement labels | State limitations, perform leakage/subgroup checks, position as decision support |
| LLM hallucination | Retrieval threshold, curated corpus, citation validation, no-context response |
| Scope creep | Lock two fully supported tracks and a small corpus; defer live integrations and scraping |
| Sensitive student data exposure | Tenant RBAC, minimal provider context, redacted logs, audit trail |
| Model/RAG conflation | Separate APIs, modules, tests, and UI labels; only ML returns probability |

## Deferred beyond MVP

Automated retraining, complex multi-agent coaching, third-party course/job integrations, recruitment workflows, web scraping, advanced notification systems, and exhaustive role coverage are intentionally deferred. After this plan is approved, implementation can begin with Milestone 1.

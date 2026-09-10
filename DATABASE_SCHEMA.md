# EmployIQ Database Schema

PostgreSQL is the transactional source of truth. Enable `vector` extension for retrieval. All timestamps are UTC; UUID primary keys are recommended.

## Identity and tenancy

| Table | Key columns | Notes |
|---|---|---|
| `institutions` | `id`, `name`, `slug`, `is_active` | Tenant boundary |
| `users` | `id`, `institution_id`, `email`, `role`, `is_active` | Django custom user; unique `(institution_id, email)` |
| `student_profiles` | `user_id`, `cohort`, `department`, academic fields | One-to-one with student user |

`role` is constrained to `student`, `tpo`, `admin`. Every tenant-owned table carries `institution_id` directly where query isolation/performance benefits, or derives it through a strictly enforced parent relation. Application permissions are mandatory; PostgreSQL row-level security is a recommended production defense-in-depth layer.

## Profile and assessment facts

| Table | Key columns | Notes |
|---|---|---|
| `student_skills` | `id`, `student_id`, `skill_id`, `proficiency`, `source` | Languages, frameworks, and related skills |
| `skills` | `id`, `name`, `category`, `canonical_key` | Canonical controlled vocabulary |
| `student_certifications` | `id`, `student_id`, `name`, `issuer`, `earned_at` | User-provided evidence |
| `student_experiences` | `id`, `student_id`, `kind`, `complexity`, `duration_months`, `metadata` | Project/internship/open-source facts |
| `assessments` | `id`, `student_id`, `type`, `submitted_at`, `status` | Assessment header |
| `assessment_scores` | `id`, `assessment_id`, `dimension`, `score`, `max_score` | Quantitative, logical, coding, communication, interview, presentation |

Academic values (`cgpa`, tenth/twelfth percentage, backlogs) sit on `student_profiles`; validation rules belong to Django model/serializer constraints. Use JSON only for sparse experience metadata—not for fields used in filtering, features, or analytics.

## Prediction and career records

| Table | Key columns | Notes |
|---|---|---|
| `model_versions` | `id`, `version`, `algorithm`, `feature_schema_version`, `metrics`, `artifact_uri`, `is_active` | Approved reproducible model registry |
| `prediction_runs` | `id`, `student_id`, `model_version_id`, `probability`, `readiness`, `input_snapshot`, `created_at` | Immutable historical result |
| `prediction_explanations` | `id`, `prediction_run_id`, `feature_key`, `shap_value`, `direction`, `rank` | Individual contributions; indexed by run/rank |
| `career_roles` | `id`, `slug`, `name`, `support_level`, `description` | Initial four roles |
| `role_skill_benchmarks` | `id`, `role_id`, `skill_id`, `target_level`, `priority`, `rationale` | Deterministic skill-gap source |
| `student_role_selections` | `id`, `student_id`, `role_id`, `is_primary` | Student intent |
| `skill_gap_snapshots` | `id`, `student_id`, `role_id`, `prediction_run_id?`, `gaps`, `created_at` | Versioned analysis output |

Store probability as decimal `[0,1]` and format as percent at API boundary. The 60% intervention threshold is a versioned application setting/metric, not a stored duplicate except as a derived flag on an immutable run.

## RAG and roadmap records

| Table | Key columns | Notes |
|---|---|---|
| `knowledge_documents` | `id`, `title`, `role_id?`, `topic`, `content`, `source_type`, `status`, `version`, `checksum` | Curated source and publication state |
| `knowledge_chunks` | `id`, `document_id`, `chunk_index`, `content`, `embedding vector`, `metadata` | Unique `(document_id, chunk_index)`; HNSW/IVFFlat vector index |
| `copilot_conversations` | `id`, `student_id`, `role_id?`, `created_at` | User-owned session |
| `copilot_messages` | `id`, `conversation_id`, `role`, `content`, `citation_ids`, `created_at` | Apply retention policy and redact sensitive logs |
| `roadmaps` | `id`, `student_id`, `role_id`, `based_on_gap_snapshot_id`, `status`, `generated_at` | One current roadmap per student-role |
| `roadmap_items` | `id`, `roadmap_id`, `sequence`, `title`, `skill_id?`, `resource_document_id?`, `status`, `target_date` | Human-reviewable milestones |
| `audit_events` | `id`, `actor_id?`, `institution_id`, `action`, `object_type`, `object_id`, `metadata`, `created_at` | No secrets or raw sensitive payloads |

Indexes: tenant/cohort/department for reporting; `prediction_runs(student_id, created_at desc)`; `assessment_scores(assessment_id, dimension)`; unique role/skill benchmarks; document publication filters; and a pgvector approximate-nearest-neighbor index only after enough chunks justify it.

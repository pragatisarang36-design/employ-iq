# EmployIQ RAG Architecture

## Purpose and boundary

RAG supplies grounded, career-specific help: skill explanations, learning and project suggestions, interview preparation, communication preparation, and roadmap narration. It never calculates or changes placement probability.

## Curated MVP corpus

Create 10–15 high-quality, reviewed Markdown documents with a manifest. Start with Full-Stack Developer and Data Analyst as fully supported tracks: role definition, skills/benchmarks, learning path, project ideas, interview topics, and communication guidance for each; add shared study/interview guidance and compact starter documents for Cloud/DevOps and QA.

Each document has a stable ID, title, role/topic tags, source/author, version, review date, publication status, and content checksum. Only published documents are eligible for retrieval. Keep copyright-safe, institution-approved content.

## Ingestion

1. Validate and normalize source Markdown.
2. Split by semantic headings with modest overlap; retain document ID, heading, role, topic, version, and chunk index metadata.
3. Generate Gemini embeddings in a background job and store vectors in `knowledge_chunks.embedding` using pgvector.
4. Verify chunk count/checksum and publish atomically. Re-embedding creates a new document version rather than silently replacing cited content.

## Query flow

```text
Question + selected role
  → authorize student and load minimal approved context
  → classify/filter topic and published role/shared chunks
  → pgvector similarity retrieval (top-k) + relevance threshold
  → assemble bounded grounded prompt
  → Gemini generation
  → validate citations against retrieved chunks
  → answer, citations, and audit metadata
```

Student context is purpose-limited: chosen role, declared skills, current deterministic gaps, roadmap status, and latest readiness band if genuinely helpful. Do not send unneeded academic details or full history to Gemini. The prompt says that model probability is authoritative only when supplied by the prediction service, requires citations for specific guidance, and instructs the model to acknowledge missing evidence.

## Response quality and safety

- Cite document titles/sections used; the API returns document IDs for durable UI links.
- Require a retrieval threshold. If no source qualifies, respond that the knowledge base has insufficient coverage and offer a scoped next question.
- Reject/flag prompt-injection content from retrieved documents; never let a document override system policy.
- Enforce output length, timeout, retries, and provider-error fallbacks. Store provider IDs/latency, not secrets.
- Moderate harmful or inappropriate requests under institutional policy; avoid definitive employment, medical, legal, or financial claims.

## Evaluation and evolution

Maintain a small evaluation set of student questions covering both tracks. Score retrieval relevance, citation correctness, grounding, and usefulness after each document/prompt/model change. Version the embedding model and prompt template. For hackathon scope, pgvector plus a lightweight service is preferable to extra vector infrastructure; LangChain is optional only if it reduces boilerplate without obscuring observability.

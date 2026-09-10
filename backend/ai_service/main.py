"""Small internal service; Django remains the public API and data owner."""
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ml.inference import ModelUnavailableError, predict

app = FastAPI(title="EmployIQ AI/ML Service", version="1.0")


class PredictionRequest(BaseModel):
    snapshot: dict[str, Any]


class ContextRequest(BaseModel):
    role_slug: str | None = None
    gaps: list[dict[str, Any]] = Field(default_factory=list)
    question: str | None = None
    sources: list[str] = Field(default_factory=list)


@app.get("/health")
def health():
    return {"status": "ok", "service": "employiq-ai"}


@app.post("/predict")
def prediction(payload: PredictionRequest):
    try:
        return predict(payload.snapshot)
    except (ModelUnavailableError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/predict/explain")
def explain(payload: PredictionRequest):
    result = prediction(payload)
    return {"model_version": result["model_version"], "explanation": result["explanation"]}


@app.post("/role-alignment")
def role_alignment(payload: ContextRequest):
    total = max(len(payload.gaps), 1)
    return {"role_slug": payload.role_slug, "alignment_score": max(0, round(100 - len(payload.gaps) / total * 50, 2)), "missing_skills": payload.gaps}


@app.post("/skill-gaps")
def skill_gaps(payload: ContextRequest):
    return {"role_slug": payload.role_slug, "gaps": payload.gaps}


@app.post("/roadmap")
def roadmap(payload: ContextRequest):
    return {"role_slug": payload.role_slug, "items": [{"sequence": index, "title": f"Build {gap.get('skill', 'core skill')}", "priority": gap.get("priority", "medium")} for index, gap in enumerate(payload.gaps[:6], 1)]}


@app.post("/copilot/ask")
def copilot(payload: ContextRequest):
    if not payload.sources:
        return {"answer": "The curated knowledge base does not have enough coverage for that question.", "sources": []}
    return {"answer": "\n\n".join(payload.sources[:3]), "sources": payload.sources[:3]}

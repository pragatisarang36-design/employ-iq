"""In-process, versioned placement-readiness inference."""

from pathlib import Path
from time import perf_counter

import joblib
import pandas as pd

from .feature_schema import FEATURE_LABELS, FEATURE_NAMES, FEATURE_SCHEMA_VERSION, vector_from_snapshot

ARTIFACT_PATH = Path(__file__).resolve().parent / "artifacts" / "placement_readiness_v1.joblib"


class ModelUnavailableError(RuntimeError):
    pass


def load_active_artifact():
    if not ARTIFACT_PATH.exists():
        raise ModelUnavailableError("No approved ML artifact is available. Run the model training command first.")
    artifact = joblib.load(ARTIFACT_PATH)
    if artifact.get("feature_schema_version") != FEATURE_SCHEMA_VERSION or tuple(artifact.get("feature_names", ())) != FEATURE_NAMES:
        raise ModelUnavailableError("The active ML artifact is incompatible with feature schema v1.0.")
    return artifact


def predict(snapshot: dict) -> dict:
    artifact = load_active_artifact()
    vector = vector_from_snapshot(snapshot)
    started = perf_counter()
    feature_frame = pd.DataFrame([vector], columns=FEATURE_NAMES)
    probability = float(artifact["pipeline"].predict_proba(feature_frame)[0][1])
    latency_ms = round((perf_counter() - started) * 1000, 2)

    readiness = "ready" if probability >= 0.75 else "near_ready" if probability >= 0.60 else "needs_training"
    explanation = _linear_attributions(artifact, vector)
    return {
        "probability": probability,
        "readiness": readiness,
        "intervention_required": probability < 0.60,
        "model_version": artifact["version"],
        "feature_schema_version": artifact["feature_schema_version"],
        "explanation": explanation,
        "latency_ms": latency_ms,
    }


def _linear_attributions(artifact: dict, vector: list[float]) -> list[dict]:
    """Exact mean-background linear SHAP-style attributions for the selected logistic model."""
    pipeline = artifact["pipeline"]
    scaler = pipeline.named_steps["scaler"]
    classifier = pipeline.named_steps["classifier"]
    contributions = classifier.coef_[0] * scaler.transform(pd.DataFrame([vector], columns=FEATURE_NAMES))[0]
    ranked = sorted(zip(FEATURE_NAMES, contributions), key=lambda item: abs(item[1]), reverse=True)[:5]
    return [
        {"feature_key": key, "label": FEATURE_LABELS[key], "shap_value": round(float(value), 4),
         "direction": "positive" if value >= 0 else "negative"}
        for key, value in ranked
    ]

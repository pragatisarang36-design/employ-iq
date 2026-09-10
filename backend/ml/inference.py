"""Versioned LightGBM inference and genuine SHAP explanations."""

from pathlib import Path
from time import perf_counter

import joblib
import pandas as pd
import shap

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
    if artifact.get("algorithm") != "lightgbm" or "primary_model" not in artifact:
        raise ModelUnavailableError("The active artifact is not the required LightGBM model. Run model training.")
    return artifact


def _shap_attributions(model, feature_frame):
    values = shap.TreeExplainer(model).shap_values(feature_frame)
    # SHAP versions return either (samples, features) or class-specific arrays.
    if isinstance(values, list):
        values = values[1]
    values = getattr(values, "values", values)
    if getattr(values, "ndim", 0) == 3:
        values = values[:, :, 1]
    row = values[0]
    ranked = sorted(zip(FEATURE_NAMES, row), key=lambda item: abs(float(item[1])), reverse=True)[:5]
    return [{"feature_key": key, "label": FEATURE_LABELS[key], "shap_value": round(float(value), 4), "direction": "positive" if float(value) >= 0 else "negative"} for key, value in ranked]


def predict(snapshot: dict) -> dict:
    artifact = load_active_artifact()
    vector = vector_from_snapshot(snapshot)
    started = perf_counter()
    feature_frame = pd.DataFrame([vector], columns=FEATURE_NAMES)
    probability = float(artifact["primary_model"].predict_proba(feature_frame)[0][1])
    baseline_probability = float(artifact["baseline_model"].predict_proba(feature_frame)[0][1])
    explanation = _shap_attributions(artifact["primary_model"], feature_frame)
    return {"probability": probability, "baseline_probability": baseline_probability,
            "readiness": "ready" if probability >= 0.75 else "near_ready" if probability >= 0.60 else "needs_training",
            "intervention_required": probability < 0.60, "model_version": artifact["version"],
            "feature_schema_version": artifact["feature_schema_version"], "explanation": explanation,
            "latency_ms": round((perf_counter() - started) * 1000, 2)}

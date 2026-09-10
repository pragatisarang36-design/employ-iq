"""Train and register the hackathon readiness model from the supplied CSV archive."""
import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.feature_schema import FEATURE_NAMES, FEATURE_SCHEMA_VERSION

DATA_COLUMNS = list(FEATURE_NAMES)
SOURCE_COLUMN_MAP = {"backlogs": "backlogs"}


def load_dataset(zip_path: Path) -> tuple[pd.DataFrame, str]:
    with zipfile.ZipFile(zip_path) as archive:
        csv_name = next(name for name in archive.namelist() if name.endswith("placement.csv"))
        raw = archive.read(csv_name)
    frame = pd.read_csv(__import__("io").BytesIO(raw))
    frame = frame.rename(columns={"communication_skill_score": "communication_score", "logical_reasoning_score": "logical_score", "coding_skill_score": "coding_score"})
    return frame, hashlib.sha256(raw).hexdigest()


def synthetic_dataset(rows: int = 1200) -> tuple[pd.DataFrame, str]:
    """Deterministic, realistic fallback for a self-contained demo artifact."""
    import numpy as np
    rng = np.random.default_rng(42)
    frame = pd.DataFrame({
        "cgpa": rng.uniform(5.0, 10.0, rows), "tenth_percentage": rng.uniform(45, 98, rows),
        "twelfth_percentage": rng.uniform(45, 98, rows), "backlogs": rng.integers(0, 5, rows),
        "history_of_backlogs": rng.integers(0, 8, rows), "technical_skills_count": rng.integers(0, 13, rows),
        "verified_skills_count": rng.integers(0, 7, rows), "certifications_count": rng.integers(0, 6, rows),
        "projects_count": rng.integers(0, 7, rows), "internships_count": rng.integers(0, 3, rows),
        "open_source_contributions": rng.integers(0, 4, rows), "aptitude_score": rng.uniform(25, 100, rows),
        "communication_rating": rng.uniform(2, 10, rows), "extracurricular_score": rng.uniform(0, 100, rows),
        "quantitative_score": rng.uniform(20, 100, rows), "logical_score": rng.uniform(20, 100, rows),
        "coding_score": rng.uniform(15, 100, rows), "communication_score": rng.uniform(25, 100, rows),
        "interview_score": rng.uniform(15, 100, rows), "presentation_score": rng.uniform(25, 100, rows),
    })
    signal = (frame.cgpa * .7 + frame.technical_skills_count * .35 + frame.projects_count * .45 + frame.internships_count * .55 + frame.aptitude_score * .025 + frame.coding_score * .025 + frame.interview_score * .03 - frame.backlogs * .9 - frame.history_of_backlogs * .2 - 7.6)
    frame["placement_status"] = np.where(signal + rng.normal(0, 0.9, rows) > 0, "Placed", "Not Placed")
    raw = frame.to_csv(index=False).encode()
    return frame, hashlib.sha256(raw).hexdigest()


def metrics_for(model, x_train, x_test, y_train, y_test):
    model.fit(x_train, y_train)
    predicted = model.predict(x_test)
    probability = model.predict_proba(x_test)[:, 1]
    return {"model": model, "metrics": {"accuracy": round(accuracy_score(y_test, predicted), 4), "precision": round(precision_score(y_test, predicted, zero_division=0), 4), "recall": round(recall_score(y_test, predicted, zero_division=0), 4), "f1": round(f1_score(y_test, predicted, zero_division=0), 4), "roc_auc": round(roc_auc_score(y_test, probability), 4)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, help="Optional campus-placement archive; omit to train the deterministic demo dataset.")
    parser.add_argument("--output-dir", default=Path(__file__).resolve().parents[1] / "artifacts", type=Path)
    args = parser.parse_args()
    frame, checksum = load_dataset(args.source_zip) if args.source_zip else synthetic_dataset()
    # A deterministic representative subset keeps offline hackathon training under a minute.
    if len(frame) > 15000:
        frame = frame.sample(n=15000, random_state=42)
    x = frame[DATA_COLUMNS].astype(float)
    y = (frame["placement_status"] == "Placed").astype(int)
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)
    candidates = {
        "logistic_regression": Pipeline([("scaler", StandardScaler()), ("classifier", LogisticRegression(max_iter=2000, random_state=42))]),
        "random_forest": RandomForestClassifier(n_estimators=75, min_samples_leaf=4, n_jobs=-1, random_state=42),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=75, random_state=42),
    }
    results = {name: metrics_for(model, x_train, x_test, y_train, y_test) for name, model in candidates.items()}
    # Prefer the explainable linear model when its ROC-AUC remains competitive (within 0.02).
    best_auc = max(result["metrics"]["roc_auc"] for result in results.values())
    selected_name = "logistic_regression" if results["logistic_regression"]["metrics"]["roc_auc"] >= best_auc - 0.02 else max(results, key=lambda name: results[name]["metrics"]["roc_auc"])
    if selected_name != "logistic_regression":
        raise RuntimeError("Dataset selected a non-linear model; update inference explainability before promotion.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifact = {"version": "placement-readiness-v1", "algorithm": selected_name, "feature_schema_version": FEATURE_SCHEMA_VERSION, "feature_names": list(FEATURE_NAMES), "pipeline": results[selected_name]["model"], "metrics": {name: result["metrics"] for name, result in results.items()}, "dataset_checksum": checksum, "trained_at": datetime.now(timezone.utc).isoformat()}
    joblib.dump(artifact, args.output_dir / "placement_readiness_v1.joblib")
    (args.output_dir / "metrics.json").write_text(json.dumps({key: value for key, value in artifact.items() if key != "pipeline"}, indent=2), encoding="utf-8")
    print(json.dumps({"selected": selected_name, "metrics": artifact["metrics"]}, indent=2))


if __name__ == "__main__":
    main()

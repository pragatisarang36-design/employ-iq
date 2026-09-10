# EmployIQ ML Architecture

## Purpose and boundary

The ML layer estimates placement readiness from validated student data. It produces an empirical probability, classification, and explanation. It does not generate career advice, choose learning resources, or answer chat questions.

## Input contract

A versioned feature schema derives features from profile and assessment facts: academic (CGPA, marks, backlogs), technical proficiency/certifications, experience (projects, complexity, internships, open source), aptitude (quantitative, logical, coding), communication/interview/presentation, and extracurricular signals. Transformations—category encodings, null handling, scaling, feature order—are fitted on training data and saved with the artifact.

Persist the validated raw/derived input snapshot for each prediction. Reject an incompatible snapshot rather than silently imputing unknown schema fields.

## Training and selection

1. Define an ethically reviewed target label and data dictionary; remove direct identifiers and assess proxy bias.
2. Split data by student, stratified where feasible, into train/validation/test; prevent temporal and duplicate leakage.
3. Train pipelines for Logistic Regression, Random Forest, and LightGBM with equivalent preprocessing and a reproducible seed.
4. Evaluate held-out performance: accuracy, precision, recall, F1-score, ROC-AUC, calibration, confusion matrix, and subgroup checks when sample sizes permit.
5. Select the best candidate by predeclared primary metric (ROC-AUC) with F1/recall and calibration as guardrails—not by algorithm preference. Record rationale.
6. Register artifact, dependency versions, dataset version/checksum, feature schema, metrics, and approval date. Only an approved model can be active.

LightGBM is the expected candidate, not the default winner. If data size/quality is weak, Logistic Regression may be more stable and interpretable.

## Inference output

The service loads the active `joblib` artifact, validates the exact feature order, emits probability in `[0,1]`, and maps it to `ready`, `near_ready`, or `needs_training` using documented, versioned thresholds based on validation results and institutional policy. The API formats it as 0–100%. Separately, `intervention_required = probability < 0.60`.

No arbitrary values are hardcoded in the frontend or LLM. The response includes model and schema versions, timestamp, and a statement that the score is decision support, not a guarantee of placement.

## Explainability

Generate SHAP values for the selected supported model: `LinearExplainer` for linear models and `TreeExplainer` for tree-based models. Keep a fixed, non-sensitive background dataset/summary with the model artifact. Return a small ranked set of feature labels, direction, and contribution—not raw vectors or training records. If SHAP is unsupported/unavailable, return a clearly labeled explanation-unavailable state; do not fabricate reasons.

## Operations and safeguards

- Batch retraining is offline and manually approved for the hackathon; online learning is out of scope.
- Log model ID, latency, schema validation failure, and aggregate confidence distribution; do not log full feature snapshots unnecessarily.
- Monitor input drift, missingness, calibration, and post-hoc outcome performance when legitimate outcomes become available.
- Keep prediction requests synchronous only within a defined latency budget; queue bulk cohort refreshes.
- Test feature parity between training and inference and make a golden-input regression test mandatory before model promotion.

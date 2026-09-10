from django.test import SimpleTestCase

from ml.inference import load_active_artifact, predict


GOLDEN_SNAPSHOT = {
    "feature_schema_version": "v1.0",
    "features": {
        "cgpa": 8.2, "internships_count": 1, "projects_count": 2,
        "certifications_count": 1, "coding_score": 80, "aptitude_score": 75,
        "communication_score": 70, "logical_score": 72, "backlogs": 0,
        "extracurricular_score": 60,
    },
}


class ApprovedModelContractTests(SimpleTestCase):
    def test_approved_artifact_has_all_required_candidate_metrics(self):
        artifact = load_active_artifact()
        self.assertEqual(artifact["algorithm"], "lightgbm")
        self.assertEqual(artifact["feature_schema_version"], "v1.0")
        self.assertEqual(set(artifact["metrics"]), {"lightgbm", "logistic_regression", "random_forest"})
        for metrics in artifact["metrics"].values():
            self.assertTrue({"accuracy", "precision", "recall", "f1", "roc_auc", "brier_score", "confusion_matrix", "calibration_curve"}.issubset(metrics))

    def test_golden_input_is_stable_for_approved_model(self):
        result = predict(GOLDEN_SNAPSHOT)
        self.assertEqual(result["model_version"], "placement-readiness-lightgbm-v3")
        self.assertEqual(result["readiness"], "ready")
        self.assertAlmostEqual(result["probability"], 0.9997759757, places=8)
        self.assertEqual(len(result["explanation"]), 5)

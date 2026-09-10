from fastapi.testclient import TestClient

from ai_service.main import app
client = TestClient(app)
GOLDEN_SNAPSHOT = {"feature_schema_version": "v1.0", "features": {"cgpa": 8.2, "internships_count": 1, "projects_count": 2, "certifications_count": 1, "coding_score": 80, "aptitude_score": 75, "communication_score": 70, "logical_score": 72, "backlogs": 0, "extracurricular_score": 60}}


def test_health_and_prediction_contract():
    assert client.get("/health").json() == {"status": "ok", "service": "employiq-ai"}
    result = client.post("/predict", json={"snapshot": GOLDEN_SNAPSHOT})
    assert result.status_code == 200
    assert result.json()["model_version"] == "placement-readiness-lightgbm-v3"
    explanation = client.post("/predict/explain", json={"snapshot": GOLDEN_SNAPSHOT})
    assert explanation.status_code == 200
    assert len(explanation.json()["explanation"]) == 5


def test_supporting_ai_endpoints_are_available():
    context = {"role_slug": "data-analyst", "gaps": [{"skill": "SQL", "priority": "high"}], "sources": ["Practise SQL joins."]}
    for endpoint in ("/role-alignment", "/skill-gaps", "/roadmap", "/copilot/ask"):
        assert client.post(endpoint, json=context).status_code == 200

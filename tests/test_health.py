from fastapi.testclient import TestClient

from nflviewer.app import app


def test_health_reports_formula_and_supported_season() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "dataLoaded": False,
        "supportedSeason": 2025,
        "formulaVersion": "dynamic-watchability-v5",
    }

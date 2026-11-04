from fastapi.testclient import TestClient

from app import main
from app.database import Database
from app.services import Simulation


def test_api_envelope_roles_and_reset(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "api.sqlite3"))
    simulation = Simulation(database)
    monkeypatch.setattr(main, "database", database)
    monkeypatch.setattr(main, "simulation", simulation)
    client = TestClient(main.app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["success"] is True
    assert health.json()["data"]["database"] == "ready"
    assert health.headers["x-correlation-id"] == health.json()["correlation_id"]

    forbidden = client.post("/api/v1/simulation/reset", headers={"X-Demo-Role": "patient"})
    assert forbidden.status_code == 403
    assert forbidden.json()["success"] is False

    reset = client.post("/api/v1/simulation/reset", headers={"X-Demo-Role": "presenter"})
    assert reset.status_code == 200
    assert reset.json()["data"]["counts"]["hospital"] == 12

    patient_headers = {"X-Demo-Role": "patient"}
    blocked_search = client.get("/api/v1/availability", headers=patient_headers)
    assert blocked_search.status_code == 422
    screen = client.post(
        "/api/v1/patient-access/screen?red_flag_present=false",
        headers=patient_headers,
    )
    assert screen.status_code == 200
    assert client.get("/api/v1/availability", headers=patient_headers).status_code == 200
    client.post(
        "/api/v1/patient-access/screen?red_flag_present=true",
        headers=patient_headers,
    )
    blocked_after_flag = client.get("/api/v1/availability", headers=patient_headers)
    assert blocked_after_flag.status_code == 422

    denied_operations = client.get("/api/v1/hospitals", headers=patient_headers)
    assert denied_operations.status_code == 403

    not_found = client.get("/api/v1/patients/UNKNOWN")
    assert not_found.status_code == 404
    assert not_found.json()["error"]["code"] == "patient_not_found"

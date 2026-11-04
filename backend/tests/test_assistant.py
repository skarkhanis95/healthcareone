import pytest
from fastapi.testclient import TestClient

from app import main
from app.assistant import UNSUPPORTED_REPLY, classify_keywords, is_red_flag
from app.database import Database
from app.services import Simulation

PATIENT = {"X-Demo-Role": "patient"}
URL = "/api/v1/patient-access/assistant/message"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "assistant.sqlite3"))
    monkeypatch.setattr(main, "database", database)
    monkeypatch.setattr(main, "simulation", Simulation(database))
    monkeypatch.setattr(main, "runtime_status", lambda: {"configured": False})
    return TestClient(main.app)


def send(client, text):
    response = client.post(URL, json={"message": text}, headers=PATIENT)
    assert response.status_code == 200, response.text
    return response.json()["data"]


@pytest.mark.parametrize("text,intent", [
    ("I need an orthopaedic doctor this week", "book_appointment"),
    ("my knee hurts, can I book an appointment", "book_appointment"),
    ("Can I see a doctor by video today?", "virtual_consult"),
    ("I want a virtual consult for my shoulder", "virtual_consult"),
    ("I need a cardiologist", "unsupported"),
    ("what is the weather", "unsupported"),
    ("hello", "unsupported"),
])
def test_keyword_intents(text, intent):
    assert classify_keywords(text)["intent"] == intent


def test_red_flags_detected():
    assert is_red_flag("I have chest pain and can't breathe")
    assert not is_red_flag("I need an orthopaedic doctor")


def test_book_returns_options_without_booking(client):
    data = send(client, "I need an orthopaedic doctor this week")
    assert data["intent"] == "book_appointment"
    assert data["mode"] == "deterministic_simulation"
    assert len(data["slots"]) == 2
    journey = client.get("/api/v1/patients/PAT-1001/journey", headers=PATIENT).json()["data"]
    assert journey["appointments"] == []


def test_virtual_filters_to_virtual_slots(client):
    data = send(client, "I'd like a video consult with a doctor")
    assert data["intent"] == "virtual_consult"
    assert [slot["mode"] for slot in data["slots"]] == ["virtual"]


def test_unsupported_gets_generic_reply(client):
    data = send(client, "Can you refill my prescription?")
    assert data["intent"] == "unsupported"
    assert data["reply"] == UNSUPPORTED_REPLY
    assert data["slots"] == []


def test_safety_guard_blocks_scheduling_and_booking(client):
    data = send(client, "I have severe chest pain, book me a doctor")
    assert data["safety_escalated"] is True
    assert data["intent"] == "safety_escalation"
    assert data["slots"] == []
    blocked = client.post("/api/v1/appointments", headers=PATIENT, json={
        "slot_id": "SLOT-TODAY-02", "patient_confirmed": True, "idempotency_key": "k1",
    })
    assert blocked.status_code == 422


def test_benign_message_reopens_gate_then_booking_needs_confirmation(client):
    send(client, "chest pain")
    data = send(client, "book an orthopaedic appointment")
    slot_id = data["slots"][0]["id"]
    unconfirmed = client.post("/api/v1/appointments", headers=PATIENT, json={
        "slot_id": slot_id, "patient_confirmed": False, "idempotency_key": "k2",
    })
    assert unconfirmed.status_code == 422
    booked = client.post("/api/v1/appointments", headers=PATIENT, json={
        "slot_id": slot_id, "patient_confirmed": True, "idempotency_key": "k2",
    })
    assert booked.status_code == 201


def test_role_and_validation(client):
    assert client.post(URL, json={"message": "hi"}, headers={"X-Demo-Role": "presenter"}).status_code == 403
    assert client.post(URL, json={"message": ""}, headers=PATIENT).status_code == 422
    assert client.post(URL, json={"message": "x" * 501}, headers=PATIENT).status_code == 422


def test_live_failure_falls_back(client, monkeypatch):
    monkeypatch.setattr(main, "runtime_status", lambda: {"configured": True})

    async def boom(text):
        raise RuntimeError("down")

    monkeypatch.setattr("app.assistant.classify_live", boom)
    data = send(client, "book an orthopaedic appointment")
    assert data["mode"] == "deterministic_simulation"
    assert "Live AI failed" in data["fallback_reason"]
    assert data["intent"] == "book_appointment"


def test_live_success_labelled_live(client, monkeypatch):
    monkeypatch.setattr(main, "runtime_status", lambda: {"configured": True})

    async def fake(text):
        return {"intent": "virtual_consult", "preferred_mode": "virtual", "classifier": "gemini"}

    monkeypatch.setattr("app.assistant.classify_live", fake)
    data = send(client, "something phrased oddly about seeing a doctor")
    assert data["mode"] == "live_gemini"
    assert data["intent"] == "virtual_consult"

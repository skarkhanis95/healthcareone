import asyncio

import pytest
from fastapi.testclient import TestClient

from app import main
from app.database import Database
from app.services import DomainError, Simulation

MEDS = [{"name": "Ibuprofen", "dose": "400 mg", "frequency": "Twice daily", "duration": "5 days", "instructions": "With food."}]


@pytest.fixture()
def sim(tmp_path):
    return Simulation(Database(str(tmp_path / "clinical.sqlite3")))


def test_patient_profile_and_seed_prescription(sim):
    patient = sim.get_patient("PAT-1001")
    assert patient["allergies"] == ["Penicillin"] and patient["past_visits"]
    assert [rx["id"] for rx in sim.prescriptions("PAT-1001")] == ["RX-1001"]


def test_issue_prescription_requires_clinician_confirmation_and_blocks_allergy(sim):
    with pytest.raises(DomainError) as forbidden:
        sim.issue_prescription("PAT-1001", "Pain", MEDS, "", True, "patient")
    assert forbidden.value.status_code == 403
    with pytest.raises(DomainError) as unconfirmed:
        sim.issue_prescription("PAT-1001", "Pain", MEDS, "", False, "clinician")
    assert unconfirmed.value.code == "confirmation_required"
    blocked = [{"name": "Amoxicillin", "dose": "500 mg", "frequency": "TDS", "duration": "7 days", "instructions": ""}]
    with pytest.raises(DomainError) as conflict:
        sim.issue_prescription("PAT-1001", "Infection", blocked, "", True, "clinician")
    assert conflict.value.code == "allergy_conflict"
    assert len(sim.prescriptions("PAT-1001")) == 1
    issued = sim.issue_prescription("PAT-1001", "Knee pain", MEDS, "Review in 2 weeks", True, "clinician")
    assert issued["id"] == "RX-1002" and issued["status"] == "active"
    assert sim.prescriptions("PAT-1001")[0]["id"] == "RX-1002" or len(sim.prescriptions("PAT-1001")) == 2


def test_prescription_pdf_is_valid(sim):
    pdf = sim.prescription_pdf("RX-1001")
    assert pdf.startswith(b"%PDF-1.4") and pdf.rstrip().endswith(b"%%EOF")
    assert b"Paracetamol" in pdf and b"Alex Morgan" in pdf


def test_ward_is_deterministic_and_charting_flow(sim):
    ward = sim.ward("HCO-CENTRAL")
    assert ward["summary"]["census"] == 10 and ward["summary"]["charted"] == 0
    assert sim.ward("HCO-CENTRAL")["patients"][0]["name"] == ward["patients"][0]["name"]
    patient = ward["patients"][0]
    pid = patient["id"]
    with pytest.raises(DomainError):
        sim.capture_vitals(pid, "patient")
    before = len(patient["vitals"])
    assert len(sim.capture_vitals(pid, "nurse")["vitals"]) == before + 1
    due = next(m for m in sim.ipd_patient(pid)["meds"] if m["status"] == "due" and not _blocked(sim.ipd_patient(pid), m))
    assert next(m for m in sim.administer_medication(pid, due["id"], "nurse")["meds"] if m["id"] == due["id"])["given"]
    draft = asyncio.run(__import__("app.clinical", fromlist=["x"]).draft_chart(sim.ipd_patient(pid), False))
    assert draft["mode"] == "deterministic_simulation" and patient["name"] in draft["narrative"]
    with pytest.raises(DomainError):
        sim.save_chart(pid, draft["narrative"], draft["mode"], False, "nurse")
    saved = sim.save_chart(pid, draft["narrative"], draft["mode"], True, "nurse")
    assert saved["charted_today"] and sim.ward("HCO-CENTRAL")["summary"]["charted"] == 1
    sim.reset()
    assert sim.ward("HCO-CENTRAL")["summary"]["charted"] == 0


def _blocked(patient, med):
    from app.clinical import allergy_conflicts
    return bool(allergy_conflicts(patient["allergies"], [med]))


def test_some_ward_patients_are_high_risk_somewhere(sim):
    levels = {p["risk"] for h in ("HCO-CENTRAL", "HCO-NORTH", "HCO-WEST") for p in sim.ward(h)["patients"]}
    assert "low" in levels and levels & {"medium", "high"}


def test_api_endpoints(tmp_path, monkeypatch):
    database = Database(str(tmp_path / "api2.sqlite3"))
    monkeypatch.setattr(main, "database", database)
    monkeypatch.setattr(main, "simulation", Simulation(database))
    client = TestClient(main.app)
    clin = {"X-Demo-Role": "clinician"}
    body = {"patient_id": "PAT-1001", "diagnosis": "Knee pain", "medications": MEDS, "notes": "", "clinician_confirmed": True}
    assert client.post("/api/v1/prescriptions", json=body, headers={"X-Demo-Role": "patient"}).status_code == 403
    created = client.post("/api/v1/prescriptions", json=body, headers=clin)
    assert created.status_code == 201
    listing = client.get("/api/v1/patients/PAT-1001/prescriptions", headers={"X-Demo-Role": "patient"}).json()["data"]
    assert len(listing) == 2
    pdf = client.get("/api/v1/prescriptions/%s/pdf" % created.json()["data"]["id"])
    assert pdf.headers["content-type"] == "application/pdf" and pdf.content.startswith(b"%PDF")
    nurse = {"X-Demo-Role": "nurse"}
    ward = client.get("/api/v1/hospitals/HCO-NORTH/ipd", headers=nurse).json()["data"]
    pid = ward["patients"][0]["id"]
    assert client.get("/api/v1/hospitals/HCO-NORTH/ipd", headers={"X-Demo-Role": "patient"}).status_code == 403
    draft = client.post("/api/v1/ipd/%s/chart/draft" % pid, headers=nurse)
    assert draft.status_code == 200 and draft.json()["data"]["narrative"]
    saved = client.post("/api/v1/ipd/%s/chart" % pid, headers=nurse,
                        json={"narrative": draft.json()["data"]["narrative"], "nurse_confirmed": True})
    assert saved.status_code == 201 and saved.json()["data"]["charted_today"] is True

"""Synthetic clinical content: patient record, inpatient wards, nursing charts and prescription PDFs.

Everything here is pure (no database access) so it is deterministic and easy to test.
"""
import asyncio
import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional

SIM_DATE = "2026-11-02"
SIM_HOUR = 9

# Drug names that must be blocked when the matching allergy is on record.
ALLERGY_CLASSES = {
    "penicillin": ("penicillin", "amoxicillin", "ampicillin", "flucloxacillin", "piperacillin", "co-amoxiclav"),
    "sulfa": ("sulfa", "sulfamethoxazole", "co-trimoxazole", "trimethoprim"),
    "nsaid": ("ibuprofen", "diclofenac", "naproxen", "aspirin", "ketorolac"),
    "latex": ("latex",),
}


def patient_profile() -> Dict[str, Any]:
    return {
        "id": "PAT-1001", "name": "Alex Morgan", "locality": "North District", "synthetic": True,
        "dob": "1984-03-14", "age": 42, "sex": "Male", "blood_group": "O positive",
        "phone": "+1 555 0142", "email": "alex.morgan@example.test",
        "address": "14 Orchard Lane, North District",
        "primary_doctor": "Dr. Meera Shah", "insurance": {"plan": "CareFlow Plus", "member_id": "CF-88-120934", "valid_through": "2027-06-30"},
        "emergency_contact": {"name": "Jamie Morgan", "relation": "Spouse", "phone": "+1 555 0177"},
        "allergies": ["Penicillin"],
        "conditions": ["Right knee osteoarthritis", "Mild hypertension"],
        "vitals": {"recorded_at": "2026-10-21", "bp": "128/82", "heart_rate": 72, "weight_kg": 81.5, "height_cm": 178, "bmi": 25.7, "spo2": 98},
        "labs": [
            {"test": "HbA1c", "value": "5.4 %", "range": "4.0 - 5.6", "status": "Normal", "date": "2026-10-21"},
            {"test": "LDL cholesterol", "value": "3.4 mmol/L", "range": "< 3.0", "status": "High", "date": "2026-10-21"},
            {"test": "Vitamin D", "value": "52 nmol/L", "range": "50 - 125", "status": "Normal", "date": "2026-10-21"},
            {"test": "CRP", "value": "6 mg/L", "range": "< 5", "status": "Borderline", "date": "2026-10-21"},
        ],
        "immunizations": [
            {"name": "Influenza", "date": "2025-10-04"}, {"name": "COVID-19 booster", "date": "2025-10-04"},
            {"name": "Tetanus (Td)", "date": "2022-05-17"},
        ],
        "past_visits": [
            {"date": "2026-10-21", "doctor": "Dr. Meera Shah", "reason": "Knee pain review", "summary": "Mild joint-space narrowing. Physiotherapy and analgesia advised."},
            {"date": "2026-07-09", "doctor": "Dr. Arjun Rao", "reason": "Annual check", "summary": "Blood pressure borderline. Lifestyle advice given."},
        ],
    }


def seed_prescriptions() -> List[Dict[str, Any]]:
    return [{
        "id": "RX-1001", "patient_id": "PAT-1001", "doctor_id": "DOC-0021", "doctor_name": "Dr. Meera Shah",
        "specialty": "Orthopaedics", "hospital": "North District Hospital", "diagnosis": "Right knee osteoarthritis",
        "medications": [{"name": "Paracetamol", "dose": "500 mg", "frequency": "Every 6 hours as needed", "duration": "14 days",
                         "instructions": "Do not exceed 4 g in 24 hours."}],
        "notes": "Review in four weeks.", "issued_at": "2026-10-21T10:30:00", "status": "completed",
    }]


def allergy_conflicts(allergies: List[str], medications: List[Dict[str, Any]]) -> List[str]:
    conflicts = []
    for medication in medications:
        name = medication["name"].lower()
        for allergy in allergies:
            terms = ALLERGY_CLASSES.get(allergy.lower(), (allergy.lower(),))
            if any(term in name for term in terms):
                conflicts.append("%s conflicts with the recorded %s allergy." % (medication["name"], allergy))
    return conflicts


# ---------------------------------------------------------------- prescription PDF

def _pdf_text(value: str) -> str:
    cleaned = value.encode("latin-1", "replace").decode("latin-1")
    return cleaned.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def prescription_pdf(rx: Dict[str, Any], patient: Dict[str, Any]) -> bytes:
    ops: List[str] = ["0.05 0.55 0.52 rg 0 770 595 72 re f"]
    y = 800

    def text(x: int, size: int, content: str, bold: bool = False, color: str = "0.1 0.15 0.2") -> None:
        ops.append("BT /%s %d Tf %s rg %d %d Td (%s) Tj ET" % ("F2" if bold else "F1", size, color, x, y, _pdf_text(content)))

    text(40, 20, "HealthCareOne - Prescription", True, "1 1 1")
    y = 782
    text(40, 10, "CareFlow One  |  Synthetic demonstration document", False, "0.85 0.95 0.95")
    y = 740
    text(40, 11, "Rx No: %s" % rx["id"], True)
    y -= 16
    text(40, 10, "Issued: %s" % rx["issued_at"].replace("T", " "))
    y -= 28
    text(40, 11, "Patient", True)
    y -= 15
    text(40, 10, "%s  (%s)  |  DOB %s  |  %s" % (patient["name"], patient["id"], patient.get("dob", "n/a"), patient.get("sex", "")))
    y -= 14
    text(40, 10, "Allergies: %s" % (", ".join(patient.get("allergies", [])) or "None recorded"))
    y -= 26
    text(40, 11, "Prescriber", True)
    y -= 15
    text(40, 10, "%s  |  %s  |  %s" % (rx["doctor_name"], rx["specialty"], rx["hospital"]))
    y -= 26
    text(40, 11, "Diagnosis", True)
    y -= 15
    text(40, 10, rx["diagnosis"])
    y -= 28
    ops.append("0.8 0.85 0.88 RG 40 %d m 555 %d l S" % (y + 14, y + 14))
    text(40, 12, "Medications", True)
    y -= 20
    for index, medication in enumerate(rx["medications"], 1):
        text(40, 11, "%d. %s  %s" % (index, medication["name"], medication["dose"]), True)
        y -= 14
        text(56, 10, "%s  |  %s" % (medication["frequency"], medication["duration"]))
        y -= 14
        for line in textwrap.wrap(medication.get("instructions") or "", 90):
            text(56, 9, line, False, "0.35 0.4 0.45")
            y -= 12
        y -= 8
    if rx.get("notes"):
        y -= 6
        text(40, 11, "Notes", True)
        y -= 15
        for line in textwrap.wrap(rx["notes"], 95):
            text(40, 10, line)
            y -= 13
    y = 90
    ops.append("0.8 0.85 0.88 RG 40 110 m 555 110 l S")
    text(40, 10, "Electronically issued by %s" % rx["doctor_name"], True)
    y = 74
    text(40, 8, "Synthetic demonstration prescription. Not valid for dispensing or clinical use.", False, "0.5 0.3 0.1")
    stream = "\n".join(ops)

    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 6 0 R "
        "/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        "<< /Length %d >>\nstream\n%s\nendstream" % (len(stream.encode("latin-1")), stream),
    ]
    body = b"%PDF-1.4\n"
    offsets = []
    for number, content in enumerate(objects, 1):
        offsets.append(len(body))
        body += ("%d 0 obj\n%s\nendobj\n" % (number, content)).encode("latin-1")
    xref = len(body)
    body += ("xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)).encode("latin-1")
    for offset in offsets:
        body += ("%010d 00000 n \n" % offset).encode("latin-1")
    body += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)).encode("latin-1")
    return body


# ---------------------------------------------------------------- inpatient wards

# name, age, sex, diagnosis, doctor, allergies, latest vitals (rr, spo2, temp, sbp, hr), trend, meds, pain, mobility
_TEMPLATES: List[Dict[str, Any]] = [
    {"name": "Marcus Bell", "age": 67, "sex": "M", "dx": "Community-acquired pneumonia", "doctor": "Dr. Priya Nair", "allergies": ["Penicillin"],
     "vitals": (22, 93, 38.4, 108, 104), "trend": 1, "pain": 3, "mobility": "Bed rest with assistance",
     "meds": [("Azithromycin", "500 mg", "IV", 8), ("Paracetamol", "1 g", "Oral", 8), ("Enoxaparin", "40 mg", "SC", 12), ("Paracetamol", "1 g", "Oral", 14)]},
    {"name": "Elena Ruiz", "age": 54, "sex": "F", "dx": "Post-op day 2, total knee replacement", "doctor": "Dr. Meera Shah", "allergies": [],
     "vitals": (16, 97, 37.1, 124, 78), "trend": 0, "pain": 4, "mobility": "Walking with frame",
     "meds": [("Oxycodone", "5 mg", "Oral", 8), ("Enoxaparin", "40 mg", "SC", 9), ("Cefazolin", "1 g", "IV", 14), ("Paracetamol", "1 g", "Oral", 12)]},
    {"name": "Henry Okafor", "age": 72, "sex": "M", "dx": "Congestive heart failure, decompensated", "doctor": "Dr. Sam Whitfield", "allergies": ["Sulfa"],
     "vitals": (20, 94, 36.8, 132, 96), "trend": 1, "pain": 1, "mobility": "Assisted to chair",
     "meds": [("Furosemide", "40 mg", "IV", 8), ("Ramipril", "5 mg", "Oral", 8), ("Bisoprolol", "2.5 mg", "Oral", 9), ("Furosemide", "40 mg", "IV", 16)]},
    {"name": "Grace Lindholm", "age": 41, "sex": "F", "dx": "Acute pancreatitis", "doctor": "Dr. Priya Nair", "allergies": [],
     "vitals": (18, 98, 37.6, 118, 88), "trend": -1, "pain": 5, "mobility": "Mobilising independently",
     "meds": [("Morphine", "2 mg", "IV", 9), ("Ondansetron", "4 mg", "IV", 8), ("Pantoprazole", "40 mg", "IV", 10), ("IV fluids Hartmann's", "1 L", "IV", 12)]},
    {"name": "Tobias Nguyen", "age": 29, "sex": "M", "dx": "Appendectomy, post-op day 1", "doctor": "Dr. Alan Brooks", "allergies": [],
     "vitals": (14, 99, 36.9, 122, 70), "trend": -1, "pain": 2, "mobility": "Walking in ward",
     "meds": [("Paracetamol", "1 g", "Oral", 8), ("Ibuprofen", "400 mg", "Oral", 12), ("Amoxicillin-clavulanate", "625 mg", "Oral", 9)]},
    {"name": "Ruth Abernathy", "age": 81, "sex": "F", "dx": "Hip fracture, awaiting surgery", "doctor": "Dr. Meera Shah", "allergies": ["Latex"],
     "vitals": (17, 95, 37.0, 104, 92), "trend": 0, "pain": 6, "mobility": "Bed rest",
     "meds": [("Morphine", "2.5 mg", "SC", 8), ("Paracetamol", "1 g", "Oral", 8), ("Enoxaparin", "40 mg", "SC", 18)]},
    {"name": "Samuel Adeyemi", "age": 58, "sex": "M", "dx": "COPD exacerbation", "doctor": "Dr. Sam Whitfield", "allergies": [],
     "vitals": (24, 91, 37.8, 114, 112), "trend": 1, "pain": 1, "mobility": "Bed rest, oxygen therapy",
     "meds": [("Prednisolone", "40 mg", "Oral", 8), ("Salbutamol nebuliser", "5 mg", "Inhaled", 9), ("Doxycycline", "100 mg", "Oral", 9)]},
    {"name": "Priya Raman", "age": 36, "sex": "F", "dx": "Diabetic ketoacidosis, recovering", "doctor": "Dr. Lena Park", "allergies": [],
     "vitals": (16, 98, 36.7, 116, 82), "trend": -1, "pain": 0, "mobility": "Mobilising independently",
     "meds": [("Insulin infusion", "Per protocol", "IV", 8), ("Potassium chloride", "20 mmol", "IV", 10), ("Insulin glargine", "18 units", "SC", 21)]},
    {"name": "Walter Kowalski", "age": 75, "sex": "M", "dx": "Stroke, rehabilitation phase", "doctor": "Dr. Lena Park", "allergies": [],
     "vitals": (16, 96, 36.9, 146, 74), "trend": 0, "pain": 1, "mobility": "Physiotherapy twice daily",
     "meds": [("Aspirin", "75 mg", "Oral", 8), ("Atorvastatin", "40 mg", "Oral", 20), ("Amlodipine", "5 mg", "Oral", 9)]},
    {"name": "Isabel Moreau", "age": 63, "sex": "F", "dx": "Cellulitis, left leg", "doctor": "Dr. Alan Brooks", "allergies": ["Penicillin"],
     "vitals": (18, 97, 37.9, 120, 94), "trend": 0, "pain": 4, "mobility": "Walking with assistance",
     "meds": [("Clindamycin", "600 mg", "IV", 8), ("Paracetamol", "1 g", "Oral", 12), ("Clindamycin", "600 mg", "IV", 16)]},
    {"name": "Daniel Fischer", "age": 49, "sex": "M", "dx": "Renal colic", "doctor": "Dr. Sam Whitfield", "allergies": [],
     "vitals": (16, 98, 36.8, 126, 76), "trend": -1, "pain": 3, "mobility": "Mobilising independently",
     "meds": [("Diclofenac", "75 mg", "IM", 8), ("Tamsulosin", "400 mcg", "Oral", 20), ("Ondansetron", "4 mg", "IV", 9)]},
    {"name": "Aaliyah Brown", "age": 33, "sex": "F", "dx": "Post-op day 1, laparoscopic cholecystectomy", "doctor": "Dr. Alan Brooks", "allergies": [],
     "vitals": (15, 99, 37.0, 112, 80), "trend": 0, "pain": 3, "mobility": "Walking in ward",
     "meds": [("Paracetamol", "1 g", "Oral", 8), ("Tramadol", "50 mg", "Oral", 12), ("Enoxaparin", "40 mg", "SC", 18)]},
]

_TASKS = ["2-hourly repositioning", "Fluid balance chart", "Pressure area check", "Mobilise with physiotherapy",
          "Wound dressing check", "Oxygen saturation spot checks", "Falls risk review", "Oral hygiene and nutrition check"]
_TIMES = ["01:00", "04:00", "07:00"]


def hospital_code(hospital_id: str) -> str:
    return hospital_id[4:7]


def news2(rr: float, spo2: float, temp: float, sbp: float, hr: float) -> int:
    score = 3 if rr <= 8 else 1 if rr <= 11 else 0 if rr <= 20 else 2 if rr <= 24 else 3
    score += 3 if spo2 <= 91 else 2 if spo2 <= 93 else 1 if spo2 <= 95 else 0
    score += 3 if temp <= 35 else 1 if temp <= 36 else 0 if temp <= 38 else 1 if temp <= 39 else 2
    score += 3 if sbp <= 90 else 2 if sbp <= 100 else 1 if sbp <= 110 else 0 if sbp <= 219 else 3
    score += 3 if hr <= 40 else 1 if hr <= 50 else 0 if hr <= 90 else 1 if hr <= 110 else 2 if hr <= 130 else 3
    return score


def risk_level(score: int) -> str:
    return "high" if score >= 7 else "medium" if score >= 5 else "low"


def _reading(time: str, rr: float, spo2: float, temp: float, sbp: float, hr: float) -> Dict[str, Any]:
    rr, spo2, sbp, hr = int(round(rr)), int(round(min(100, spo2))), int(round(sbp)), int(round(hr))
    temp = round(temp, 1)
    score = news2(rr, spo2, temp, sbp, hr)
    return {"time": time, "rr": rr, "spo2": spo2, "temp": temp, "sbp": sbp, "hr": hr, "news2": score}


def _series(template: Dict[str, Any]) -> List[Dict[str, Any]]:
    rr, spo2, temp, sbp, hr = template["vitals"]
    trend = template["trend"]
    readings = []
    for index, time in enumerate(_TIMES):
        back = 2 - index
        readings.append(_reading("%sT%s" % (SIM_DATE, time), rr - trend * back, spo2 + trend * back,
                                 temp - trend * back * 0.3, sbp + trend * back * 4, hr - trend * back * 4))
    return readings


def _extra_reading(template: Dict[str, Any], base: Dict[str, Any], count: int) -> Dict[str, Any]:
    trend = template["trend"]
    wobble = (-1) ** count
    return _reading("%sT%02d:%02d" % (SIM_DATE, SIM_HOUR + count, 5), base["rr"] + trend + wobble * 0.4, base["spo2"] - trend + (0 if wobble > 0 else 1),
                    base["temp"] + trend * 0.2, base["sbp"] - trend * 2, base["hr"] + trend * 2 + wobble)


def ward_patients(hospital_id: str, count: Optional[int] = None) -> List[Dict[str, Any]]:
    code = hospital_code(hospital_id)
    seed = sum(ord(char) for char in hospital_id)
    total = count or (10 if hospital_id == "HCO-CENTRAL" else 6 + seed % 3)
    patients = []
    for index in range(total):
        template = _TEMPLATES[(seed + index * 5) % len(_TEMPLATES)]
        tasks = [_TASKS[(seed + index + step * 3) % len(_TASKS)] for step in range(3)]
        meds = [{"id": "IPD-%s-%02d-M%d" % (code, index + 1, number + 1), "name": name, "dose": dose, "route": route,
                 "time": "%02d:00" % hour} for number, (name, dose, route, hour) in enumerate(template["meds"])]
        patients.append({
            "id": "IPD-%s-%02d" % (code, index + 1), "hospital_id": hospital_id, "name": template["name"], "age": template["age"],
            "sex": template["sex"], "bed": "W%d-%02d" % (2 + index % 3, 1 + index), "diagnosis": template["dx"],
            "doctor": template["doctor"], "allergies": template["allergies"], "admitted": "2026-10-%02d" % (28 + index % 4),
            "pain_score": template["pain"], "mobility": template["mobility"], "tasks": tasks, "meds": meds,
            "vitals": _series(template), "template_index": (seed + index * 5) % len(_TEMPLATES),
            "intake_ml": 1200 + (seed + index * 90) % 700, "output_ml": 900 + (seed + index * 70) % 500,
        })
    return patients


def apply_state(patient: Dict[str, Any], state: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    state = state or {}
    given = set(state.get("given", []))
    template = _TEMPLATES[patient["template_index"]]
    vitals = list(patient["vitals"])
    for count in range(1, state.get("extra_vitals", 0) + 1):
        vitals.append(_extra_reading(template, vitals[-1], count))
    meds = [dict(med, given=med["id"] in given,
                 status="given" if med["id"] in given else "due" if int(med["time"][:2]) <= SIM_HOUR else "scheduled")
            for med in patient["meds"]]
    latest = vitals[-1]
    charts = state.get("charts", [])
    return dict(patient, vitals=vitals, meds=meds, latest=latest, news2=latest["news2"], risk=risk_level(latest["news2"]),
                charted_today=bool(charts), charts=charts,
                meds_due=sum(1 for med in meds if med["status"] == "due"))


# ---------------------------------------------------------------- nursing chart drafting

def chart_sections(patient: Dict[str, Any]) -> Dict[str, str]:
    latest = patient["latest"]
    given = [m for m in patient["meds"] if m["given"]]
    outstanding = [m for m in patient["meds"] if m["status"] == "due"]
    trend = patient["vitals"][-1]["news2"] - patient["vitals"][0]["news2"]
    direction = "rising" if trend > 0 else "falling" if trend < 0 else "stable"
    escalation = {
        "high": "NEWS2 %d (high). Urgent clinical review requested and escalated to the medical team." % latest["news2"],
        "medium": "NEWS2 %d (medium). Increase observation frequency and inform the nurse in charge." % latest["news2"],
        "low": "NEWS2 %d (low). Continue routine observations." % latest["news2"],
    }[patient["risk"]]
    return {
        "assessment": "RR %d, SpO2 %d%%, temp %.1f C, BP %d systolic, HR %d. NEWS2 %d and %s over the shift. Pain %d/10. %s."
                      % (latest["rr"], latest["spo2"], latest["temp"], latest["sbp"], latest["hr"], latest["news2"], direction, patient["pain_score"], patient["mobility"]),
        "interventions": "; ".join(patient["tasks"]) + ".",
        "medications": ("Given: " + ", ".join("%s %s (%s)" % (m["name"], m["dose"], m["time"]) for m in given) if given else "No medications recorded as given yet.")
                       + ((". Outstanding: " + ", ".join("%s (%s)" % (m["name"], m["time"]) for m in outstanding)) if outstanding else ". No doses outstanding."),
        "fluid_balance": "Intake %d mL, output %d mL, net %+d mL." % (patient["intake_ml"], patient["output_ml"], patient["intake_ml"] - patient["output_ml"]),
        "plan": "Continue the plan under %s. Re-check observations in %s hours. %s" % (
            patient["doctor"], {"high": "1", "medium": "2", "low": "4"}[patient["risk"]], escalation),
    }


def compose_narrative(patient: Dict[str, Any], sections: Dict[str, str]) -> str:
    return ("%s, %d%s, bed %s. Admitted for %s under %s. Allergies: %s.\nAssessment: %s\nInterventions: %s\nMedications: %s\n"
            "Fluid balance: %s\nPlan: %s") % (
        patient["name"], patient["age"], patient["sex"], patient["bed"], patient["diagnosis"], patient["doctor"],
        ", ".join(patient["allergies"]) or "none recorded", sections["assessment"], sections["interventions"],
        sections["medications"], sections["fluid_balance"], sections["plan"])


_DRAFT_INSTRUCTION = (
    "You are a nursing documentation assistant. Write one concise end-of-day nursing progress note in SBAR style "
    "(Situation, Background, Assessment, Recommendation) from the structured facts provided. Use only the facts given, "
    "never invent values, never add medical advice beyond the stated plan. Plain text, under 170 words."
)
_drafter: Optional[Any] = None


async def _draft_live(facts: str) -> str:
    global _drafter
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    if _drafter is None:
        _drafter = Agent(name="nursing_chart_drafter", model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
                         description="Drafts nursing progress notes.", instruction=_DRAFT_INSTRUCTION)
    service = InMemorySessionService()
    session = await service.create_session(app_name="healthcareone_charting", user_id="synthetic_nurse")
    runner = Runner(agent=_drafter, app_name="healthcareone_charting", session_service=service)
    output = ""
    message = types.Content(role="user", parts=[types.Part(text=facts)])
    async for event in runner.run_async(user_id="synthetic_nurse", session_id=session.id, new_message=message):
        for part in getattr(getattr(event, "content", None), "parts", None) or []:
            if getattr(part, "text", None):
                output += part.text
    cleaned = re.sub(r"\n{3,}", "\n\n", output).strip()
    if len(cleaned) < 40:
        raise RuntimeError("The model returned an empty note.")
    return cleaned


async def draft_chart(patient: Dict[str, Any], live_available: bool) -> Dict[str, Any]:
    sections = chart_sections(patient)
    fallback = compose_narrative(patient, sections)
    if not live_available:
        return {"sections": sections, "narrative": fallback, "mode": "deterministic_simulation", "fallback_reason": "AI is not configured."}
    facts = json.dumps({"patient": {k: patient[k] for k in ("name", "age", "sex", "bed", "diagnosis", "doctor", "allergies")},
                        "sections": sections}, indent=1)
    try:
        narrative = await asyncio.wait_for(_draft_live(facts), timeout=25)
        return {"sections": sections, "narrative": narrative, "mode": "live_gemini", "fallback_reason": None}
    except Exception as error:  # drafting must degrade to the deterministic note, never fail the nurse's workflow
        return {"sections": sections, "narrative": fallback, "mode": "deterministic_simulation",
                "fallback_reason": "Live AI failed (%s); used the rule-based note." % type(error).__name__}


OPD_DOCTORS = [
    ("Dr. Meera Shah", "Orthopaedics"), ("Dr. Priya Nair", "General Medicine"), ("Dr. Sam Whitfield", "Cardiology"),
    ("Dr. Alan Brooks", "General Surgery"), ("Dr. Lena Park", "Neurology"), ("Dr. Arjun Rao", "Orthopaedics"),
    ("Dr. Neha Kapoor", "Paediatrics"), ("Dr. Rahul Menon", "ENT"),
]


def opd_board(hospital_id: str) -> Dict[str, Any]:
    """Deterministic synthetic OPD board: one row per doctor with room, load, queue and wait."""
    seed = sum(ord(char) for char in hospital_id)
    count = 6 + seed % 3
    rows = []
    for index in range(count):
        name, specialty = OPD_DOCTORS[(index + seed) % len(OPD_DOCTORS)]
        booked = 12 + (seed * (index + 3)) % 14
        seen = min(booked, 3 + (seed + index * 5) % 9)
        queue = (seed * 3 + index * 5 + index * index) % 8
        status = "On break" if (seed + index) % 9 == 0 else ("In consultation" if queue or seen < booked else "Free")
        if status == "On break":
            queue = 0
        wait = 0 if not queue else 6 + queue * 4 + (seed + index) % 5
        rows.append({
            "doctor": name, "specialty": specialty, "room": "OPD-%d%02d" % (1 + index // 4, index + 1),
            "status": status, "appointments": booked, "seen": seen, "in_queue": queue, "avg_wait_minutes": wait,
            "now_serving": "Token %d" % (seen + 1) if status == "In consultation" else None,
        })
    waiting = [row for row in rows if row["in_queue"]]
    total_queue = sum(row["in_queue"] for row in rows)
    return {
        "hospital_id": hospital_id, "doctors": rows,
        "summary": {
            "doctors_on_opd": sum(1 for row in rows if row["status"] != "On break"), "appointments": sum(row["appointments"] for row in rows),
            "seen": sum(row["seen"] for row in rows), "in_queue": total_queue,
            "avg_wait_minutes": round(sum(row["avg_wait_minutes"] * row["in_queue"] for row in waiting) / total_queue) if total_queue else 0,
        },
    }

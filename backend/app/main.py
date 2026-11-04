import asyncio
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

try:  # trust the OS certificate store so Gemini calls work behind corporate/proxy TLS inspection
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except ImportError:
    pass

from fastapi import FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from .agents import AGENT_SPECS, run_live_smoke, runtime_status
from .assistant import classify, is_red_flag
from . import clinical
from .database import Database
from .services import DomainError, Simulation


logger = logging.getLogger("healthcareone.api")
database = Database()
simulation = Simulation(database)
app = FastAPI(title="HealthCareOne Simulation API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Demo-Role", "X-Correlation-ID"],
)


def envelope(data: Any, correlation_id: Optional[str] = None) -> Dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "error": None,
        "correlation_id": correlation_id or str(uuid.uuid4()),
    }


@app.middleware("http")
async def correlation_middleware(request: Request, call_next: Any) -> Any:
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, error: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": error.code, "message": error.message},
            "correlation_id": getattr(request.state, "correlation_id", str(uuid.uuid4())),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "data": None,
            "error": {"code": "invalid_request", "message": "Request fields did not pass validation."},
            "correlation_id": getattr(request.state, "correlation_id", str(uuid.uuid4())),
        },
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, error: Exception) -> JSONResponse:
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    logger.exception("Unhandled API error; correlation_id=%s", correlation_id)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {"code": "unexpected_error", "message": "The request could not be completed. Retry or reset the simulation."},
            "correlation_id": correlation_id,
        },
    )


class RescheduleRequest(BaseModel):
    slot_id: str
    patient_confirmed: bool
    idempotency_key: str = Field(..., min_length=1, max_length=128)


class BookingRequest(BaseModel):
    patient_id: str = "PAT-1001"
    slot_id: str
    patient_confirmed: bool
    idempotency_key: str = Field(..., min_length=1, max_length=128)


class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class MedicationIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    dose: str = Field(..., min_length=1, max_length=40)
    frequency: str = Field(..., min_length=1, max_length=60)
    duration: str = Field(..., min_length=1, max_length=40)
    instructions: str = Field("", max_length=160)


class PrescriptionRequest(BaseModel):
    patient_id: str = "PAT-1001"
    diagnosis: str = Field(..., min_length=1, max_length=120)
    medications: List[MedicationIn] = Field(..., min_length=1, max_length=8)
    notes: str = Field("", max_length=300)
    clinician_confirmed: bool


class ChartRequest(BaseModel):
    narrative: str = Field(..., min_length=10, max_length=2000)
    ai_mode: str = Field("deterministic_simulation", max_length=40)
    nurse_confirmed: bool


class SessionRequest(BaseModel):
    appointment_id: str
    patient_confirmed: bool


class PlanRequest(BaseModel):
    scenario_id: str
    selected_staff_ids: List[str] = Field(default_factory=list)
    defer_procedure: bool = False


class ApprovalRequest(BaseModel):
    decision: str
    notes: str = Field("", max_length=500)


class ExecuteRequest(BaseModel):
    plan_id: str
    idempotency_key: str = Field(..., min_length=1, max_length=128)


def response(request: Request, data: Any) -> Dict[str, Any]:
    return envelope(data, request.state.correlation_id)


def selected_role(value: Optional[str]) -> str:
    return value or "patient"


def require_operations_role(role: Optional[str]) -> str:
    selected = selected_role(role)
    simulation.require_role(selected, ("presenter", "supervisor"))
    return selected


def require_safe_patient_access(role: Optional[str]) -> None:
    if selected_role(role) != "patient":
        return
    screen = database.get_entity("access_screen", "PAT-1001")
    if not screen or not screen["safe_to_schedule"]:
        raise DomainError(422, "safety_screen_required", "Complete a safe access screen before searching for appointments.")


@app.get("/health")
@app.get("/api/v1/health")
def health(request: Request) -> Dict[str, Any]:
    counts = simulation.counts()
    db_ready = sum(counts.values()) > 0
    ai = runtime_status()
    return response(request, {
        "status": "ready" if db_ready else "degraded",
        "database": "ready" if db_ready else "unavailable",
        "ai": ai,
    })


@app.get("/api/v1/simulation/state")
def state(request: Request) -> Dict[str, Any]:
    return response(request, simulation.state())


@app.post("/api/v1/simulation/reset")
def reset(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    result = simulation.reset(selected_role(role), request.state.correlation_id)
    return response(request, result)


@app.get("/api/v1/simulation/scenarios")
def scenarios(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.scenario_list())


@app.post("/api/v1/simulation/scenarios/{scenario_id}/trigger")
def trigger_scenario(
    scenario_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(
        request,
        simulation.trigger_scenario(scenario_id, selected_role(role), request.state.correlation_id),
    )


@app.post("/api/v1/simulation/events/{event_id}/advance")
def advance_event(
    event_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("presenter",))
    if event_id == "collision":
        result = simulation.trigger_scenario("collision", selected_role(role), request.state.correlation_id)
    elif event_id == "procedure-absence":
        result = simulation.trigger_scenario("procedure-absence", selected_role(role), request.state.correlation_id)
    else:
        raise DomainError(404, "event_not_found", "Simulation event was not found.")
    return response(request, result)


@app.get("/api/v1/patients/{patient_id}")
def patient(patient_id: str, request: Request) -> Dict[str, Any]:
    return response(request, simulation.get_patient(patient_id))


@app.get("/api/v1/patients/{patient_id}/journey")
def journey(patient_id: str, request: Request) -> Dict[str, Any]:
    return response(request, simulation.patient_journey(patient_id))


@app.get("/api/v1/doctors")
def doctors(
    request: Request,
    specialty: Optional[str] = None,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_safe_patient_access(role)
    available = simulation.availability(specialty=specialty)
    records: Dict[str, Dict[str, Any]] = {}
    for item in available:
        records[item["doctor"]["id"]] = item["doctor"]
    return response(request, list(records.values()))


@app.get("/api/v1/availability")
def availability(
    request: Request,
    specialty: Optional[str] = None,
    locality: Optional[str] = None,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_safe_patient_access(role)
    return response(request, simulation.availability(specialty, locality))


@app.post("/api/v1/patient-access/screen")
def screen_access(
    request: Request,
    red_flag_present: bool = Query(False),
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("patient",))
    return response(request, simulation.safety_screen(red_flag_present, request.state.correlation_id))


@app.get("/api/v1/patient-access/screen")
def access_screen_status(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("patient",))
    screen = database.get_entity("access_screen", "PAT-1001")
    return response(request, {
        "screened": screen is not None,
        "safe_to_schedule": bool(screen and screen["safe_to_schedule"]),
    })


@app.post("/api/v1/patient-access/assistant/message")
async def assistant_message(
    body: AssistantRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("patient",))
    text = body.message.strip()
    if is_red_flag(text):
        classification: Dict[str, Any] = {"intent": "unsupported", "mode": "deterministic_policy"}
    else:
        classification = await classify(text, bool(runtime_status()["configured"]))
    return response(request, simulation.assistant_reply(
        text, classification, selected_role(role), request.state.correlation_id,
    ))


@app.post("/api/v1/appointments", status_code=201)
def create_appointment(
    body: BookingRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.book_appointment(
        body.patient_id, body.slot_id, body.patient_confirmed, body.idempotency_key,
        selected_role(role), request.state.correlation_id,
    ))


@app.post("/api/v1/appointments/{appointment_id}/reschedule")
def reschedule_appointment(
    appointment_id: str,
    body: RescheduleRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.reschedule_appointment(
        appointment_id, body.slot_id, body.patient_confirmed, body.idempotency_key,
        selected_role(role), request.state.correlation_id,
    ))


@app.get("/api/v1/appointments/{appointment_id}")
def appointment(
    appointment_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    value = database.get_entity("appointment", appointment_id)
    if not value:
        raise DomainError(404, "appointment_not_found", "Appointment was not found.")
    if selected_role(role) == "patient" and value["patient_id"] != "PAT-1001":
        raise DomainError(403, "patient_forbidden", "Patients can only view their own appointments.")
    return response(request, value)


@app.post("/api/v1/virtual-sessions", status_code=201)
def create_session(
    body: SessionRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.create_virtual_session(
        body.appointment_id, body.patient_confirmed, selected_role(role), request.state.correlation_id
    ))


@app.get("/api/v1/virtual-sessions/{session_id}")
def virtual_session(
    session_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    value = database.get_entity("virtual_session", session_id)
    if not value:
        raise DomainError(404, "session_not_found", "Virtual session was not found.")
    if selected_role(role) == "patient" and value["patient_id"] != "PAT-1001":
        raise DomainError(403, "patient_forbidden", "Patients can only view their own virtual sessions.")
    return response(request, value)


@app.get("/api/v1/simulation/actions/{action_id}")
def action_status(
    action_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    value = database.get_entity("action", action_id)
    if not value:
        raise DomainError(404, "action_not_found", "Simulation action was not found.")
    return response(request, value)


@app.post("/api/v1/virtual-sessions/{session_id}/advance")
def advance_session(
    session_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.advance_virtual_session(
        session_id, selected_role(role), request.state.correlation_id
    ))


@app.post("/api/v1/virtual-sessions/{session_id}/complete")
def complete_session(
    session_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.complete_virtual_session(
        session_id, selected_role(role), request.state.correlation_id
    ))


@app.get("/api/v1/hospitals")
def hospitals(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.capacity())


@app.get("/api/v1/hospitals/{hospital_id}/opd")
def hospital_opd(
    hospital_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.opd_board(hospital_id))


@app.get("/api/v1/hospitals/{hospital_id}/live")
def hospital_live(
    hospital_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.hospital_live(hospital_id))


@app.get("/api/v1/hospitals/{hospital_id}/ipd")
def hospital_ipd(
    hospital_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("nurse", "presenter", "supervisor"))
    return response(request, simulation.ward(hospital_id))


@app.get("/api/v1/ipd/{patient_id}")
def ipd_patient(
    patient_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("nurse", "presenter", "supervisor"))
    return response(request, simulation.ipd_patient(patient_id))


@app.post("/api/v1/ipd/{patient_id}/vitals")
def ipd_vitals(
    patient_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.capture_vitals(patient_id, selected_role(role), request.state.correlation_id))


@app.post("/api/v1/ipd/{patient_id}/medications/{med_id}/administer")
def ipd_administer(
    patient_id: str,
    med_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.administer_medication(patient_id, med_id, selected_role(role), request.state.correlation_id))


@app.post("/api/v1/ipd/{patient_id}/chart/draft")
async def ipd_chart_draft(
    patient_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    simulation.require_role(selected_role(role), ("nurse",))
    patient = simulation.ipd_patient(patient_id)
    draft = await clinical.draft_chart(patient, runtime_status()["configured"])
    return response(request, draft)


@app.post("/api/v1/ipd/{patient_id}/chart", status_code=201)
def ipd_chart_save(
    patient_id: str,
    payload: ChartRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.save_chart(
        patient_id, payload.narrative, payload.ai_mode, payload.nurse_confirmed, selected_role(role), request.state.correlation_id))


@app.get("/api/v1/patients/{patient_id}/prescriptions")
def patient_prescriptions(patient_id: str, request: Request) -> Dict[str, Any]:
    return response(request, simulation.prescriptions(patient_id))


@app.post("/api/v1/prescriptions", status_code=201)
def create_prescription(
    payload: PrescriptionRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.issue_prescription(
        payload.patient_id, payload.diagnosis, [item.model_dump() for item in payload.medications], payload.notes,
        payload.clinician_confirmed, selected_role(role), request.state.correlation_id))


@app.get("/api/v1/prescriptions/{prescription_id}/pdf")
def prescription_pdf(prescription_id: str) -> Response:
    pdf = simulation.prescription_pdf(prescription_id)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="%s.pdf"' % prescription_id})


@app.get("/api/v1/hospitals/{hospital_id}/capacity")
def hospital_capacity(
    hospital_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    hospital = database.get_entity("hospital", hospital_id)
    if not hospital:
        raise DomainError(404, "hospital_not_found", "Hospital was not found.")
    return response(request, hospital)


@app.get("/api/v1/staff")
def staff(
    request: Request,
    hospital_id: Optional[str] = None,
    role_name: Optional[str] = Query(None, alias="role"),
    available: Optional[bool] = None,
    demo_role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(demo_role)
    result = simulation.workforce()
    if hospital_id:
        result = [item for item in result if item["hospital_id"] == hospital_id]
    if role_name:
        result = [item for item in result if item["role"].lower() == role_name.lower()]
    if available is not None:
        result = [item for item in result if item["available"] is available]
    return response(request, result)


@app.get("/api/v1/staff/availability")
def staff_availability(
    request: Request,
    scenario_id: str = "collision",
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    if scenario_id == "collision":
        return response(request, simulation.collision_candidates())
    if scenario_id == "procedure-absence":
        return response(request, simulation.procedure_candidates())
    raise DomainError(422, "invalid_scenario", "Unsupported staff availability scenario.")


@app.get("/api/v1/staff/{staff_id}")
def staff_member(
    staff_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    value = database.get_entity("staff", staff_id)
    if not value:
        raise DomainError(404, "staff_not_found", "Staff member was not found.")
    return response(request, value)


@app.get("/api/v1/procedures")
def procedures(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.procedure_details())


@app.get("/api/v1/procedures/{procedure_id}")
def procedure(
    procedure_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    value = next((item for item in simulation.procedure_details() if item["id"] == procedure_id), None)
    if not value:
        raise DomainError(404, "procedure_not_found", "Procedure was not found.")
    return response(request, value)


@app.post("/api/v1/workforce/augmentation-plans", status_code=201)
def create_plan(
    body: PlanRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.create_plan(
        body.scenario_id, body.selected_staff_ids, body.defer_procedure,
        selected_role(role), request.state.correlation_id,
    ))


@app.get("/api/v1/workforce/augmentation-plans")
def plans(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.list_plans())


@app.get("/api/v1/workforce/augmentation-plans/{plan_id}")
def plan(
    plan_id: str,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.get_plan(plan_id))


@app.post("/api/v1/approvals/{plan_id}/decision")
def decide(
    plan_id: str,
    body: ApprovalRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.decide_plan(
        plan_id, body.decision, body.notes, selected_role(role), request.state.correlation_id
    ))


@app.post("/api/v1/simulation/actions/execute", status_code=201)
def execute(
    body: ExecuteRequest,
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    return response(request, simulation.execute_plan(
        body.plan_id, body.idempotency_key, selected_role(role), request.state.correlation_id
    ))


@app.get("/api/v1/events")
def events(
    request: Request,
    scenario_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.events(scenario_id, correlation_id))


@app.get("/api/v1/audit")
def audit(
    request: Request,
    scenario_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.records("audits", scenario_id, correlation_id))


@app.get("/api/v1/agents/traces")
def traces(
    request: Request,
    scenario_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Dict[str, Any]:
    require_operations_role(role)
    return response(request, simulation.records("traces", scenario_id, correlation_id))


@app.get("/api/v1/agents")
def agents(request: Request) -> Dict[str, Any]:
    return response(request, {
        "runtime": runtime_status(),
        "specifications": [
            {"name": name, "description": description, "tools": tools}
            for name, description, tools in AGENT_SPECS
        ],
    })


@app.post("/api/v1/ai/smoke")
async def ai_smoke(
    request: Request,
    role: Optional[str] = Header(None, alias="X-Demo-Role"),
) -> Any:
    require_operations_role(role)
    correlation_id = request.state.correlation_id
    try:
        result = await run_live_smoke()
    except RuntimeError as error:
        return JSONResponse(
            status_code=503,
            content={
                "success": False, "data": None,
                "error": {"code": "ai_unavailable", "message": str(error)},
                "correlation_id": correlation_id,
            },
        )
    except asyncio.TimeoutError:
        with database.transaction() as connection:
            simulation._trace(connection, "Patient Access Agent", correlation_id, "failed", {
                "mode": "live_gemini", "error": "The Gemini request timed out after 30 seconds.",
            })
        return JSONResponse(
            status_code=504,
            content={
                "success": False, "data": None,
                "error": {"code": "ai_timeout", "message": "The Gemini request timed out after 30 seconds. Retry the smoke test."},
                "correlation_id": correlation_id,
            },
        )
    except Exception:
        with database.transaction() as connection:
            simulation._trace(connection, "Patient Access Agent", correlation_id, "failed", {
                "mode": "live_gemini", "error": "The Gemini request failed. Check configuration and retry.",
            })
        return JSONResponse(
            status_code=502,
            content={
                "success": False, "data": None,
                "error": {"code": "ai_request_failed", "message": "The Gemini request failed. Check configuration and retry."},
                "correlation_id": correlation_id,
            },
        )
    with database.transaction() as connection:
        simulation._trace(connection, "Patient Access Agent", correlation_id, "completed", {
            "mode": "live_gemini", "tool_calls": result["tool_calls"],
            "summary": result["summary"],
        })
    return response(request, result)


# Serve the built frontend (single-container deploys). Skipped when no build exists.
_DIST = os.environ.get(
    "FRONTEND_DIST",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist"),
)
if os.path.isfile(os.path.join(_DIST, "index.html")):
    from fastapi.responses import FileResponse

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str) -> Any:
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"success": False, "error": {"code": "not_found", "message": "Not found"}})
        candidate = os.path.realpath(os.path.join(_DIST, path))
        if path and candidate.startswith(os.path.realpath(_DIST) + os.sep) and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_DIST, "index.html"))

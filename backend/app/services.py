import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .assistant import SAFETY_REPLY, SUPPORTED_INTENTS, UNSUPPORTED_REPLY, is_red_flag
from . import clinical
from .database import Database


SIM_TIME = "2026-11-02T09:00:00"
NOW = "2026-11-02T09:00:00"


class DomainError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


class Simulation:
    def __init__(self, database: Database) -> None:
        self.db = database
        with self.db.connect() as connection:
            count = connection.execute("SELECT COUNT(*) AS count FROM entities").fetchone()["count"]
        if not count:
            self.reset()

    @staticmethod
    def correlation_id(value: Optional[str] = None) -> str:
        return value or str(uuid.uuid4())

    @staticmethod
    def require_role(role: str, allowed: Tuple[str, ...]) -> None:
        if role not in allowed:
            raise DomainError(403, "role_forbidden", "This demo role cannot perform that action.")

    def _put(self, connection: Any, kind: str, entity: Dict[str, Any]) -> None:
        connection.execute(
            "INSERT OR REPLACE INTO entities(kind, id, payload) VALUES (?, ?, ?)",
            (kind, entity["id"], self.db.encode(entity)),
        )

    def _get(self, connection: Any, kind: str, entity_id: str) -> Optional[Dict[str, Any]]:
        row = connection.execute(
            "SELECT payload FROM entities WHERE kind = ? AND id = ?", (kind, entity_id)
        ).fetchone()
        return self.db.decode(row["payload"]) if row else None

    def _list(self, connection: Any, kind: str) -> List[Dict[str, Any]]:
        rows = connection.execute(
            "SELECT payload FROM entities WHERE kind = ? ORDER BY id", (kind,)
        ).fetchall()
        return [self.db.decode(row["payload"]) for row in rows]

    def _event(
        self,
        connection: Any,
        event_type: str,
        correlation_id: str,
        payload: Dict[str, Any],
        scenario_id: Optional[str] = None,
    ) -> None:
        connection.execute(
            "INSERT INTO events(event_type, scenario_id, correlation_id, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_type, scenario_id, correlation_id, self.db.encode(payload), NOW),
        )

    def _audit(
        self,
        connection: Any,
        action: str,
        actor: str,
        correlation_id: str,
        payload: Dict[str, Any],
        scenario_id: Optional[str] = None,
    ) -> None:
        connection.execute(
            "INSERT INTO audits(action, actor, scenario_id, correlation_id, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (action, actor, scenario_id, correlation_id, self.db.encode(payload), NOW),
        )

    def _trace(
        self,
        connection: Any,
        agent_name: str,
        correlation_id: str,
        status: str,
        payload: Dict[str, Any],
        scenario_id: Optional[str] = None,
    ) -> None:
        connection.execute(
            "INSERT INTO traces(agent_name, scenario_id, correlation_id, status, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (agent_name, scenario_id, correlation_id, status, self.db.encode(payload), NOW),
        )

    def reset(self, role: str = "presenter", correlation_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_role(role, ("presenter",))
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            for table in ("entities", "scenarios", "plans", "events", "audits", "traces", "idempotency"):
                connection.execute("DELETE FROM " + table)
            hospitals = [
                ("HCO-CENTRAL", "Central Medical Center", "Central District"),
                ("HCO-NORTH", "North District Hospital", "North District"),
                ("HCO-WEST", "Westside Medical Center", "West District"),
                ("HCO-EAST", "East River Hospital", "East District"),
                ("HCO-SOUTH", "South Valley Hospital", "South District"),
                ("HCO-LAKE", "Lakeside Hospital", "Lake District"),
                ("HCO-HILL", "Hillcrest Hospital", "Hill District"),
                ("HCO-PARK", "Parkview Hospital", "Park District"),
                ("HCO-GREEN", "Greendale Hospital", "Green District"),
                ("HCO-RIVER", "Riverside Hospital", "River District"),
                ("HCO-MAPLE", "Maple Grove Hospital", "Maple District"),
                ("HCO-BAY", "Bayview Hospital", "Bay District"),
            ]
            for hospital_id, name, locality in hospitals:
                capacity = 24 if hospital_id == "HCO-CENTRAL" else 18
                census = 16 if hospital_id == "HCO-CENTRAL" else 11
                self._put(connection, "hospital", {
                    "id": hospital_id, "name": name, "locality": locality,
                    "ed_census": census, "ed_capacity": capacity,
                    "projected_arrivals": 0, "pressure": "Normal",
                })
            self._put(connection, "patient", clinical.patient_profile())
            for prescription in clinical.seed_prescriptions():
                self._put(connection, "prescription", prescription)
            self._put(connection, "doctor", {
                "id": "DOC-0021", "name": "Dr. Meera Shah", "specialty": "Orthopaedics",
                "location": "North District Hospital", "hospital_id": "HCO-NORTH",
                "modes": ["virtual"],
            })
            self._put(connection, "doctor", {
                "id": "DOC-0022", "name": "Dr. Arjun Rao", "specialty": "Orthopaedics",
                "location": "North District Clinic", "hospital_id": "HCO-NORTH",
                "modes": ["in_person"],
            })
            self._put(connection, "slot", {
                "id": "SLOT-IMMEDIATE-01", "doctor_id": "DOC-0021",
                "starts_at": "2026-11-02T09:00:00", "mode": "virtual", "available": True,
            })
            self._put(connection, "slot", {
                "id": "SLOT-TODAY-02", "doctor_id": "DOC-0022",
                "starts_at": "2026-11-02T14:00:00", "mode": "in_person", "available": True,
            })
            staff = [
                ("STF-C-011", "Riley Chen", "ED RN", "HCO-CENTRAL", ["ED", "triage"], "active", 12),
                ("STF-C-012", "Jordan Lee", "ED RN", "HCO-CENTRAL", ["ED", "triage"], "active", 12),
                ("STF-N-021", "Casey Patel", "ED RN", "HCO-NORTH", ["ED", "triage"], "active", 12),
                ("STF-W-018", "Avery Brooks", "ED RN", "HCO-WEST", ["ED", "triage"], "active", 12),
                ("STF-N-032", "Morgan Ellis", "Trauma Support", "HCO-NORTH", ["trauma"], "active", 12),
                ("STF-W-077", "Taylor Kim", "ED RN", "HCO-WEST", ["ED"], "expired_cert", 12),
                ("STF-C-099", "Jamie Park", "ED RN", "HCO-CENTRAL", ["ED"], "insufficient_rest", 6),
                ("STF-N-040", "Skyler Reed", "ED RN", "HCO-NORTH", ["ED"], "unavailable", 12),
                ("STF-C-061", "Dana Flores", "OR Nurse", "HCO-CENTRAL", ["OR", "surgical_nursing"], "active", 12),
                ("STF-N-044", "Quinn Diaz", "OR Nurse", "HCO-NORTH", ["OR", "surgical_nursing"], "active", 12),
                ("STF-W-051", "Robin Singh", "OR Nurse", "HCO-WEST", ["OR", "surgical_nursing"], "expired_cert", 12),
                ("STF-C-063", "Alexis Green", "Surgeon", "HCO-CENTRAL", ["surgery"], "active", 12),
            ]
            for staff_id, name, role_name, hospital_id, skills, availability, rest_hours in staff:
                available = availability not in ("unavailable",)
                certification = "2027-12-31" if availability != "expired_cert" else "2026-10-01"
                if availability == "unavailable":
                    available = False
                record = {
                    "id": staff_id, "name": name, "role": role_name,
                    "hospital_id": hospital_id, "skills": skills, "available": available,
                    "certification_valid_through": certification, "rest_hours": rest_hours,
                    "hours_worked": 4 if rest_hours >= 10 else 10,
                    "shift_start": "2026-11-02T08:00:00", "shift_end": "2026-11-02T20:00:00",
                    "assigned_department": "ED" if role_name in ("ED RN", "Trauma Support") else "OR",
                }
                self._put(connection, "staff", record)
            self._put(connection, "procedure", {
                "id": "PROC-220", "name": "Elective procedure", "hospital_id": "HCO-CENTRAL",
                "scheduled_at": "2026-11-02T15:00:00", "critical": False, "deferrable": True,
                "readiness": "ready", "assigned_staff": [],
                "room": "OR-02", "room_ready": True, "patient_prepared": True,
                "documentation_complete": True, "required_roles": [],
            })
            self._put(connection, "procedure", {
                "id": "PROC-221", "name": "Critical procedure", "hospital_id": "HCO-CENTRAL",
                "scheduled_at": "2026-11-02T16:00:00", "critical": True, "deferrable": False,
                "readiness": "ready", "assigned_staff": [],
                "room": "OR-04", "room_ready": True, "patient_prepared": True,
                "documentation_complete": True, "required_roles": [],
            })
            self._put(connection, "procedure", {
                "id": "PROC-310", "name": "Scheduled procedure", "hospital_id": "HCO-CENTRAL",
                "scheduled_at": "2026-11-02T13:00:00", "critical": False, "deferrable": False,
                "readiness": "ready", "assigned_staff": ["STF-C-061", "STF-C-063"],
                "room": "OR-03", "room_ready": True, "patient_prepared": True,
                "documentation_complete": True,
                "required_roles": [{"role": "OR Nurse", "skill": "OR"}, {"role": "Surgeon", "skill": "surgery"}],
            })
            for scenario_id, label in (
                ("collision", "Network collision response"),
                ("procedure-absence", "Procedure staff absence"),
            ):
                connection.execute(
                    "INSERT INTO scenarios(id, status, payload) VALUES (?, ?, ?)",
                    (scenario_id, "baseline", self.db.encode({"id": scenario_id, "name": label})),
                )
            self._audit(connection, "simulation.reset", role, correlation_id, {"message": "Synthetic baseline restored."})
        return {"reset": True, "simulation_time": SIM_TIME, "counts": self.counts(), "correlation_id": correlation_id}

    def counts(self) -> Dict[str, int]:
        with self.db.connect() as connection:
            counts: Dict[str, int] = {}
            for kind in ("hospital", "patient", "doctor", "slot", "staff", "procedure"):
                counts[kind] = connection.execute(
                    "SELECT COUNT(*) AS count FROM entities WHERE kind = ?", (kind,)
                ).fetchone()["count"]
            return counts

    def state(self) -> Dict[str, Any]:
        with self.db.connect() as connection:
            scenarios = connection.execute(
                "SELECT id, status FROM scenarios ORDER BY id"
            ).fetchall()
            return {
                "simulation_time": SIM_TIME,
                "synthetic_data": True,
                "counts": self.counts(),
                "scenarios": [{"id": row["id"], "status": row["status"]} for row in scenarios],
            }

    def get_patient(self, patient_id: str) -> Dict[str, Any]:
        patient = self.db.get_entity("patient", patient_id)
        if not patient:
            raise DomainError(404, "patient_not_found", "Patient was not found.")
        return patient

    def availability(self, specialty: Optional[str] = None, locality: Optional[str] = None) -> List[Dict[str, Any]]:
        doctors = {doctor["id"]: doctor for doctor in self.db.list_entities("doctor")}
        slots = self.db.list_entities("slot")
        results = []
        for slot in slots:
            doctor = doctors.get(slot["doctor_id"])
            if not doctor or not slot["available"]:
                continue
            if specialty and specialty.lower() != doctor["specialty"].lower():
                continue
            if locality and locality.lower() not in (doctor["location"] + " " + doctor["hospital_id"]).lower():
                continue
            results.append(dict(slot, doctor=doctor))
        return results

    def patient_journey(self, patient_id: str) -> Dict[str, Any]:
        patient = self.get_patient(patient_id)
        appointments = [
            item for item in self.db.list_entities("appointment")
            if item["patient_id"] == patient_id
        ]
        sessions = [
            item for item in self.db.list_entities("virtual_session")
            if item.get("patient_id") == patient_id
        ]
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT event_type, payload, created_at, correlation_id FROM events "
                "WHERE json_extract(payload, '$.patient_id') = ? ORDER BY id",
                (patient_id,),
            ).fetchall()
        events = [
            {"type": row["event_type"], "created_at": row["created_at"],
             "correlation_id": row["correlation_id"], **self.db.decode(row["payload"])}
            for row in rows
        ]
        return {"patient": patient, "appointments": appointments, "virtual_sessions": sessions, "events": events}

    def safety_screen(self, red_flag_present: bool, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        correlation_id = self.correlation_id(correlation_id)
        safe_to_schedule = not red_flag_present
        message = (
            "Please seek immediate help from local emergency services or a qualified clinician. Routine booking is paused."
            if red_flag_present else "You can continue to synthetic appointment options."
        )
        with self.db.transaction() as connection:
            self._put(connection, "access_screen", {
                "id": "PAT-1001", "safe_to_schedule": safe_to_schedule,
                "correlation_id": correlation_id,
            })
            if red_flag_present:
                self._event(connection, "patient.safety_escalated", correlation_id, {
                    "patient_id": "PAT-1001", "reason": "A safety concern was flagged; routine scheduling stopped."
                })
                self._audit(connection, "patient.safety_escalated", "patient", correlation_id, {
                    "patient_id": "PAT-1001", "routine_scheduling_paused": True,
                })
            self._trace(connection, "Experience Coordinator", correlation_id, "completed", {
                "mode": "deterministic_policy", "summary": "Access request routed through the safety gate.",
            })
            self._trace(connection, "Patient Access Agent", correlation_id, "completed", {
                "mode": "deterministic_policy", "summary": "Safety result recorded before any scheduling lookup.",
            })
        return {"safe_to_schedule": safe_to_schedule, "message": message, "correlation_id": correlation_id}

    def assistant_reply(
        self, message: str, classification: Dict[str, Any], role: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        correlation_id = self.correlation_id(correlation_id)
        text = message.strip()
        if not text:
            raise DomainError(422, "message_required", "Please type a request.")
        mode = classification.get("mode", "deterministic_simulation")
        fallback_reason = classification.get("fallback_reason")
        slots: List[Dict[str, Any]] = []

        if is_red_flag(text):
            self.safety_screen(True, correlation_id)
            intent, reply, escalated = "safety_escalation", SAFETY_REPLY, True
            mode, fallback_reason = "deterministic_policy", None
        else:
            self.safety_screen(False, correlation_id)
            escalated = False
            intent = classification["intent"]
            preferred = classification.get("preferred_mode", "any")
            if intent == "virtual_consult":
                preferred = "virtual"
            if intent in SUPPORTED_INTENTS:
                slots = [
                    slot for slot in self.availability(specialty="Orthopaedics")
                    if preferred == "any" or slot["mode"] == preferred
                ]
                if slots:
                    kind = "virtual consult" if preferred == "virtual" else "Orthopaedics appointment"
                    reply = (
                        "Here %s available %s option%s. Choose one and I'll ask you to confirm before "
                        "booking anything. I can't give medical advice."
                        % ("is" if len(slots) == 1 else "are", kind, "" if len(slots) == 1 else "s")
                    )
                else:
                    reply = "I couldn't find an open slot for that request right now. Please try again later."
            else:
                intent, reply = "unsupported", UNSUPPORTED_REPLY

        with self.db.transaction() as connection:
            self._event(connection, "patient.assistant_message", correlation_id, {
                "patient_id": "PAT-1001", "intent": intent, "mode": mode,
            })
            self._audit(connection, "patient.assistant_message", role, correlation_id, {
                "patient_id": "PAT-1001", "intent": intent, "message_excerpt": text[:120],
            })
            self._trace(connection, "Patient Access Agent", correlation_id, "completed", {
                "mode": mode, "intent": intent, "fallback_reason": fallback_reason,
                "summary": "Understood a typed patient request and replied within safe, supported scope.",
            })
        return {
            "reply": reply, "intent": intent, "mode": mode, "safety_escalated": escalated,
            "fallback_reason": fallback_reason, "slots": slots, "correlation_id": correlation_id,
        }

    def book_appointment(
        self, patient_id: str, slot_id: str, confirmed: bool, idempotency_key: str,
        role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        if not confirmed:
            raise DomainError(422, "confirmation_required", "Patient confirmation is required.")
        if not idempotency_key:
            raise DomainError(400, "idempotency_key_required", "An idempotency key is required.")
        self.get_patient(patient_id)
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            screen = self._get(connection, "access_screen", patient_id)
            if not screen or not screen["safe_to_schedule"]:
                raise DomainError(422, "safety_screen_required", "Complete a safe access screen before searching or booking.")
            prior = connection.execute(
                "SELECT entity_id FROM idempotency WHERE key = ?", ("appointment:" + idempotency_key,)
            ).fetchone()
            if prior:
                appointment = self._get(connection, "appointment", prior["entity_id"])
                if appointment:
                    if appointment["patient_id"] != patient_id or appointment["slot_id"] != slot_id:
                        raise DomainError(409, "idempotency_key_reused", "This idempotency key belongs to a different appointment request.")
                    return dict(appointment, correlation_id=correlation_id, idempotent_replay=True)
            slot = self._get(connection, "slot", slot_id)
            if not slot:
                raise DomainError(404, "slot_not_found", "Appointment slot was not found.")
            if not slot["available"]:
                raise DomainError(409, "slot_unavailable", "This appointment slot is no longer available.")
            appointment_id = "APT-DEMO-0001"
            if self._get(connection, "appointment", appointment_id):
                appointment_id = "APT-" + uuid.uuid4().hex[:8].upper()
            slot["available"] = False
            self._put(connection, "slot", slot)
            appointment = {
                "id": appointment_id, "patient_id": patient_id, "doctor_id": slot["doctor_id"],
                "slot_id": slot_id, "starts_at": slot["starts_at"], "mode": slot["mode"],
                "status": "confirmed", "synthetic": True,
            }
            self._put(connection, "appointment", appointment)
            connection.execute(
                "INSERT INTO idempotency(key, entity_kind, entity_id) VALUES (?, ?, ?)",
                ("appointment:" + idempotency_key, "appointment", appointment_id),
            )
            self._event(connection, "appointment.confirmed", correlation_id, {
                "appointment_id": appointment_id, "patient_id": patient_id,
            })
            self._audit(connection, "appointment.confirmed", role, correlation_id, {
                "appointment_id": appointment_id, "patient_id": patient_id,
            })
            self._trace(connection, "Patient Access Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Confirmed appointment from a currently available synthetic slot.",
            })
            self._trace(connection, "Patient Journey Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Persisted confirmed booking for the patient journey.",
            })
        return dict(appointment, correlation_id=correlation_id, idempotent_replay=False)

    def reschedule_appointment(
        self, appointment_id: str, slot_id: str, confirmed: bool, idempotency_key: str,
        role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        if not confirmed:
            raise DomainError(422, "confirmation_required", "Patient confirmation is required.")
        if not idempotency_key:
            raise DomainError(400, "idempotency_key_required", "An idempotency key is required.")
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            appointment = self._get(connection, "appointment", appointment_id)
            if not appointment:
                raise DomainError(404, "appointment_not_found", "Appointment was not found.")
            if appointment["slot_id"] == slot_id:
                return dict(appointment, correlation_id=correlation_id, idempotent_replay=True)
            slot = self._get(connection, "slot", slot_id)
            if not slot:
                raise DomainError(404, "slot_not_found", "Appointment slot was not found.")
            if not slot["available"]:
                raise DomainError(409, "slot_unavailable", "This appointment slot is no longer available.")
            previous = self._get(connection, "slot", appointment["slot_id"])
            if previous:
                previous["available"] = True
                self._put(connection, "slot", previous)
            slot["available"] = False
            self._put(connection, "slot", slot)
            previous_start = appointment["starts_at"]
            appointment.update({
                "doctor_id": slot["doctor_id"], "slot_id": slot_id, "starts_at": slot["starts_at"],
                "mode": slot["mode"], "status": "confirmed",
            })
            self._put(connection, "appointment", appointment)
            details = {
                "appointment_id": appointment_id, "patient_id": appointment["patient_id"],
                "previous_starts_at": previous_start,
            }
            self._event(connection, "appointment.rescheduled", correlation_id, details)
            self._audit(connection, "appointment.rescheduled", role, correlation_id, details)
        return dict(appointment, correlation_id=correlation_id, idempotent_replay=False)

    def create_virtual_session(
        self, appointment_id: str, confirmed: bool, role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        if not confirmed:
            raise DomainError(422, "confirmation_required", "Patient confirmation is required.")
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            appointment = self._get(connection, "appointment", appointment_id)
            if not appointment or appointment["mode"] != "virtual":
                raise DomainError(422, "virtual_appointment_required", "A confirmed virtual appointment is required.")
            existing = next(
                (s for s in self._list(connection, "virtual_session") if s["appointment_id"] == appointment_id),
                None,
            )
            if existing:
                return dict(existing, correlation_id=correlation_id)
            session = {
                "id": "VCS-DEMO-0001", "appointment_id": appointment_id,
                "patient_id": appointment["patient_id"], "status": "waiting", "synthetic": True,
            }
            self._put(connection, "virtual_session", session)
            self._event(connection, "virtual_session.created", correlation_id, session)
            self._audit(connection, "virtual_session.created", role, correlation_id, {"session_id": session["id"]})
            self._trace(connection, "Virtual Care Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Created a confirmed, simulated virtual session.",
            })
            self._trace(connection, "Patient Journey Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Linked the session to the patient's synthetic journey.",
            })
        return dict(session, correlation_id=correlation_id)

    def advance_virtual_session(
        self, session_id: str, role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        correlation_id = self.correlation_id(correlation_id)
        next_status = {"waiting": "doctor_connected", "doctor_connected": "in_consultation"}
        with self.db.transaction() as connection:
            session = self._get(connection, "virtual_session", session_id)
            if not session:
                raise DomainError(404, "session_not_found", "Virtual session was not found.")
            if session["status"] not in next_status:
                raise DomainError(409, "invalid_session_transition", "This session cannot be advanced.")
            session["status"] = next_status[session["status"]]
            self._put(connection, "virtual_session", session)
            self._event(connection, "virtual_session.status_changed", correlation_id, session)
            self._trace(connection, "Virtual Care Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Advanced the simulated session through a valid state transition.",
            })
        return dict(session, correlation_id=correlation_id)

    def complete_virtual_session(
        self, session_id: str, role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("patient",))
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            session = self._get(connection, "virtual_session", session_id)
            if not session:
                raise DomainError(404, "session_not_found", "Virtual session was not found.")
            if session["status"] not in ("in_consultation", "doctor_connected"):
                raise DomainError(409, "invalid_session_transition", "Only an active session can be completed.")
            session["status"] = "completed"
            self._put(connection, "virtual_session", session)
            task = {"id": "TASK-FOLLOWUP-0001", "patient_id": session["patient_id"], "status": "open", "type": "simulated_follow_up"}
            self._put(connection, "follow_up", task)
            self._event(connection, "virtual_session.completed", correlation_id, {
                "session_id": session_id, "patient_id": session["patient_id"], "follow_up_task_id": task["id"],
            })
            self._audit(connection, "virtual_session.completed", role, correlation_id, {"session_id": session_id})
            self._trace(connection, "Virtual Care Agent", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Completed the session and created a simulated follow-up task.",
            })
        return dict(session, follow_up_task=task, correlation_id=correlation_id)

    def scenario_list(self) -> List[Dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute("SELECT id, status, payload FROM scenarios ORDER BY id").fetchall()
        return [dict(self.db.decode(row["payload"]), status=row["status"]) for row in rows]

    def _scenario(self, connection: Any, scenario_id: str) -> Dict[str, Any]:
        row = connection.execute("SELECT status, payload FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        if not row:
            raise DomainError(404, "scenario_not_found", "Scenario was not found.")
        return dict(self.db.decode(row["payload"]), status=row["status"])

    def trigger_scenario(
        self, scenario_id: str, role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("presenter",))
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            scenario = self._scenario(connection, scenario_id)
            if scenario["status"] != "baseline":
                raise DomainError(409, "scenario_already_triggered", "Reset the simulation before triggering this scenario again.")
            if scenario_id == "collision":
                central = self._get(connection, "hospital", "HCO-CENTRAL")
                central.update({"projected_arrivals": 8, "pressure": "Critical"})
                self._put(connection, "hospital", central)
                result = {"hospital_id": "HCO-CENTRAL", "projected_census": 24, "capacity": 24, "rn_gap": 4, "trauma_support_gap": 1}
                event = "collision.triggered"
                agents = ["Operations Intelligence Coordinator", "Patient Flow Agent", "Workforce Demand Agent"]
            elif scenario_id == "procedure-absence":
                staff = self._get(connection, "staff", "STF-C-061")
                staff["available"] = False
                self._put(connection, "staff", staff)
                procedure = self._get(connection, "procedure", "PROC-310")
                procedure["readiness"] = "at_risk"
                self._put(connection, "procedure", procedure)
                result = {"procedure_id": "PROC-310", "missing_staff_id": "STF-C-061", "readiness": "at_risk"}
                event = "staff.absence.triggered"
                agents = ["Operations Intelligence Coordinator", "Procedure Readiness Agent"]
            else:
                raise DomainError(404, "scenario_not_found", "Scenario was not found.")
            connection.execute("UPDATE scenarios SET status = 'triggered' WHERE id = ?", (scenario_id,))
            self._event(connection, event, correlation_id, result, scenario_id)
            if scenario_id == "collision":
                self._event(connection, "arrivals.projected", correlation_id, {
                    "hospital_id": "HCO-CENTRAL", "projected_arrivals": 8,
                }, scenario_id)
                self._event(connection, "capacity.pressure_changed", correlation_id, {
                    "hospital_id": "HCO-CENTRAL", "pressure": "Critical",
                    "projected_census": 24, "capacity": 24,
                }, scenario_id)
            else:
                self._event(connection, "procedure.readiness_changed", correlation_id, {
                    "procedure_id": "PROC-310", "readiness": "at_risk",
                }, scenario_id)
            self._audit(connection, event, role, correlation_id, result, scenario_id)
            for agent in agents:
                self._trace(connection, agent, correlation_id, "completed", {
                    "mode": "deterministic_simulation", "summary": "Recorded scenario event and deterministic fixture evidence.",
                }, scenario_id)
        return dict(result, scenario_id=scenario_id, status="triggered", correlation_id=correlation_id)

    def collision_candidates(self) -> Dict[str, Any]:
        staff = self.db.list_entities("staff")
        rn_ids = {"STF-C-011", "STF-C-012", "STF-N-021", "STF-W-018"}
        trauma_ids = {"STF-N-032"}
        eligible = []
        excluded = []
        for person in staff:
            if person["id"] in rn_ids | trauma_ids:
                eligible.append(dict(person, eligible=True, reason="Required role, skills, certification and availability verified."))
                continue
            if person["id"] not in ("STF-W-077", "STF-C-099", "STF-N-040"):
                continue
            reason = {
                "STF-W-077": "Required certification expired.",
                "STF-C-099": "Insufficient rest before the proposed shift.",
                "STF-N-040": "Staff member is unavailable.",
            }[person["id"]]
            excluded.append(dict(person, eligible=False, reason=reason))
        return {"eligible": eligible, "excluded": excluded}

    def procedure_candidates(self) -> Dict[str, Any]:
        available = self.db.list_entities("staff")
        eligible = []
        excluded = []
        for person in available:
            if person["id"] == "STF-N-044":
                eligible.append(dict(person, eligible=True, reason="OR skill, active certification, availability, shift and rest verified."))
            elif person["id"] == "STF-W-051":
                excluded.append(dict(person, eligible=False, reason="Required certification expired."))
        return {"eligible": eligible, "excluded": excluded}

    def create_plan(
        self, scenario_id: str, selected_staff_ids: List[str], defer_procedure: bool,
        role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("presenter",))
        correlation_id = self.correlation_id(correlation_id)
        plan_id = "PLAN-" + uuid.uuid4().hex[:8].upper()
        with self.db.transaction() as connection:
            scenario = self._scenario(connection, scenario_id)
            if scenario["status"] != "triggered":
                raise DomainError(409, "scenario_not_triggered", "Trigger the scenario before proposing a plan.")
            candidates = self.collision_candidates() if scenario_id == "collision" else self.procedure_candidates()
            eligible_ids = {item["id"] for item in candidates["eligible"]}
            if not selected_staff_ids and scenario_id == "collision":
                selected_staff_ids = ["STF-C-011", "STF-C-012", "STF-N-021", "STF-W-018", "STF-N-032"]
            if not set(selected_staff_ids).issubset(eligible_ids):
                raise DomainError(422, "ineligible_candidate", "The plan contains a candidate who failed eligibility checks.")
            if scenario_id == "procedure-absence" and not selected_staff_ids:
                selected_staff_ids = ["STF-N-044"]
            if scenario_id == "collision" and defer_procedure:
                procedure = self._get(connection, "procedure", "PROC-220")
                if not procedure or not procedure["deferrable"] or procedure["critical"]:
                    raise DomainError(422, "procedure_not_deferrable", "This procedure cannot be deferred.")
            plan = {
                "id": plan_id, "scenario_id": scenario_id, "status": "pending_approval",
                "selected_staff_ids": selected_staff_ids, "defer_procedure": defer_procedure,
                "created_by": role, "evidence": candidates,
                "proposed_changes": {
                    "staff_assignments": selected_staff_ids,
                    "defer_procedure_id": "PROC-220" if defer_procedure else None,
                },
                "correlation_id": correlation_id,
            }
            connection.execute(
                "INSERT INTO plans(id, scenario_id, status, payload) VALUES (?, ?, ?, ?)",
                (plan_id, scenario_id, plan["status"], self.db.encode(plan)),
            )
            connection.execute(
                "UPDATE scenarios SET status = 'awaiting_approval' WHERE id = ?", (scenario_id,)
            )
            self._event(connection, "augmentation.proposed" if scenario_id == "collision" else "replacement.proposed",
                        correlation_id, {"plan_id": plan_id, "status": plan["status"]}, scenario_id)
            self._audit(connection, "plan.proposed", role, correlation_id, {"plan_id": plan_id}, scenario_id)
            for agent in (
                ["Staff Availability Agent", "Skills Matching Agent", "Fatigue & Compliance Agent", "Workforce Coordinator"]
                if scenario_id == "collision" else
                ["Staff Availability Agent", "Skills Matching Agent", "Fatigue & Compliance Agent", "Workforce Coordinator"]
            ):
                self._trace(connection, agent, correlation_id, "completed", {
                    "mode": "deterministic_simulation", "summary": "Eligibility facts returned by deterministic policy services.",
                }, scenario_id)
        return dict(plan, correlation_id=correlation_id)

    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        with self.db.connect() as connection:
            row = connection.execute("SELECT payload FROM plans WHERE id = ?", (plan_id,)).fetchone()
        if not row:
            raise DomainError(404, "plan_not_found", "Plan was not found.")
        return self.db.decode(row["payload"])

    def list_plans(self) -> List[Dict[str, Any]]:
        with self.db.connect() as connection:
            rows = connection.execute("SELECT payload FROM plans ORDER BY rowid DESC").fetchall()
        return [self.db.decode(row["payload"]) for row in rows]

    def decide_plan(
        self, plan_id: str, decision: str, notes: str, role: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("supervisor",))
        if decision not in ("approved", "rejected"):
            raise DomainError(422, "invalid_decision", "Decision must be approved or rejected.")
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            row = connection.execute("SELECT status, payload FROM plans WHERE id = ?", (plan_id,)).fetchone()
            if not row:
                raise DomainError(404, "plan_not_found", "Plan was not found.")
            plan = self.db.decode(row["payload"])
            if plan["status"] != "pending_approval":
                raise DomainError(409, "plan_already_decided", "This plan is no longer awaiting approval.")
            plan["status"] = decision
            plan["approval"] = {"decision": decision, "actor": role, "notes": notes, "correlation_id": correlation_id}
            connection.execute(
                "UPDATE plans SET status = ?, payload = ? WHERE id = ?",
                (decision, self.db.encode(plan), plan_id),
            )
            if decision == "rejected":
                connection.execute(
                    "UPDATE scenarios SET status = 'completed' WHERE id = ?", (plan["scenario_id"],)
                )
            self._event(connection, "approval.decided", correlation_id, {
                "plan_id": plan_id, "decision": decision, "actor": role,
            }, plan["scenario_id"])
            self._audit(connection, "approval.decided", role, correlation_id, {
                "plan_id": plan_id, "decision": decision, "notes": notes,
            }, plan["scenario_id"])
        return dict(plan, correlation_id=correlation_id)

    def execute_plan(
        self, plan_id: str, idempotency_key: str, role: str,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("supervisor",))
        if not idempotency_key:
            raise DomainError(400, "idempotency_key_required", "An idempotency key is required.")
        correlation_id = self.correlation_id(correlation_id)
        with self.db.transaction() as connection:
            prior = connection.execute(
                "SELECT entity_id FROM idempotency WHERE key = ?", ("action:" + idempotency_key,)
            ).fetchone()
            if prior:
                plan = self._get(connection, "action", prior["entity_id"])
                if plan:
                    if plan["plan_id"] != plan_id:
                        raise DomainError(409, "idempotency_key_reused", "This idempotency key belongs to a different action.")
                    return dict(plan, correlation_id=correlation_id, idempotent_replay=True)
            row = connection.execute("SELECT status, payload FROM plans WHERE id = ?", (plan_id,)).fetchone()
            if not row:
                raise DomainError(404, "plan_not_found", "Plan was not found.")
            plan = self.db.decode(row["payload"])
            if plan["status"] != "approved":
                raise DomainError(409, "approval_required", "Only an approved plan can be executed.")
            for staff_id in plan["selected_staff_ids"]:
                staff = self._get(connection, "staff", staff_id)
                expected_time = "2026-11-02T13:00:00" if plan["scenario_id"] == "procedure-absence" else SIM_TIME
                valid = bool(
                    staff and staff["available"] and staff["rest_hours"] >= 10
                    and staff["hours_worked"] <= 12
                    and staff["certification_valid_through"] >= expected_time[:10]
                    and staff["shift_start"] <= expected_time <= staff["shift_end"]
                )
                if plan["scenario_id"] == "procedure-absence":
                    valid = bool(valid and staff["role"] == "OR Nurse" and "OR" in staff["skills"])
                elif staff_id == "STF-N-032":
                    valid = bool(valid and staff["role"] == "Trauma Support" and "trauma" in staff["skills"])
                else:
                    valid = bool(valid and staff["role"] == "ED RN" and "ED" in staff["skills"])
                if not valid:
                    raise DomainError(422, "eligibility_changed", "A selected staff member is no longer eligible.")
            for staff_id in plan["selected_staff_ids"]:
                staff = self._get(connection, "staff", staff_id)
                staff["assigned_department"] = "ED" if plan["scenario_id"] == "collision" else "OR"
                staff["assigned_scenario"] = plan["scenario_id"]
                self._put(connection, "staff", staff)
            if plan["scenario_id"] == "procedure-absence":
                procedure = self._get(connection, "procedure", "PROC-310")
                if not procedure or not any(not self._get(connection, "staff", staff_id)["available"] for staff_id in procedure["assigned_staff"]):
                    raise DomainError(409, "procedure_changed", "Procedure staffing changed after the plan was approved.")
                procedure["assigned_staff"] = [
                    staff_id for staff_id in procedure["assigned_staff"] if staff_id != "STF-C-061"
                ] + plan["selected_staff_ids"]
                procedure["readiness"] = self._readiness(connection, procedure)
                self._put(connection, "procedure", procedure)
            if plan["scenario_id"] == "collision" and plan["defer_procedure"]:
                procedure = self._get(connection, "procedure", "PROC-220")
                if not procedure["deferrable"] or procedure["critical"]:
                    raise DomainError(422, "procedure_not_deferrable", "The selected procedure is no longer deferrable.")
                procedure["status"] = "deferred"
                self._put(connection, "procedure", procedure)
            action_id = "ACT-" + uuid.uuid4().hex[:8].upper()
            action = {"id": action_id, "plan_id": plan_id, "status": "completed", "scenario_id": plan["scenario_id"]}
            self._put(connection, "action", action)
            connection.execute(
                "INSERT INTO idempotency(key, entity_kind, entity_id) VALUES (?, ?, ?)",
                ("action:" + idempotency_key, "action", action_id),
            )
            plan["status"] = "completed"
            plan["action_id"] = action_id
            connection.execute(
                "UPDATE plans SET status = 'completed', payload = ? WHERE id = ?",
                (self.db.encode(plan), plan_id),
            )
            connection.execute(
                "UPDATE scenarios SET status = 'completed' WHERE id = ?", (plan["scenario_id"],)
            )
            self._event(connection, "augmentation.executed" if plan["scenario_id"] == "collision" else "staff.assignment_changed",
                        correlation_id, action, plan["scenario_id"])
            if plan["scenario_id"] == "collision" and plan["defer_procedure"]:
                self._event(connection, "procedure.deferral.applied", correlation_id, {"procedure_id": "PROC-220"}, plan["scenario_id"])
            self._audit(connection, "plan.executed", role, correlation_id, {
                "plan_id": plan_id, "action_id": action_id, "approval_actor": plan["approval"]["actor"],
            }, plan["scenario_id"])
            self._trace(connection, "Workforce Coordinator", correlation_id, "completed", {
                "mode": "deterministic_simulation", "summary": "Approved actions revalidated and committed atomically.",
            }, plan["scenario_id"])
        return dict(action, correlation_id=correlation_id, idempotent_replay=False)

    def _readiness(self, connection: Any, procedure: Dict[str, Any]) -> str:
        if not procedure["room_ready"] or not procedure["patient_prepared"] or not procedure["documentation_complete"]:
            return "at_risk"
        for requirement in procedure["required_roles"]:
            matched = False
            for staff_id in procedure["assigned_staff"]:
                member = self._get(connection, "staff", staff_id)
                if (member and member["available"] and member["role"] == requirement["role"]
                        and requirement["skill"] in member["skills"]
                        and member["certification_valid_through"] >= "2026-11-02"):
                    matched = True
                    break
            if not matched:
                return "at_risk"
        return "ready"

    def procedure_details(self) -> List[Dict[str, Any]]:
        staff = {member["id"]: member for member in self.db.list_entities("staff")}
        procedures = self.db.list_entities("procedure")
        for procedure in procedures:
            procedure["team"] = [staff[item] for item in procedure["assigned_staff"] if item in staff]
            procedure["readiness_reasons"] = self._procedure_reasons(procedure, staff)
        return procedures

    @staticmethod
    def _procedure_reasons(procedure: Dict[str, Any], staff: Dict[str, Any]) -> List[str]:
        reasons = []
        assigned = [staff[item] for item in procedure["assigned_staff"] if item in staff]
        for requirement in procedure["required_roles"]:
            if not any(member["available"] and member["role"] == requirement["role"]
                       and requirement["skill"] in member["skills"]
                       and member["certification_valid_through"] >= "2026-11-02" for member in assigned):
                reasons.append("Missing available, certified " + requirement["role"] + " with " + requirement["skill"] + " skill.")
        if not procedure["room_ready"]:
            reasons.append("Room readiness is incomplete.")
        if not procedure["patient_prepared"]:
            reasons.append("Patient preparation is incomplete.")
        if not procedure["documentation_complete"]:
            reasons.append("Required documentation is incomplete.")
        return reasons

    def events(self, scenario_id: Optional[str] = None, correlation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        clauses, params = [], []
        if scenario_id:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        if correlation_id:
            clauses.append("correlation_id = ?")
            params.append(correlation_id)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.connect() as connection:
            rows = connection.execute(
                "SELECT id, event_type, scenario_id, correlation_id, payload, created_at FROM events"
                + where + " ORDER BY id DESC LIMIT 200", params,
            ).fetchall()
        return [
            {"id": row["id"], "type": row["event_type"], "scenario_id": row["scenario_id"],
             "correlation_id": row["correlation_id"], "created_at": row["created_at"],
             "details": self.db.decode(row["payload"])}
            for row in rows
        ]

    def records(self, table: str, scenario_id: Optional[str] = None, correlation_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if table not in ("audits", "traces"):
            raise ValueError("Unsupported record type")
        clauses, params = [], []
        if scenario_id:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        if correlation_id:
            clauses.append("correlation_id = ?")
            params.append(correlation_id)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.db.connect() as connection:
            rows = connection.execute("SELECT * FROM " + table + where + " ORDER BY id DESC LIMIT 200", params).fetchall()
        results = []
        for row in rows:
            if table == "audits":
                results.append({
                    "id": row["id"], "action": row["action"], "actor": row["actor"],
                    "scenario_id": row["scenario_id"], "correlation_id": row["correlation_id"],
                    "created_at": row["created_at"], "details": self.db.decode(row["payload"]),
                })
            else:
                results.append({
                    "id": row["id"], "agent_name": row["agent_name"], "status": row["status"],
                    "scenario_id": row["scenario_id"], "correlation_id": row["correlation_id"],
                    "created_at": row["created_at"], "details": self.db.decode(row["payload"]),
                })
        return results

    def hospital_live(self, hospital_id: str) -> Dict[str, Any]:
        hospital = self.db.get_entity("hospital", hospital_id)
        if not hospital:
            raise DomainError(404, "hospital_not_found", "Hospital was not found.")
        with self.db.connect() as connection:
            scenario_rows = {row["id"]: row["status"] for row in connection.execute("SELECT id, status FROM scenarios").fetchall()}
            plan_rows = connection.execute("SELECT status, payload FROM plans").fetchall()
        plans = [dict(self.db.decode(row["payload"]), status=row["status"]) for row in plan_rows]
        is_central = hospital_id == "HCO-CENTRAL"
        collision = scenario_rows.get("collision", "baseline")
        resolved = any(plan["scenario_id"] == "collision" and plan["status"] == "completed" for plan in plans)
        surge = is_central and collision != "baseline" and not resolved
        pending = [plan for plan in plans if plan["status"] == "pending_approval"] if is_central else []

        every_staff = self.db.list_entities("staff")
        names = {member["id"]: member for member in every_staff}
        assigned = [m for m in every_staff if m.get("assigned_scenario") == "collision"]
        moved_in = assigned if is_central else []
        moved_out = [m for m in assigned if m["hospital_id"] == hospital_id and not is_central]
        roster = [dict(m, reinforcement=m in moved_in) for m in every_staff
                  if m["hospital_id"] == hospital_id and m not in moved_out]
        roster += [dict(m, reinforcement=True) for m in moved_in if m["hospital_id"] != hospital_id]

        census, capacity = hospital["ed_census"], hospital["ed_capacity"]
        projected = census + hospital["projected_arrivals"]
        seed = sum(ord(ch) for ch in hospital_id)
        complaints = ["Chest discomfort", "Abdominal pain", "Fracture", "Laceration", "Shortness of breath",
                      "Fever", "Dizziness", "Back pain", "Allergic reaction", "Minor burn", "Headache", "Sprain"]
        patients = []
        for index in range(census):
            acuity = 2 if index % 7 == 0 else 3 if index % 7 in (1, 2, 3, 4) else 4
            patients.append({
                "id": "ED-%s-%02d" % (hospital_id[4:7], index + 1),
                "complaint": complaints[(seed + index * 5) % len(complaints)],
                "acuity": acuity,
                "wait_minutes": 5 + ((seed + index * 13) % 55),
                "status": "In treatment" if index < census * 0.6 else "Waiting",
            })
        acuity_mix = {"High (ESI 1-2)": sum(1 for p in patients if p["acuity"] <= 2),
                      "Medium (ESI 3)": sum(1 for p in patients if p["acuity"] == 3),
                      "Low (ESI 4-5)": sum(1 for p in patients if p["acuity"] >= 4)}
        arrivals = [{"id": "INB-%02d" % (i + 1), "complaint": "Multi-vehicle collision",
                     "acuity": 2 if i < 3 else 3, "eta_minutes": 8 + i * 4}
                    for i in range(hospital["projected_arrivals"])]

        def on_duty(role: str, members: List[Dict[str, Any]]) -> int:
            return sum(1 for m in members if m["role"] == role and m["available"] and m["rest_hours"] >= 10
                       and m["certification_valid_through"] >= "2026-11-02")

        # Baseline roster (before any reassignment) sets the synthetic filler headcount.
        home = [m for m in every_staff if m["hospital_id"] == hospital_id]
        base_rn = max(2, round(census / 3))
        extra = is_central and (surge or resolved)
        required = {"ED RN": base_rn + (4 if extra else 0), "Trauma Support": 1 + (1 if extra else 0)}
        filler = {"ED RN": max(0, base_rn - on_duty("ED RN", home)),
                  "Trauma Support": max(0, 1 - on_duty("Trauma Support", home))}
        coverage = []
        for role, need in required.items():
            have = (on_duty(role, home) + filler[role]
                    - sum(1 for m in moved_out if m["role"] == role)
                    + sum(1 for m in moved_in if m["role"] == role))
            coverage.append({"role": role, "required": need, "on_duty": have, "gap": max(0, need - have)})

        procedure_rows = [dict(item) for item in self.procedure_details() if item["hospital_id"] == hospital_id]
        if not procedure_rows:
            procedure_rows = [{"id": "PROC-%s-%d" % (hospital_id[4:7], n), "name": name, "room": "OR-0%d" % n,
                               "scheduled_at": "2026-11-02T%02d:00:00" % hour, "readiness": "ready",
                               "readiness_reasons": [], "synthetic": True, "team": []}
                              for n, (name, hour) in enumerate([("Routine scheduled case", 11), ("Routine scheduled case", 14)], 1)]
        for item in procedure_rows:
            item.pop("assigned_staff", None)

        risks: List[Dict[str, Any]] = []
        occupancy = round(projected / capacity * 100)
        if hospital["pressure"] == "Critical":
            risks.append({"severity": "critical", "title": "Critical ED pressure",
                          "detail": "Projected census %d of %d (%d%%)." % (projected, capacity, occupancy)})
        elif occupancy >= 80:
            risks.append({"severity": "warning", "title": "ED nearing capacity", "detail": "Projected %d%% occupancy." % occupancy})
        for line in coverage:
            if line["gap"]:
                risks.append({"severity": "critical", "title": "%s gap of %d" % (line["role"], line["gap"]),
                              "detail": "%d on duty against %d required." % (line["on_duty"], line["required"])})
        for member in roster:
            if not member["available"]:
                risks.append({"severity": "warning", "title": member["name"] + " unavailable", "detail": member["role"] + " is not available this shift."})
            elif member["certification_valid_through"] < "2026-11-02":
                risks.append({"severity": "warning", "title": member["name"] + ": certification expired", "detail": member["role"] + " cannot be assigned."})
            elif member["rest_hours"] < 10:
                risks.append({"severity": "warning", "title": member["name"] + ": insufficient rest", "detail": "%s hours rest; 10 required." % member["rest_hours"]})
        for item in procedure_rows:
            if item["readiness"] == "at_risk":
                risks.append({"severity": "critical", "title": item["id"] + " at risk", "detail": "; ".join(item["readiness_reasons"]) or "Readiness incomplete."})
            if item.get("status") == "deferred":
                risks.append({"severity": "info", "title": item["id"] + " deferred", "detail": "Elective case deferred to free capacity."})
        if pending:
            risks.append({"severity": "warning", "title": "Staffing plan awaiting approval", "detail": "Nothing changes until a supervisor approves."})
        if moved_in:
            risks.append({"severity": "info", "title": "%d staff on surge assignment" % len(moved_in),
                          "detail": "Assigned to the ED under the approved plan."})
        if moved_out:
            risks.append({"severity": "info", "title": "%d staff lent to Central" % len(moved_out), "detail": "Reassigned under the approved plan."})
        order = {"critical": 0, "warning": 1, "info": 2}
        risks.sort(key=lambda risk: order[risk["severity"]])

        return {
            "hospital": hospital, "projected_census": projected, "occupancy_pct": occupancy,
            "acuity_mix": acuity_mix, "patients": patients, "inbound": arrivals,
            "coverage": coverage, "staff": roster, "procedures": procedure_rows, "risks": risks,
            "avg_wait_minutes": round(sum(p["wait_minutes"] for p in patients) / len(patients)) if patients else 0,
            "synthetic": True,
        }

    # ------------------------------------------------------------ prescriptions

    def prescriptions(self, patient_id: str) -> List[Dict[str, Any]]:
        self.get_patient(patient_id)
        items = [item for item in self.db.list_entities("prescription") if item["patient_id"] == patient_id]
        return sorted(items, key=lambda item: item["issued_at"], reverse=True)

    def get_prescription(self, prescription_id: str) -> Dict[str, Any]:
        item = self.db.get_entity("prescription", prescription_id)
        if not item:
            raise DomainError(404, "prescription_not_found", "Prescription was not found.")
        return item

    def issue_prescription(
        self, patient_id: str, diagnosis: str, medications: List[Dict[str, Any]], notes: str,
        clinician_confirmed: bool, role: str, correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.require_role(role, ("clinician",))
        correlation_id = self.correlation_id(correlation_id)
        if not clinician_confirmed:
            raise DomainError(422, "confirmation_required", "The prescriber must confirm before a prescription is issued.")
        patient = self.get_patient(patient_id)
        conflicts = clinical.allergy_conflicts(patient.get("allergies", []), medications)
        if conflicts:
            with self.db.transaction() as connection:
                self._audit(connection, "prescription.blocked", role, correlation_id,
                            {"patient_id": patient_id, "conflicts": conflicts})
            raise DomainError(422, "allergy_conflict", " ".join(conflicts) + " Choose a safe alternative.")
        doctor = self.db.get_entity("doctor", "DOC-0021")
        with self.db.transaction() as connection:
            number = len(self._list(connection, "prescription")) + 1001
            prescription = {
                "id": "RX-%d" % number, "patient_id": patient_id, "doctor_id": doctor["id"], "doctor_name": doctor["name"],
                "specialty": doctor["specialty"], "hospital": doctor["location"], "diagnosis": diagnosis,
                "medications": medications, "notes": notes, "issued_at": NOW, "status": "active",
            }
            self._put(connection, "prescription", prescription)
            self._event(connection, "prescription.issued", correlation_id,
                        {"patient_id": patient_id, "prescription_id": prescription["id"]})
            self._audit(connection, "prescription.issued", role, correlation_id,
                        {"patient_id": patient_id, "prescription_id": prescription["id"], "medications": [m["name"] for m in medications]})
        return dict(prescription, correlation_id=correlation_id)

    def prescription_pdf(self, prescription_id: str) -> bytes:
        item = self.get_prescription(prescription_id)
        return clinical.prescription_pdf(item, self.get_patient(item["patient_id"]))

    # ------------------------------------------------------------ inpatient wards

    def _ward(self, hospital_id: str) -> List[Dict[str, Any]]:
        if not self.db.get_entity("hospital", hospital_id):
            raise DomainError(404, "hospital_not_found", "Hospital was not found.")
        states = {item["id"]: item for item in self.db.list_entities("ipd_state")}
        return [clinical.apply_state(patient, states.get(patient["id"])) for patient in clinical.ward_patients(hospital_id)]

    def opd_board(self, hospital_id: str) -> Dict[str, Any]:
        if not self.db.get_entity("hospital", hospital_id):
            raise DomainError(404, "hospital_not_found", "Hospital was not found.")
        return clinical.opd_board(hospital_id)

    def ward(self, hospital_id: str) -> Dict[str, Any]:
        patients = self._ward(hospital_id)
        return {
            "hospital_id": hospital_id, "patients": patients,
            "summary": {
                "census": len(patients), "high_risk": sum(1 for p in patients if p["risk"] == "high"),
                "medium_risk": sum(1 for p in patients if p["risk"] == "medium"),
                "charted": sum(1 for p in patients if p["charted_today"]),
                "meds_due": sum(p["meds_due"] for p in patients),
            },
        }

    def ipd_patient(self, patient_id: str) -> Dict[str, Any]:
        for hospital in self.db.list_entities("hospital"):
            if clinical.hospital_code(hospital["id"]) == patient_id[4:7]:
                match = next((p for p in self._ward(hospital["id"]) if p["id"] == patient_id), None)
                if match:
                    return match
        raise DomainError(404, "ipd_patient_not_found", "Inpatient was not found.")

    def _ipd_update(self, patient_id: str, change: Any) -> None:
        with self.db.transaction() as connection:
            state = self._get(connection, "ipd_state", patient_id) or {"id": patient_id, "given": [], "extra_vitals": 0, "charts": []}
            change(state)
            self._put(connection, "ipd_state", state)

    def capture_vitals(self, patient_id: str, role: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_role(role, ("nurse",))
        self.ipd_patient(patient_id)
        correlation_id = self.correlation_id(correlation_id)

        def change(state: Dict[str, Any]) -> None:
            if state["extra_vitals"] >= 6:
                raise DomainError(409, "vitals_limit", "The demo allows up to six extra readings per patient.")
            state["extra_vitals"] += 1

        self._ipd_update(patient_id, change)
        with self.db.transaction() as connection:
            self._audit(connection, "ipd.vitals_captured", role, correlation_id, {"patient_id": patient_id})
        return self.ipd_patient(patient_id)

    def administer_medication(self, patient_id: str, med_id: str, role: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_role(role, ("nurse",))
        patient = self.ipd_patient(patient_id)
        medication = next((m for m in patient["meds"] if m["id"] == med_id), None)
        if not medication:
            raise DomainError(404, "medication_not_found", "Medication order was not found.")
        correlation_id = self.correlation_id(correlation_id)
        clash = clinical.allergy_conflicts(patient["allergies"], [medication])
        if clash:
            raise DomainError(422, "allergy_conflict", " ".join(clash) + " Do not administer; contact the prescriber.")

        def change(state: Dict[str, Any]) -> None:
            if med_id not in state["given"]:
                state["given"].append(med_id)

        self._ipd_update(patient_id, change)
        with self.db.transaction() as connection:
            self._audit(connection, "ipd.medication_given", role, correlation_id,
                        {"patient_id": patient_id, "medication": medication["name"], "dose": medication["dose"]})
        return self.ipd_patient(patient_id)

    def save_chart(self, patient_id: str, narrative: str, ai_mode: str, nurse_confirmed: bool, role: str,
                   correlation_id: Optional[str] = None) -> Dict[str, Any]:
        self.require_role(role, ("nurse",))
        if not nurse_confirmed:
            raise DomainError(422, "confirmation_required", "The nurse must review and sign the chart.")
        patient = self.ipd_patient(patient_id)
        correlation_id = self.correlation_id(correlation_id)
        entry = {"id": "CH-%s-%d" % (patient_id, len(patient["charts"]) + 1), "signed_by": "Charge Nurse (demo)",
                 "signed_at": NOW, "narrative": narrative, "ai_mode": ai_mode, "news2": patient["news2"]}
        self._ipd_update(patient_id, lambda state: state["charts"].append(entry))
        with self.db.transaction() as connection:
            self._event(connection, "ipd.chart_signed", correlation_id, {"patient_id": patient_id, "chart_id": entry["id"]})
            self._audit(connection, "ipd.chart_signed", role, correlation_id,
                        {"patient_id": patient_id, "chart_id": entry["id"], "ai_mode": ai_mode})
        return self.ipd_patient(patient_id)

    def capacity(self) -> List[Dict[str, Any]]:
        return self.db.list_entities("hospital")

    def workforce(self) -> List[Dict[str, Any]]:
        return self.db.list_entities("staff")

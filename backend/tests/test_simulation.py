import pytest

from app.database import Database
from app.services import DomainError, Simulation
from app.agents import AGENT_SPECS


@pytest.fixture
def simulation(tmp_path):
    database = Database(str(tmp_path / "test.sqlite3"))
    return Simulation(database)


def test_reset_is_deterministic_and_seeds_linked_scenarios(simulation):
    initial = simulation.state()
    assert initial["counts"] == {
        "hospital": 12,
        "patient": 1,
        "doctor": 2,
        "slot": 2,
        "staff": 12,
        "procedure": 3,
    }

    initial_ids = [item["id"] for item in simulation.db.list_entities("hospital")]
    simulation.reset()
    second = simulation.state()
    assert second["counts"] == initial["counts"]
    assert [item["id"] for item in simulation.db.list_entities("hospital")] == initial_ids
    assert simulation.get_patient("PAT-1001")["name"] == "Alex Morgan"
    assert next(item for item in simulation.procedure_details() if item["id"] == "PROC-310")["readiness"] == "ready"


def test_safety_gate_stops_routine_access(simulation):
    result = simulation.safety_screen(True, "safety-correlation")
    assert result["safe_to_schedule"] is False
    assert simulation.db.list_entities("appointment") == []
    assert simulation.events(correlation_id="safety-correlation")[0]["type"] == "patient.safety_escalated"
    with pytest.raises(DomainError) as blocked:
        simulation.book_appointment("PAT-1001", "SLOT-IMMEDIATE-01", True, "unsafe-booking", "patient")
    assert blocked.value.code == "safety_screen_required"


def test_booking_requires_confirmation_and_is_idempotent(simulation):
    with pytest.raises(DomainError) as unscreened:
        simulation.book_appointment("PAT-1001", "SLOT-IMMEDIATE-01", True, "unscreened", "patient")
    assert unscreened.value.code == "safety_screen_required"
    with pytest.raises(DomainError) as error:
        simulation.book_appointment("PAT-1001", "SLOT-IMMEDIATE-01", False, "booking-a", "patient")
    assert error.value.code == "confirmation_required"

    simulation.safety_screen(False)
    booking = simulation.book_appointment(
        "PAT-1001", "SLOT-IMMEDIATE-01", True, "booking-a", "patient", "booking-correlation"
    )
    replay = simulation.book_appointment(
        "PAT-1001", "SLOT-IMMEDIATE-01", True, "booking-a", "patient"
    )
    assert booking["id"] == "APT-DEMO-0001"
    assert replay["id"] == booking["id"]
    assert replay["idempotent_replay"] is True
    assert len(simulation.db.list_entities("appointment")) == 1
    with pytest.raises(DomainError) as conflict:
        simulation.book_appointment("PAT-1001", "SLOT-IMMEDIATE-01", True, "booking-b", "patient")
    assert conflict.value.status_code == 409


def test_virtual_session_lifecycle_and_confirmation_barrier(simulation):
    with pytest.raises(DomainError) as invalid:
        simulation.create_virtual_session("APT-UNKNOWN", True, "patient")
    assert invalid.value.status_code == 422

    simulation.safety_screen(False)
    appointment = simulation.book_appointment(
        "PAT-1001", "SLOT-IMMEDIATE-01", True, "booking-session", "patient"
    )
    with pytest.raises(DomainError) as missing_confirmation:
        simulation.create_virtual_session(appointment["id"], False, "patient")
    assert missing_confirmation.value.code == "confirmation_required"

    session = simulation.create_virtual_session(appointment["id"], True, "patient")
    with pytest.raises(DomainError) as early_complete:
        simulation.complete_virtual_session(session["id"], "patient")
    assert early_complete.value.status_code == 409
    assert simulation.advance_virtual_session(session["id"], "patient")["status"] == "doctor_connected"
    assert simulation.advance_virtual_session(session["id"], "patient")["status"] == "in_consultation"
    completed = simulation.complete_virtual_session(session["id"], "patient")
    assert completed["status"] == "completed"
    assert len(simulation.db.list_entities("follow_up")) == 1


def test_collision_plan_is_grounded_and_requires_approval(simulation):
    result = simulation.trigger_scenario("collision", "presenter", "collision-correlation")
    assert result["rn_gap"] == 4
    assert result["trauma_support_gap"] == 1
    candidates = simulation.collision_candidates()
    assert {item["id"] for item in candidates["eligible"]} == {
        "STF-C-011", "STF-C-012", "STF-N-021", "STF-W-018", "STF-N-032"
    }
    assert {item["id"]: item["reason"] for item in candidates["excluded"]} == {
        "STF-W-077": "Required certification expired.",
        "STF-C-099": "Insufficient rest before the proposed shift.",
        "STF-N-040": "Staff member is unavailable.",
    }
    plan = simulation.create_plan("collision", [], True, "presenter", "plan-correlation")
    assert plan["status"] == "pending_approval"
    assert simulation.db.get_entity("staff", "STF-C-011").get("assigned_scenario") is None
    assert simulation.db.get_entity("procedure", "PROC-220").get("status") is None

    with pytest.raises(DomainError) as unauthorized:
        simulation.execute_plan(plan["id"], "execute-before-approval", "supervisor")
    assert unauthorized.value.code == "approval_required"
    simulation.decide_plan(plan["id"], "approved", "Reviewed evidence.", "supervisor")
    action = simulation.execute_plan(plan["id"], "collision-execute", "supervisor")
    assert action["status"] == "completed"
    assert simulation.db.get_entity("procedure", "PROC-220")["status"] == "deferred"
    assert simulation.db.get_entity("procedure", "PROC-221").get("status") is None
    assert simulation.db.get_entity("staff", "STF-C-011")["assigned_scenario"] == "collision"


def test_rejection_does_not_change_assignments(simulation):
    simulation.trigger_scenario("collision", "presenter")
    plan = simulation.create_plan("collision", [], True, "presenter")
    simulation.decide_plan(plan["id"], "rejected", "Do not proceed.", "supervisor")
    assert simulation.db.get_entity("staff", "STF-C-011").get("assigned_scenario") is None
    assert simulation.db.get_entity("procedure", "PROC-220").get("status") is None
    with pytest.raises(DomainError):
        simulation.execute_plan(plan["id"], "rejected-execute", "supervisor")


def test_procedure_absence_recovers_after_approved_replacement(simulation):
    procedure = next(item for item in simulation.procedure_details() if item["id"] == "PROC-310")
    assert procedure["readiness"] == "ready"
    simulation.trigger_scenario("procedure-absence", "presenter")
    procedure = next(item for item in simulation.procedure_details() if item["id"] == "PROC-310")
    assert procedure["readiness"] == "at_risk"
    candidates = simulation.procedure_candidates()
    assert [item["id"] for item in candidates["eligible"]] == ["STF-N-044"]
    assert candidates["excluded"][0]["reason"] == "Required certification expired."

    plan = simulation.create_plan("procedure-absence", ["STF-N-044"], False, "presenter")
    simulation.decide_plan(plan["id"], "approved", "Qualified replacement.", "supervisor")
    simulation.execute_plan(plan["id"], "procedure-execute", "supervisor")
    procedure = next(item for item in simulation.procedure_details() if item["id"] == "PROC-310")
    assert procedure["readiness"] == "ready"
    assert "STF-N-044" in procedure["assigned_staff"]


def test_execution_revalidates_eligibility_without_partial_mutation(simulation):
    simulation.trigger_scenario("collision", "presenter")
    plan = simulation.create_plan("collision", ["STF-C-011"], False, "presenter")
    simulation.decide_plan(plan["id"], "approved", "Reviewed evidence.", "supervisor")
    with simulation.db.transaction() as connection:
        candidate = simulation._get(connection, "staff", "STF-C-011")
        candidate["available"] = False
        simulation._put(connection, "staff", candidate)

    with pytest.raises(DomainError) as ineligible:
        simulation.execute_plan(plan["id"], "stale-candidate", "supervisor")
    assert ineligible.value.code == "eligibility_changed"
    assert simulation.db.list_entities("action") == []
    assert simulation.db.get_entity("staff", "STF-C-011").get("assigned_scenario") is None


def test_replacement_does_not_override_other_readiness_blockers(simulation):
    simulation.trigger_scenario("procedure-absence", "presenter")
    with simulation.db.transaction() as connection:
        procedure = simulation._get(connection, "procedure", "PROC-310")
        procedure["room_ready"] = False
        simulation._put(connection, "procedure", procedure)

    plan = simulation.create_plan("procedure-absence", ["STF-N-044"], False, "presenter")
    simulation.decide_plan(plan["id"], "approved", "Replacement reviewed.", "supervisor")
    simulation.execute_plan(plan["id"], "replacement-room-blocker", "supervisor")
    procedure = next(item for item in simulation.procedure_details() if item["id"] == "PROC-310")
    assert procedure["readiness"] == "at_risk"
    assert "Room readiness is incomplete." in procedure["readiness_reasons"]


def test_role_and_invalid_candidate_are_rejected(simulation):
    with pytest.raises(DomainError) as role_error:
        simulation.trigger_scenario("collision", "patient")
    assert role_error.value.status_code == 403
    simulation.trigger_scenario("collision", "presenter")
    with pytest.raises(DomainError) as candidate_error:
        simulation.create_plan("collision", ["STF-W-077"], False, "presenter")
    assert candidate_error.value.code == "ineligible_candidate"


def test_agent_specifications_are_named_and_have_separate_tool_allowlists():
    names = [name for name, _, _ in AGENT_SPECS]
    assert len(names) == 12
    assert len(set(names)) == 12
    assert all(tools for _, _, tools in AGENT_SPECS)
    assert len({tuple(tools) for _, _, tools in AGENT_SPECS}) == 12


def test_hospital_live_reflects_surge_and_plan(simulation):
    baseline = simulation.hospital_live("HCO-CENTRAL")
    assert all(line["gap"] == 0 for line in baseline["coverage"])
    assert len(baseline["patients"]) == baseline["hospital"]["ed_census"]
    simulation.trigger_scenario("collision", "presenter", "live-corr")
    surge = simulation.hospital_live("HCO-CENTRAL")
    assert {line["role"]: line["gap"] for line in surge["coverage"]} == {"ED RN": 4, "Trauma Support": 1}
    assert len(surge["inbound"]) == 8
    plan = simulation.create_plan("collision", [], True, "presenter", "live-plan")
    simulation.decide_plan(plan["id"], "approved", "ok", "supervisor")
    simulation.execute_plan(plan["id"], "live-exec", "supervisor")
    after = simulation.hospital_live("HCO-CENTRAL")
    assert all(line["gap"] == 0 for line in after["coverage"])
    assert any(item.get("status") == "deferred" for item in after["procedures"])
    assert simulation.hospital_live("HCO-NORTH")["synthetic"] is True

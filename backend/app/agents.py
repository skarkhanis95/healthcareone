import asyncio
import os
import re
from typing import Any, Callable, Dict, List, Optional


AGENT_SPECS = [
    ("Experience Coordinator", "Routes patient requests to safe patient-access workflows.", ["get_patient_context", "screen_emergency_red_flags"]),
    ("Operations Intelligence Coordinator", "Coordinates read-only operations evidence and stops for approval.", ["get_hospital_capacity", "get_procedure_details"]),
    ("Patient Access Agent", "Finds synthetic care options after deterministic safety screening.", ["get_patient_context", "search_doctors", "get_doctor_availability"]),
    ("Patient Journey Agent", "Reads synthetic appointments and journey events.", ["get_patient_journey", "get_patient_appointments"]),
    ("Virtual Care Agent", "Reads virtual-care availability and session state.", ["check_virtual_session_availability", "get_virtual_session_status"]),
    ("Patient Flow Agent", "Reads hospital capacity and simulated arrival events.", ["get_hospital_capacity", "get_arrival_events"]),
    ("Workforce Demand Agent", "Reads deterministic staffing requirements and gaps.", ["get_staffing_requirements", "calculate_staffing_gap"]),
    ("Staff Availability Agent", "Retrieves staff availability and shift evidence.", ["search_available_staff", "get_staff_shift"]),
    ("Skills Matching Agent", "Checks role skills and certification evidence.", ["match_staff_skills", "check_certification_validity"]),
    ("Fatigue & Compliance Agent", "Checks deterministic workload and rest constraints.", ["check_staff_constraints", "get_deployment_policy"]),
    ("Procedure Readiness Agent", "Evaluates required team and procedure readiness.", ["get_procedure_details", "evaluate_procedure_readiness"]),
    ("Workforce Coordinator", "Prepares proposals and reads approval/action status.", ["create_augmentation_plan", "get_augmentation_plan"]),
]

_adk_agents: Optional[Dict[str, Any]] = None
_adk_import_error: Optional[str] = None


def _patient_access_snapshot() -> Dict[str, Any]:
    from .main import database, simulation

    screen = database.get_entity("access_screen", "PAT-1001")
    return {
        "patient": simulation.get_patient("PAT-1001"),
        "safety_screen_complete": bool(screen and screen["safe_to_schedule"]),
        "available_options": simulation.availability(specialty="Orthopaedics")
        if screen and screen["safe_to_schedule"] else [],
    }


def _tool_for_agent(name: str) -> Callable[[], Dict[str, Any]]:
    def read_synthetic_healthcareone_data() -> Dict[str, Any]:
        if name in ("Patient Access Agent", "Experience Coordinator"):
            return _patient_access_snapshot()
        from .main import simulation

        return {
            "simulation_time": "2026-11-02T09:00:00",
            "hospitals": simulation.capacity(),
            "procedures": simulation.procedure_details(),
        }

    read_synthetic_healthcareone_data.__name__ = "read_synthetic_healthcareone_data"
    read_synthetic_healthcareone_data.__doc__ = (
        "Read synthetic, deterministic HealthCareOne demo facts. Never create or change records."
    )
    return read_synthetic_healthcareone_data


def get_adk_agents() -> Dict[str, Any]:
    global _adk_agents, _adk_import_error
    if _adk_agents is not None:
        return _adk_agents
    try:
        from google.adk.agents import Agent
    except ImportError as error:
        _adk_import_error = str(error)
        return {}
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    _adk_agents = {
        name: Agent(
            name=re.sub(r"[^a-zA-Z0-9]+", "_", name.lower()).strip("_"),
            model=model,
            description=description,
            instruction=(
                description + " Use only supplied tool evidence. Do not diagnose, invent entities, "
                "claim that an action succeeded, or mutate state."
            ),
            tools=[_tool_for_agent(name)],
        )
        for name, description, _ in AGENT_SPECS
    }
    return _adk_agents


def runtime_status() -> Dict[str, Any]:
    agents = get_adk_agents()
    key_configured = bool(os.environ.get("GOOGLE_API_KEY"))
    return {
        "provider": "Google ADK + Gemini",
        "configured": bool(agents) and key_configured,
        "package_available": bool(agents),
        "api_key_configured": key_configured,
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        "agent_count": len(agents),
        "specification_count": len(AGENT_SPECS),
        "agents": [
            {"name": name, "tools": tools}
            for name, _, tools in AGENT_SPECS
        ],
        "unavailable_reason": None if agents and key_configured else (
            "GOOGLE_API_KEY is not configured." if not key_configured
            else "Google ADK is not installed for this Python environment."
        ),
    }


async def run_live_smoke() -> Dict[str, Any]:
    return await asyncio.wait_for(_run_live_smoke(), timeout=30)


async def _run_live_smoke() -> Dict[str, Any]:
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is not configured.")
    agents = get_adk_agents()
    if not agents:
        raise RuntimeError("Google ADK is unavailable in this Python environment.")
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
    except ImportError as error:
        raise RuntimeError("Google ADK runtime dependencies are unavailable.") from error

    agent = agents["Patient Access Agent"]
    app_name, user_id = "healthcareone_demo", "synthetic_patient"
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=session_service)
    message = types.Content(
        role="user",
        parts=[types.Part(text="Use your read-only tool to summarize the available synthetic appointment options.")],
    )
    tool_calls: List[str] = []
    summary = ""
    async for event in runner.run_async(
        user_id=user_id, session_id=session.id, new_message=message
    ):
        if getattr(event, "content", None):
            for part in getattr(event.content, "parts", []) or []:
                function_call = getattr(part, "function_call", None)
                if function_call and getattr(function_call, "name", None):
                    tool_calls.append(function_call.name)
                text = getattr(part, "text", None)
                if text:
                    summary += text
    if not tool_calls:
        raise RuntimeError("Gemini completed without invoking the required read-only tool.")
    return {
        "live": True,
        "agent": agent.name,
        "tool_calls": tool_calls,
        "summary": summary[:1000],
        "model": os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
    }

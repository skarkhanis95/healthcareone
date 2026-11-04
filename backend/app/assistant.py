"""Patient access assistant: deterministic safety guard plus intent classification."""
import asyncio
import json
import os
import re
from typing import Any, Dict, Optional

SUPPORTED_INTENTS = ("book_appointment", "virtual_consult")

UNSUPPORTED_REPLY = (
    "I'm still learning, so I can't help with that yet. Right now I can help you book an "
    "appointment or arrange a virtual consult. Try something like \"I need an orthopaedic "
    "doctor this week\" or \"Can I see a doctor by video today?\""
)

SAFETY_REPLY = (
    "What you describe may be urgent. I can't help with that through scheduling, and I haven't booked "
    "anything. Please contact local emergency services or a qualified clinician right away."
)

RED_FLAG_PATTERN = re.compile(
    r"chest pain|chest tightness|can'?t breathe|cannot breathe|trouble breathing|difficulty breathing|"
    r"short(ness)? of breath|heart attack|stroke|face droop|slurred speech|unconscious|passed out|"
    r"not responding|severe bleeding|bleeding (heavily|a lot|badly)|won'?t stop bleeding|seizure|"
    r"overdose|poison|suicid|kill myself|self[- ]harm|want to die|anaphyla|allergic reaction|"
    r"emergency|severe pain|head injury|choking|open fracture|bone (is )?(sticking|poking)",
    re.IGNORECASE,
)
VIRTUAL_PATTERN = re.compile(
    r"virtual|video|online|tele ?health|tele ?medicine|remote|from home|over (a |the )?call|phone consult",
    re.IGNORECASE,
)
IN_PERSON_PATTERN = re.compile(r"in[- ]person|face[- ]to[- ]face|visit the clinic|come in", re.IGNORECASE)
BOOKING_PATTERN = re.compile(
    r"\bbook|appointment|schedule|\bsee (a|an|the|my)\b|\bdoctor\b|\bconsult|specialist|\bvisit\b|"
    r"\bslot|availab|check[- ]?up|\bappt\b",
    re.IGNORECASE,
)
ORTHO_PATTERN = re.compile(
    r"orthop|\bbone|\bknee|\bjoint|fracture|back pain|\bshoulder|\bhip\b|\bankle|\bspine|sprain|"
    r"\bwrist|\bmusculo",
    re.IGNORECASE,
)
OTHER_SPECIALTY_PATTERN = re.compile(
    r"cardio|\bheart\b|dermat|\bskin\b|\beye\b|ophthal|dentist|dental|pediatric|paediatric|gyn|"
    r"pregnan|\bent\b|psychiat|psycholog|mental health|neuro|migraine|oncolog|urolog|diabet|"
    r"\bcancer|lab test|blood test|prescription|refill|insurance|billing",
    re.IGNORECASE,
)


def is_red_flag(text: str) -> bool:
    return bool(RED_FLAG_PATTERN.search(text))


def classify_keywords(text: str) -> Dict[str, Any]:
    """Deterministic intent classification used when live AI is unavailable."""
    wants_virtual = bool(VIRTUAL_PATTERN.search(text))
    wants_in_person = bool(IN_PERSON_PATTERN.search(text))
    ortho = bool(ORTHO_PATTERN.search(text))
    if OTHER_SPECIALTY_PATTERN.search(text) and not ortho:
        intent = "unsupported"
    elif wants_virtual and (BOOKING_PATTERN.search(text) or ortho):
        intent = "virtual_consult"
    elif BOOKING_PATTERN.search(text) or ortho:
        intent = "book_appointment"
    else:
        intent = "unsupported"
    preferred_mode = "virtual" if wants_virtual else ("in_person" if wants_in_person else "any")
    return {"intent": intent, "preferred_mode": preferred_mode, "classifier": "keyword_rules"}


_classifier_agent: Optional[Any] = None

CLASSIFIER_INSTRUCTION = (
    "You classify one patient message for a scheduling assistant. Reply with a single JSON object and "
    "nothing else, using exactly these keys: "
    '{"intent": "book_appointment" | "virtual_consult" | "unsupported", '
    '"specialty": "orthopaedics" | "none" | "other", "preferred_mode": "virtual" | "in_person" | "any"}. '
    "book_appointment: the patient wants to find or book an appointment. virtual_consult: the patient wants "
    "a video, online or virtual consultation. unsupported: anything else, including medical advice, billing, "
    "prescriptions or chit-chat. Use specialty other when a non-orthopaedic specialty is requested. "
    "Never give medical advice."
)


def _get_classifier() -> Optional[Any]:
    global _classifier_agent
    if _classifier_agent is not None:
        return _classifier_agent
    try:
        from google.adk.agents import Agent
    except ImportError:
        return None
    _classifier_agent = Agent(
        name="patient_intent_classifier",
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        description="Classifies patient scheduling requests.",
        instruction=CLASSIFIER_INSTRUCTION,
    )
    return _classifier_agent


async def classify_live(text: str) -> Dict[str, Any]:
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    agent = _get_classifier()
    if agent is None:
        raise RuntimeError("Google ADK is unavailable in this Python environment.")
    app_name, user_id = "healthcareone_assistant", "synthetic_patient"
    service = InMemorySessionService()
    session = await service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=agent, app_name=app_name, session_service=service)
    message = types.Content(role="user", parts=[types.Part(text=text)])
    output = ""
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
        for part in getattr(getattr(event, "content", None), "parts", None) or []:
            if getattr(part, "text", None):
                output += part.text
    match = re.search(r"\{.*\}", output, re.DOTALL)
    if not match:
        raise RuntimeError("The model did not return a classification.")
    parsed = json.loads(match.group(0))
    intent = parsed.get("intent")
    if intent not in SUPPORTED_INTENTS + ("unsupported",):
        raise RuntimeError("The model returned an unknown intent.")
    if parsed.get("specialty") == "other":
        intent = "unsupported"
    mode = parsed.get("preferred_mode")
    if mode not in ("virtual", "in_person", "any"):
        mode = "any"
    return {"intent": intent, "preferred_mode": mode, "classifier": "gemini"}


async def classify(text: str, live_available: bool) -> Dict[str, Any]:
    """Return classification plus the mode that produced it; never raises for AI failures."""
    keyword = classify_keywords(text)
    if not live_available:
        return dict(keyword, mode="deterministic_simulation", fallback_reason="AI is not configured.")
    try:
        result = await asyncio.wait_for(classify_live(text), timeout=15)
        return dict(result, mode="live_gemini", fallback_reason=None)
    except Exception as error:  # AI failure must degrade to deterministic rules, not break the chat
        return dict(keyword, mode="deterministic_simulation",
                    fallback_reason="Live AI failed (%s); used rule-based understanding." % type(error).__name__)

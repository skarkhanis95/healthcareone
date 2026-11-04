# HealthCareOne

A local, demonstration-grade simulation of the CareFlow One patient experience and Workforce One operations platform. Every patient, clinician, staff member, hospital, appointment, procedure and operational action in the seeded dataset is synthetic. The application does not connect to real healthcare systems or perform real-world actions.

## Requirements

- Python 3.10 or later (the Google ADK runtime requires Python 3.10+)
- Node.js 18 or later and npm
- A Google Gemini API key only for the optional live ADK smoke test

The backend's deterministic simulation and tests do not require a Google key or network access. The live ADK integration is deliberately reported as unavailable until both the ADK package and `GOOGLE_API_KEY` are configured.

## Local setup

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
```

The venv must be active (`source .venv/bin/activate` from the project root) in any terminal that runs the API. Live Gemini via Google ADK needs Python 3.10+.

In one terminal, start the API:

```bash
source .venv/bin/activate
cd backend
set -a
source ../.env
set +a
python -m uvicorn app.main:app --reload
```

In another terminal, install and start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> for the launch dashboard. Each card opens a separate experience in its own tab: `/patient`, `/clinician`, `/hospital`, `/workforce` and `/director`. API health and OpenAPI docs are available at <http://localhost:8000/health> and <http://localhost:8000/docs>.

The SQLite database is initialized and seeded on first startup. It is stored at `backend/healthcareone.db` by default; set `HEALTHCAREONE_DB` to change that path.

## Run and verify

```bash
# Backend tests
python -m pytest backend/tests -q

# Frontend checks
cd frontend
npm run typecheck
npm run build
```

To restore the deterministic baseline, open `/director` and use **Reset all data**. The API equivalent is:

```bash
curl -X POST http://localhost:8000/api/v1/simulation/reset \
  -H 'X-Demo-Role: presenter'
```

Reset removes scenario-owned bookings, virtual sessions, plans, actions, events, traces and audit entries, then restores the stable seed fixture.

## Optional live Google ADK / Gemini smoke

Install the extra dependency set in Python 3.10+ and configure the key in the process environment. The backend and Google ADK dependency pins are aligned; use the project virtual environment for both. Never put a real key in source control or the UI.

```bash
python -m pip install -r backend/requirements-ai.txt
export GOOGLE_API_KEY='your-key'
export GEMINI_MODEL='gemini-2.0-flash'
```

With the backend running, use Demo Director → **Run live Gemini tool smoke** or:

```bash
curl -X POST http://localhost:8000/api/v1/ai/smoke \
  -H 'X-Demo-Role: presenter'
```

This makes a real ADK/Gemini model request with a 30-second timeout and requires an actual read-only synthetic-data tool call. A missing key, missing ADK package, timeout, provider error or response without a tool call is returned as an error; it is never reported as a successful AI run. No prompt, API key or private model reasoning is stored in the trace.

## Demonstration flows

1. **Patient access:** open `/patient` and type a request in your own words, such as "I need an orthopaedic doctor this week" or "Can I see a doctor by video today?". The assistant understands book-appointment and virtual-consult requests (Gemini via ADK when a key is set, deterministic keyword rules otherwise; each reply is labelled LIVE AI or SIMULATION). Anything else gets an "I'm still learning" reply. A deterministic safety check runs on every message first: urgent symptoms stop scheduling and nothing is booked. The patient chooses a slot, confirms, and for virtual slots can start and end a simulated visit.
2. **Collision response:** open `/workforce` as Operations planner, trigger the collision, review the fixed 4-RN / 1-trauma-support gap and candidate exclusions, and submit a plan. Switch to Supervisor in the same page to approve or reject. Only approval followed by service-side eligibility revalidation can commit simulated assignments. Watch `/hospital` update live.
3. **Procedure recovery:** on `/workforce`, pick Procedure recovery, trigger the staff absence for `PROC-310`, inspect candidate evidence, and submit a replacement. Approve as Supervisor; execution revalidates the replacement and recomputes readiness.

All experiences read the same persisted SQLite state and refresh each other across tabs. Events, traces and audit summaries are in `/director`. Each experience fixes its own demo role; this is a demonstration affordance, not production authentication. See [docs/demo-runbook.md](docs/demo-runbook.md) for the presenter script.

## Scope and known limitations

- Google ADK is optional for local deterministic tests. Without it and a configured key, the UI explicitly shows AI as offline; scenario recommendations remain deterministic and are not represented as live AI output.
- Scenario progression uses a fixed simulation clock. Operational updates are refreshed from the API by polling; no external systems, WebSocket service, real video, messaging or staff deployment are used.
- This is a compact vertical slice of the supplied implementation plan, not a production clinical, scheduling, HR or workforce system. Do not use the synthetic fixture values as clinical or employment policy.
- The project pins direct Python and frontend dependencies. This workspace did not include Node.js, so npm lockfile generation, frontend typecheck/build and browser E2E could not be run here.

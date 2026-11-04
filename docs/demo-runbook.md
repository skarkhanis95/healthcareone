# HealthCareOne Demo Runbook

For the presenter: what to run, which windows to open, and how to explain each scenario to a client.

## 1. The message

HealthCareOne simulates two connected platforms on one shared data set:

- **CareFlow One** (patient access): the patient app and the clinician workspace.
- **Workforce One** (operations): hospital command, workforce planning and approvals.

> AI understands and recommends. Deterministic policy decides what is safe and eligible. Humans approve. Everything is audited.

All data is fictional. Nothing connects to real systems.

## 2. Start the app

Terminal 1, backend:

```bash
cd ~/Downloads/Code/HealthCareOne
source .venv/bin/activate
cd backend
set -a; source ../.env; set +a
python -m uvicorn app.main:app --reload
```

Terminal 2, frontend:

```bash
cd ~/Downloads/Code/HealthCareOne/frontend
npm run dev
```

## 3. Windows to open

Open <http://localhost:5173>. This is the **launch dashboard**; it shows whether the backend and AI are connected. Each card opens its own tab:

| Tab | URL | Audience / role | Use it for |
|---|---|---|---|
| Launcher | `/` | You | Starting point and status |
| Demo Director | `/director` | You (presenter screen) | Reset, trigger, live events, audit, agent traces, AI smoke test |
| Patient app | `/patient` | Client sees this | Typing requests, booking, virtual visit |
| Clinician workspace | `/clinician` | Client sees this | Patient journey updating live |
| Hospital command | `/hospital` | Client sees this | Capacity, gaps, procedures at risk |
| Workforce & approvals | `/workforce` | Client sees this | Candidates, plans, supervisor approval |

Suggested layout: Demo Director on your own screen; the audience screen shows one experience at a time, or Patient app and Clinician workspace side by side. All tabs share the same state and refresh each other within seconds.

Before the client joins: open `/director`, click **Reset all data**, and confirm the AI runtime says READY (if it doesn't, the demo still works and labels replies SIMULATION).

## 4. How scenarios work

A scenario is a scripted event that changes shared state. Every scenario follows the same lifecycle:

```
baseline -> trigger -> candidates evaluated -> plan submitted
         -> supervisor approval -> execution (re-validated) -> audit trail
```

1. **Baseline:** fixture data, nothing wrong.
2. **Trigger:** state changes and events, audit entries and agent traces are written. Each scenario triggers once until reset.
3. **Candidates:** policy lists eligible and excluded staff, with a reason for each exclusion.
4. **Plan:** the planner submits a plan. It waits for approval. **Nothing has changed yet.**
5. **Approval:** only a Supervisor can approve or reject.
6. **Execution:** eligibility is re-checked at execution time, so an unsafe or stale plan is rejected.
7. **Audit:** every step is traceable by correlation ID in the Demo Director.

## 5. Scenario A: Patient access (CareFlow One)

Tabs: `/patient`, `/clinician`.

1. In the Patient app the chat starts empty. The patient types in their own words. Try:
   - `I need an orthopaedic doctor this week` shows both slots.
   - `Can I see a doctor by video today?` shows only the virtual slot.
2. The reply carries a tag: **LIVE AI** (Gemini understood the request) or **SIMULATION** (keyword rules). Say which it is.
3. Show the **safety guard**: type `I have chest pain`. The assistant refuses scheduling, shows a SAFETY POLICY reply, and nothing is booked. This check is deterministic and runs on every message before any AI.
4. Show the **boundary**: type `Can you refill my prescription?`. The assistant replies "I'm still learning…" and offers what it can do.
5. Choose a slot. The patient must **Confirm booking**. Nothing is booked before that.
6. For the virtual slot: **Start virtual visit**, then simulate the doctor joining, begin, and **End visit**. A follow-up task is created.
7. Switch to the Clinician workspace: the appointment, session status and timeline updated live.

Talking points: natural language in, safe deterministic action out; explicit patient confirmation; AI never books on its own.

## 6. Scenario B: Collision response (Workforce One)

Tabs: `/hospital`, `/workforce`, `/director`.

1. Show `/hospital` at baseline: calm, 12 hospitals normal.
2. On `/workforce` (Operations planner), pick **Collision response** and **Trigger scenario**. `/hospital` flips Central to Critical with an alert: ED RN gap 4, trauma support gap 1.
3. Walk through **Candidate evidence**: 5 eligible, 3 excluded with reasons (rest, unavailable, expired certification). This is the trust moment.
4. Optionally tick **Defer PROC-220** (elective). PROC-221 stays protected.
5. **Submit for approval**. Point out nothing has changed yet.
6. Toggle to **Supervisor** (top right) and click **Approve & execute**.
7. `/hospital` shows the plan executed and gaps resolved. Click the **Central Medical Center** tile (and optionally a second hospital such as North District) to open a **live view** with risks, ED staffing coverage, staff, procedures and emergency patients; select up to two to compare. Roster and patient detail beyond the seeded staff is synthetic. Show `/director` for the audit trail.

## 7. Scenario C: Procedure recovery (Workforce One)

Run after **Reset all data** if you ran B first.

1. `/workforce`, pick **Procedure recovery**, **Trigger scenario**. PROC-310 becomes **at risk** (staff member unavailable).
2. Review candidates, submit the replacement plan, switch to Supervisor, **Approve & execute**.
3. PROC-310 readiness returns to ready in `/workforce` and `/hospital`.

## 8. 15-minute flow

| Time | Step |
|---|---|
| 0-2 | Launcher and the key message |
| 2-7 | Scenario A (Patient + Clinician tabs) |
| 7-12 | Scenario B (Hospital, Workforce, Supervisor) |
| 12-14 | Reset, Scenario C (short) |
| 14-15 | Demo Director audit and traces, then Q&A |

## 9. Client questions

- **Is this real AI?** Request understanding runs on Gemini through Google ADK when a key is set; every reply is labelled LIVE AI or SIMULATION. Safety, eligibility, booking and approvals are deterministic code either way.
- **What if the AI is wrong?** It only classifies a request. It cannot book, approve or execute. Booking needs patient confirmation; plans need supervisor approval and are re-validated.
- **Can it handle other requests?** Today it handles booking and virtual consults. Everything else gets an honest "I'm still learning" reply, and new intents are added deliberately.
- **Real data?** No, synthetic fixtures only.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| Tab shows "Cannot reach the service" | Check Terminal 1 is running; open <http://127.0.0.1:8000/api/v1/health>. |
| "Scenario already triggered" | `/director` then **Reset all data**. |
| Replies say SIMULATION | `GOOGLE_API_KEY` missing or `.env` not sourced before starting the backend. Restart the backend after sourcing. |
| Patient chat shows an old booking | Reset in `/director`; the chat clears itself, or refresh the tab. |
| `command not found: uvicorn` or `python` | `source .venv/bin/activate` first. |
| Frontend will not start | Run `npm install` once in `frontend/`. |

## 11. After the demo

Stop both servers with Ctrl+C. Reset in `/director` so the next session starts clean.

## Patient portal, prescribing and hospital app

- **Patient portal** (`/patient`): Home, Book & ask (typed AI assistant), Appointments, Prescriptions (Download PDF), Health record, My profile.
- **Prescribing** (`/clinician`): use the Prescribe panel. "Allergy conflict demo" shows the safety block (Penicillin allergy). A signed Rx appears in the patient portal within seconds and can be downloaded as PDF.
- **Hospital app**: `/hospital` is the network wall; click a hospital to open `/hospital/HCO-XXX` in a new window. Switch persona between Hospital administrator and Nurse station.
- **Nurse station**: pick an IPD patient, capture demo vitals, give medications, then "Daily chart (AI)": draft with AI, review, sign and save.
- Reset all demo data with the Director reset button before each demo.

## Deploying to Render (single service)

The `Dockerfile` builds the frontend and serves it from FastAPI, so one Render web service hosts everything at one URL.

1. Push the project to a GitHub repo (`.env` is git-ignored; never commit it).
2. In Render: **New → Blueprint**, pick the repo. It reads `render.yaml`.
3. When prompted, set `GOOGLE_API_KEY` (a secret). `GEMINI_MODEL` is preset.
4. Wait for the build, then open the `https://healthcareone-demo.onrender.com` URL shown.
5. Check `/api/v1/health`, then use the Director reset before the demo.

Notes: the free plan sleeps after ~15 minutes idle (open it a few minutes early); the SQLite DB lives in `/tmp` and resets on restart, which is fine for a demo. Without a key the app runs in SIMULATION mode.

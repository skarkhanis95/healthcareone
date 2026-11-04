# HealthCareOne Implementation Plan

**Source:** `docs/prd.md` v1.0  
**Delivery window:** Three days  
**Status:** Execution baseline, locked to the decisions in Section 10  
**Scope:** Demonstration-grade simulation; synthetic records and simulated actions only

## 1. Delivery Approach

Deliver the product as three end-to-end phases, one per delivery day. Each phase has a hard exit gate. Work vertically from persisted simulation state through API and UI so every phase leaves the application runnable. Prioritize the three flagship scenarios and presenter recovery over optional breadth.

| Phase | Day | Outcome | Gate |
|---|---:|---|---|
| 1. Runnable foundation | 1 | Local app, synthetic baseline, reset, product shells, API and ADK/Gemini connectivity | A clean local setup can reset and read seeded data; a real Gemini-backed ADK tool call succeeds when credentials are configured |
| 2. Patient access and surge response | 2 | Patient booking/virtual-care journey and approved mass-casualty workforce plan | Scenario 1 completes; Scenario 2 produces a grounded plan and changes state only after approval |
| 3. Procedure readiness and demo hardening | 3 | Staff-absence recovery, complete Demo Director, audit/trace and rehearsed repeatable demos | All three scenarios pass reset/replay, safety, approval and cross-platform checks |

### Working rules

- Keep one local backend, one frontend, and SQLite. Use the PRD stack unless an existing repository decision already establishes an equivalent choice.
- Keep source-system adapters local. No external healthcare APIs, real communications, real video, real employee actions, or production authentication.
- Make synthetic IDs and scenario seeds stable. Scenario triggers must be idempotent or reject duplicate triggers clearly.
- Deterministic code owns safety screening, eligibility, capacity calculations, approval enforcement and state mutation. Gemini interprets, coordinates and explains using tool results.
- Separate read, recommendation and action tools. Action tools revalidate eligibility and approval against persisted state immediately before mutation.
- Persist scenario ID, event ID where applicable, session/correlation ID, trace, audit event and action result. Never expose hidden chain-of-thought or secrets in logs/UI.
- Treat Gemini as an external dependency: show loading, timeout/error and retry states. Do not describe deterministic fallback text as live AI output.
- The three end-to-end demonstrations are the delivery priority. This solo three-day plan is a demo-critical subset of PRD P0, not a commitment to full P0 breadth. P1 and P2 remain out of scope unless all scenario gates pass early.

## 2. Shared Contracts and Architecture

Agree these boundaries during Phase 1 before frontend and backend work proceeds independently:

1. **Simulation domain:** patients, doctors, slots, appointments, hospitals, departments, capacity, staff, shifts, skills, certifications, procedures, rooms, events, plans, approvals, traces and audit records.
2. **API envelope:** JSON responses use `success`, `data`, `error` and `correlation_id`; write failures return meaningful HTTP status codes and do not partially mutate state.
3. **Agent tool envelope:** typed input and output schemas; every tool result is traceable. Tools access data through services/repositories, never direct UI state.
4. **Action policy:** appointment creation requires explicit patient confirmation and a currently available slot. Virtual session creation requires patient confirmation. Workforce/procedure actions require an approved plan and a second eligibility check at execution.
5. **Shared updates:** committed simulation actions produce persisted events. The UI refreshes from the API and receives live updates through WebSocket or a documented polling fallback.
6. **Scenario lifecycle:** `baseline -> triggered -> processing -> awaiting_approval -> completed` or `failed`; reset returns the scenario and related state to a known baseline.
7. **Trace display:** show agent/task labels, tool inputs/outputs in safe summarized form, evidence, status and elapsed time. Do not show prompts, private reasoning or API keys.

The recommended module separation is frontend, FastAPI routes/schemas, domain services and policy checks, repositories/SQLite, scenario engine/mock adapters, ADK agents/tools, and audit/event services. Keep deployment local and simple.

## 3. Phase 1 — Runnable Foundation (Day 1)

### Goal

Create a working local application with consistent synthetic records, resettable scenarios, stable API contracts, navigable product shells and a verified ADK-to-Gemini call. Do not start broad agent workflows before the underlying tools and data are reliable.

### Work sequence and deliverables

| ID | Work item | Deliverable | Verification / pass condition |
|---|---|---|---|
| 1.1 | Establish repository and local run path | Frontend/backend project structure, dependency manifests, environment example, README setup/start/reset instructions, health endpoint | From a clean checkout, documented install and startup commands work; health endpoint reports app and database ready. `.env.example` contains placeholders only. |
| 1.2 | Define schemas and persistence | SQLite schema/migrations or deterministic schema initialization; typed domain/API schemas; consistent IDs and timestamps | Fresh database initializes without manual edits. Invalid references and invalid enum values are rejected by schema/service validation. |
| 1.3 | Seed synthetic baseline | 12 hospitals, synthetic localities/clinics and the minimum linked patient, doctor, appointment, staff, procedure, room, skill, certification and shift records needed by all scenarios | Seed validation reports no dangling references; all names/locations are fictional; baseline procedures satisfy their staffing and readiness requirements. Counts may be smaller than PRD recommendations if all scenario fixtures are covered. |
| 1.4 | Implement reset and scenario fixtures | Reset restores identical baseline; explicit fixtures for Alex Morgan, the collision response and the at-risk procedure | Run reset twice and compare stable entity IDs, counts and scenario-critical values; prior bookings, approvals, events and assignments do not leak across reset. |
| 1.5 | Add read APIs and mock adapters | Patient, doctor/availability, hospital/capacity, staff, procedure and simulation-state reads; local SchedPlus/ShiftWise/MediCore/ConnectCare-style adapters only where needed | API integration tests verify envelope, filters, not-found behavior, references and correlation IDs. Reads do not mutate state. |
| 1.6 | Build navigable application shell | Light-theme CareFlow One and Workforce One navigation; patient portal, Patient 360, clinical workspace, hospital command, workforce, procedure readiness, approvals, activity/audit and Demo Director entry points; persistent synthetic-data label | Frontend typecheck/build passes. Each navigation item opens a usable view with real seeded API data or an explicit empty state; no dead-end placeholder links. |
| 1.7 | Implement shared observability skeleton | Persisted event, audit and agent trace schemas/services; correlation ID middleware; UI activity/audit panel skeleton | A test read/write flow can be followed by correlation ID through API response, audit/event record and UI. Sensitive configuration is absent from records and UI. |
| 1.8 | Verify ADK/Gemini integration | Configurable model and API key; one ADK agent with a read-only synthetic-data tool; bounded timeout and clear connection test | With a valid key, a real model run calls the read tool and returns tool-grounded data; trace records tool/result. With missing/invalid credentials, health/test reports a clear failure without crashing or claiming AI success. |

### Phase 1 test set

- **Backend unit tests:** seed integrity; reset determinism; slot lookup; capacity and readiness fixture calculations; schema validation; correlation ID creation.
- **API integration tests:** health, simulation state, patient/doctor/availability reads, hospital capacity, workforce/procedure reads, reset, error envelope and no-mutation-on-read.
- **Frontend checks:** lint/typecheck and production build; navigation smoke test at desktop and mobile widths; simulation label remains visible.
- **ADK integration smoke:** live Gemini check is a separately marked test, requires `GOOGLE_API_KEY`, and must prove at least one actual tool call. Normal tests must not require network credentials.

### Phase 1 exit gate

Proceed only when a new local setup starts from documented instructions, reset restores valid baseline data, required views load from the API, API contracts are stable, and the live ADK/Gemini tool smoke passes with credentials. If Gemini is unavailable, preserve the integration error state and continue only with deterministic tests explicitly labelled as non-live; do not mark AI connectivity complete.

## 4. Phase 2 — Patient Access and Network Surge (Day 2)

### Goal

Complete the two highest-value operational stories on the Phase 1 foundation: patient access through virtual consultation, and collision-driven workforce planning with human approval and shared updates.

### Work sequence and deliverables

| ID | Work item | Deliverable | Verification / pass condition |
|---|---|---|---|
| 2.1 | Implement patient access policy and tools | Safety screen, fixed request-to-specialty mapping, location lookup, doctor search, availability lookup and booking service/tools | Unit tests prove red-flag answers stop routine booking; no red flag permits the seeded access path; invalid specialty, doctor, slot or missing confirmation cannot create a booking. |
| 2.2 | Implement patient-access ADK workflow | Experience Coordinator/Patient Access Agent with bounded delegation, conversation context and tool-grounded response | Agent trace shows required reads before options. Returned doctors/slots are a subset of tool results; fabricated IDs and success claims are rejected by response validation. Gemini tests assert structure/evidence, not exact prose. |
| 2.3 | Build chat and manual booking UI | Patient chat with clarifying prompts, safety escalation, two appointment options, explicit selection/confirmation; doctor search/filter, profile, slot selection and confirmation | Browser test completes chat booking and manual booking. Both display persisted booking reference and Patient 360 update. Safety branch presents emergency-care guidance and creates no routine appointment. |
| 2.4 | Implement virtual-care lifecycle | ConnectCare simulation for availability, create, status and completion; session linked to confirmed appointment; simulated follow-up task | Service tests reject session creation without patient confirmation or valid appointment. Session state transitions are valid and repeatable. No camera/microphone permissions or media APIs are requested. |
| 2.5 | Build simulated consultation and journey views | Waiting/doctor-joined/in-consultation/completed UI; simulated call controls; Patient 360 timeline, appointments, in-app notifications and staff workspace reflection | Browser test starts session, advances simulated doctor connection, ends call and verifies appointment/session/journey/status in patient and clinical staff views. No diagnosis or treatment advice is generated. |
| 2.6 | Implement demand and capacity rules | Deterministic role-based staffing gap calculation and seeded collision event progression | Unit tests verify expected Central emergency pressure and role gaps after trigger, no gaps before trigger, and stable results after reset/replay. Capacity arithmetic is not delegated to Gemini. |
| 2.7 | Implement candidate eligibility services | Staff availability, skills/certification, shift/rest/workload constraints, cross-department/hospital policy and exclusion reasons | Tests include eligible local, eligible cross-hospital, unavailable, expired certification, wrong skill, insufficient rest and non-deployable candidates. Every hard-failing candidate is excluded. |
| 2.8 | Implement augmentation plan and approval gate | Plan proposal, evidence, policy results, approval decision and simulated action executor | Before approval, no assignments/procedures change. Reject leaves baseline state intact. Approve executes only eligible selected actions; stale or forged approval and duplicate execution are rejected or idempotently handled. |
| 2.9 | Build collision scenario and operational UI | Trigger/advance collision, capacity/arrival dashboards, Workforce One demand/capacity and candidates, plan review/approve/reject, event and audit timelines | End-to-end test triggers incident, observes both dashboards, inspects plan/evidence/exclusions, approves, and verifies shared state plus audit. Deferrable seeded procedure may be recommended; non-deferrable/critical procedure is never changed. |
| 2.10 | Add event-driven refresh | Publish committed events after trigger, approval and execution; WebSocket updates or tested polling fallback in both products | With two open views, an approved action becomes visible in each within the chosen update interval. Reconnect or polling recovers missed updates from persisted state. |

### Phase 2 scenario tests

**Scenario 1 — patient access and virtual consultation**

1. Reset and open Alex Morgan's patient portal.
2. Submit the seeded left-knee request; answer safety screen and North District location.
3. Verify specialty mapping and at least two available tool-grounded options, including the immediate virtual option and later in-person option.
4. Confirm the virtual option; assert one appointment and one session are persisted with a booking reference.
5. Complete the simulated call; assert status, journey event, follow-up task and clinical workspace update.
6. Reset; take the emergency-warning branch; assert escalation and zero routine bookings.
7. Reset; book the in-person option and assert no virtual session was created.

**Scenario 2 — collision response**

1. Reset; record baseline capacity, assignments and procedure statuses.
2. Trigger the collision; assert arrival events and Central pressure update deterministically.
3. Run the operations workflow; assert role gaps, candidate evidence, exclusion reasons and at least one eligible cross-hospital option are visible.
4. Assert proposal is pending approval and state is unchanged.
5. Reject once and verify no operational mutation; reset and repeat, approving selected eligible actions.
6. Verify assignment/procedure changes, both platform views, action status, audit approver and correlation IDs.
7. Reset and replay; compare scenario-critical results for determinism.

### Phase 2 exit gate

Both scenario flows pass end to end using persisted backend state. Patient safety and explicit confirmation are enforced. Workforce state changes are impossible before human approval and hard eligibility checks are enforced in services, not prompts. AI traces prove live tool use when Gemini credentials are available; UI/API still handles model failure honestly and allows presenter recovery.

## 5. Phase 3 — Procedure Readiness and Demo Hardening (Day 3)

### Goal

Complete the staff-absence workflow, close the presenter control loop, verify cross-platform behavior and rehearse all scenarios from clean reset through final audit state.

### Work sequence and deliverables

| ID | Work item | Deliverable | Verification / pass condition |
|---|---|---|---|
| 3.1 | Implement procedure readiness evaluator | Deterministic evaluation of required roles/skills, assigned staff availability, certification, room, patient preparation and documentation; Ready/At Risk/Blocked result with reasons | Unit tests cover each independent blocker, multiple simultaneous blockers, recovered readiness and baseline Ready procedure. AI cannot override a failed hard requirement. |
| 3.2 | Implement absence event and replacement workflow | Trigger marks seeded required staff unavailable; readiness becomes At Risk; agents/tools find eligible and unsuitable candidates; recommendation includes operational consequences | Integration tests prove the required staff is excluded, at least one seeded valid replacement is found, one unsuitable candidate is explained, and non-staff readiness statuses are surfaced. |
| 3.3 | Add procedure approval and execution | Replacement/operational rescheduling plan, approval decision, revalidation, assignment update and readiness recomputation | No mutation while pending or after rejection. Approval with a candidate who became ineligible is rejected at execution. Valid approval updates assignment and recomputes readiness; procedure remains At Risk/Blocked if any independent constraint remains. |
| 3.4 | Complete Procedure Readiness UI | Procedure table/detail with requirements, assigned team, room/patient/document status, reasoned status, replacement candidates, warnings and approval actions | Browser test triggers absence, inspects evidence, rejects and verifies no change; after reset, approves a valid replacement and verifies readiness on CareFlow and Workforce views. |
| 3.5 | Complete Demo Director Console | List/select scenarios, reset all, trigger/reset scenario, advance/play/pause event sequence, active scenario/time/progress/checkpoints, links to relevant views | Presenter-only browser test runs each scenario using the console without API calls, database editing or developer tools. Every control gives visible success/error feedback; reset is repeatable. |
| 3.6 | Complete agent trace, approval and audit experiences | Search/filter traces and audit by scenario/correlation; approval details and decision notes; before/after action references | A single scenario can be traced from trigger through agent tools, recommendation, policy checks, approver, executor and final event. No hidden chain-of-thought or secrets appear. |
| 3.7 | Failure and recovery hardening | Gemini timeout/error, retry, duplicate trigger, reset during pending approval, disconnected updates, invalid approval and partial API failure handling | Fault-injection tests show no false success, no unauthorized mutation, clear retry/reset path and consistent persisted state. A failed AI run can be retried without corrupting scenario state. |
| 3.8 | Accessibility and responsive pass | Keyboard-operable navigation/forms/dialogs, labels, focus handling, status conveyed with text as well as color, readable desktop/mobile layouts | Keyboard-only walkthrough completes booking, approval and reset controls. Check representative desktop and mobile viewport screenshots for clipping, overlapping text and inaccessible controls. |
| 3.9 | End-to-end rehearsal and release notes | Runbook, verified setup/reset/replay commands, known limitations, scenario seed facts and 12–15 minute demo sequence | Rehearse all three flows from clean reset twice. Presenter completes without developer tools; expected outcomes and recovery route are recorded. |

### Phase 3 scenario tests

**Scenario 3 — procedure at risk**

1. Reset and verify the seeded procedure is Ready with a complete team.
2. Trigger required-staff absence; verify absence event and At Risk status.
3. Run readiness workflow; verify missing role/skill, room/patient/document status, qualified replacement and exclusion reasons.
4. Reject; assert procedure/team remain unchanged apart from the simulated absence itself.
5. Reset and repeat; approve a valid replacement.
6. Verify assignment, readiness recomputation, shared platform updates, event, audit and approval trace.
7. Repeat after reset and verify identical recommendations from the deterministic fixture.

**Full-system regression**

- Reset between every flagship scenario; no state leaks across scenarios.
- Verify all high-impact workforce/procedure actions require approval, and appointment/session actions require patient confirmation.
- Verify one invalid or failed agent/tool/API operation cannot produce a success banner or a committed action.
- Verify patient access never returns diagnosis or treatment recommendations.
- Verify all synthetic records are marked as simulation data and no real contact, messaging, video, hospital integration or staff deployment occurs.
- Verify event history and audit are consistent with actual persisted state after approval, rejection, retry and reset.

### Phase 3 exit gate

All three scenarios pass twice from a reset baseline. Required live AI paths use ADK/Gemini and show tool traces; deterministic tests remain runnable without credentials. Approval and patient-confirmation barriers are enforced at the service/action boundary. Presenter can operate and recover the demo from the UI alone.

## 6. Test and Verification Strategy

### Required automated layers

1. **Unit:** business rules, safety screen, capacity gaps, skill/certification/shift/rest eligibility, readiness calculation, approval policy, state transitions and deterministic scenario data.
2. **API integration:** persistence, schema validation, response envelope, error behavior, read/write boundaries, reset, correlation IDs, audit and event publication.
3. **Agent contract:** tool schemas, allowed tool use, tool-grounded entities, refusal/escalation behavior, bounded execution and error handling. Use a fake/stub model for deterministic CI tests; use an explicitly marked live Gemini smoke for actual integration.
4. **Frontend/component and browser:** booking, consultation state, approval decisions, scenario controls, shared updates, error/loading/empty states, keyboard flows and responsive layout.
5. **End-to-end:** exact presenter flows in Sections 4-5, with a clean reset between scenarios.

### Acceptance test quality rules

- Assert state, authorization, tool use, evidence and visible status; do not assert exact Gemini phrasing.
- Use fixed scenario fixtures and a controllable simulation clock. Avoid wall-clock-dependent expected availability.
- Test both positive and negative paths for every action boundary.
- Keep a live API-key test separate from ordinary CI; never print the key in logs.
- Record failed runs and correlations sufficiently to diagnose failures without exposing prompts or sensitive configuration.
- A green frontend build alone does not count as scenario acceptance; scenario state must be verified through API/database-backed behavior and UI.

### Commands to provide in the application README

The exact package manager and script names should follow the repository scaffold. By the end of Phase 1, document equivalents for:

```text
backend install
backend test
frontend install
frontend lint and typecheck
frontend test
frontend production build
start the local application
reset the simulation
run the live ADK/Gemini connection smoke test
```

Do not document commands as verified until they have been run from a clean environment.

## 7. Cross-Cutting Definition of Done

An item is complete only when its implementation and verification are both present:

- Data is synthetic, linked consistently, seeded deterministically and resettable.
- UI state reflects backend state; no key demo outcome exists only in frontend memory.
- Read, recommendation and action boundaries are explicit.
- Patient confirmation and human approval are checked in backend services before mutation.
- Eligibility, safety and readiness hard constraints are deterministic and tested.
- Gemini does real reasoning/tool selection on live paths; tool output supplies source facts.
- Errors, loading, retry and empty states do not imply an action succeeded when it did not.
- Tool calls, policy decisions, approvals, events and simulated actions are traceable by scenario/correlation ID.
- Both platforms reflect shared committed state.
- Required tests pass and setup/reset/replay steps are documented.

## 8. Scope and Risk Controls

| Risk | Control / response |
|---|---|
| Three-day scope exceeds available capacity | Implement P0 vertical slices only; use compact data fixtures; defer P1 polish until all scenario gates pass; do not add P2. |
| Gemini latency, quota or outage | Bounded timeout and retry; clear unavailable state; preserve scenario data; deterministic test stub is labeled as test/fallback and never reported as live Gemini reasoning. |
| LLM invents doctors, slots, eligibility or action success | Validate structured response against tool results; render canonical entity data from API; only action service response can confirm persisted success. |
| Workforce change occurs before approval | Central policy/action service denies it; test direct API/tool invocation without approval and with stale approval. |
| Patient is routed to routine booking despite warning sign | Deterministic safety gate runs before scheduling tools; add positive, negative and ambiguous-input tests; show safety escalation without diagnosis. |
| Reset leaves stale events or assignments | Reset transaction clears/restores all scenario-owned records; assert repeatability and cross-scenario isolation. |
| WebSocket delivery fails during demo | Persist events and re-fetch on reconnect; provide polling fallback and visible last-updated status. |
| Frontend and backend drift on contracts | Commit schemas/OpenAPI early; test typed client or generated contract; avoid duplicated business-rule implementations in UI. |
| Seed fixture lacks demonstrable candidates | Validate scenario preconditions at seed time and expose a scenario readiness check in Demo Director. |

## 9. Explicitly Deferred Work

Do not spend the three-day delivery window on production authentication, real FHIR/EHR integrations, real video or device permissions, real messaging, real staffing/shift changes, clinical decisions, distributed infrastructure, Kubernetes, predictive models, or national-scale optimization. Appointment cancellation/rescheduling, richer workforce fairness analysis and advanced chart interactions are deferred until all P0 gates pass.

## 10. Locked Execution Decisions

These decisions come from the implementation-plan clarification and are binding for this delivery unless the owner changes them:

| Decision | Locked choice | Implementation consequence |
|---|---|---|
| Team and time | One developer, three days | Plan against 24 focused hours. If available hours are lower, preserve the three demo paths and reduce visual polish and non-demo views first. |
| Stack | PRD stack | React + Vite + TypeScript; FastAPI + Python; SQLite; Google ADK + Gemini; local single-machine execution. Pin dependency versions and commit lockfiles on Day 1. |
| AI runtime | Local laptop with Gemini key available by environment variable | Exercise live Gemini tool calls. Never request, print, or commit the key. Keep automated tests runnable without network credentials. |
| Agent architecture | Twelve distinct ADK agents | Create a separate named ADK agent for each PRD responsibility. Keep each narrow and small; all twelve must be invoked by at least one demo path and appear in traces. Do not inflate implementation with separate UI or database layers per agent. |
| Scenario data | Implementation owner defines sensible synthetic values | Use the deterministic fixtures in Section 12 as the test oracle. These are demonstration assumptions, not clinical or employment policy. |
| Demo roles | Patient, presenter, supervisor | Use a simple simulated role selector. Patient confirms own booking/session; presenter triggers and resets; supervisor approves/rejects operational plans. No production authentication. |
| Verification | Unit + API + browser E2E | Use pytest, frontend unit/component tests, and Playwright scenario tests. E2E uses a deterministic model adapter; separate live Gemini smoke tests prove real ADK/model/tool integration. |

### Capacity boundary

Three days for one developer is not enough to deliver every page, dataset count, chart, integration, and optional flow in the PRD at production depth. The deliverable is a coherent, visually credible vertical slice for each flagship demonstration. Seed only the records required to support those paths plus enough surrounding records to make the dashboards credible. Implement compact, working versions of required views rather than static full-screen mockups. Do not claim full P0 acceptance for deferred breadth.

The twelve agents are distinct ADK agent instances with separate names, instructions, and owned tools, but use one shared agent factory, shared typed schemas, and a small set of deterministic domain services. This preserves the requested architecture while keeping the implementation feasible. Every orchestration must have a bounded number of model calls; keep specialist outputs structured and short.

## 11. Day-by-Day Execution Schedule

Plan against three eight-hour days. The schedule includes integration and testing time; avoid spending the final hours adding features. If a gate slips, apply the listed scope reductions rather than silently dropping safety or state-integrity tests.

### Day 1 — Scaffold, contracts, seed, and live agent proof

| Timebox | Execute | Complete when |
|---|---|---|
| 0:00-0:45 | Create backend/frontend scaffold, local environment instructions, `.env.example`, ignore rules, and health endpoint | Both processes start locally; no secret is in source control; clean startup command is documented. |
| 0:45-2:15 | Define minimum relational schema, typed API contracts, status enums, scenario IDs, deterministic clock, and correlation ID | Schema supports patient booking, virtual session, hospital capacity, workforce plan, approval, procedure, event, audit, and trace. |
| 2:15-3:30 | Seed scenario fixtures and implement reset transaction | `seed -> verify -> reset -> verify` passes; all IDs and expected values match Section 12. |
| 3:30-4:45 | Implement health, state, patient/doctor/availability, capacity, staff/procedure read APIs | API contract tests pass and reads are side-effect-free. |
| 4:45-5:30 | Build shared navigation and simulation shell with synthetic-data banner | Patient, operations, workforce, procedure, approval, trace, and director destinations render usable data/empty states. |
| 5:30-6:45 | Define all twelve ADK agents, shared factory, typed tool registration, coordinator delegation, and trace wrapper | All named agent instances construct; a read-only agent calls a local tool. |
| 6:45-7:30 | Run live Gemini connection/tool smoke; add timeout/error UI/API handling | With configured key, Gemini invokes a tool and its result is traceable. Missing key yields an explicit unavailable result. |
| 7:30-8:00 | Run backend/frontend checks, fix blockers, record actual commands | Health, seed/reset, API tests, frontend typecheck/build pass. |

**Day 1 gate:** clean local start, deterministic reset, required read APIs, twelve agent instances, and one real Gemini-to-tool call. If the live call fails due to key/network/quota, record it as blocked; do not mark AI integration complete or fake a pass.

### Day 2 — Patient access and collision response

| Timebox | Execute | Complete when |
|---|---|---|
| 0:00-1:15 | Implement access safety gate, specialty mapping, search/availability, and booking transaction | Positive access path and emergency branch pass service tests; confirmation and slot revalidation are enforced. |
| 1:15-2:15 | Wire Experience Coordinator, Patient Access, Patient Journey, and Virtual Care agents/tools | Agent outputs reference only tool-returned IDs; explicit confirmation gates booking/session creation. |
| 2:15-3:30 | Build patient chat, two options, confirmation, Patient 360 timeline, and manual booking minimum | Browser flow books the seeded virtual or in-person option and shows persisted result. |
| 3:30-4:15 | Implement virtual session state transitions and compact simulated consultation room | Patient can start, observe doctor-joined state, end call; no device permission requested. |
| 4:15-5:15 | Implement collision trigger, deterministic demand gap calculation, and event persistence | Trigger produces the exact capacity/staff gaps in Section 12 and is resettable. |
| 5:15-6:30 | Implement Staff Availability, Skills Matching, Fatigue & Compliance, Workforce Demand, Patient Flow, and Workforce Coordinator flows | All eligible/excluded candidates have deterministic evidence; proposal is pending and no action has run. |
| 6:30-7:30 | Build compact hospital/workforce dashboards and approve/reject flow | Approve mutates only selected eligible actions; reject makes no operational mutation; both views refresh from API. |
| 7:30-8:00 | Run Scenario 1/2 browser smoke and fix highest-severity failures | Patient happy path, emergency path, and collision propose/approve/reject paths pass. |

**Day 2 gate:** Scenario 1 completes through consultation; Scenario 2 creates a grounded plan, supports approval/rejection, and updates shared state only after approval. If behind, defer manual doctor filters, rich charts, and non-demo dashboard widgets.

### Day 3 — Procedure recovery, director, and full rehearsal

| Timebox | Execute | Complete when |
|---|---|---|
| 0:00-1:00 | Implement readiness evaluator and seeded staff absence trigger | Readiness changes from Ready to At Risk for the intended missing role; independent room/preparation/document blockers remain visible. |
| 1:00-2:00 | Wire Procedure Readiness, Staff Availability, Skills Matching, Fatigue & Compliance, and Workforce Coordinator agents | Agent evidence shows valid replacement and deterministic exclusions; no action occurs before approval. |
| 2:00-3:00 | Build procedure detail, replacement review, approval, and execution UI | Reject preserves the proposed assignment; approve revalidates and recomputes readiness. |
| 3:00-4:00 | Complete Demo Director: reset, trigger, advance, replay, progress, role selector, route links | Presenter can operate every scenario without API/database/dev tools. Use persisted event history and polling for refresh if WebSockets threaten the timebox. |
| 4:00-5:30 | Implement Playwright E2E for all three demos; add API/unit regression for confirmation and approval boundaries | Three repeatable browser flows run with deterministic model adapter; direct unauthorised action tests fail closed. |
| 5:30-6:15 | Run live Gemini smoke for patient and operations coordinators; inspect agent/tool trace and errors | Live runs show actual model calls and tools; no test adapter is misreported as live AI. |
| 6:15-7:15 | Rehearse all three flows from reset twice; test failure recovery and keyboard operation on critical controls | Presenter can complete stories, reject/approve, reset and recover from a failed model call. |
| 7:15-8:00 | Fix release-blocking defects, verify documented commands, write known limitations | All exit gates are reported accurately; unresolved issues are listed, not hidden. |

**Day 3 gate:** all three browser scenarios pass twice from a reset baseline, with deterministic test-model runs and live Gemini coordinator smoke tests. If the gate cannot be met, ship only the scenarios that pass and label the others incomplete; never claim end-to-end completion based on a frontend-only simulation.

## 12. Deterministic Demo Fixtures and Test Oracles

All timestamps use a fixed simulation clock set to `2026-11-02T09:00:00` local demo time. Tests advance the clock explicitly; they do not depend on the machine's current time. IDs below are stable across reset. Values are synthetic planning fixtures, not clinical guidance or workforce policy.

### Scenario 1 — patient access

| Record | Seeded value | Expected assertion |
|---|---|---|
| Patient | `PAT-1001`, Alex Morgan, North District | Patient portal context returns the same patient and locality. |
| Virtual option | `DOC-0021`, Dr. Meera Shah, Orthopaedics, North District Hospital; `SLOT-IMMEDIATE-01`, 2026-11-02 09:00, virtual | Search and availability tools return this exact doctor/slot; session is available. |
| In-person option | `DOC-0022`, Dr. Arjun Rao, Orthopaedics, North District Clinic; `SLOT-TODAY-02`, 2026-11-02 14:00, in person | The two displayed options are precisely the available seeded options, each with canonical location/time/mode. |
| Booking | First confirmed booking after reset: `APT-DEMO-0001`, `HCO-DEMO-0001` | Booking exists once, has selected slot/type, and appears in Patient 360 and clinical workspace. |
| Safety test input | Fixture `red_flag_present=true` for the deterministic test; happy path is `false` | True stops doctor search/booking and records escalation. False allows normal scheduling. The test fixture avoids asserting medical interpretation of free text. |
| Virtual session | `VCS-DEMO-0001`, initial `waiting`, then `doctor_connected`, `in_consultation`, `completed` | Invalid transitions and create-without-confirmation fail; end-call creates completion and follow-up event. |

### Scenario 2 — collision response

| Record | Baseline / triggered value | Expected assertion |
|---|---|---|
| Affected hospital | `HCO-CENTRAL`; support hospitals `HCO-NORTH`, `HCO-WEST` | One incident is correlated across all three hospital views. |
| ED census/capacity | Central ED baseline 16/24; collision adds 8 projected arrivals; triggered pressure is Critical at 24/24 | Before trigger no collision pressure; after trigger projected census and alert match these values. No real patient/ambulance records are created. |
| Staffing requirement | Baseline 8 ED RNs required/available and 2 trauma-support staff required/available; incident requirement becomes 12 RNs and 3 trauma-support staff | Deterministic gap is 4 ED RNs and 1 trauma-support staff. Gemini does not calculate the gap. |
| Eligible RN candidates | `STF-C-011`, `STF-C-012` (eligible cross-department at Central); `STF-N-021` (eligible cross-hospital); `STF-W-018` (eligible cross-hospital) | All four may be proposed for the RN gap. Proposed plan remains pending until supervisor approval. |
| Eligible trauma candidate | `STF-N-032`, valid role/skill/certification, available shift and rest | May be proposed for the one trauma-support gap. |
| Exclusion candidates | `STF-W-077` expired required certification; `STF-C-099` insufficient rest; `STF-N-040` unavailable | Each is absent from eligible recommendations and shown with the matching deterministic exclusion reason. Demo-only thresholds: at least 10 hours rest before shift and no more than 12 hours worked in the current simulated shift. |
| Procedures | `PROC-220` elective and `deferrable=true`; `PROC-221` critical and `deferrable=false` | `PROC-220` may be recommended for supervisor-approved deferral; `PROC-221` is never proposed for deferral. No procedure changes before approval. |
| Approval | Plan begins `pending_approval`; approval actor is `supervisor` | Reject leaves assignments/procedures unchanged. Approve applies only explicitly selected, still-eligible actions once. |

### Scenario 3 — procedure readiness

| Record | Seeded value | Expected assertion |
|---|---|---|
| Procedure | `PROC-310`, Central, `OR-03`, scheduled 2026-11-02 13:00; baseline Ready | Baseline assigned team satisfies each requirement; room, preparation and documentation are Ready/Complete. |
| Absence | Required OR nurse `STF-C-061` changes to unavailable when triggered | Procedure becomes At Risk for the missing OR nurse requirement. |
| Valid replacement | `STF-N-044`, available, correct OR skill, certification valid through procedure end, shift covers procedure, at least 10h rest | Candidate can be proposed; approval and execution revalidate these conditions. |
| Invalid replacement | `STF-W-051`, required certification expired | Candidate is excluded with the certification reason. |
| Recovery | Supervisor approves valid replacement | Assignment updates once; readiness is recomputed and returns to Ready only if all other readiness dimensions remain satisfied. |

### Scenario event/status vocabulary

- Scenario: `baseline`, `triggered`, `processing`, `awaiting_approval`, `completed`, `failed`.
- Approval: `pending`, `approved`, `rejected`.
- Plan/action: `proposed`, `pending_approval`, `approved`, `rejected`, `executing`, `completed`, `failed`.
- Appointment: `confirmed`, `cancelled`, `completed` (cancellation is not in this three-day demo scope).
- Virtual session: `waiting`, `doctor_connected`, `in_consultation`, `completed`.
- Procedure readiness: `ready`, `at_risk`, `blocked`.
- Collision event names: `collision.triggered`, `arrivals.projected`, `capacity.pressure_changed`, `augmentation.proposed`, `approval.decided`, `augmentation.executed`, `procedure.deferral.applied`.
- Absence workflow event names: `staff.absence.triggered`, `procedure.readiness_changed`, `replacement.proposed`, `approval.decided`, `staff.assignment_changed`.

## 13. Agent, Tool, API, and Role Contracts

### Twelve distinct ADK agents and ownership

Each is a separately named ADK agent with a short instruction, structured output, explicit tool allowlist, and trace. Specialists return evidence and a recommendation, not mutations. Only action tools mutate, after deterministic policy checks.

| Agent | Invoked by / demo | Owned responsibility and permitted tools |
|---|---|---|
| Experience Coordinator | Patient portal / Scenario 1 | Intent routing and concise response; delegates to Patient Access, Patient Journey, and Virtual Care. No direct state writes. |
| Operations Intelligence Coordinator | Demo Director / Scenarios 2-3 | Coordinates operations agents, assembles evidence and stops at pending approval. No direct state writes. |
| Patient Access Agent | Experience Coordinator / Scenario 1 | `get_patient_context`, `screen_emergency_red_flags`, `get_location_options`, `map_request_to_specialty`, `search_doctors`, `get_doctor_availability`; booking tool only after patient selection/confirmation. |
| Patient Journey Agent | Experience Coordinator / Scenario 1 | `get_patient_journey`, `get_patient_appointments`, `get_follow_up_tasks`, `append_journey_event`; append only factual events emitted by committed services. |
| Virtual Care Agent | Experience Coordinator / Scenario 1 | `check_virtual_session_availability`, `create_virtual_session`, `get_virtual_session_status`, `complete_virtual_session`, `create_simulated_follow_up`; session creation requires patient confirmation. |
| Patient Flow Agent | Operations Coordinator / Scenario 2 | `get_hospital_capacity`, `get_department_census`, `get_arrival_events`, `get_pending_discharges`, `get_scheduled_procedures`; read-only. |
| Workforce Demand Agent | Operations Coordinator / Scenario 2 | `get_staffing_requirements`, `get_department_staffing`, `calculate_staffing_gap`, `get_network_capacity`; deterministic tool returns the gap. |
| Staff Availability Agent | Operations Coordinator / Scenarios 2-3 | `search_available_staff`, `get_staff_profile`, `get_staff_shift`, `get_staff_assignment`; read-only candidate retrieval. |
| Skills Matching Agent | Operations Coordinator / Scenarios 2-3 | `match_staff_skills`, `check_certification_validity`, `get_role_requirements`; deterministic hard requirements, ranked evidence. |
| Fatigue & Compliance Agent | Operations Coordinator / Scenarios 2-3 | `check_staff_constraints`, `get_workload_summary`, `get_deployment_policy`; hard failures exclude candidates, soft warnings remain visible. |
| Procedure Readiness Agent | Operations Coordinator / Scenario 3 | `get_procedure_details`, `get_procedure_team_requirements`, `get_room_readiness`, `get_patient_preparation_status`, `get_documentation_status`, `evaluate_procedure_readiness`; read/recommend only. |
| Workforce Coordinator | Operations Coordinator / Scenarios 2-3 | `create_augmentation_plan`, `get_augmentation_plan`, `submit_plan_for_approval`, `execute_approved_augmentation`, `get_plan_execution_status`; proposal tool cannot mutate; executor requires approved plan and revalidation. |

**Agent acceptance:** each of the 12 agents has a construction test, tool allowlist test, and trace-name assertion; each is invoked in its listed end-to-end scenario. Agent test doubles are allowed only in deterministic automated tests. The live smoke runs through both coordinators and proves at least one specialist tool call per path.

### Minimum API surface for the three demos

Prefix all routes with `/api/v1`; preserve the PRD response envelope. Use Pydantic request/response models and publish OpenAPI. Add `correlation_id` to every response and persisted write/event.

| Route | Purpose and write guard |
|---|---|
| `GET /health` | App/database readiness and Gemini configuration status without revealing key or value. |
| `GET /simulation/state`, `POST /simulation/reset` | Read state; reset transaction clears scenario-owned writes and restores fixtures. Reset requires presenter role. |
| `GET /simulation/scenarios`, `POST /simulation/scenarios/{id}/trigger`, `POST /simulation/events/{id}/advance` | List/trigger/advance seeded scenarios; presenter role; reject duplicate or invalid transitions with 409. |
| `GET /patients/{id}`, `GET /patients/{id}/journey`, `GET /doctors`, `GET /availability` | Scenario 1 reads; filters are constrained to seeded data. |
| `POST /appointments`, `GET /appointments/{id}` | Booking requires patient role, patient confirmation, currently available slot and idempotency key. A conflicting slot returns 409 and creates no record. |
| `POST /virtual-sessions`, `GET /virtual-sessions/{id}`, `POST /virtual-sessions/{id}/complete` | Session lifecycle; patient confirmation and valid appointment required for creation; invalid transition returns 409. |
| `GET /hospitals`, `GET /hospitals/{id}/capacity`, `GET /procedures`, `GET /procedures/{id}` | Current hospital and procedure state for both platforms. |
| `GET /staff`, `GET /staff/availability`, `GET /staff/{id}` | Workforce records with hospital, role, skill and availability filters. |
| `POST /workforce/augmentation-plans`, `GET /workforce/augmentation-plans/{id}` | Create/read proposals; creation never changes staffing or procedure state. |
| `POST /approvals/{id}/decision`, `POST /simulation/actions/execute`, `GET /simulation/actions/{id}` | Supervisor decision; executor requires approved, unexpired/current plan and idempotency key; revalidate before transaction. |
| `GET /events`, `GET /agents/traces`, `GET /audit` | Read persisted event, trace and audit summaries filtered by scenario/correlation. |

Use status codes consistently: 200/201 success, 400 malformed request, 401/403 simulated role denied, 404 unknown ID, 409 invalid transition/stale slot/duplicate action, 422 deterministic policy validation failure, and 500 unexpected server error. Error responses include `success=false`, stable error code/message, null `data`, and correlation ID. Never return stack traces or secrets to the UI.

### Demo permission matrix

| Capability | Patient | Presenter | Supervisor |
|---|---:|---:|---:|
| Chat, view own journey, confirm own booking/session | Yes | No | No |
| View operational dashboards, agent traces, audit | No | Yes | Yes |
| Trigger, advance, reset a scenario | No | Yes | No |
| Approve/reject workforce or procedure plan | No | No | Yes |
| Execute approved action | No | No | Service only after supervisor approval |

Implement the role selector as a demo affordance, not production authentication. Backend route guards must still check the selected simulated role so UI hiding alone is not the control. Audit every scenario trigger and approval with actor role and timestamp.

## 14. Test Execution Matrix and Release Decision

| Test ID | Level | Test | Required result |
|---|---|---|---|
| T-01 | Unit | Seed integrity, fixed clock, reset twice | Stable IDs/counts/fixture values; no dangling references or scenario leakage. |
| T-02 | Unit/API | Book valid and invalid appointment requests | Confirmed valid booking once; missing confirmation, wrong patient, unknown slot, or occupied slot creates no booking. |
| T-03 | Unit/API | Safety escalation | Red-flag fixture stops scheduling and records escalation; no appointment/session exists. |
| T-04 | Unit/API | Session lifecycle | Confirmation required; valid state transitions only; completion and follow-up are persisted. |
| T-05 | Unit | Collision demand and candidate filters | Exact 4 RN + 1 trauma gap; valid four RN and one trauma candidates; all three seeded exclusions have expected reasons. |
| T-06 | API | Approval and execution boundary | Direct execution without approval, rejected plan, stale approval, or ineligible candidate makes no operational mutation. |
| T-07 | Unit/API | Procedure readiness/absence | `PROC-310` Ready -> At Risk -> Ready after valid approved replacement; expired certification excluded. |
| T-08 | Agent contract | Twelve agent construction/allowlists | All names construct and call only owned tools; trace records tool input/output summaries and status. |
| T-09 | Browser E2E | Scenario 1 patient flow | Seeded chat options, confirmation, simulated consult completion, Patient 360 and clinical view reflect one persisted appointment. |
| T-10 | Browser E2E | Scenario 2 collision flow | Trigger, pressure, grounded plan, exclusion evidence, reject path, then reset/approve path and shared update. |
| T-11 | Browser E2E | Scenario 3 staff absence flow | At Risk, replacement evidence, reject path, reset/approve path, readiness and audit update. |
| T-12 | Live integration | Gemini patient and operations coordinator smoke | Real Gemini calls ADK tools; results match tool records; timeout/error is visible and no false success occurs. |
| T-13 | Browser/manual | Critical accessibility/responsive check | Keyboard can book/approve/reset; status not color-only; no clipped/overlapping critical content at desktop and mobile widths. |

**Release decision:** mark a scenario Passed only when its API-backed browser flow, negative authorization/policy checks, and audit/trace assertions all pass. If a live Gemini outage blocks T-12, report the demo as functionally rehearsed with live AI integration blocked; do not count model-stub results as fulfillment of the live-AI criterion. Attach the actual test command and result to the day-three runbook.

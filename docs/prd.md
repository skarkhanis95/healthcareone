# HealthCareOne Agentic Healthcare Operations Simulation
## Product Requirements Document — v1.0

**Prepared for:** Kyndryl Academy Level 3 — Three-Day Client Simulation  
**Client:** HealthCareOne (fictional healthcare network)  
**Products:** CareFlow One + Workforce One  
**AI foundation:** Google ADK + Gemini API  
**Delivery:** Three days  
**Status:** Scope locked for implementation

---

# 1. Executive Summary

Kyndryl will demonstrate an agentic healthcare operations ecosystem for HealthCareOne, consisting of two connected platforms:

1. **CareFlow One — Intelligent Patient & Hospital Management**
   - Patient-facing agentic portal
   - Patient 360 and care journey
   - Clinical staff workspace
   - Hospital operations command centre

2. **Workforce One — Intelligent Workforce Augmentation**
   - Workforce command centre
   - Demand and capacity intelligence
   - Staff availability and skills matching
   - Cross-department and cross-hospital augmentation
   - Procedure readiness and workforce coordination

Both platforms operate on a shared **Kyndryl Agentic Intelligence Foundation**, providing agent orchestration, simulated integrations, policy enforcement, human approvals, audit trails and observability.

This is not a production healthcare information system. It is a polished, interactive, demonstration-grade simulation.

All patients, clinicians, employees, hospitals, appointments, procedures, rooms, schedules, events, source systems and operational actions are synthetic or simulated.

The AI layer must be real: Google ADK agents will call Gemini and use tools to inspect synthetic data, reason over operational context, coordinate tasks and propose or execute permitted simulated actions.

## 1.1 Central demonstration story

HealthCareOne wants to improve patient satisfaction, reduce avoidable readmissions, increase telehealth adoption and introduce AI into clinical and operational domains.

Kyndryl demonstrates how patient access and hospital operations can work as one connected, governed ecosystem:

- A patient describes a healthcare need, finds an appropriate doctor, books an appointment and can immediately start a simulated video consultation.
- A multi-vehicle collision creates a sudden emergency demand surge. Agents identify capacity pressure, recommend workforce augmentation across departments and hospitals, and evaluate non-emergency procedure changes to free resources.
- A scheduled procedure becomes at risk when a key staff member becomes unavailable. Agents identify qualified alternatives, validate readiness constraints and request supervisor approval.

## 1.2 Product principles

1. Simulation-first: do not build production systems or real healthcare integrations.
2. Real agentic intelligence: Gemini/ADK must perform actual reasoning and tool selection.
3. Polished enterprise UI: the experience should look like a credible enterprise product.
4. Repeatable demonstrations: deterministic seed data, known scenario outcomes and one-click reset.
5. Visible orchestration: users can inspect agent activity, tool calls, evidence, approvals and outcomes.
6. Human control: high-impact operational changes require human approval.
7. Safe healthcare boundaries: no diagnosis, treatment recommendations or autonomous clinical decisions.
8. Connected platforms: both products share operational events and state through the simulation layer.

---

# 2. HealthCareOne Strategic Alignment

HealthCareOne is a fictional healthcare network serving more than 8 million residents, with 12 hospitals and 45 outpatient clinics.

| Strategic objective | Stated target | Product contribution |
|---|---:|---|
| Patient satisfaction | +15% | Conversational access, appointment discovery, reduced booking friction and journey visibility |
| Avoidable readmissions | -10% | Discharge coordination, follow-up booking and post-visit continuity |
| Telehealth | 25% of outpatient visits | Immediate virtual consultation offered and launched from patient chat |
| AI adoption | AI in at least two clinical/operational domains | Patient access, hospital operations and workforce augmentation |

Additional scenario context:
- 48% of surveyed patients reported dissatisfaction with appointment wait times.
- 34% experienced delays during in-person visits.
- 65% expressed interest in a virtual assistant.
- 58% use the patient portal; 41% of portal users reported usability challenges.
- 72% rated care good or excellent.
- Previous AI initiatives struggled to scale due to integration, data, compliance and workflow challenges.

These are scenario facts, not measured outcomes of this prototype. Do not claim that the simulation has achieved HealthCareOne's targets.

## 2.1 Executive value narrative

- **CEO:** Better patient experience and visible digital transformation.
- **CIO:** Reusable, governed agentic architecture that works with existing systems rather than replacing them.
- **COO:** Better operational visibility, resilience and capacity coordination.
- **CFO:** Improved utilization of staff, rooms and procedure capacity.
- **Chief People & Culture:** Skills-based workforce augmentation, fatigue-aware recommendations and human oversight.
- **CMO:** Better care coordination and follow-up visibility without AI making clinical decisions.
- **CISO:** Synthetic data, simulated role-based access, policy controls and traceable agent activity.

---

# 3. Goals, Non-Goals and Success Criteria

## 3.1 Goals

- Deliver two connected, visually polished platforms.
- Demonstrate natural-language patient access from request to appointment booking.
- Demonstrate immediate virtual consultation launched from the same chat experience.
- Demonstrate network-level emergency surge and workforce augmentation.
- Demonstrate procedure readiness and replacement-staff coordination.
- Use Google ADK and a real Gemini API key.
- Provide synthetic datasets and mock APIs representing existing HealthCareOne systems.
- Provide a Demo Director Console for scenario triggering, reset and presentation.
- Make the application easy to run locally and resilient to intermittent AI API failures.

## 3.2 Non-goals

Do not build:
- Production EHR, EMR, PACS, pharmacy, HR, payroll or hospital scheduling systems.
- Real FHIR integrations or connections to HealthCareOne systems.
- Real patient registration, identity verification or patient records.
- Real doctor availability or actual appointment booking.
- Real video calling, WebRTC infrastructure or live doctor participation.
- Real SMS, WhatsApp, email, phone, ambulance or staff notifications.
- Payroll changes, employee transfers, shifts or real workforce assignments.
- Clinical diagnosis, treatment plans, prescriptions or autonomous care recommendations.
- Predictive models trained on real clinical data.
- Production-grade multi-tenant security or regulatory certification.
- Native mobile apps.
- A full patient mobile application.
- Kubernetes or distributed production infrastructure.

## 3.3 Demonstration success criteria

1. Presenter can launch and reset all scenarios without developer intervention.
2. Patient can describe a need, answer questions, receive two suitable synthetic options and book one through chat.
3. Patient can choose immediate virtual consultation and see a convincing simulated video-consultation room.
4. Presenter can trigger a multi-vehicle collision and see a coordinated workforce response.
5. Response includes cross-department and cross-hospital recommendations, elective procedure deferral options and human approval.
6. Staff absence triggers procedure-readiness workflow with replacement options and approval.
7. Both platforms visibly reflect shared events and approved simulated actions.
8. Agent activity is inspectable: reasoning summary, tool calls, evidence, approvals and outcomes.
9. No scenario depends on external healthcare systems or real patient information.
10. All three scenarios can be repeated reliably.

---

# 4. Product Architecture

## 4.1 Logical architecture

```text
                         USER EXPERIENCES
        ┌────────────────────────┐  ┌────────────────────────┐
        │      CareFlow One      │  │      Workforce One     │
        │ Patient Portal         │  │ Workforce Command      │
        │ Patient 360             │  │ Demand & Capacity       │
        │ Clinical Workspace     │  │ Skills & Availability   │
        │ Hospital Command       │  │ Procedure Readiness     │
        └────────────┬───────────┘  └────────────┬───────────┘
                     │                           │
                     └─────────────┬─────────────┘
                                   │
                   SHARED AGENTIC INTELLIGENCE
        ┌────────────────────────────────────────────────┐
        │ Google ADK Runtime + Gemini API                 │
        │ Coordinator and Specialist Agents              │
        │ Tool Registry / Policy Gate / Approval Service │
        │ Agent Trace / Audit / Observability             │
        └────────────────────────┬───────────────────────┘
                                 │
                      SIMULATION SERVICE LAYER
        ┌────────────────────────────────────────────────┐
        │ Synthetic Data Store (SQLite)                  │
        │ Mock APIs / System Adapters                    │
        │ Scenario & Event Engine                        │
        │ Simulated Action Executor                      │
        │ Shared Event Bus / WebSocket Updates            │
        └────────────────────────┬───────────────────────┘
                                 │
                       SIMULATED SOURCE SYSTEMS
        ┌────────────────────────────────────────────────┐
        │ MediCore EHR | SchedPlus | ShiftWise            │
        │ ImageLink    | PharmaTrack | ConnectCare        │
        │ FinEdge      | DocuCode                         │
        └────────────────────────────────────────────────┘
```

## 4.2 Existing systems to simulate

| System | Simulated purpose | Required data |
|---|---|---|
| MediCore EHR | Patient and encounter record | Patient demographics, encounter summaries, care-team references, discharge status |
| SchedPlus | Outpatient scheduling | Appointment slots, bookings, cancellations, clinic schedules |
| ShiftWise | Workforce management | Staff profiles, roles, skills, certifications, shifts, leave and availability |
| ImageLink | Radiology/PACS | Imaging order/status metadata only |
| PharmaTrack | Pharmacy workflow | Medication reconciliation status and synthetic task status |
| ConnectCare | Telehealth | Virtual session status and metadata |
| FinEdge | HR and finance | Department cost-centre and staffing cost estimates if useful |
| DocuCode | HIM/documentation | Discharge document and clinical note completion status |

These are fictional source-system representations. Implement only the data and mock operations required by the scenarios.

Source systems remain simulated systems of record. CareFlow One and Workforce One are operational experiences over those sources, not replacements for them.

## 4.3 Shared foundation

Working name: **Kyndryl Agentic Intelligence Foundation**.

Required capabilities:
- ADK agent runtime.
- Coordinator-led specialist execution.
- Tool registry with typed input/output contracts.
- Simulation data access tools.
- Simulated action tools.
- Policy checks and approval gates.
- Agent execution trace.
- Audit log.
- Error handling and fallback responses.
- Scenario correlation ID across events and agent runs.

Separate three tool classes:
- **Read tools:** retrieve synthetic information.
- **Recommendation tools:** create proposed plans without changing state.
- **Action tools:** change simulated state only after required policy and approval checks.

---

# 5. User Roles and Experiences

## 5.1 Patient

Uses CareFlow One to:
- Describe a healthcare need in chat.
- Answer clarifying questions.
- Select a seeded locality.
- Discover doctors and specialties.
- Compare in-person and virtual appointments.
- Book, reschedule or cancel simulated appointments.
- Start an immediate simulated video consultation.
- View appointment and care journey timeline.
- View simulated follow-up and discharge tasks.

## 5.2 Hospital operations manager

Uses the hospital command centre to:
- Monitor patient arrivals, occupancy, capacity and operational alerts.
- See emergency surge events.
- View department and hospital pressure.
- Inspect agent recommendations.
- Approve or reject operational plans.
- Monitor approved simulated actions.

## 5.3 Doctor / clinical staff

Uses the clinical workspace to:
- View today's appointments and procedures.
- View synthetic patient summary and journey.
- See virtual consultation requests and session state.
- See procedure readiness indicators.
- Review patient follow-up and discharge tasks.

This is not an EHR replacement.

## 5.4 Workforce supervisor

Uses Workforce One to:
- View workforce availability across departments and hospitals.
- Filter by role, skill, qualification, shift and location.
- Inspect demand-versus-capacity gaps.
- Review augmentation recommendations.
- Review elective procedure deferral options.
- Approve or reject proposed changes.
- View fatigue, rest and fairness warnings.

## 5.5 Demo presenter / administrator

Uses Demo Director Console to:
- Reset the simulation.
- Select and trigger scenarios.
- Advance or replay events.
- See scenario state.
- Open relevant product views.
- Pause or resume event playback.
- Restore baseline data.

---

# 6. CareFlow One — Functional Requirements

## 6.1 Patient Agentic Portal

### Landing experience

- Clean, modern, light-theme healthcare interface.
- Brand name: CareFlow One.
- Primary actions: Chat with CareFlow, Find a Doctor, My Appointments, My Care Journey.
- Visible “Simulation environment – synthetic data” label.
- Responsive desktop-first experience.

### Agentic chat

The chat is the primary patient interaction surface.

Example request:

> “I have severe pain in my left knee. I need to see a doctor urgently.”

The agent must:
1. Understand the request.
2. Recognize it as a care-access request, not a diagnosis request.
3. Ask concise follow-up questions.
4. Apply conservative emergency-warning screening.
5. If warning signs are reported, stop routine booking and direct the patient to emergency care.
6. Ask for location or allow seeded locality selection.
7. Identify an appropriate specialty using a fixed synthetic mapping.
8. Query synthetic doctors and availability through tools.
9. Return two ranked options with reasons, consultation mode, location and time.
10. Let the patient book directly in chat.
11. Confirm the simulated booking and update the patient journey.

The agent must not invent doctor names, availability or booking confirmations. Such information must come from tool results.

### Doctor discovery and manual booking

Provide a non-chat path:
- Search by doctor name or specialty.
- Filter by specialty, hospital/clinic, locality, consultation type and availability.
- Display doctor cards with synthetic avatar, specialty, hospital, experience band, next available slot and consultation modes.
- Open doctor detail view.
- Select an available slot.
- Confirm simulated appointment.
- Show booking reference.

### Appointment options

Each option must show:
- Doctor name and specialty.
- Hospital or clinic.
- In-person or virtual mode.
- Date and time.
- Location or “Online”.
- Short factual reason why it matches the request.
- Book action.

### In-chat virtual consultation

When an immediate virtual option is available:
1. Agent offers “Start virtual consultation now”.
2. Patient confirms.
3. Simulated appointment/session is created.
4. UI transitions to an embedded consultation experience while retaining CareFlow context.
5. Show synthetic doctor profile and “Doctor joining” state.
6. Display a video-call layout with doctor avatar/video placeholder, patient self-view placeholder and call controls.
7. Include microphone, camera, end-call and elapsed-time controls. These are simulation controls only.
8. Show session states: Waiting, Doctor connected, In consultation, Completed.
9. On end call, show a synthetic completion message without diagnosis or treatment advice.
10. Update patient journey and appointment history.
11. Offer a simulated follow-up booking action.

No real video stream, WebRTC, recording, microphone or camera access is required. Do not request device permissions.

### Patient 360 and journey timeline

Display:
- Synthetic patient ID.
- Upcoming and previous appointments.
- Care journey events.
- Consultation mode.
- Hospital/clinic.
- Follow-up status.
- Discharge status where relevant.
- Pending administrative tasks.

Example timeline:
1. Care request received.
2. Specialty identified.
3. Doctor options retrieved.
4. Appointment booked.
5. Patient checked in (simulated).
6. Consultation completed (simulated).
7. Follow-up scheduled.

### Patient communication simulation

Show in-app notifications only:
- Appointment booked.
- Virtual consultation ready.
- Consultation completed.
- Follow-up due.
- Discharge follow-up reminder.

Do not send real SMS, email or WhatsApp messages.

## 6.2 Clinical Staff Workspace

Provide:
- Today's appointment list.
- Patient summary and journey.
- Appointment type and status.
- Virtual consultation session status.
- Procedure list and readiness status.
- Follow-up tasks.
- Discharge coordination status.

Clinical data must be concise and synthetic. No clinical decision-making by AI.

## 6.3 Hospital Operations Command Centre

Display:
- Hospital selector for 12 synthetic hospitals.
- Emergency department arrivals.
- Inpatient census.
- Bed occupancy and available capacity.
- Department-level demand.
- Scheduled procedures.
- Pending discharges.
- Staff coverage summary.
- Active operational alerts.
- Agent recommendations and approvals.

Use charts, status cards, tables and event timelines. Data updates when scenario events occur and when simulated actions are approved.

Distinguish:
- Current simulated state.
- AI-generated recommendation.
- Pending approval.
- Approved action.
- Completed simulated action.

---

# 7. Workforce One — Functional Requirements

## 7.1 Workforce Command Centre

Display:
- Total synthetic staff.
- On-duty staff.
- Available staff.
- Staff on leave/unavailable.
- Department staffing coverage.
- Current demand and capacity.
- Critical skill shortages.
- Cross-hospital availability.
- Pending augmentation requests.
- Pending approvals.
- Workforce alerts.

Filters: hospital, department, role, skill and shift.

## 7.2 Staff profiles and availability

Each synthetic staff profile includes:
- Staff ID and display name.
- Home hospital.
- Department.
- Role/designation.
- Skills and skill levels.
- Certifications and expiry status.
- Current shift.
- Availability status.
- Current assignment.
- Workload indicator.
- Hours worked in current period.
- Rest/fatigue warning.
- Cross-hospital deployment eligibility.
- Generic policy flags where required.

Do not model real employees or use protected personal characteristics.

## 7.3 Demand and capacity intelligence

Use synthetic data from CareFlow One and mock source systems:
- Emergency arrivals and scenario demand.
- Current patient census.
- Synthetic acuity bands for operational planning.
- Admissions and discharges.
- Planned procedures.
- Room/bed availability.
- Required staff mix by department/procedure.
- Staff availability and skills.

Show demand-versus-capacity by hospital and department. Deterministic code calculates capacity gaps; AI explains and coordinates the response.

## 7.4 Workforce augmentation recommendations

The agent should:
1. Detect or receive an operational demand event.
2. Read current hospital and department capacity.
3. Identify workforce gaps by role and skill.
4. Search available qualified staff in the affected department.
5. Search other departments where policy permits.
6. Search other hospitals for cross-hospital augmentation candidates.
7. Check shift, certification, workload, rest and fatigue constraints.
8. Rank candidate options and explain evidence.
9. Identify seeded elective procedures that could be considered for rescheduling.
10. Create a proposed augmentation plan.
11. Submit the plan for supervisor approval.
12. Execute simulated changes only after approval.
13. Publish events so both platforms update.

Recommendations must not automatically change employee assignments.

## 7.5 Procedure readiness

For each procedure, display:
- Procedure ID and synthetic patient reference.
- Hospital and operating room.
- Scheduled time.
- Required roles and skills.
- Assigned staff.
- Staff availability.
- Room readiness.
- Patient preparation status.
- Documentation status.
- Overall readiness: Ready, At Risk or Blocked.

When a required staff member becomes unavailable:
1. Detect the gap.
2. Identify the role/skill requirement.
3. Find eligible replacement candidates.
4. Validate certification and shift constraints.
5. Check room and patient readiness.
6. Present replacement options and consequences.
7. Request supervisor approval.
8. Update simulated assignment and readiness after approval.

AI must not make clinical priority decisions. Procedure priority and rescheduling eligibility are seeded operational attributes.

---

# 8. Three Flagship Demonstration Scenarios

## Scenario 1 — Agentic Patient Access and Immediate Teleconsultation

### Objective

Demonstrate a patient moving from a natural-language care request to an appropriate appointment and immediate virtual consultation, with a connected patient journey.

### Initial state

- Patient: Alex Morgan (synthetic).
- Location: North District.
- Request: severe left knee pain; wants urgent care.
- Seeded emergency red flags: denied in the happy-path scenario.
- Specialty mapping: Orthopaedics.
- Doctor A: Dr. Meera Shah, North District Hospital, virtual consultation available now.
- Doctor B: Dr. Arjun Rao, North District Clinic, in-person slot available later today.
- ConnectCare mock service: immediate simulated session available.
- SchedPlus mock service: both slots available.

### Presenter flow

1. Open patient portal as Alex Morgan.
2. Enter symptom/request in chat.
3. Agent asks safety and location questions.
4. Patient answers and selects location.
5. Agent calls patient-context, specialty mapping, doctor search and availability tools.
6. Agent presents two appointment options.
7. Patient selects immediate virtual consultation.
8. Agent confirms simulated booking.
9. Agent initiates ConnectCare simulated session.
10. Patient enters video consultation room.
11. Simulated doctor joins.
12. Presenter ends the call.
13. Appointment and journey timeline update.
14. Show clinical staff workspace reflecting completed virtual appointment.

### Expected outcome

- Real ADK/Gemini conversation.
- Tool calls visible in trace.
- Two tool-grounded appointment options.
- Simulated booking reference.
- Convincing video consultation UI.
- Updated Patient 360 and staff view.

### Alternate path

Patient chooses in-person appointment. Booking completes and journey reflects an in-person visit.

### Safety branch

If the patient reports a seeded emergency warning sign, the agent must not continue routine booking. It displays emergency-care guidance and logs a safety escalation.

## Scenario 2 — Multi-Vehicle Collision: Network-Wide Workforce Augmentation

### Objective

Demonstrate how sudden emergency demand is detected, assessed and addressed through coordinated patient operations and workforce augmentation.

### Initial state

- Network contains 12 synthetic hospitals.
- Incident hospital: HealthCareOne Central.
- Support hospitals: HealthCareOne North and HealthCareOne West.
- Multi-vehicle collision is triggered through Demo Director Console.
- Seeded ambulance arrivals increase demand.
- Emergency department at Central moves into critical pressure.
- Emergency nursing and trauma-support role gaps are seeded.
- Some staff are available at nearby hospitals.
- Some elective procedures are explicitly marked operationally deferrable.

### Presenter flow

1. Open Hospital Command Centre and Workforce Command Centre.
2. Trigger “Multi-Vehicle Collision”.
3. Event engine publishes incident and arrival events.
4. CareFlow updates arrivals, capacity pressure and affected departments.
5. Patient Flow / Operations Intelligence agents assess impact.
6. Workforce Demand Agent calculates role-based staffing gaps.
7. Skills Matching and Availability agents search candidates across departments and hospitals.
8. Fatigue & Compliance Agent excludes unsuitable candidates and explains constraints.
9. Workforce Optimization identifies seeded elective procedures that could be rescheduled.
10. Workforce Coordinator assembles a proposed response plan.
11. Supervisor reviews the plan, candidate list, procedure impacts and rationale.
12. Supervisor approves selected actions.
13. Simulation executor updates assignments, procedure statuses and capacity indicators.
14. Both platforms receive shared events and update.
15. Audit timeline records proposal, approver and simulated actions.

### Example response plan

- Reassign eligible staff within Central.
- Request qualified support from North and West.
- Use only candidates passing availability, qualification, shift and rest checks.
- Recommend deferring one explicitly deferrable elective procedure.
- Preserve critical procedures and staffing minimums.
- Show any remaining capacity gap.

### Important constraints

- No real emergency services, ambulance dispatch or patient transfers.
- No real employee communication or assignment.
- No autonomous staff reassignment.
- Do not portray AI as replacing clinical incident command.

## Scenario 3 — Procedure at Risk: Staff Absence and Readiness Recovery

### Objective

Demonstrate how agents protect procedure readiness when a critical team member becomes unavailable.

### Initial state

- Synthetic procedure scheduled at HealthCareOne Central.
- Required staff member becomes unavailable due to simulated absence.
- Procedure requirements include explicit roles and skills.
- Candidate replacements exist across the network, with varied availability and certification states.
- Room and patient preparation statuses are seeded.

### Presenter flow

1. Open Procedure Readiness.
2. Trigger “Required Staff Member Unavailable”.
3. Procedure becomes At Risk.
4. Procedure Readiness Agent identifies missing role/skill.
5. Staff Availability and Skills Matching agents search candidates.
6. Fatigue & Compliance Agent validates eligibility and excludes unsuitable candidates.
7. Room, patient preparation and documentation are checked.
8. Agent proposes replacement or operational rescheduling.
9. Supervisor reviews and approves or rejects.
10. Simulated executor updates assignment and readiness.
11. Both platforms update.
12. Audit trail shows complete workflow.

### Expected outcome

- Procedure moves from Ready to At Risk.
- AI-generated replacement options with evidence.
- Policy-based exclusions.
- Human approval.
- Procedure returns to Ready or remains At Risk with an explained reason.
- Shared platform updates.

---

# 9. Agent Design and Responsibilities

Use coordinator-led multi-agent orchestration. Agents must have narrow responsibilities and explicit tools. Avoid agents that merely pass messages without adding value.

## 9.1 Shared orchestration agents

### 1. Experience Coordinator

- Entry point for patient-facing requests.
- Determines intent and delegates to specialist agents.
- Maintains conversation context and scenario correlation ID.
- Does not invent source-system facts.
- Returns concise user-facing explanations.

### 2. Operations Intelligence Coordinator

- Entry point for operations and workforce scenarios.
- Coordinates Patient Flow, Workforce Demand, Skills Matching and Procedure Readiness agents.
- Aggregates evidence and recommendations.
- Ensures approval-required actions are not executed prematurely.

## 9.2 CareFlow One agents

### 3. Patient Access Agent

Responsibilities:
- Understand appointment intent.
- Ask for missing information.
- Apply fixed safety-screening rules.
- Identify specialty using seeded mapping.
- Request doctor and availability search.
- Present grounded options.
- Initiate booking only after patient selection and confirmation.

Tools:
- `get_patient_context`
- `screen_emergency_red_flags`
- `get_location_options`
- `map_request_to_specialty`
- `search_doctors`
- `get_doctor_availability`
- `create_simulated_appointment`
- `get_appointment_details`

### 4. Patient Journey Agent

Responsibilities:
- Retrieve synthetic journey events.
- Summarize upcoming and completed steps.
- Identify pending administrative follow-up tasks.
- Update journey after simulated events.

Tools:
- `get_patient_journey`
- `get_patient_appointments`
- `get_follow_up_tasks`
- `append_journey_event`

### 5. Virtual Care Agent

Responsibilities:
- Check simulated virtual session availability.
- Create consultation session after patient confirmation.
- Return session state and UI launch metadata.
- Complete simulated session when ended.
- Trigger follow-up task.

Tools:
- `check_virtual_session_availability`
- `create_virtual_session`
- `get_virtual_session_status`
- `complete_virtual_session`
- `create_simulated_follow_up`

### 6. Patient Flow Agent

Responsibilities:
- Summarize hospital-level patient flow.
- Identify seeded capacity pressure and operational bottlenecks.
- Explain impact of arrivals, admissions, discharges and procedures.
- Provide operational facts to Workforce One.

Tools:
- `get_hospital_capacity`
- `get_department_census`
- `get_arrival_events`
- `get_pending_discharges`
- `get_scheduled_procedures`

## 9.3 Workforce One agents

### 7. Workforce Demand Agent

Responsibilities:
- Translate patient demand and operational events into role-based staffing requirements.
- Calculate gaps using deterministic rules and seeded staffing ratios.
- Explain demand drivers.

Tools:
- `get_staffing_requirements`
- `get_department_staffing`
- `calculate_staffing_gap`
- `get_network_capacity`

### 8. Staff Availability Agent

Responsibilities:
- Search available staff by hospital, department, role and shift.
- Return current assignment and availability.
- Exclude unavailable staff.

Tools:
- `search_available_staff`
- `get_staff_profile`
- `get_staff_shift`
- `get_staff_assignment`

### 9. Skills Matching Agent

Responsibilities:
- Match required roles and skills to candidates.
- Validate certification and skill requirements.
- Rank eligible candidates and explain match.
- Never recommend candidates who fail mandatory seeded requirements.

Tools:
- `match_staff_skills`
- `check_certification_validity`
- `get_role_requirements`

### 10. Fatigue & Compliance Agent

Responsibilities:
- Check shift, rest, workload, overtime and policy flags.
- Exclude candidates who violate hard constraints.
- Flag soft constraints for supervisor review.
- Explain exclusions.

Tools:
- `check_staff_constraints`
- `get_workload_summary`
- `get_deployment_policy`

### 11. Procedure Readiness Agent

Responsibilities:
- Evaluate staffing, room, patient preparation and documentation readiness.
- Identify cause of procedure risk.
- Search for replacement options.
- Recommend readiness recovery plan.

Tools:
- `get_procedure_details`
- `get_procedure_team_requirements`
- `get_room_readiness`
- `get_patient_preparation_status`
- `get_documentation_status`
- `evaluate_procedure_readiness`

### 12. Workforce Coordinator

Responsibilities:
- Assemble staffing augmentation plans.
- Identify cross-department and cross-hospital options.
- Include eligible procedure deferral recommendations where seeded policy permits.
- Submit plan for human approval.
- Execute only approved simulated actions.

Tools:
- `create_augmentation_plan`
- `get_augmentation_plan`
- `submit_plan_for_approval`
- `execute_approved_augmentation`
- `get_plan_execution_status`

## 9.4 Agent implementation rules

- Use ADK agents and real Gemini calls.
- Use structured tool schemas and typed results.
- Keep hard business constraints in deterministic code, not only prompts.
- Use AI for intent understanding, synthesis, coordination and explanation.
- Tools are the only way agents access or change simulated source data.
- Never let an agent fabricate successful actions.
- Every tool call returns a structured result and is logged.
- Every run carries scenario ID, session ID and correlation ID.
- Use bounded retries and timeouts.
- If the model/API fails, display an error and allow retry or use a clearly labeled deterministic fallback. Never pretend fallback output was AI reasoning.

---

# 10. Simulation Engine and Synthetic Data

## 10.1 General rules

- All data is synthetic and generated locally.
- Seed the database on first startup.
- Provide a reset operation restoring baseline data.
- Use stable IDs and deterministic scenario seeds.
- Scenario event generation must be repeatable.
- Keep a simulation clock or event timeline where useful.
- No external APIs except Gemini.
- No real patient or staff data.

## 10.2 Seed dataset

Recommended minimum:

| Entity | Quantity |
|---|---:|
| Hospitals | 12 |
| Outpatient clinics | 45 |
| Patients | 150 |
| Doctors | 50 |
| Non-physician staff | 300 |
| Departments | 10 per hospital template |
| Appointments | 250 |
| Procedures | 40 |
| Rooms / operating rooms | 60 |
| Skill types | 20 |
| Certification types | 10 |
| Patient journey events | 300 |
| Workforce shifts | 400 |
| Synthetic alerts | 30 |

These are demonstration targets, not a national-scale data platform requirement. Smaller datasets are acceptable if every scenario is fully supported.

## 10.3 Suggested hospital network

1. HealthCareOne Central
2. HealthCareOne North
3. HealthCareOne West
4. HealthCareOne East
5. HealthCareOne South
6. HealthCareOne Riverside
7. HealthCareOne Lakeside
8. HealthCareOne Valley
9. HealthCareOne Metro
10. HealthCareOne Greenfield
11. HealthCareOne Summit
12. HealthCareOne Community

Use synthetic locality labels. Do not use real hospital names or addresses.

## 10.4 Core data entities

### Patient
- `patient_id`
- `display_name`
- `age_band`
- `locality_id`
- `preferred_contact_mode`
- `journey_status`
- `created_at`

### Doctor
- `doctor_id`
- `display_name`
- `specialty_id`
- `hospital_id`
- `clinic_id`
- `experience_band`
- `consultation_modes`
- `active_status`

### Appointment
- `appointment_id`
- `patient_id`
- `doctor_id`
- `hospital_id`
- `appointment_type` (in_person / virtual)
- `start_time`
- `status`
- `booking_reference`
- `scenario_id`

### Staff
- `staff_id`
- `display_name`
- `home_hospital_id`
- `department_id`
- `role_id`
- `skills`
- `certifications`
- `shift_start`
- `shift_end`
- `availability_status`
- `current_assignment_id`
- `hours_worked`
- `rest_status`
- `cross_hospital_eligible`

### Procedure
- `procedure_id`
- `patient_id`
- `hospital_id`
- `room_id`
- `scheduled_start`
- `procedure_category`
- `priority_band` (seeded operational attribute)
- `required_roles`
- `assigned_staff`
- `patient_preparation_status`
- `room_readiness_status`
- `documentation_status`
- `readiness_status`
- `deferrable`

### Hospital capacity
- `hospital_id`
- `department_id`
- `current_census`
- `capacity`
- `available_capacity`
- `incoming_arrivals`
- `staffing_requirement`
- `staffing_available`
- `pressure_status`

### Simulation event
- `event_id`
- `scenario_id`
- `event_type`
- `entity_type`
- `entity_id`
- `payload_json`
- `created_at`
- `processed_at`
- `status`

### Approval
- `approval_id`
- `plan_id`
- `requested_by_agent`
- `approval_type`
- `summary`
- `evidence_json`
- `status`
- `approved_by`
- `decision_note`
- `created_at`
- `decided_at`

### Agent trace
- `trace_id`
- `scenario_id`
- `correlation_id`
- `agent_name`
- `task_summary`
- `tool_name`
- `tool_input_json`
- `tool_output_json`
- `status`
- `duration_ms`
- `created_at`

## 10.5 Synthetic data quality

Seed data must be internally consistent:
- Every appointment references an existing patient, doctor and hospital/clinic.
- Every doctor has a valid specialty and consultation mode.
- Every staff member has a home hospital, department, role and shift.
- Every baseline procedure has staff who satisfy its requirements.
- Scenario 2 intentionally creates a shortage and eligible support candidates.
- Scenario 3 intentionally makes one required staff member unavailable while providing at least one viable replacement and one unsuitable candidate.
- Scenario reset recreates the same baseline and event sequence.

---

# 11. Mock APIs and Tool Contracts

All mock APIs are local. ADK tools call the simulation service layer rather than manipulating UI state or database tables directly.

## 11.1 API conventions

Base path: `/api/v1`

Use JSON request/response bodies with:
- `success`
- `data`
- `error` (nullable)
- `correlation_id`

Use consistent HTTP status codes. All simulated write endpoints create audit events.

## 11.2 Required API groups

### Patient and scheduling
- `GET /patients/{patient_id}`
- `GET /patients/{patient_id}/journey`
- `GET /doctors`
- `GET /doctors/{doctor_id}`
- `GET /availability`
- `POST /appointments`
- `GET /appointments/{appointment_id}`
- `POST /appointments/{appointment_id}/cancel`
- `POST /appointments/{appointment_id}/reschedule`

### Virtual care
- `POST /virtual-sessions`
- `GET /virtual-sessions/{session_id}`
- `POST /virtual-sessions/{session_id}/complete`

### Hospital operations
- `GET /hospitals`
- `GET /hospitals/{hospital_id}/capacity`
- `GET /departments/{department_id}/census`
- `GET /procedures`
- `GET /procedures/{procedure_id}`

### Workforce
- `GET /staff`
- `GET /staff/{staff_id}`
- `GET /staff/availability`
- `POST /workforce/augmentation-plans`
- `GET /workforce/augmentation-plans/{plan_id}`

### Approval and simulated execution
- `POST /approvals`
- `POST /approvals/{approval_id}/decision`
- `POST /simulation/actions/execute`
- `GET /simulation/actions/{action_id}`

### Demo Director
- `GET /simulation/scenarios`
- `POST /simulation/scenarios/{scenario_id}/trigger`
- `POST /simulation/reset`
- `POST /simulation/events/{event_id}/advance`
- `GET /simulation/state`

### Observability
- `GET /agents/traces`
- `GET /agents/traces/{trace_id}`
- `GET /audit`
- `GET /events`

## 11.3 Appointment tool example

Input:
```json
{
  "patient_id": "PAT-1001",
  "doctor_id": "DOC-0021",
  "appointment_type": "virtual",
  "slot_id": "SLOT-IMMEDIATE-01",
  "patient_confirmation": true,
  "scenario_id": "PATIENT_ACCESS"
}
```

Output:
```json
{
  "success": true,
  "data": {
    "appointment_id": "APT-5001",
    "booking_reference": "HCO-DEMO-5001",
    "status": "confirmed",
    "appointment_type": "virtual"
  },
  "error": null,
  "correlation_id": "CORR-DEMO-001"
}
```

The tool validates slot availability and patient confirmation before creating the booking.

## 11.4 Augmentation plan contract

Input includes:
- Scenario ID.
- Affected hospital ID.
- Recommended staff IDs, target departments and rationale.
- Procedure recommendations and rationale.

Output includes:
- Plan ID.
- Recommended staff and procedures.
- Eligibility checks.
- Policy warnings.
- Approval status.

No assignments or procedure changes occur until approval.

---

# 12. Human Approval, Policy and Audit

## 12.1 Approval-required actions

Always require explicit human approval before:
- Reassigning staff.
- Requesting cross-hospital augmentation.
- Changing staff assignments or shifts.
- Deferring or rescheduling a procedure.
- Changing procedure team assignments.
- Any material hospital operational change.

Patient appointment booking is allowed after explicit patient confirmation. Virtual consultation initiation requires explicit patient confirmation.

## 12.2 Approval interface

Every proposed plan shows:
- Proposed action.
- Why it is proposed.
- Supporting synthetic data.
- Staff, department and hospital affected.
- Expected operational impact.
- Constraints checked.
- Warnings and exclusions.
- Approve / Reject.
- Optional decision note.

## 12.3 Audit requirements

Record:
- User/presenter initiating scenario.
- Scenario and event IDs.
- Agent name and task.
- Tool calls and structured results.
- Recommendation generated.
- Policy checks.
- Approval decision and approver role.
- Simulated action executed.
- Before/after state references.
- Timestamp and correlation ID.

Provide an audit timeline. Do not expose hidden chain-of-thought. Display concise reasoning summaries, evidence and tool traces.

---

# 13. UI / UX Requirements

## 13.1 Design direction

- Light theme only.
- Calm, professional healthcare enterprise aesthetic.
- Clear hierarchy and high information density without clutter.
- Modern typography and consistent spacing.
- Restrained accent colors for status and actions.
- Avoid dark command-centre styling.
- Responsive layouts, cards, tables, charts, drawers and timelines.
- Synthetic names, initials or generated avatars; do not spend time sourcing real doctor photography.
- All screens visibly indicate simulation status.

## 13.2 Navigation

**CareFlow One**
- Patient Portal
- Patient 360
- Clinical Workspace
- Hospital Command Centre

**Workforce One**
- Workforce Overview
- Staff Directory
- Demand & Capacity
- Augmentation Plans
- Procedure Readiness

**Shared**
- Agent Activity
- Approvals
- Audit Timeline
- Demo Director Console

## 13.3 Agent activity panel

Provide a collapsible panel showing:
- Current agent.
- Current task.
- Delegated agents.
- Tools called.
- Tool results summarized.
- Recommendation status.
- Approval status.
- Execution result.

Example activity labels:
- “Checking patient location”
- “Mapping request to specialty”
- “Searching available orthopaedic doctors”
- “Checking immediate virtual consultation availability”
- “Comparing workforce capacity across hospitals”
- “Validating certification and shift constraints”

Do not show hidden reasoning or internal prompts.

## 13.4 Visual feedback

Use:
- Toasts for simulated action completion.
- Status chips: Ready / At Risk / Blocked / Pending Approval / Approved / Completed.
- Loading states during agent execution.
- Event timeline for scenario progression.
- Clear empty, error and retry states.
- Confirmation dialogs for booking and supervisor approval.

---

# 14. Demo Director Console

This is mandatory, not optional.

Capabilities:
- Reset all synthetic data to baseline.
- Select one of three scenarios.
- Trigger scenario.
- Advance events manually or play sequence.
- Pause/resume event playback.
- View scenario progress and expected checkpoints.
- Open relevant product screens.
- Reset a single scenario or entire environment.
- Show simulation time and active scenario.

Scenario controls:
1. Patient Access: reset patient, start patient conversation, seed immediate virtual availability.
2. Mass Casualty: trigger collision, advance arrivals, initiate agent response, release approvals.
3. Procedure Readiness: trigger staff absence, initiate replacement search, submit approval.

Presenter must be able to recover from a failed AI call without corrupting simulation state.

---

# 15. Technical Architecture and Implementation Choices

## 15.1 Recommended stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + TypeScript |
| UI components | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Backend | Python + FastAPI |
| Agent framework | Google ADK |
| LLM | Gemini API |
| Database | SQLite |
| Real-time updates | WebSockets |
| API contracts | Pydantic / OpenAPI |
| Execution | Single-machine local setup |

Do not introduce distributed infrastructure. Run locally with a small number of processes.

## 15.2 Suggested repository structure

```text
healthcareone-simulation/
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── layouts/
│       ├── pages/
│       ├── features/
│       │   ├── patient-portal/
│       │   ├── patient-360/
│       │   ├── clinical-workspace/
│       │   ├── hospital-command/
│       │   ├── workforce/
│       │   ├── procedures/
│       │   ├── approvals/
│       │   └── demo-director/
│       └── services/
├── backend/
│   └── app/
│       ├── main.py
│       ├── api/
│       ├── models/
│       ├── schemas/
│       ├── database/
│       ├── simulation/
│       ├── mock_systems/
│       ├── services/
│       ├── policies/
│       ├── audit/
│       └── agents/
│           ├── coordinator/
│           ├── careflow/
│           ├── workforce/
│           └── tools/
├── docs/
│   ├── PRD.md
│   ├── API_CONTRACTS.md
│   ├── AGENT_DESIGN.md
│   └── DEMO_RUNBOOK.md
├── .env.example
└── README.md
```

This is a suggested structure. It may be simplified, but separation between UI, agents, simulation data, policies and action execution must be preserved.

## 15.3 Environment configuration

Use `.env` for:
- `GOOGLE_API_KEY`
- `GEMINI_MODEL`
- `DATABASE_URL`
- `APP_ENV`
- `SIMULATION_MODE=true`

Never commit API keys. Include `.env.example` with placeholders. Provide setup instructions and startup health check.

## 15.4 Agent runtime requirements

- Use a Gemini model supported by the installed Google ADK version.
- Keep model selection configurable.
- Define agents and tools in code with clear descriptions.
- Use structured outputs where appropriate.
- Limit delegation depth and tool-call loops.
- Set sensible timeouts and retries.
- Log model errors without exposing secrets.
- Provide a “Test Gemini connection” health check.
- Include deterministic fallback only if clearly labeled as simulation, not live AI.

---

# 16. Non-Functional Requirements

| Area | Requirement |
|---|---|
| Startup | Application starts locally using documented commands |
| Responsiveness | UI interactions feel immediate; long agent runs show progress |
| AI latency | Display progress and allow reasonable timeout/retry |
| Reliability | Scenario reset restores known baseline |
| Data integrity | References and constraints remain consistent |
| Observability | Every tool call and simulated action is traceable |
| Safety | No real patient data or real-world clinical actions |
| Security hygiene | API key stored only in environment variables |
| Accessibility | Readable contrast, keyboard-accessible controls and clear labels |
| Demo usability | Presenter can trigger and recover scenarios without developer intervention |

---

# 17. Three-Day Delivery Plan

## Day 1 — Foundation and UI

Must complete:
- Repository and local startup.
- React/Vite shell and navigation.
- FastAPI service.
- SQLite schema and seed data.
- Simulation reset.
- Mock source-system adapters.
- Hospital, patient, doctor, staff and procedure dashboards.
- Google ADK + Gemini connectivity test.
- Demo Director Console skeleton.

**Exit criteria:** Both platform shells are navigable, data is visible and consistent, reset works, Gemini can be called through ADK, and at least one tool reads synthetic data.

## Day 2 — Agentic scenarios

Must complete:
- Patient Access Agent and booking tools.
- Doctor search and availability.
- Virtual Care Agent and simulated consultation room.
- Workforce demand and skills matching agents.
- Mass-casualty event injection.
- Augmentation plan and approval workflow.
- Shared event updates between platforms.

**Exit criteria:** Patient completes booking and simulated virtual consultation. Mass-casualty scenario generates grounded workforce plan. Approval changes simulated state and both dashboards update.

## Day 3 — Procedure readiness and polish

Must complete:
- Procedure Readiness Agent.
- Staff absence event.
- Replacement search and approval.
- Agent activity and audit views.
- Demo Director Console complete.
- Error handling, reset/replay and visual polish.
- Rehearsal of all scenarios.

**Exit criteria:** All three demos work end-to-end, can be reset and replayed, AI and simulation actions are visibly distinguished, and presenter can complete the story without editing data or using developer tools.

## 17.1 Priority classification

### P0 — Mandatory

- Patient chat and doctor discovery.
- Appointment availability and booking.
- Immediate simulated video consultation.
- Patient journey timeline.
- Hospital command centre.
- Workforce command centre.
- Mass-casualty event.
- Staff search and augmentation recommendations.
- Approval workflow.
- Procedure readiness scenario.
- ADK/Gemini integration.
- Synthetic data and reset.
- Agent trace and audit.
- Demo Director Console.

### P1 — Include if time permits after P0

- Manual doctor filters and richer doctor profile.
- Patient appointment reschedule/cancel.
- More detailed discharge follow-up journey.
- Additional hospital comparison views.
- Advanced dashboard filters and chart interactions.
- More detailed workforce fairness explanations.

### P2 — Explicitly out of scope

- Real video calling.
- Real FHIR integration.
- Real EHR connectivity.
- Real patient authentication.
- Native mobile applications.
- Production-grade optimization algorithms.
- Predictive clinical models.
- Real staff messaging or deployment.
- Payment, insurance or pharmacy workflows.

---

# 18. Acceptance Criteria

## 18.1 Patient access

- [ ] Patient can enter free-text request.
- [ ] Agent asks for missing location/context.
- [ ] Emergency safety branch is applied before routine booking.
- [ ] Specialty is derived through defined mapping/tool.
- [ ] Two doctor options are retrieved from synthetic data.
- [ ] Availability is tool-grounded.
- [ ] Patient can book one option through chat.
- [ ] Booking is persisted and appears in Patient 360.
- [ ] Manual doctor search and booking also work.

## 18.2 Virtual consultation

- [ ] Agent offers immediate virtual consultation when seeded availability exists.
- [ ] Patient explicitly confirms.
- [ ] Simulated session is created.
- [ ] Patient enters convincing video-call UI.
- [ ] Simulated doctor can join.
- [ ] Patient can end session.
- [ ] Session status and journey timeline update.
- [ ] No camera/microphone permissions or real video infrastructure are used.

## 18.3 Workforce surge

- [ ] Presenter can trigger collision scenario.
- [ ] Hospital capacity and arrival data update.
- [ ] Agent detects staffing gaps using tools.
- [ ] Candidate staff are retrieved from seeded data.
- [ ] Mandatory skill/certification/shift constraints are enforced.
- [ ] Ineligible staff are excluded with explanations.
- [ ] Cross-hospital recommendations are shown.
- [ ] Eligible elective procedure deferral options are identified.
- [ ] Supervisor approval is required.
- [ ] Approved actions update synthetic assignments and dashboards.
- [ ] Audit records the workflow.

## 18.4 Procedure readiness

- [ ] Presenter can trigger staff absence.
- [ ] Procedure status changes to At Risk.
- [ ] Agent identifies missing requirement.
- [ ] Candidate replacements are evaluated.
- [ ] Room, patient preparation and documentation are checked.
- [ ] Supervisor approval is required.
- [ ] Approved action updates procedure readiness.
- [ ] Both platforms reflect the change.

## 18.5 Platform and demo operations

- [ ] One-click reset works.
- [ ] All three scenarios can be replayed.
- [ ] Gemini API connection is verified.
- [ ] Agent activity and tool calls are visible.
- [ ] Simulated actions are clearly labeled.
- [ ] No real patient or employee data is present.
- [ ] API keys are not committed or shown in the UI.

---

# 19. Demo Presentation Runbook

Suggested final-day narrative: approximately 12–15 minutes.

### Opening — 1 minute

“HealthCareOne's challenge is not simply digitizing individual workflows. It is connecting the patient experience with the operational decisions that make care possible.”

### Demo 1 — Patient access and virtual care — 4 minutes

- Start with patient chat.
- Describe the knee pain.
- Let the agent ask questions and retrieve two options.
- Book immediate virtual consultation.
- Show simulated video consultation.
- Show Patient 360 and clinical workspace.

### Demo 2 — Mass-casualty surge — 5 minutes

- Show normal hospital capacity.
- Trigger multi-vehicle collision.
- Show arrivals and capacity pressure.
- Show agents identifying workforce gaps and cross-hospital candidates.
- Show procedure deferral recommendation.
- Approve plan.
- Show both platforms updating.

### Demo 3 — Procedure readiness — 3 minutes

- Trigger staff absence.
- Show procedure becoming At Risk.
- Show replacement options and constraints.
- Approve replacement.
- Show procedure returning to Ready.

### Closing — 1–2 minutes

Emphasize:
- Two connected business platforms.
- Real agent reasoning and tool execution.
- Simulated systems demonstrating integration patterns.
- Human governance and auditability.
- Reusable architecture that can be connected to real systems in a future implementation.

Do not claim the prototype is production-ready or that it has already delivered HealthCareOne's strategic KPI improvements.

---

# 20. Implementation Guardrails for AI Coding Agents

This section is mandatory context for every coding agent implementing the PRD.

1. **Do not research healthcare systems, standards, vendors or real hospitals.** This is a fictional simulation. Required business rules and data are specified here.
2. **Do not build production integrations.** Implement local mock adapters and synthetic data.
3. **Do not expand scope.** Build the three scenarios and required screens before optional features.
4. **Do not hardcode AI conversation outcomes.** Use Google ADK and Gemini for real intent understanding, agent coordination and tool selection.
5. **Do hardcode deterministic business constraints.** Availability, mandatory qualifications, rest rules, procedure deferrability and approval requirements must be validated by code.
6. **Do not let the LLM invent source facts.** Doctors, slots, staff, capacity, procedures and booking results must come from tools.
7. **Do not allow unapproved workforce or procedure changes.**
8. **Do not build real telehealth infrastructure.** Consultation is a UI and state simulation.
9. **Do not use real patient or employee information.** All records must be synthetic.
10. **Do not build production authentication.** Use simple demo role selection or seeded personas.
11. **Do not add Kubernetes, distributed microservices or complex infrastructure.**
12. **Do not hide simulation status.** Clearly label simulated records and actions.
13. **Do not expose hidden chain-of-thought.** Display concise reasoning summaries, evidence and tool traces.
14. **Prioritize end-to-end flows over breadth.** A complete scenario is more valuable than many unfinished screens.
15. **Keep the app runnable locally.** Provide exact install, environment setup, seed, reset and run commands.
16. **Keep a working demo after every milestone.** Avoid large untested batches of changes.
17. **When a requirement is ambiguous, prefer the smallest implementation that supports the stated demonstration.** Do not spend time researching or inventing additional requirements.

---

# 21. Definition of Done

PRD v1.0 is implemented when:
- CareFlow One and Workforce One are visually complete enough for executive demonstration.
- Shared ADK/Gemini agent foundation is operational.
- All three scenarios work end-to-end.
- Synthetic source systems, mock APIs and simulation events support the flows.
- Patient appointment booking and immediate simulated video consultation work.
- Emergency surge recommendations, approvals and simulated execution work.
- Procedure readiness recovery works.
- Shared state is visible across both platforms.
- Agent traces, approvals and audit history are inspectable.
- Demo Director Console can reset and replay every scenario.
- Full demonstration can be rehearsed repeatedly without manual database edits.

**Final scope statement:** Build a polished, repeatable, agentic healthcare operations simulation in three days. Real AI; simulated healthcare systems, data, events and actions. Two connected platforms. Three executive-ready demonstrations. Human-governed operational changes.
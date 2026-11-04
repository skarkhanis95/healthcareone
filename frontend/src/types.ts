export interface Scenario { id: string; name?: string; status: string }
export interface Doctor { name: string; specialty: string; location: string }
export interface Slot {
  id: string; doctor_id: string; starts_at: string; mode: string; available: boolean; doctor: Doctor;
}
export interface Hospital {
  id: string; name: string; locality: string; ed_census: number;
  ed_capacity: number; projected_arrivals: number; pressure: string;
}
export interface Staff {
  id: string; name: string; role: string; hospital_id: string;
  available: boolean; skills: string[]; eligible?: boolean; reason?: string;
}
export interface Procedure {
  id: string; name: string; readiness: string; scheduled_at: string;
  room: string; room_ready: boolean; patient_prepared: boolean;
  documentation_complete: boolean; team: Staff[]; readiness_reasons: string[];
}
export interface Plan {
  id: string; scenario_id: string; status: string; selected_staff_ids: string[];
  defer_procedure: boolean; evidence: { eligible: Staff[]; excluded: Staff[] };
  approval?: { decision: string; actor: string; notes: string };
}
export interface DemoState {
  simulation_time: string; counts: Record<string, number>; scenarios: Scenario[]; synthetic_data: boolean;
}
export interface Appointment {
  id: string; doctor_id: string; starts_at: string; mode: string; status: string; slot_id?: string;
}
export interface VirtualSession { id: string; appointment_id?: string; status: string }
export interface JourneyEvent { type: string; created_at: string; [key: string]: unknown }
export interface Journey {
  patient: PatientProfile;
  appointments: Appointment[];
  virtual_sessions: VirtualSession[];
  events: JourneyEvent[];
}
export interface AuditItem {
  id: number; type?: string; event_type?: string; action?: string; actor?: string; agent_name?: string; status?: string;
  scenario_id?: string; correlation_id: string; created_at: string; details: Record<string, unknown>;
}
export interface AiRuntime { configured: boolean; unavailable_reason: string | null; model?: string; agent_count?: number }
export interface AssistantReply {
  reply: string; intent: string; mode: string; safety_escalated: boolean;
  fallback_reason: string | null; slots: Slot[]; correlation_id: string;
}
export interface Candidates { eligible: Staff[]; excluded: Staff[] }
export interface LiveRisk { severity: "critical" | "warning" | "info"; title: string; detail: string }
export interface HospitalLive {
  hospital: Hospital; projected_census: number; occupancy_pct: number; avg_wait_minutes: number;
  acuity_mix: Record<string, number>;
  patients: { id: string; complaint: string; acuity: number; wait_minutes: number; status: string }[];
  inbound: { id: string; complaint: string; acuity: number; eta_minutes: number }[];
  coverage: { role: string; required: number; on_duty: number; gap: number }[];
  staff: (Staff & { reinforcement: boolean; assigned_department?: string; rest_hours: number; certification_valid_through: string })[];
  procedures: (Procedure & { status?: string; synthetic?: boolean })[];
  risks: LiveRisk[];
}

export interface PatientProfile {
  id: string; name: string; locality: string; dob: string; age: number; sex: string; blood_group: string;
  phone: string; email: string; address: string; primary_doctor: string;
  insurance: { plan: string; member_id: string; valid_through: string };
  emergency_contact: { name: string; relation: string; phone: string };
  allergies: string[]; conditions: string[];
  vitals: { recorded_at: string; bp: string; heart_rate: number; weight_kg: number; height_cm: number; bmi: number; spo2: number };
  labs: { test: string; value: string; range: string; status: string; date: string }[];
  immunizations: { name: string; date: string }[];
  past_visits: { date: string; doctor: string; reason: string; summary: string }[];
}
export interface Medication { name: string; dose: string; frequency: string; duration: string; instructions: string }
export interface Prescription {
  id: string; patient_id: string; doctor_name: string; specialty: string; hospital: string; diagnosis: string;
  medications: Medication[]; notes: string; issued_at: string; status: string;
}
export interface Vitals { time: string; rr: number; spo2: number; temp: number; sbp: number; hr: number; news2: number }
export interface IpdMed { id: string; name: string; dose: string; route: string; time: string; given: boolean; status: string }
export interface ChartEntry { id: string; signed_by: string; signed_at: string; narrative: string; ai_mode: string; news2: number }
export interface IpdPatient {
  id: string; hospital_id: string; name: string; age: number; sex: string; bed: string; diagnosis: string; doctor: string;
  allergies: string[]; admitted: string; pain_score: number; mobility: string; tasks: string[]; meds: IpdMed[];
  vitals: Vitals[]; latest: Vitals; news2: number; risk: "low" | "medium" | "high"; charted_today: boolean;
  charts: ChartEntry[]; meds_due: number; intake_ml: number; output_ml: number;
}
export interface Ward {
  hospital_id: string; patients: IpdPatient[];
  summary: { census: number; high_risk: number; medium_risk: number; charted: number; meds_due: number };
}
export interface ChartDraft { sections: Record<string, string>; narrative: string; mode: string; fallback_reason: string | null }
export interface OpdDoctor {
  doctor: string; specialty: string; room: string; status: string; appointments: number; seen: number;
  in_queue: number; avg_wait_minutes: number; now_serving: string | null;
}
export interface OpdBoard {
  hospital_id: string; doctors: OpdDoctor[];
  summary: { doctors_on_opd: number; appointments: number; seen: number; in_queue: number; avg_wait_minutes: number };
}

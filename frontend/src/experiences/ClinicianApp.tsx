import { useState } from "react";
import { API_BASE, api } from "../api";
import { formatTime, useAction, useLive, useToast } from "../hooks";
import { Journey, Medication, Prescription } from "../types";
import { Empty, Metric, Panel, Shell, StatusBadge, SyntheticBanner, ToastView } from "../ui";

const ROLE = "clinician" as const;
const blankMed = (): Medication => ({ name: "", dose: "", frequency: "", duration: "", instructions: "" });

const TEMPLATES: { label: string; diagnosis: string; meds: Medication[]; note: string }[] = [
  { label: "Knee OA flare", diagnosis: "Right knee osteoarthritis flare", note: "Review in four weeks. Continue physiotherapy.",
    meds: [{ name: "Paracetamol", dose: "1 g", frequency: "Every 6 hours as needed", duration: "10 days", instructions: "Do not exceed 4 g in 24 hours." },
      { name: "Diclofenac gel 1%", dose: "4 g", frequency: "Apply to knee three times daily", duration: "14 days", instructions: "Topical use only." }] },
  { label: "Post-consult analgesia", diagnosis: "Musculoskeletal pain after virtual consult", note: "Take with food. Return if pain worsens.",
    meds: [{ name: "Ibuprofen", dose: "400 mg", frequency: "Twice daily after meals", duration: "5 days", instructions: "Stop if stomach upset occurs." },
      { name: "Omeprazole", dose: "20 mg", frequency: "Once daily in the morning", duration: "5 days", instructions: "" }] },
  { label: "⚠ Allergy conflict demo", diagnosis: "Suspected soft tissue infection", note: "",
    meds: [{ name: "Amoxicillin", dose: "500 mg", frequency: "Three times daily", duration: "7 days", instructions: "" }] },
];

const eventLabels: Record<string, string> = {
  "patient.assistant_message": "Patient used the access assistant",
  "patient.safety_escalated": "Safety escalation. Routine scheduling stopped",
  "appointment.confirmed": "Appointment confirmed by patient",
  "virtual_session.created": "Virtual visit started",
  "virtual_session.status_changed": "Virtual visit status changed",
  "virtual_session.completed": "Visit completed. Follow-up task created",
  "prescription.issued": "Prescription issued",
};

export default function ClinicianApp() {
  const { toast, notify } = useToast();
  const { data: journey, error } = useLive(() => api<Journey>("/patients/PAT-1001/journey", ROLE), [], 5000);
  const { data: prescriptions, reload } = useLive(() => api<Prescription[]>("/patients/PAT-1001/prescriptions", ROLE), [], 5000);
  const { busy, run } = useAction(reload, notify);
  const [diagnosis, setDiagnosis] = useState("");
  const [meds, setMeds] = useState<Medication[]>([blankMed()]);
  const [notes, setNotes] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const filled = diagnosis.trim() && meds.length > 0 && meds.every((m) => m.name.trim() && m.dose.trim() && m.frequency.trim() && m.duration.trim());

  const setMed = (index: number, key: keyof Medication, value: string) =>
    setMeds((current) => current.map((item, position) => position === index ? { ...item, [key]: value } : item));
  const useTemplate = (template: typeof TEMPLATES[number]) => {
    setDiagnosis(template.diagnosis); setMeds(template.meds.map((item) => ({ ...item }))); setNotes(template.note);
    setConfirmed(false); setProblem(null);
  };
  async function issue() {
    setProblem(null);
    await run(async () => {
      try {
        await api("/prescriptions", ROLE, { method: "POST", body: { patient_id: "PAT-1001", diagnosis, medications: meds, notes, clinician_confirmed: confirmed } });
      } catch (failure) {
        setProblem(failure instanceof Error ? failure.message : "Could not issue the prescription.");
        throw failure;
      }
      setDiagnosis(""); setMeds([blankMed()]); setNotes(""); setConfirmed(false);
    }, "Prescription issued. It is now visible in the patient's portal.");
  }
  const followUps = (journey?.events ?? []).filter((event) => event.type === "virtual_session.completed");
  const live = journey?.virtual_sessions.filter((session) => session.status !== "completed") ?? [];
  const nextAppointment = journey?.appointments[0];

  return <Shell theme="clinician" brand="CareFlow One" tag="CLINICIAN WORKSPACE" right={<span className="user-chip"><span className="avatar">MS</span>Dr. Meera Shah</span>}>
    <ToastView toast={toast} />
    <SyntheticBanner />
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    <div className="clin-layout">
      <aside className="patient-card">
        <span className="avatar xl">AM</span>
        <h2>{journey?.patient.name ?? "Alex Morgan"}</h2>
        <p>{journey?.patient.id ?? "PAT-1001"} · {journey?.patient.locality ?? "North District"}</p>
        <div className="kv"><span>Referral</span><b>Orthopaedics</b></div>
        <div className="kv"><span>Next appointment</span><b>{nextAppointment ? formatTime(nextAppointment.starts_at) : "None booked"}</b></div>
        <div className="kv"><span>Open follow-ups</span><b>{followUps.length}</b></div>
        <p className="muted">Information shown is limited to what the patient has confirmed in this demo.</p>
      </aside>
      <div className="clin-main">
        <div className="metric-row">
          <Metric label="Appointments" value={journey?.appointments.length ?? 0} note="Confirmed" tone="blue" />
          <Metric label="Live virtual visits" value={live.length} note="In progress" tone={live.length ? "teal" : "neutral"} />
          <Metric label="Follow-up tasks" value={followUps.length} note="Simulated" tone="neutral" />
        </div>
        <Panel title="Prescribe" subtitle="Issued prescriptions appear instantly in the patient's portal, with a PDF">
          <div className="rx-form">
            <div className="rx-allergy">Allergies on record: {(journey?.patient.allergies ?? []).map((item) => <span className="pill pill-bad" key={item}>{item}</span>)}</div>
            <div className="template-row"><small>Demo templates</small>
              {TEMPLATES.map((template) => <button key={template.label} className="btn btn-outline btn-small" onClick={() => useTemplate(template)}>{template.label}</button>)}</div>
            <label className="form-field"><small>Diagnosis</small><input value={diagnosis} maxLength={120} onChange={(event) => setDiagnosis(event.target.value)} placeholder="e.g. Right knee osteoarthritis flare" /></label>
            {meds.map((med, index) => <div className="med-row" key={index}>
              <input value={med.name} maxLength={80} onChange={(event) => setMed(index, "name", event.target.value)} placeholder="Medication" aria-label="Medication" />
              <input value={med.dose} maxLength={40} onChange={(event) => setMed(index, "dose", event.target.value)} placeholder="Dose" aria-label="Dose" />
              <input value={med.frequency} maxLength={60} onChange={(event) => setMed(index, "frequency", event.target.value)} placeholder="Frequency" aria-label="Frequency" />
              <input value={med.duration} maxLength={40} onChange={(event) => setMed(index, "duration", event.target.value)} placeholder="Duration" aria-label="Duration" />
              <button className="btn btn-quiet btn-small" disabled={meds.length === 1} onClick={() => setMeds((current) => current.filter((_, position) => position !== index))} aria-label="Remove medication">✕</button>
            </div>)}
            <div><button className="btn btn-outline btn-small" disabled={meds.length >= 8} onClick={() => setMeds((current) => [...current, blankMed()])}>＋ Add medication</button></div>
            <label className="form-field"><small>Notes to patient</small><input value={notes} maxLength={300} onChange={(event) => setNotes(event.target.value)} placeholder="Optional" /></label>
            {problem && <div className="inline-error rx-error">{problem}</div>}
            <label className="check-row"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
              I have reviewed the patient's allergies and confirm this prescription.</label>
            <div><button className="btn btn-primary" disabled={busy || !filled || !confirmed} onClick={() => void issue()}>Sign & issue prescription</button></div>
          </div>
        </Panel>
        <Panel title="Issued prescriptions" subtitle="Visible to the patient">
          {prescriptions && prescriptions.length > 0 ? <table><thead><tr><th>Rx</th><th>Diagnosis</th><th>Medications</th><th>Status</th><th /></tr></thead>
            <tbody>{prescriptions.map((rx) => <tr key={rx.id}><td><strong>{rx.id}</strong><small>{rx.issued_at.slice(0, 10)}</small></td><td>{rx.diagnosis}</td>
              <td>{rx.medications.map((item) => `${item.name} ${item.dose}`).join(", ")}</td><td><StatusBadge status={rx.status} /></td>
              <td><a className="btn btn-outline btn-small" href={`${API_BASE}/prescriptions/${rx.id}/pdf`} download={`${rx.id}.pdf`}>PDF</a></td></tr>)}</tbody></table>
            : <Empty title="No prescriptions" text="Issue one above." />}
        </Panel>
        <Panel title="Appointments" subtitle="Updates when the patient books">
          {journey && journey.appointments.length > 0 ? <table><thead><tr><th>ID</th><th>When</th><th>Mode</th><th>Status</th><th>Virtual visit</th></tr></thead>
            <tbody>{journey.appointments.map((item) => {
              const session = journey.virtual_sessions.find((entry) => entry.appointment_id === item.id);
              return <tr key={item.id}><td><strong>{item.id}</strong></td><td>{formatTime(item.starts_at)}</td><td>{item.mode.replace("_", " ")}</td>
                <td><StatusBadge status={item.status} /></td><td>{session ? <StatusBadge status={session.status} /> : <span className="muted">{item.mode === "virtual" ? "Not started" : "n/a"}</span>}</td></tr>;
            })}</tbody></table>
            : <Empty title="No appointments yet" text="When the patient books in the Patient app, it appears here within seconds." />}
        </Panel>
        <Panel title="Patient journey" subtitle="Events recorded for this patient">
          {journey && journey.events.length > 0 ? <ol className="timeline">
            {[...journey.events].reverse().map((event, index) => <li key={index}>
              <b>{eventLabels[event.type] ?? event.type}</b><small>{event.created_at.replace("T", " ")}</small></li>)}
          </ol> : <Empty title="No activity yet" text="Patient activity will build the journey timeline." />}
        </Panel>
      </div>
    </div>
  </Shell>;
}

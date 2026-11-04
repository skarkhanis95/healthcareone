import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { API_BASE, api, newIdempotencyKey } from "../api";
import { formatTime, useAction, useLive, useToast } from "../hooks";
import { Appointment, AssistantReply, Journey, Prescription, Slot } from "../types";
import { BookingNotice, PhoneDrawer } from "./PhoneDrawer";
import { Empty, ModeTag, Panel, Shell, StatusBadge, SyntheticBanner, ToastView } from "../ui";

interface Msg {
  id: string;
  from: "user" | "assistant";
  text: string;
  mode?: string;
  note?: string | null;
  slots?: Slot[];
  appointmentId?: string;
}

type Section = "home" | "appointments" | "prescriptions" | "record" | "profile" | "assistant";

const ROLE = "patient" as const;
const PATIENT_ID = "PAT-1001";
let counter = 0;
const nextId = () => `m${++counter}`;

const NAV: { id: Section; label: string; icon: string }[] = [
  { id: "home", label: "Home", icon: "⌂" },
  { id: "assistant", label: "Book & ask", icon: "✦" },
  { id: "appointments", label: "Appointments", icon: "▦" },
  { id: "prescriptions", label: "Prescriptions", icon: "℞" },
  { id: "record", label: "Health record", icon: "♥" },
  { id: "profile", label: "My profile", icon: "☺" },
];

const eventLabels: Record<string, string> = {
  "patient.assistant_message": "You used the assistant",
  "patient.safety_escalated": "Safety escalation: routine scheduling stopped",
  "appointment.confirmed": "Appointment confirmed",
  "virtual_session.created": "Virtual visit started",
  "virtual_session.completed": "Virtual visit completed",
  "prescription.issued": "New prescription issued by your doctor",
};

function PdfLink({ id }: { id: string }) {
  return <a className="btn btn-outline btn-small" href={`${API_BASE}/prescriptions/${id}/pdf`} download={`${id}.pdf`}>⬇ Download PDF</a>;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <div className="field-row"><small>{label}</small><span>{children}</span></div>;
}

export default function PatientApp() {
  const { toast, notify } = useToast();
  const { data: journey, error, reload } = useLive(() => api<Journey>(`/patients/${PATIENT_ID}/journey`, ROLE), []);
  const { data: prescriptions } = useLive(() => api<Prescription[]>(`/patients/${PATIENT_ID}/prescriptions`, ROLE), [], 5000);
  const { busy, run } = useAction(reload, notify);
  const [section, setSection] = useState<Section>("home");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [confirming, setConfirming] = useState<{ slot: Slot; key: string; rescheduleId?: string } | null>(null);
  const [resched, setResched] = useState<{ appointmentId: string; slots: Slot[] } | null>(null);
  const [notice, setNotice] = useState<BookingNotice | null>(null);
  const bottom = useRef<HTMLDivElement>(null);
  const seenAppointments = useRef(0);
  const seenRx = useRef<number | null>(null);

  const patient = journey?.patient;
  const rxList = prescriptions ?? [];

  useEffect(() => { bottom.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, thinking, section]);

  // A reset from the Demo Director clears the conversation so it never shows stale bookings.
  useEffect(() => {
    const count = journey?.appointments.length ?? 0;
    if (seenAppointments.current > 0 && count === 0) { setMessages([]); setConfirming(null); setResched(null); setNotice(null); }
    seenAppointments.current = count;
  }, [journey]);

  // Tell the patient when the doctor issues a new prescription from the clinician workspace.
  useEffect(() => {
    if (!prescriptions) return;
    if (seenRx.current !== null && prescriptions.length > seenRx.current) notify("success", "Your doctor issued a new prescription.");
    seenRx.current = prescriptions.length;
  }, [prescriptions, notify]);

  const bookedSlots = new Set((journey?.appointments ?? []).map((item) => item.slot_id));
  const activeRx = rxList.filter((item) => item.status === "active");

  async function send(event?: FormEvent, preset?: string) {
    event?.preventDefault();
    const text = (preset ?? input).trim();
    if (!text || thinking) return;
    setInput("");
    setConfirming(null);
    setSection("assistant");
    setMessages((current) => [...current, { id: nextId(), from: "user", text }]);
    setThinking(true);
    try {
      const reply = await api<AssistantReply>("/patient-access/assistant/message", ROLE, { method: "POST", body: { message: text } });
      setMessages((current) => [...current, { id: nextId(), from: "assistant", text: reply.reply, mode: reply.mode, note: reply.fallback_reason, slots: reply.slots }]);
    } catch (failure) {
      setMessages((current) => [...current, { id: nextId(), from: "assistant", text: failure instanceof Error ? failure.message : "Something went wrong. Please try again." }]);
    } finally {
      setThinking(false);
    }
  }

  const confirmBooking = () => confirming && run(async () => {
    const { slot, rescheduleId } = confirming;
    const body = { patient_confirmed: true, idempotency_key: confirming.key };
    const saved = rescheduleId
      ? await api<{ id: string }>(`/appointments/${rescheduleId}/reschedule`, ROLE, { method: "POST", body: { ...body, slot_id: slot.id } })
      : await api<{ id: string }>("/appointments", ROLE, { method: "POST", body: { ...body, patient_id: PATIENT_ID, slot_id: slot.id } });
    setConfirming(null);
    setResched(null);
    setNotice({ kind: rescheduleId ? "rescheduled" : "booked", slot, appointmentId: saved.id, patientName: patient?.name ?? "there", patientAddress: patient?.address ?? "" });
    setMessages((current) => [...current, {
      id: nextId(), from: "assistant", appointmentId: saved.id,
      text: rescheduleId ? `Done. Your appointment moved to ${formatTime(slot.starts_at)} with ${slot.doctor.name}.`
        : `You're booked with ${slot.doctor.name}. Nothing was booked until you confirmed. A confirmation was sent to your phone.`,
    }]);
  }, confirming?.rescheduleId ? "Appointment rescheduled." : "Appointment booked.");

  const openReschedule = (appointment: Appointment) => run(async () => {
    const open = await api<Slot[]>("/availability", ROLE);
    const options = open.filter((slot) => slot.id !== appointment.slot_id)
      .sort((a, b) => Number(b.doctor_id === appointment.doctor_id) - Number(a.doctor_id === appointment.doctor_id) || a.starts_at.localeCompare(b.starts_at))
      .slice(0, 4);
    setResched({ appointmentId: appointment.id, slots: options });
  });

  function ReschedulePanel({ appointment }: { appointment: Appointment }) {
    if (resched?.appointmentId !== appointment.id) return null;
    return <div className="resched-panel slot-list">
      <small><strong>Next available slots</strong></small>
      {resched.slots.length === 0 && <small>No other slots are open right now.</small>}
      {resched.slots.map((slot) => <div className="slot-card" key={slot.id}>
        <span className="avatar">{slot.doctor.name.split(" ").slice(-1)[0][0]}</span>
        <div><strong>{slot.doctor.name}</strong><small>{slot.doctor.specialty} · {slot.doctor.location}</small><small>{formatTime(slot.starts_at)} · {slot.mode.replace("_", " ")}</small></div>
        <button className="btn btn-primary btn-small" disabled={busy} onClick={() => setConfirming({ slot, key: newIdempotencyKey(), rescheduleId: appointment.id })}>Choose</button>
      </div>)}
      <button className="btn btn-quiet btn-small" onClick={() => { setResched(null); setConfirming(null); }}>Keep current time</button>
    </div>;
  }

  const startSession = (appointmentId: string) => run(() => api("/virtual-sessions", ROLE, { method: "POST", body: { appointment_id: appointmentId, patient_confirmed: true } }));
  const advanceSession = (id: string) => run(() => api(`/virtual-sessions/${id}/advance`, ROLE, { method: "POST" }));
  const endSession = (id: string) => run(() => api(`/virtual-sessions/${id}/complete`, ROLE, { method: "POST" }), "Visit complete. A follow-up task was created.");

  function VisitControls({ appointmentId }: { appointmentId: string }) {
    const session = journey?.virtual_sessions.find((item) => item.appointment_id === appointmentId);
    return <div className="visit">
      {!session && <button className="btn btn-primary btn-small" disabled={busy} onClick={() => startSession(appointmentId)}>Join virtual visit</button>}
      {session && <>
        <div className="video-stage"><span className="avatar">AM</span><small>SIMULATED VIDEO VISIT</small><strong>{session.status.replaceAll("_", " ")}</strong></div>
        <div className="btn-row">
          {session.status === "waiting" && <button className="btn btn-outline btn-small" disabled={busy} onClick={() => advanceSession(session.id)}>Doctor joins (simulate)</button>}
          {session.status === "doctor_connected" && <button className="btn btn-outline btn-small" disabled={busy} onClick={() => advanceSession(session.id)}>Begin consultation (simulate)</button>}
          {["doctor_connected", "in_consultation"].includes(session.status) && <button className="btn btn-primary btn-small" disabled={busy} onClick={() => endSession(session.id)}>End visit</button>}
        </div>
        {session.status === "completed" && <small>Visit complete. Your care team has a follow-up task.</small>}
      </>}
    </div>;
  }

  function RxCard({ rx }: { rx: Prescription }) {
    return <div className="rx-card">
      <div className="rx-top">
        <div><strong>{rx.id}</strong><small>{rx.doctor_name} · {rx.specialty} · {rx.issued_at.slice(0, 10)}</small></div>
        <div className="btn-row"><span className={`pill ${rx.status === "active" ? "pill-good" : ""}`}>{rx.status}</span><PdfLink id={rx.id} /></div>
      </div>
      <p className="rx-dx">For: {rx.diagnosis}</p>
      <ul className="rx-meds">{rx.medications.map((med, index) => <li key={index}>
        <strong>{med.name} <span>{med.dose}</span></strong><small>{med.frequency} · {med.duration}</small>
        {med.instructions && <small>{med.instructions}</small>}</li>)}</ul>
      {rx.notes && <small>Doctor's note: {rx.notes}</small>}
    </div>;
  }

  const upcoming = journey?.appointments ?? [];

  const home = <div className="portal-stack">
    <div className="welcome">
      <div><h1>Good morning, {patient?.name.split(" ")[0] ?? "Alex"}</h1>
        <p>Here's what's happening with your care today.</p></div>
      <button className="btn btn-primary" onClick={() => setSection("assistant")}>＋ Book an appointment</button>
    </div>
    <div className="tile-row">
      <button className="stat-tile" onClick={() => setSection("appointments")}><small>UPCOMING APPOINTMENTS</small><strong>{upcoming.length}</strong>
        <span>{upcoming[0] ? `Next: ${formatTime(upcoming[0].starts_at)}` : "Nothing booked yet"}</span></button>
      <button className="stat-tile" onClick={() => setSection("prescriptions")}><small>ACTIVE PRESCRIPTIONS</small><strong>{activeRx.length}</strong>
        <span>{activeRx[0] ? `Latest: ${activeRx[0].medications[0].name}` : "None active"}</span></button>
      <button className="stat-tile" onClick={() => setSection("record")}><small>BLOOD PRESSURE</small><strong>{patient?.vitals.bp ?? "-"}</strong>
        <span>Recorded {patient?.vitals.recorded_at}</span></button>
      <button className="stat-tile" onClick={() => setSection("profile")}><small>CARE TEAM</small><strong className="small-value">{patient?.primary_doctor ?? "-"}</strong>
        <span>Primary doctor</span></button>
    </div>
    <div className="portal-two">
      <Panel title="Next appointment">
        {upcoming[0] ? <div><strong>{formatTime(upcoming[0].starts_at)}</strong><small>{upcoming[0].mode.replace("_", " ")} · {upcoming[0].id}</small>
          {upcoming[0].mode === "virtual" && <VisitControls appointmentId={upcoming[0].id} />}</div>
          : <Empty title="No upcoming visits" text="Ask the assistant to find an orthopaedic appointment or a virtual consult." />}
      </Panel>
      <Panel title="Latest prescription">
        {rxList[0] ? <RxCard rx={rxList[0]} /> : <Empty title="No prescriptions" text="Prescriptions from your doctor appear here." />}
      </Panel>
    </div>
    <Panel title="Recent activity">
      {journey && journey.events.length > 0 ? <ol className="timeline">
        {[...journey.events].reverse().slice(0, 6).map((event, index) => <li key={index}><b>{eventLabels[event.type] ?? event.type}</b><small>{event.created_at.replace("T", " ")}</small></li>)}
      </ol> : <Empty title="No activity yet" text="Bookings, visits and prescriptions will show here." />}
    </Panel>
  </div>;

  const confirmBar = confirming && <div className="confirm-bar">
    <p>{confirming.rescheduleId ? "Move your appointment to" : "Book"} <strong>{confirming.slot.doctor.name}</strong> on {formatTime(confirming.slot.starts_at)} ({confirming.slot.mode.replace("_", " ")})?</p>
    <div className="btn-row"><button className="btn btn-primary btn-small" disabled={busy} onClick={confirmBooking}>{confirming.rescheduleId ? "Confirm new time" : "Confirm booking"}</button>
      <button className="btn btn-quiet btn-small" onClick={() => setConfirming(null)}>Cancel</button></div>
  </div>;

  const appointments = <div className="portal-stack">
    <div className="section-head"><h1>Appointments</h1><button className="btn btn-primary" onClick={() => setSection("assistant")}>＋ Book with assistant</button></div>
    <Panel title="Upcoming">
      {upcoming.length > 0 ? <div className="list-stack">{upcoming.map((item) => <div className="appt-row" key={item.id}>
        <div><strong>{formatTime(item.starts_at)}</strong><small>{item.id} · {item.mode.replace("_", " ")}</small></div>
        <StatusBadge status={item.status} />
        {item.mode === "virtual" && <VisitControls appointmentId={item.id} />}
        {!resched && <button className="btn btn-outline btn-small" disabled={busy} onClick={() => void openReschedule(item)}>Reschedule</button>}
        <ReschedulePanel appointment={item} />
      </div>)}</div> : <Empty title="No upcoming appointments" text="Type what you need in the assistant, for example: I need an orthopaedic appointment this week." />}
    </Panel>
    {confirmBar}
    <Panel title="Past visits">
      <div className="list-stack">{(patient?.past_visits ?? []).map((visit) => <div className="appt-row" key={visit.date + visit.reason}>
        <div><strong>{visit.reason}</strong><small>{visit.date} · {visit.doctor}</small><small>{visit.summary}</small></div><StatusBadge status="completed" /></div>)}</div>
    </Panel>
  </div>;

  const prescriptionsView = <div className="portal-stack">
    <div className="section-head"><h1>Prescriptions</h1><small>{activeRx.length} active · {rxList.length} total</small></div>
    {rxList.length === 0 ? <Empty title="No prescriptions" text="Prescriptions from your doctor appear here." />
      : <div className="list-stack">{rxList.map((rx) => <RxCard key={rx.id} rx={rx} />)}</div>}
  </div>;

  const record = patient && <div className="portal-stack">
    <div className="section-head"><h1>Health record</h1></div>
    <div className="portal-two">
      <Panel title="Allergies & conditions">
        <div className="chips">{patient.allergies.map((item) => <span className="pill pill-bad" key={item}>Allergy: {item}</span>)}
          {patient.conditions.map((item) => <span className="pill" key={item}>{item}</span>)}</div>
      </Panel>
      <Panel title="Latest vitals" subtitle={`Recorded ${patient.vitals.recorded_at}`}>
        <div className="vital-grid">
          <div><small>BP</small><strong>{patient.vitals.bp}</strong></div><div><small>HEART RATE</small><strong>{patient.vitals.heart_rate}</strong></div>
          <div><small>SpO2</small><strong>{patient.vitals.spo2}%</strong></div><div><small>WEIGHT</small><strong>{patient.vitals.weight_kg} kg</strong></div>
          <div><small>HEIGHT</small><strong>{patient.vitals.height_cm} cm</strong></div><div><small>BMI</small><strong>{patient.vitals.bmi}</strong></div>
        </div>
      </Panel>
    </div>
    <Panel title="Lab results">
      <table><thead><tr><th>Test</th><th>Result</th><th>Reference</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>{patient.labs.map((lab) => <tr key={lab.test}><td><strong>{lab.test}</strong></td><td>{lab.value}</td><td>{lab.range}</td>
          <td><span className={`pill ${lab.status === "Normal" ? "pill-good" : "pill-warn"}`}>{lab.status}</span></td><td>{lab.date}</td></tr>)}</tbody></table>
    </Panel>
    <Panel title="Immunisations">
      <div className="list-stack">{patient.immunizations.map((item) => <div className="field-row" key={item.name}><span>{item.name}</span><small>{item.date}</small></div>)}</div>
    </Panel>
  </div>;

  const profile = patient && <div className="portal-stack">
    <div className="section-head"><h1>My profile</h1></div>
    <div className="profile-hero"><span className="avatar xl">{patient.name.split(" ").map((part) => part[0]).join("")}</span>
      <div><h2>{patient.name}</h2><p>{patient.id} · {patient.age} years · {patient.sex} · Blood group {patient.blood_group}</p></div></div>
    <div className="portal-two">
      <Panel title="Personal details">
        <Field label="Date of birth">{patient.dob}</Field><Field label="Phone">{patient.phone}</Field>
        <Field label="Email">{patient.email}</Field><Field label="Address">{patient.address}</Field>
        <Field label="Primary doctor">{patient.primary_doctor}</Field>
      </Panel>
      <div className="portal-stack">
        <Panel title="Insurance">
          <Field label="Plan">{patient.insurance.plan}</Field><Field label="Member ID">{patient.insurance.member_id}</Field>
          <Field label="Valid through">{patient.insurance.valid_through}</Field>
        </Panel>
        <Panel title="Emergency contact">
          <Field label="Name">{patient.emergency_contact.name} ({patient.emergency_contact.relation})</Field>
          <Field label="Phone">{patient.emergency_contact.phone}</Field>
        </Panel>
      </div>
    </div>
  </div>;

  const assistant = <div className="portal-stack chat-page">
    <div className="section-head"><h1>Book & ask</h1><small>Type in your own words. The assistant can book appointments and virtual consults. It can't give medical advice.</small></div>
    <div className="chat-card">
      <div className="chat" aria-live="polite">
        {messages.length === 0 && <div className="chat-empty">
          <span className="orb">✦</span>
          <h2>How can we help today?</h2>
          <div className="suggestions">
            {["I need an orthopaedic appointment this week", "Can I see a doctor by video today?"].map((text) =>
              <button key={text} className="suggest" onClick={() => void send(undefined, text)}>{text}</button>)}
          </div>
        </div>}
        {messages.map((message) => <div key={message.id} className={`bubble-row ${message.from}`}>
          <div className={`bubble ${message.from}`}>
            <p>{message.text}</p>
            {message.from === "assistant" && message.mode && <div className="bubble-meta"><ModeTag mode={message.mode} />{message.note && <small>{message.note}</small>}</div>}
            {message.appointmentId && (() => { const appt = (journey?.appointments ?? []).find((item) => item.id === message.appointmentId);
              return appt && <div className="btn-row">
                {!resched && <button className="btn btn-outline btn-small" disabled={busy} onClick={() => void openReschedule(appt)}>Reschedule · see next slots</button>}
                <ReschedulePanel appointment={appt} /></div>; })()}
            {message.slots && message.slots.length > 0 && <div className="slot-list">
              {message.slots.map((slot) => { const lockedOut = !bookedSlots.has(slot.id) && message.slots!.some((other) => bookedSlots.has(other.id));
                return <div className={`slot-card${lockedOut ? " slot-disabled" : ""}`} key={slot.id}>
                <span className="avatar">{slot.doctor.name.split(" ").slice(-1)[0][0]}</span>
                <div><strong>{slot.doctor.name}</strong><small>{slot.doctor.specialty} · {slot.doctor.location}</small><small>{formatTime(slot.starts_at)} · {slot.mode.replace("_", " ")}</small></div>
                <button className="btn btn-primary btn-small" disabled={busy || lockedOut || bookedSlots.has(slot.id)} onClick={() => setConfirming({ slot, key: newIdempotencyKey() })}>
                  {bookedSlots.has(slot.id) ? "Booked" : lockedOut ? "Unavailable" : "Choose"}</button>
              </div>; })}
            </div>}
          </div>
        </div>)}
        {thinking && <div className="bubble-row assistant"><div className="bubble assistant typing"><i /><i /><i /></div></div>}
        <div ref={bottom} />
      </div>
      {confirmBar}
      <form className="composer" onSubmit={(event) => void send(event)}>
        <input value={input} maxLength={500} onChange={(event) => setInput(event.target.value)} aria-label="Type your request" placeholder="Type your request…" />
        <button className="btn btn-primary" type="submit" disabled={!input.trim() || thinking}>Send</button>
      </form>
    </div>
  </div>;

  const views: Record<Section, ReactNode> = {
    home, appointments, prescriptions: prescriptionsView, record, profile, assistant,
  };

  return <Shell theme="patient" brand="CareFlow One" tag="PATIENT PORTAL"
    right={<span className="user-chip"><span className="avatar">AM</span>{patient?.name ?? "Alex Morgan"}</span>}>
    <ToastView toast={toast} />
    <PhoneDrawer notice={notice} onClose={() => setNotice(null)} />
    <SyntheticBanner />
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    <div className="portal">
      <nav className="side-nav" aria-label="Patient portal">
        {NAV.map((item) => <button key={item.id} className={section === item.id ? "active" : ""} onClick={() => setSection(item.id)}>
          <span>{item.icon}</span>{item.label}
          {item.id === "prescriptions" && activeRx.length > 0 && <em>{activeRx.length}</em>}
        </button>)}
      </nav>
      <main className="portal-main">{views[section] ?? <Empty title="Loading" text="Loading your portal…" />}</main>
    </div>
  </Shell>;
}

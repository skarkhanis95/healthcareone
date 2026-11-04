import { ReactNode, useEffect, useState } from "react";
import { api } from "../api";
import { formatTime, useAction, useLive, useToast } from "../hooks";
import { ChartDraft, HospitalLive, IpdPatient, OpdBoard, Ward } from "../types";
import { Empty, ModeTag, Panel, Shell, StatusBadge, SyntheticBanner, ToastView } from "../ui";

type Persona = "admin" | "nurse";
type AdminTab = "overview" | "emergency" | "opd" | "wards" | "staffing" | "theatre";
type NurseTab = "obs" | "meds" | "chart";

const ADMIN_TABS: { id: AdminTab; label: string; icon: string }[] = [
  { id: "overview", label: "Overview", icon: "▤" },
  { id: "emergency", label: "Emergency dept", icon: "✚" },
  { id: "opd", label: "OPD board", icon: "☷" },
  { id: "wards", label: "Inpatient wards", icon: "▦" },
  { id: "staffing", label: "Staffing", icon: "☺" },
  { id: "theatre", label: "Operating theatre", icon: "⚕" },
];

const riskText: Record<string, string> = { low: "Low", medium: "Medium", high: "High" };

function NewsChip({ score, risk }: { score: number; risk: string }) {
  return <span className={`news news-${risk}`}>NEWS2 {score} · {riskText[risk]}</span>;
}

function Spark({ values }: { values: number[] }) {
  const max = Math.max(9, ...values);
  const points = values.map((value, index) => `${(index / Math.max(1, values.length - 1)) * 160},${44 - (value / max) * 40}`).join(" ");
  return <svg className="spark" viewBox="0 0 160 48" role="img" aria-label="NEWS2 trend"><polyline points={points} fill="none" strokeWidth="2.5" /></svg>;
}

function Kpi({ label, value, tone = "" }: { label: string; value: ReactNode; tone?: string }) {
  return <div className={`kpi ${tone}`}><small>{label}</small><strong>{value}</strong></div>;
}

export default function HospitalConsole({ hospitalId }: { hospitalId: string }) {
  const initial = new URLSearchParams(window.location.search).get("persona") === "nurse" ? "nurse" : "admin";
  const [persona, setPersona] = useState<Persona>(initial);
  const [adminTab, setAdminTab] = useState<AdminTab>("overview");
  const [nurseTab, setNurseTab] = useState<NurseTab>("obs");
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<ChartDraft | null>(null);
  const [text, setText] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [drafting, setDrafting] = useState(false);
  const { toast, notify } = useToast();
  const role = persona === "nurse" ? "nurse" : "presenter";

  const { data: live, error } = useLive(() => api<HospitalLive>(`/hospitals/${hospitalId}/live`, "presenter"), [hospitalId], 5000);
  const { data: ward, reload } = useLive(() => api<Ward>(`/hospitals/${hospitalId}/ipd`, role), [hospitalId, role], 5000);
  const { data: opd } = useLive(() => api<OpdBoard>(`/hospitals/${hospitalId}/opd`, "presenter"), [hospitalId], 5000);
  const { busy, run } = useAction(reload, notify);

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("persona", persona);
    window.history.replaceState(null, "", url);
  }, [persona]);

  const patients = ward?.patients ?? [];
  const current: IpdPatient | undefined = patients.find((item) => item.id === selected) ?? patients[0];
  const hospital = live?.hospital;
  const pending = patients.filter((item) => !item.charted_today);

  useEffect(() => { setDraft(null); setText(""); setReviewed(false); }, [current?.id]);
  useEffect(() => { if (hospital) document.title = `${hospital.name} | HealthCareOne`; }, [hospital]);

  const openChart = (id: string) => { setSelected(id); setNurseTab("obs"); setPersona("nurse"); };

  async function generate() {
    if (!current) return;
    setDrafting(true);
    try {
      const result = await api<ChartDraft>(`/ipd/${current.id}/chart/draft`, "nurse", { method: "POST" });
      setDraft(result); setText(result.narrative); setReviewed(false);
    } catch (failure) {
      notify("error", failure instanceof Error ? failure.message : "Could not draft the chart.");
    } finally {
      setDrafting(false);
    }
  }
  const signChart = () => current && draft && run(async () => {
    await api(`/ipd/${current.id}/chart`, "nurse", { method: "POST", body: { narrative: text, ai_mode: draft.mode, nurse_confirmed: reviewed } });
    setDraft(null); setText(""); setReviewed(false);
  }, "Chart signed and saved.");
  const capture = () => current && run(() => api(`/ipd/${current.id}/vitals`, "nurse", { method: "POST" }), "Vitals captured from the bedside monitor (demo).");
  const give = (medId: string) => current && run(() => api(`/ipd/${current.id}/medications/${medId}/administer`, "nurse", { method: "POST" }), "Medication recorded as given.");

  const adminView: Record<AdminTab, ReactNode> = {
    opd: opd && <div className="portal-stack">
      <div className="btn-row"><a className="btn btn-primary" href={`/hospital/${hospitalId}/display`} target="_blank" rel="noreferrer">▣ Show Display Board</a>
        <small>Opens a full-screen, high-contrast board for waiting areas.</small></div>
      <div className="kpi-strip">
        <Kpi label="DOCTORS ON OPD" value={opd.summary.doctors_on_opd} />
        <Kpi label="APPOINTMENTS TODAY" value={opd.summary.appointments} />
        <Kpi label="SEEN SO FAR" value={opd.summary.seen} />
        <Kpi label="IN QUEUE" value={opd.summary.in_queue} tone={opd.summary.in_queue > 20 ? "kpi-warn" : ""} />
        <Kpi label="AVG WAIT" value={`${opd.summary.avg_wait_minutes} min`} tone={opd.summary.avg_wait_minutes > 30 ? "kpi-warn" : ""} />
      </div>
      <Panel title="Doctors on OPD" subtitle="Synthetic demo data">
        <table><thead><tr><th>Doctor</th><th>Room</th><th>Status</th><th>Appointments</th><th>Seen</th><th>In queue</th><th>Avg wait</th></tr></thead>
          <tbody>{opd.doctors.map((row) => <tr key={row.room}>
            <td><strong>{row.doctor}</strong><br /><small>{row.specialty}</small></td><td>{row.room}</td>
            <td><span className={`pill ${row.status === "On break" ? "pill-warn" : row.status === "Free" ? "pill-good" : ""}`}>{row.status}</span>{row.now_serving && <small> {row.now_serving}</small>}</td>
            <td>{row.appointments}</td><td>{row.seen}</td><td><strong>{row.in_queue}</strong></td>
            <td className={row.avg_wait_minutes > 30 ? "cov-gap" : ""}>{row.avg_wait_minutes ? `${row.avg_wait_minutes} min` : "-"}</td></tr>)}</tbody></table>
      </Panel>
    </div>,
    overview: live && <div className="portal-stack">
      <div className="kpi-strip">
        <Kpi label="ED CENSUS" value={`${live.hospital.ed_census}/${live.hospital.ed_capacity}`} tone={live.hospital.pressure === "Critical" ? "kpi-bad" : ""} />
        <Kpi label="PROJECTED OCCUPANCY" value={`${live.occupancy_pct}%`} tone={live.occupancy_pct >= 95 ? "kpi-bad" : ""} />
        <Kpi label="INPATIENTS" value={ward?.summary.census ?? "-"} />
        <Kpi label="HIGH-RISK INPATIENTS" value={(ward?.summary.high_risk ?? 0) + (ward?.summary.medium_risk ?? 0)} tone={ward && ward.summary.high_risk ? "kpi-bad" : ward?.summary.medium_risk ? "kpi-warn" : ""} />
        <Kpi label="CHARTING TODAY" value={ward ? `${ward.summary.charted}/${ward.summary.census}` : "-"} />
        <Kpi label="STAFFING GAPS" value={live.coverage.reduce((sum, line) => sum + line.gap, 0)} tone={live.coverage.some((line) => line.gap) ? "kpi-warn" : ""} />
      </div>
      <div className="portal-two">
        <Panel title="Risks & alerts">
          {live.risks.length ? <div className="risk-list">{live.risks.map((risk) => <div key={risk.title} className={`risk ${risk.severity}`}><b>{risk.title}</b><small>{risk.detail}</small></div>)}</div>
            : <Empty title="No active risks" text="Everything is within normal limits." />}
        </Panel>
        <Panel title="ED staffing coverage">
          {live.coverage.map((line) => <div key={line.role} className="cov-row"><span>{line.role}</span>
            <span>{line.on_duty} on duty / {line.required} required · <span className={line.gap ? "cov-gap" : "cov-ok"}>{line.gap ? `gap ${line.gap}` : "covered"}</span></span></div>)}
          <h3 className="sub-h">ED acuity mix</h3>
          <small>{Object.entries(live.acuity_mix).map(([name, count]) => `${name}: ${count}`).join(" · ")}</small>
          <small>Average wait {live.avg_wait_minutes} minutes</small>
        </Panel>
      </div>
    </div>,
    emergency: live && <div className="portal-stack">
      <Panel title="Inbound" subtitle={`${live.inbound.length} projected arrivals`}>
        {live.inbound.length ? <table><thead><tr><th>ID</th><th>Presentation</th><th>Acuity</th><th>ETA</th></tr></thead>
          <tbody>{live.inbound.map((item) => <tr key={item.id}><td><strong>{item.id}</strong></td><td>{item.complaint}</td><td><span className={`pill acuity-${item.acuity}`}>ESI {item.acuity}</span></td><td>{item.eta_minutes} min</td></tr>)}</tbody></table>
          : <Empty title="No inbound patients" text="Trigger the collision scenario from Demo Director on the Central hospital." />}
      </Panel>
      <Panel title="In department" subtitle={`${live.patients.length} patients`}>
        <table><thead><tr><th>ID</th><th>Complaint</th><th>Status</th><th>Wait</th><th>Acuity</th></tr></thead>
          <tbody>{live.patients.map((item) => <tr key={item.id}><td><strong>{item.id}</strong></td><td>{item.complaint}</td><td>{item.status}</td><td>{item.wait_minutes} min</td>
            <td><span className={`pill acuity-${item.acuity}`}>ESI {item.acuity}</span></td></tr>)}</tbody></table>
      </Panel>
    </div>,
    wards: <Panel title="Inpatient wards" subtitle="Select a patient to open their chart in the nurse station">
      {patients.length ? <table><thead><tr><th>Bed</th><th>Patient</th><th>Diagnosis</th><th>Doctor</th><th>Risk</th><th>Meds due</th><th>Daily chart</th><th /></tr></thead>
        <tbody>{patients.map((item) => <tr key={item.id}><td><strong>{item.bed}</strong></td><td>{item.name}<small>{item.age}{item.sex} · {item.id}</small></td><td>{item.diagnosis}</td><td>{item.doctor}</td>
          <td><NewsChip score={item.news2} risk={item.risk} /></td><td>{item.meds_due}</td>
          <td>{item.charted_today ? <span className="pill pill-good">Signed</span> : <span className="pill pill-warn">Pending</span>}</td>
          <td><button className="btn btn-outline btn-small" onClick={() => openChart(item.id)}>Open chart</button></td></tr>)}</tbody></table>
        : <Empty title="Loading wards" text="Loading inpatient list…" />}
    </Panel>,
    staffing: live && <Panel title="Staff on record" subtitle="Synthetic roster">
      <table><thead><tr><th>Name</th><th>Role</th><th>Rest</th><th>Status</th></tr></thead>
        <tbody>{live.staff.map((member) => <tr key={member.id}><td><strong>{member.name}</strong><small>{member.id}</small></td><td>{member.role}</td><td>{member.rest_hours}h</td>
          <td>{member.reinforcement ? <span className="pill surge">Surge assignment</span>
            : <span className="pill">{!member.available ? "Unavailable" : member.certification_valid_through < "2026-11-02" ? "Cert expired" : member.rest_hours < 10 ? "Low rest" : "On duty"}</span>}</td></tr>)}</tbody></table>
    </Panel>,
    theatre: live && <Panel title="Operating theatre" subtitle="Scheduled procedures">
      <table><thead><tr><th>ID</th><th>Procedure</th><th>Room</th><th>When</th><th>Readiness</th></tr></thead>
        <tbody>{live.procedures.map((item) => <tr key={item.id}><td><strong>{item.id}</strong></td><td>{item.name}
          {item.readiness_reasons.filter((reason) => reason.startsWith("Missing")).map((reason) => <small key={reason} className="bad-text">{reason}</small>)}</td>
          <td>{item.room}</td><td>{formatTime(item.scheduled_at)}</td><td><StatusBadge status={item.status === "deferred" ? "deferred" : item.readiness} /></td></tr>)}</tbody></table>
    </Panel>,
  };

  const admin = <div className="portal">
    <nav className="side-nav" aria-label="Hospital administration">
      {ADMIN_TABS.map((tab) => <button key={tab.id} className={adminTab === tab.id ? "active" : ""} onClick={() => setAdminTab(tab.id)}><span>{tab.icon}</span>{tab.label}</button>)}
    </nav>
    <main className="portal-main">
      <div className="section-head"><h1>{ADMIN_TABS.find((tab) => tab.id === adminTab)?.label}</h1>{hospital && <StatusBadge status={hospital.pressure} />}</div>
      {adminView[adminTab] ?? <Empty title="Loading" text="Loading hospital data…" />}
    </main>
  </div>;

  const nurse = <div className="portal">
    <nav className="side-nav ward-nav" aria-label="Ward patients">
      <div className="ward-head"><strong>Ward round</strong>
        <small>{ward ? `${ward.summary.charted}/${ward.summary.census} charts signed` : "Loading"}</small>
        <div className="progress"><i style={{ width: ward ? `${(ward.summary.charted / Math.max(1, ward.summary.census)) * 100}%` : 0 }} /></div></div>
      {patients.map((item) => <button key={item.id} className={current?.id === item.id ? "active" : ""} onClick={() => { setSelected(item.id); setNurseTab("obs"); }}>
        <div className="ward-pt"><strong>{item.bed} · {item.name}</strong><small>{item.diagnosis}</small>
          <div className="ward-tags"><NewsChip score={item.news2} risk={item.risk} />{item.charted_today && <span className="pill pill-good">✓ charted</span>}</div></div>
      </button>)}
    </nav>
    <main className="portal-main">
      {!current ? <Empty title="Loading ward" text="Loading inpatients…" /> : <div className="portal-stack">
        <div className="patient-banner">
          <div><h1>{current.name}</h1><p>{current.age}{current.sex} · Bed {current.bed} · {current.id} · Admitted {current.admitted}</p>
            <p>{current.diagnosis} · {current.doctor}</p></div>
          <div className="banner-right">{current.allergies.length > 0 && <span className="pill pill-bad">Allergy: {current.allergies.join(", ")}</span>}
            <NewsChip score={current.news2} risk={current.risk} />
            {current.charted_today ? <span className="pill pill-good">Daily chart signed</span> : <span className="pill pill-warn">Daily chart pending</span>}</div>
        </div>
        <div className="tabs">{([["obs", "Observations"], ["meds", `Medications${current.meds_due ? ` (${current.meds_due} due)` : ""}`], ["chart", "Daily chart (AI)"]] as [NurseTab, string][]).map(([id, label]) =>
          <button key={id} className={nurseTab === id ? "active" : ""} onClick={() => setNurseTab(id)}>{label}</button>)}</div>

        {nurseTab === "obs" && <Panel title="Observations" subtitle="Bedside monitor feed (demo)" actions={<button className="btn btn-primary btn-small" disabled={busy} onClick={() => void capture()}>＋ Capture vitals (demo device)</button>}>
          <div className="obs-top"><Spark values={current.vitals.map((item) => item.news2)} /><small>NEWS2 trend · latest {current.latest.news2}</small></div>
          <table><thead><tr><th>Time</th><th>RR</th><th>SpO2</th><th>Temp</th><th>BP sys</th><th>HR</th><th>NEWS2</th></tr></thead>
            <tbody>{[...current.vitals].reverse().map((reading) => <tr key={reading.time}><td>{reading.time.slice(11, 16)}</td><td>{reading.rr}</td><td>{reading.spo2}%</td><td>{reading.temp}</td><td>{reading.sbp}</td><td>{reading.hr}</td>
              <td><span className={`news news-${reading.news2 >= 7 ? "high" : reading.news2 >= 5 ? "medium" : "low"}`}>{reading.news2}</span></td></tr>)}</tbody></table>
          <div className="mini-kpis"><div><small>PAIN</small><strong>{current.pain_score}/10</strong></div><div><small>INTAKE</small><strong>{current.intake_ml}</strong></div>
            <div><small>OUTPUT</small><strong>{current.output_ml}</strong></div><div><small>MOBILITY</small><strong className="small-value">{current.mobility}</strong></div></div>
        </Panel>}

        {nurseTab === "meds" && <Panel title="Medication administration" subtitle="Tap Give after administering (demo)">
          <table><thead><tr><th>Time</th><th>Medication</th><th>Route</th><th>Status</th><th /></tr></thead>
            <tbody>{current.meds.map((med) => <tr key={med.id}><td>{med.time}</td><td><strong>{med.name}</strong><small>{med.dose}</small></td><td>{med.route}</td>
              <td><span className={`pill ${med.status === "given" ? "pill-good" : med.status === "due" ? "pill-warn" : ""}`}>{med.status}</span></td>
              <td>{!med.given && <button className="btn btn-outline btn-small" disabled={busy} onClick={() => void give(med.id)}>Give</button>}</td></tr>)}</tbody></table>
        </Panel>}

        {nurseTab === "chart" && <Panel title="Daily nursing chart" subtitle="AI drafts from observations, medications and fluid balance. You review and sign."
          actions={<button className="btn btn-primary btn-small" disabled={drafting || busy} onClick={() => void generate()}>{drafting ? "Drafting…" : "✦ Draft chart with AI"}</button>}>
          {!draft && <Empty title="No draft yet" text="Nothing needs typing. Record vitals and medications, then draft the chart." />}
          {draft && <div className="portal-stack">
            <div className="bubble-meta"><ModeTag mode={draft.mode} />{draft.fallback_reason && <small>{draft.fallback_reason}</small>}</div>
            <div className="section-grid">{Object.entries(draft.sections).map(([name, value]) => <div className="section-card" key={name}><small>{name.replaceAll("_", " ").toUpperCase()}</small><p>{value}</p></div>)}</div>
            <label className="form-field"><small>Progress note (editable)</small><textarea rows={9} value={text} maxLength={2000} onChange={(event) => setText(event.target.value)} /></label>
            <label className="check-row"><input type="checkbox" checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} />I have reviewed this chart and it is accurate.</label>
            <div><button className="btn btn-primary" disabled={busy || !reviewed || text.trim().length < 10} onClick={() => void signChart()}>Sign & save chart</button></div>
          </div>}
          {current.charts.length > 0 && <div className="signed-list"><h3 className="sub-h">Signed today</h3>
            {current.charts.map((entry) => <div className="section-card" key={entry.id}><small>{entry.id} · {entry.signed_by} · {entry.signed_at.replace("T", " ")} · {entry.ai_mode === "live_gemini" ? "AI drafted (live)" : "AI drafted (simulation)"}</small><p className="pre">{entry.narrative}</p></div>)}</div>}
        </Panel>}
      </div>}
    </main>
  </div>;

  return <Shell theme="hospital" brand={hospital?.name ?? "Hospital"} tag="HOSPITAL OPERATIONS"
    right={<div className="persona-switch" role="group" aria-label="Persona">
      <button className={persona === "admin" ? "active" : ""} onClick={() => setPersona("admin")}>Hospital administrator</button>
      <button className={persona === "nurse" ? "active" : ""} onClick={() => setPersona("nurse")}>Nurse station</button>
    </div>}>
    <ToastView toast={toast} />
    <SyntheticBanner />
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    {persona === "admin" ? admin : nurse}
    {persona === "nurse" && pending.length === 0 && patients.length > 0 && <div className="inline-ok">All daily charts for this ward are signed.</div>}
  </Shell>;
}

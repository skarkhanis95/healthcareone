import { api } from "../api";
import { useLive } from "../hooks";
import { AiRuntime } from "../types";

const experiences = [
  { href: "/patient", icon: "P", title: "Patient portal", group: "CareFlow One", accent: "teal",
    text: "A full portal: profile, appointments, prescriptions with PDF download, health record, and an AI assistant that books by typing.", who: "Alex Morgan · Patient" },
  { href: "/clinician", icon: "✚", title: "Clinician workspace", group: "CareFlow One", accent: "blue",
    text: "See the patient's journey and issue prescriptions that appear instantly in the patient portal, with PDF export.", who: "Dr. Meera Shah · Clinician" },
  { href: "/hospital", icon: "▦", title: "Hospital command", group: "Workforce One", accent: "navy",
    text: "Network capacity wall. Open any hospital as its own app with administrator and nurse stations, including AI-drafted daily charting.", who: "Operations · Nurses" },
  { href: "/workforce", icon: "♧", title: "Workforce & approvals", group: "Workforce One", accent: "indigo",
    text: "Evaluate eligible staff, submit staffing and recovery plans, then approve and execute them.", who: "Presenter / Supervisor" },
  { href: "/director", icon: "▶", title: "Demo Director", group: "Simulation", accent: "slate",
    text: "Reset, trigger scenarios, and watch events, audit trail and agent traces. Keep this on the presenter screen.", who: "Presenter" },
];

export default function Launcher() {
  const { data, error } = useLive(() => api<{ status: string; ai: AiRuntime }>("/health", "presenter"), [], 6000);
  const online = !!data && !error;
  return <div className="experience theme-launcher">
    <div className="launcher-hero">
      <div className="launcher-brand"><span className="logo">H</span><strong>HealthCare<span>One</span></strong></div>
      <h1>One connected health network.<br />Pick an experience to open.</h1>
      <p>Each card opens in its own tab, tailored to who is using it. All tabs share the same live simulation, so a booking in the patient app shows up for the clinician and the command centre.</p>
      <div className="launcher-status">
        <span className={`dot ${online ? "on" : "off"}`} />{online ? "Backend connected" : "Backend not reachable. Start the API on port 8000."}
        {online && <><span className="sep" /><span className={`dot ${data.ai.configured ? "on" : "warn"}`} />
          {data.ai.configured ? `Live AI ready · ${data.ai.model}` : `AI simulation mode · ${data.ai.unavailable_reason ?? "not configured"}`}</>}
      </div>
    </div>
    <div className="launcher-grid">
      {experiences.map((item) => <a key={item.href} className={`launch-card accent-${item.accent}`} href={item.href} target="_blank" rel="noopener noreferrer">
        <span className="launch-icon">{item.icon}</span>
        <small>{item.group.toUpperCase()}</small>
        <h2>{item.title}</h2>
        <p>{item.text}</p>
        <div className="launch-foot"><span>{item.who}</span><b>Open in new tab ↗</b></div>
      </a>)}
    </div>
    <footer className="launcher-foot">Synthetic data only · Safety, eligibility and approvals are deterministic; AI never acts alone.</footer>
  </div>;
}

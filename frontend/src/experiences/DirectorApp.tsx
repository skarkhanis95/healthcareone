import { useState } from "react";
import { api } from "../api";
import { useAction, useLive, useToast } from "../hooks";
import { AiRuntime, AuditItem, DemoState } from "../types";
import { Empty, ModeTag, Panel, Shell, StatusBadge, ToastView } from "../ui";

const ROLE = "presenter" as const;
const scenarios = [
  { id: "collision", label: "Network collision response" },
  { id: "procedure-absence", label: "Procedure readiness recovery" },
];
type Tab = "events" | "audit" | "traces";

export default function DirectorApp() {
  const [tab, setTab] = useState<Tab>("events");
  const [scenarioId, setScenarioId] = useState("collision");
  const { toast, notify } = useToast();
  const { data, error, reload } = useLive(async () => {
    const [state, events, audit, traces, agents] = await Promise.all([
      api<DemoState>("/simulation/state", ROLE),
      api<AuditItem[]>("/events", ROLE),
      api<AuditItem[]>("/audit", ROLE),
      api<AuditItem[]>("/agents/traces", ROLE),
      api<{ runtime: AiRuntime }>("/agents", ROLE),
    ]);
    return { state, events, audit, traces, ai: agents.runtime };
  }, [], 4000);
  const { busy, run } = useAction(reload, notify);

  const status = data?.state.scenarios.find((item) => item.id === scenarioId)?.status ?? "baseline";
  const rows = data ? data[tab] : [];

  const smoke = () => run(async () => {
    const result = await api<{ model: string; tool_calls: string[] }>("/ai/smoke", ROLE, { method: "POST" });
    notify("success", `Live Gemini responded using ${result.tool_calls.join(", ")}.`);
  });

  return <Shell theme="director" brand="HealthCareOne" tag="DEMO DIRECTOR" right={<span className="chip">Presenter control room</span>}>
    <ToastView toast={toast} />
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    <div className="dir-layout">
      <div className="dir-side">
        <Panel title="Scenario control" subtitle="Every action is persisted and audited">
          <label className="field">Scenario
            <select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
              {scenarios.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
            </select></label>
          <div className="row"><span>Status</span><StatusBadge status={status} /></div>
          <div className="stack">
            <button className="btn btn-primary" disabled={busy || status !== "baseline"}
              onClick={() => run(() => api(`/simulation/scenarios/${scenarioId}/trigger`, ROLE, { method: "POST" }), "Scenario triggered.")}>▶ Trigger scenario</button>
            <button className="btn btn-outline" disabled={busy}
              onClick={() => run(() => api("/simulation/reset", ROLE, { method: "POST" }), "Reset to the baseline.")}>↻ Reset all data</button>
          </div>
          <p className="muted">Reset clears bookings, approvals, assignments, events and traces so the next run starts clean.</p>
          <div className="open-links"><b>Open the audience views</b>
            {[["/patient", "Patient portal"], ["/clinician", "Clinician workspace"], ["/hospital", "Hospital command"], ["/workforce", "Workforce & approvals"]].map(([href, label]) =>
              <a key={href} href={href} target="_blank" rel="noopener noreferrer">{label} ↗</a>)}
          </div>
        </Panel>
        <Panel title="AI runtime" subtitle={data?.ai.model}>
          <div className="row"><span>Gemini</span><StatusBadge status={data?.ai.configured ? "ready" : "unavailable"} /></div>
          {!data?.ai.configured && <p className="muted">{data?.ai.unavailable_reason ?? "Checking…"} The demo runs in labelled simulation mode.</p>}
          <button className="btn btn-outline" disabled={busy || !data?.ai.configured} onClick={smoke}>Run live Gemini smoke test</button>
        </Panel>
      </div>
      <Panel className="dir-stream" title="Activity" actions={<div className="segmented">
        {(["events", "audit", "traces"] as Tab[]).map((value) => <button key={value} className={tab === value ? "on" : ""} onClick={() => setTab(value)}>
          {value === "events" ? "Events" : value === "audit" ? "Audit" : "Agent traces"}</button>)}</div>}>
        {rows.length === 0 ? <Empty title="Nothing recorded yet" text="Trigger a scenario or use the patient app to generate activity." />
          : <ul className="stream">{rows.slice(0, 80).map((row) => <li key={`${tab}-${row.id}`}>
            <div className="stream-top"><strong>{row.type ?? row.action ?? row.agent_name}</strong>
              {tab === "traces" && typeof row.details?.mode === "string" && <ModeTag mode={row.details.mode} />}
              {row.actor && <span className="chip">{row.actor}</span>}
              {row.scenario_id && <span className="chip">{row.scenario_id}</span>}
              <small>{row.correlation_id.slice(0, 8)}</small></div>
            <code>{summary(row)}</code></li>)}</ul>}
      </Panel>
    </div>
  </Shell>;
}

function summary(row: AuditItem): string {
  const text = typeof row.details?.summary === "string" ? row.details.summary : JSON.stringify(row.details);
  return text.length > 220 ? text.slice(0, 217) + "…" : text;
}

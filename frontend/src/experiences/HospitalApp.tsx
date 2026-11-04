import { api } from "../api";
import { formatTime, useLive } from "../hooks";
import { DemoState, Hospital, Plan, Procedure } from "../types";
import { Empty, Panel, Shell, StatusBadge } from "../ui";

export default function HospitalApp() {
  const { data, error } = useLive(async () => {
    const [state, hospitals, procedures, plans] = await Promise.all([
      api<DemoState>("/simulation/state", "presenter"),
      api<Hospital[]>("/hospitals", "presenter"),
      api<Procedure[]>("/procedures", "presenter"),
      api<Plan[]>("/workforce/augmentation-plans", "presenter"),
    ]);
    return { state, hospitals, procedures, plans };
  }, [], 4000);

  const hospitals = [...(data?.hospitals ?? [])].sort((a, b) =>
    (a.id === "HCO-CENTRAL" ? -1 : 0) - (b.id === "HCO-CENTRAL" ? -1 : 0) || a.name.localeCompare(b.name));
  const central = hospitals.find((item) => item.id === "HCO-CENTRAL");
  const collision = data?.state.scenarios.find((item) => item.id === "collision")?.status ?? "baseline";
  const resolved = !!data?.plans.some((plan) => plan.scenario_id === "collision" && plan.status === "completed");
  const surge = collision !== "baseline" && !resolved;
  const pending = data?.plans.filter((plan) => plan.status === "pending_approval").length ?? 0;
  const atRisk = data?.procedures.filter((item) => item.readiness === "at_risk") ?? [];
  const deferred = data?.procedures.filter((item) => (item as Procedure & { status?: string }).status === "deferred") ?? [];
  const critical = hospitals.filter((item) => item.pressure === "Critical").length;

  return <Shell theme="hospital" brand="Workforce One" tag="NETWORK COMMAND" right={<span className="chip">Read only · live</span>}>
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    <div className="wall">
      <div className="kpi-strip">
        <div className="kpi"><small>NETWORK HOSPITALS</small><strong>{hospitals.length}</strong></div>
        <div className={`kpi ${critical ? "kpi-bad" : ""}`}><small>CRITICAL PRESSURE</small><strong>{critical}</strong></div>
        <div className={`kpi ${surge ? "kpi-warn" : ""}`}><small>ED RN GAP · CENTRAL</small><strong>{surge ? 4 : 0}</strong></div>
        <div className={`kpi ${surge ? "kpi-warn" : ""}`}><small>TRAUMA SUPPORT GAP</small><strong>{surge ? 1 : 0}</strong></div>
        <div className={`kpi ${pending ? "kpi-warn" : ""}`}><small>PLANS AWAITING APPROVAL</small><strong>{pending}</strong></div>
        <div className={`kpi ${atRisk.length ? "kpi-bad" : ""}`}><small>PROCEDURES AT RISK</small><strong>{atRisk.length}</strong></div>
      </div>

      {surge && central && <div className="alert-bar"><b>Collision response active</b>
        <span>{central.name}: {central.projected_arrivals} projected arrivals, projected census {central.ed_census + central.projected_arrivals}/{central.ed_capacity}. Workforce plan {pending ? "awaiting supervisor approval" : "not yet approved"}.</span></div>}
      {resolved && <div className="alert-bar alert-good"><b>Staffing plan executed</b><span>Gaps resolved after supervisor approval. See the audit trail in Demo Director.</span></div>}

      <div className="wall-grid">
        <Panel title="Emergency department capacity" subtitle="Open any hospital as its own app, in a new tab" className="wall-panel">
          <div className="hospital-grid">
            {hospitals.map((item) => {
              const projected = item.ed_census + item.projected_arrivals;
              const pct = Math.min(100, Math.round((projected / item.ed_capacity) * 100));
              return <a key={item.id} href={`/hospital/${item.id}`} target="_blank" rel="noopener noreferrer" className={`hospital-tile pressure-${item.pressure}`}>
                <div className="tile-top"><strong>{item.name}</strong><StatusBadge status={item.pressure} /></div>
                <div className="bar"><i style={{ width: `${pct}%` }} /></div>
                <small>{item.ed_census} in ED{item.projected_arrivals ? ` + ${item.projected_arrivals} arriving` : ""} · capacity {item.ed_capacity}</small>
                <span className="tile-hint">Open hospital app ↗</span>
              </a>;
            })}
          </div>
        </Panel>
        <Panel title="Procedures" subtitle="Central Medical Center" className="wall-panel">
          {data && data.procedures.length > 0 ? <ul className="proc-list">
            {data.procedures.map((item) => <li key={item.id}>
              <div><strong>{item.id}</strong><small>{item.name} · {item.room} · {formatTime(item.scheduled_at)}</small>
                {item.readiness_reasons.filter((reason) => reason.startsWith("Missing")).map((reason) => <small key={reason} className="bad-text">{reason}</small>)}</div>
              <StatusBadge status={deferred.includes(item) ? "deferred" : item.readiness} />
            </li>)}
          </ul> : <Empty title="No procedures" text="Procedures appear once the simulation loads." />}
        </Panel>
      </div>
    </div>
  </Shell>;
}

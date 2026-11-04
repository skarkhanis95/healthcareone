import { useEffect, useState } from "react";
import { api, DemoRole, newIdempotencyKey } from "../api";
import { useAction, useLive, useToast } from "../hooks";
import { Candidates, DemoState, Plan, Procedure } from "../types";
import { Empty, Metric, Panel, Shell, StatusBadge, ToastView } from "../ui";

const scenarios = [
  { id: "collision", label: "Collision response", blurb: "Surge at Central Medical Center needs ED nurses and trauma support from across the network." },
  { id: "procedure-absence", label: "Procedure recovery", blurb: "A team member is unavailable for PROC-310. Find a safe replacement." },
];

export default function WorkforceApp() {
  const [role, setRole] = useState<DemoRole>("presenter");
  const [scenarioId, setScenarioId] = useState("collision");
  const [selected, setSelected] = useState<string[]>([]);
  const [defer, setDefer] = useState(false);
  const { toast, notify } = useToast();

  const { data, error, reload } = useLive(async () => {
    const [state, plans, procedures] = await Promise.all([
      api<DemoState>("/simulation/state", role),
      api<Plan[]>("/workforce/augmentation-plans", role),
      api<Procedure[]>("/procedures", role),
    ]);
    const statuses = Object.fromEntries(state.scenarios.map((item) => [item.id, item.status]));
    const active = statuses[scenarioId] !== "baseline";
    const candidates = active
      ? await api<Candidates>(`/staff/availability?scenario_id=${scenarioId}`, role)
      : { eligible: [], excluded: [] };
    return { state, plans, procedures, candidates };
  }, [role, scenarioId], 5000);
  const { busy, run } = useAction(reload, notify);

  const status = data?.state.scenarios.find((item) => item.id === scenarioId)?.status ?? "baseline";
  const eligible = data?.candidates.eligible ?? [];
  const excluded = data?.candidates.excluded ?? [];
  const collision = scenarioId === "collision";
  const pendingPlans = data?.plans.filter((plan) => plan.status === "pending_approval") ?? [];
  const eligibleKey = eligible.map((item) => item.id).join(",");

  useEffect(() => {
    setSelected(collision ? eligible.map((item) => item.id) : eligible.slice(0, 1).map((item) => item.id));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eligibleKey, scenarioId]);

  const toggle = (id: string) => setSelected((current) =>
    collision ? (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]) : [id]);

  const trigger = () => run(() => api(`/simulation/scenarios/${scenarioId}/trigger`, role, { method: "POST" }), "Scenario triggered.");
  const submit = () => run(() => api("/workforce/augmentation-plans", role, {
    method: "POST", body: { scenario_id: scenarioId, selected_staff_ids: selected, defer_procedure: collision && defer },
  }), "Plan submitted. Nothing changes until a supervisor approves.");
  const decide = (plan: Plan, decision: "approved" | "rejected") => run(async () => {
    await api(`/approvals/${plan.id}/decision`, role, {
      method: "POST",
      body: { decision, notes: decision === "approved" ? "Evidence and constraints reviewed." : "Plan declined by supervisor." },
    });
    if (decision === "approved") {
      await api("/simulation/actions/execute", role, { method: "POST", body: { plan_id: plan.id, idempotency_key: newIdempotencyKey() } });
    }
  }, decision === "approved" ? "Approved, revalidated and executed." : "Plan rejected. No assignments changed.");

  const toggleRole = <div className="segmented" role="group" aria-label="Acting as">
    {(["presenter", "supervisor"] as DemoRole[]).map((value) =>
      <button key={value} className={role === value ? "on" : ""} onClick={() => setRole(value)}>{value === "presenter" ? "Operations planner" : "Supervisor"}</button>)}
  </div>;

  return <Shell theme="workforce" brand="Workforce One" tag="WORKFORCE & APPROVALS" right={toggleRole}>
    <ToastView toast={toast} />
    {error && <div className="inline-error">Cannot reach the service: {error}</div>}
    <div className="wf-layout">
      <div className="wf-main">
        <div className="scenario-tabs">
          {scenarios.map((item) => <button key={item.id} className={`scenario-tab ${scenarioId === item.id ? "on" : ""}`} onClick={() => setScenarioId(item.id)}>
            <strong>{item.label}</strong><small>{item.blurb}</small>
            <StatusBadge status={data?.state.scenarios.find((entry) => entry.id === item.id)?.status ?? "baseline"} />
          </button>)}
        </div>

        {status === "baseline"
          ? <Panel><Empty title="Scenario not started" text="The operations planner triggers the scenario to calculate gaps and evaluate candidates." />
            <div className="center"><button className="btn btn-primary" disabled={busy || role !== "presenter"} onClick={trigger}>Trigger scenario</button>
              {role !== "presenter" && <p className="muted">Switch to Operations planner to trigger.</p>}</div></Panel>
          : <>
            {collision && <div className="metric-row"><Metric label="ED RN gap" value={status === "completed" && data?.plans.some((plan) => plan.status === "completed") ? 0 : 4} tone="warn" />
              <Metric label="Trauma support gap" value={status === "completed" && data?.plans.some((plan) => plan.status === "completed") ? 0 : 1} tone="blue" />
              <Metric label="Eligible / excluded" value={`${eligible.length} / ${excluded.length}`} note="By hard constraints" tone="neutral" /></div>}
            <Panel title="Candidate evidence" subtitle="Eligibility is decided by policy services, not AI">
              <table><thead><tr><th></th><th>Staff</th><th>Role & skills</th><th>Site</th><th>Evidence</th><th>Status</th></tr></thead>
                <tbody>
                  {eligible.map((person) => <tr key={person.id}>
                    <td><input type="checkbox" aria-label={`Select ${person.name}`} checked={selected.includes(person.id)} disabled={busy || status !== "triggered"} onChange={() => toggle(person.id)} /></td>
                    <td><strong>{person.name}</strong><small>{person.id}</small></td><td>{person.role}<small>{person.skills.join(" · ")}</small></td>
                    <td>{person.hospital_id}</td><td>{person.reason}</td><td><StatusBadge status="eligible" /></td></tr>)}
                  {excluded.map((person) => <tr key={person.id} className="muted-row"><td>—</td>
                    <td><strong>{person.name}</strong><small>{person.id}</small></td><td>{person.role}<small>{person.skills.join(" · ")}</small></td>
                    <td>{person.hospital_id}</td><td>{person.reason}</td><td><StatusBadge status="excluded" /></td></tr>)}
                </tbody></table>
            </Panel>
            <Panel title={collision ? "Proposed actions" : "Replacement recommendation"} subtitle="Recommendations are not applied until a supervisor approves and the plan is executed">
              {collision && <label className="check-row"><input type="checkbox" checked={defer} disabled={status !== "triggered"} onChange={(event) => setDefer(event.target.checked)} />
                <span><strong>Defer PROC-220</strong><small>Elective and deferrable. PROC-221 stays protected.</small></span></label>}
              <div className="plan-foot"><span>{selected.length} staff selected</span>
                <button className="btn btn-primary" disabled={busy || role !== "presenter" || status !== "triggered" || selected.length === 0} onClick={submit}>Submit for approval</button></div>
              {role !== "presenter" && status === "triggered" && <p className="muted">Switch to Operations planner to submit.</p>}
            </Panel>
          </>}
      </div>

      <aside className="wf-side">
        <Panel title="Approvals" subtitle={role === "supervisor" ? "You are acting as Supervisor" : "Read only until you switch to Supervisor"}>
          {pendingPlans.length === 0 ? <Empty title="Nothing waiting" text="Submitted plans appear here for review." />
            : pendingPlans.map((plan) => <div className="approval" key={plan.id}>
              <div className="approval-top"><strong>{plan.id}</strong><StatusBadge status={plan.status} /></div>
              <small>{plan.scenario_id === "collision" ? "Collision response" : "Procedure recovery"}</small>
              <ul>{plan.selected_staff_ids.map((id) => {
                const person = plan.evidence.eligible.find((item) => item.id === id);
                return <li key={id}>{person ? `${person.name} · ${person.role}` : id}</li>;
              })}</ul>
              {plan.defer_procedure && <p className="tag-line">Defer PROC-220</p>}
              <p className="muted">Eligibility is re-checked at execution.</p>
              <div className="approval-actions">
                <button className="btn btn-primary" disabled={busy || role !== "supervisor"} onClick={() => decide(plan, "approved")}>Approve & execute</button>
                <button className="btn btn-quiet" disabled={busy || role !== "supervisor"} onClick={() => decide(plan, "rejected")}>Reject</button></div>
            </div>)}
        </Panel>
        <Panel title="Decided plans">
          {data?.plans.filter((plan) => plan.status !== "pending_approval").length
            ? data.plans.filter((plan) => plan.status !== "pending_approval").map((plan) => <div className="decided" key={plan.id}>
              <span>{plan.id} · {plan.scenario_id}</span><StatusBadge status={plan.status} /></div>)
            : <p className="muted">None yet.</p>}
        </Panel>
        {data && (() => {
          const procedure = data.procedures.find((item) => item.id === "PROC-310");
          return procedure ? <Panel title="PROC-310 readiness"><div className="decided"><span>{procedure.room} · team {procedure.team.length}</span><StatusBadge status={procedure.readiness} /></div>
            {procedure.readiness_reasons.map((reason) => <small className="bad-text" key={reason}>{reason}</small>)}</Panel> : null;
        })()}
      </aside>
    </div>
  </Shell>;
}

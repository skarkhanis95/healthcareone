import { ReactNode } from "react";
import { Toast } from "./hooks";

export function ToastView({ toast }: { toast: Toast | null }) {
  return toast ? <div className={`toast toast-${toast.kind}`} role="status">{toast.message}</div> : null;
}

const badgeTone: Record<string, string> = {
  ready: "good", available: "good", eligible: "good", approved: "good", executed: "good", completed: "good",
  confirmed: "good", Normal: "good", Elevated: "warn", at_risk: "bad", Critical: "bad", excluded: "bad",
  unavailable: "bad", rejected: "bad", triggered: "warn", pending_approval: "warn", awaiting_approval: "warn",
};

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${badgeTone[status] ?? "neutral"}`}>{status.replaceAll("_", " ")}</span>;
}

export function ModeTag({ mode }: { mode: string }) {
  if (mode === "live_gemini") return <span className="mode-tag mode-live">LIVE AI</span>;
  if (mode === "deterministic_policy") return <span className="mode-tag mode-policy">SAFETY POLICY</span>;
  return <span className="mode-tag mode-sim">SIMULATION</span>;
}

export function Metric({ label, value, note, tone = "neutral" }: { label: string; value: ReactNode; note?: string; tone?: string }) {
  return <div className={`metric metric-${tone}`}><small>{label}</small><strong>{value}</strong>{note && <span>{note}</span>}</div>;
}

export function Panel({ title, subtitle, actions, children, className = "" }: {
  title?: string; subtitle?: string; actions?: ReactNode; children: ReactNode; className?: string;
}) {
  return <section className={`panel ${className}`}>
    {title && <div className="panel-head"><div><h3>{title}</h3>{subtitle && <p>{subtitle}</p>}</div>{actions}</div>}
    {children}
  </section>;
}

export function Empty({ title, text }: { title: string; text: string }) {
  return <div className="empty"><strong>{title}</strong><p>{text}</p></div>;
}

export function SyntheticBanner({ time }: { time?: string }) {
  return <div className="synthetic-banner">
    <strong>DEMO ENVIRONMENT</strong>
    <span>All patients, staff and facilities are synthetic. No real healthcare systems are connected.</span>
    {time && <em>SIM TIME · {time.replace("T", " ")}</em>}
  </div>;
}

export function Shell({ theme, brand, tag, children, right }: {
  theme: string; brand: string; tag: string; children: ReactNode; right?: ReactNode;
}) {
  return <div className={`experience theme-${theme}`}>
    <header className="exp-header">
      <a className="exp-brand" href="/"><span className="logo">H</span><span><strong>{brand}</strong><small>{tag}</small></span></a>
      <div className="exp-right">{right}<a className="link-quiet" href="/">All experiences</a></div>
    </header>
    {children}
  </div>;
}

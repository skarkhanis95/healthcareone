import { useEffect, useState } from "react";
import { api } from "../api";
import { useLive } from "../hooks";
import { Hospital, OpdBoard } from "../types";

export default function OpdDisplayBoard({ hospitalId }: { hospitalId: string }) {
  const { data: opd, error } = useLive(() => api<OpdBoard>(`/hospitals/${hospitalId}/opd`, "presenter"), [hospitalId], 5000);
  const { data: hospitals } = useLive(() => api<Hospital[]>("/hospitals", "presenter"), []);
  const [now, setNow] = useState(new Date());
  const name = hospitals?.find((item) => item.id === hospitalId)?.name ?? "Hospital";

  useEffect(() => { const timer = window.setInterval(() => setNow(new Date()), 1000); return () => window.clearInterval(timer); }, []);
  useEffect(() => { document.title = `OPD Display | ${name}`; }, [name]);

  return <div className="board">
    <header className="board-head">
      <div><h1>{name}</h1><p>Outpatient Department · Today's consultations</p></div>
      <div className="board-clock"><strong>{now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</strong>
        <span>{now.toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" })}</span></div>
    </header>
    {error && <div className="board-error">Connection lost. Retrying…</div>}
    {opd && <>
      <div className="board-stats">
        <div><span>Doctors on duty</span><strong>{opd.summary.doctors_on_opd}</strong></div>
        <div><span>Patients waiting</span><strong>{opd.summary.in_queue}</strong></div>
        <div><span>Average wait</span><strong>{opd.summary.avg_wait_minutes} min</strong></div>
      </div>
      <div className="board-table">
        <div className="board-row board-th"><span>Room</span><span>Doctor</span><span>Now serving</span><span>Waiting</span><span>Est. wait</span></div>
        {opd.doctors.map((row) => <div key={row.room} className={`board-row ${row.status === "On break" ? "off" : ""}`}>
          <span className="board-room">{row.room}</span>
          <span><b>{row.doctor}</b><small>{row.specialty}</small></span>
          <span>{row.status === "On break" ? "On break" : row.now_serving ?? "Available"}</span>
          <span className="board-num">{row.in_queue}</span>
          <span className={`board-num ${row.avg_wait_minutes > 30 ? "long" : ""}`}>{row.avg_wait_minutes ? `${row.avg_wait_minutes} min` : "-"}</span>
        </div>)}
      </div>
    </>}
    <footer className="board-foot">Please wait for your token to be called · Synthetic demo data</footer>
  </div>;
}

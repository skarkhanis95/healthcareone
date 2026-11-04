import { Slot } from "../types";

export interface BookingNotice {
  kind: "booked" | "rescheduled";
  slot: Slot;
  appointmentId: string;
  patientName: string;
  patientAddress: string;
}

// Demo-only: a deterministic stand-in for a live traffic model, so the same slot always yields the same advice.
function trafficAdvice(notice: BookingNotice) {
  const seed = [...notice.slot.id].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const start = new Date(notice.slot.starts_at);
  const hour = start.getHours();
  const rush = (hour >= 8 && hour < 11) || (hour >= 17 && hour < 20);
  const base = 18 + (seed % 12);
  const travel = base + (rush ? 14 : 0);
  const checkIn = 15;
  const leave = new Date(start.getTime() - (travel + checkIn) * 60000);
  return { travel, rush, checkIn, leave };
}

const clock = (date: Date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
const day = (date: Date) => date.toLocaleDateString([], { weekday: "long", day: "numeric", month: "short" });

export function PhoneDrawer({ notice, onClose }: { notice: BookingNotice | null; onClose: () => void }) {
  if (!notice) return null;
  const { slot } = notice;
  const start = new Date(slot.starts_at);
  const virtual = slot.mode === "virtual";
  const advice = trafficAdvice(notice);
  const verb = notice.kind === "rescheduled" ? "rescheduled" : "confirmed";
  const sent = clock(new Date());

  return <>
    <div className="drawer-backdrop" onClick={onClose} />
    <aside className="phone-drawer" role="dialog" aria-label="Message sent to patient">
      <button className="drawer-close" onClick={onClose} aria-label="Close">✕</button>
      <p className="drawer-caption">Demo: the message your patient receives on WhatsApp</p>
      <div className="phone">
        <div className="phone-notch" />
        <div className="wa-header"><span className="wa-back">‹</span><span className="avatar">C</span>
          <div><strong>CareFlow One</strong><small>Official business account ✓</small></div></div>
        <div className="wa-chat">
          <div className="wa-day">TODAY</div>
          <div className="wa-bubble">
            <p>Hi {notice.patientName.split(" ")[0]} 👋 your appointment is <strong>{verb}</strong>.</p>
            <p>🩺 <strong>{slot.doctor.name}</strong><br />{slot.doctor.specialty}</p>
            <p>📅 {day(start)}<br />🕒 {clock(start)} · {slot.mode.replace("_", " ")}</p>
            {virtual
              ? <p>💻 Join link opens 5 minutes before: careflow.one/visit/{notice.appointmentId}</p>
              : <p>📍 {slot.doctor.location}<br />CareFlow One Hospital, Reception → OPD</p>}
            <span className="wa-time">{sent} ✓✓</span>
          </div>
          {!virtual && <div className="wa-bubble">
            <p>🚗 <strong>Leave by {clock(advice.leave)}</strong></p>
            <p>From {notice.patientAddress || "your home"} it's about {advice.travel} min with {advice.rush ? "heavy rush-hour" : "light"} traffic, plus {advice.checkIn} min for check-in.</p>
            <p>We'll re-check traffic and nudge you if you need to leave earlier.</p>
            <span className="wa-ai">✦ AI suggested · demo estimate</span>
            <span className="wa-time">{sent} ✓✓</span>
          </div>}
          <div className="wa-actions"><span>Reply 1 to confirm</span><span>Reply 2 to reschedule</span></div>
        </div>
        <div className="wa-input"><span>Message</span></div>
      </div>
    </aside>
  </>;
}

import { useEffect } from "react";
import Launcher from "./experiences/Launcher";
import PatientApp from "./experiences/PatientApp";
import ClinicianApp from "./experiences/ClinicianApp";
import HospitalApp from "./experiences/HospitalApp";
import HospitalConsole from "./experiences/HospitalConsole";
import OpdDisplayBoard from "./experiences/OpdDisplayBoard";
import WorkforceApp from "./experiences/WorkforceApp";
import DirectorApp from "./experiences/DirectorApp";

const routes: Record<string, { title: string; component: () => JSX.Element }> = {
  "/": { title: "HealthCareOne", component: Launcher },
  "/patient": { title: "Patient app | CareFlow One", component: PatientApp },
  "/clinician": { title: "Clinician workspace | CareFlow One", component: ClinicianApp },
  "/hospital": { title: "Hospital command | Workforce One", component: HospitalApp },
  "/workforce": { title: "Workforce & approvals | Workforce One", component: WorkforceApp },
  "/director": { title: "Demo Director | HealthCareOne", component: DirectorApp },
};

export default function App() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  const displayMatch = path.match(/^\/hospital\/(HCO-[A-Z]+)\/display$/i);
  if (displayMatch) return <OpdDisplayBoard hospitalId={displayMatch[1].toUpperCase()} />;
  const hospitalMatch = path.match(/^\/hospital\/(HCO-[A-Z]+)$/i);
  if (hospitalMatch) return <HospitalConsole hospitalId={hospitalMatch[1].toUpperCase()} />;
  const route = routes[path] ?? routes["/"];
  useEffect(() => { document.title = route.title; }, [route.title]);
  const Page = route.component;
  return <Page />;
}

// Lets separate browser tabs refresh each other right after a change.
const channel = typeof BroadcastChannel !== "undefined" ? new BroadcastChannel("healthcareone-sync") : null;

export function notifyChange(): void {
  channel?.postMessage("changed");
}

export function onChange(callback: () => void): () => void {
  channel?.addEventListener("message", callback);
  return () => channel?.removeEventListener("message", callback);
}

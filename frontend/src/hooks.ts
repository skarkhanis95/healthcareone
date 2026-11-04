import { useCallback, useEffect, useRef, useState } from "react";
import { notifyChange, onChange } from "./sync";

export interface Toast { kind: "success" | "error"; message: string }

export function useToast() {
  const [toast, setToast] = useState<Toast | null>(null);
  const timer = useRef<number | undefined>(undefined);
  const notify = useCallback((kind: Toast["kind"], message: string) => {
    setToast({ kind, message });
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setToast(null), 4200);
  }, []);
  return { toast, notify };
}

/** Loads data on mount, on an interval, and whenever another tab announces a change. */
export function useLive<T>(load: () => Promise<T>, deps: unknown[], intervalMs = 8000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const loader = useRef(load);
  loader.current = load;

  const reload = useCallback(async () => {
    try {
      setData(await loader.current());
      setError(null);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Could not load data.");
    }
  }, []);

  useEffect(() => {
    void reload();
    const timer = window.setInterval(() => void reload(), intervalMs);
    const unsubscribe = onChange(() => void reload());
    return () => { window.clearInterval(timer); unsubscribe(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, error, reload };
}

export function useAction(reload: () => Promise<void>, notify: (kind: Toast["kind"], message: string) => void) {
  const [busy, setBusy] = useState(false);
  const run = useCallback(async (task: () => Promise<unknown>, success?: string) => {
    setBusy(true);
    try {
      await task();
      notifyChange();
      await reload();
      if (success) notify("success", success);
    } catch (failure) {
      notify("error", failure instanceof Error ? failure.message : "The action failed.");
    } finally {
      setBusy(false);
    }
  }, [reload, notify]);
  return { busy, run };
}

export function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString([], { weekday: "short", hour: "2-digit", minute: "2-digit" });
}

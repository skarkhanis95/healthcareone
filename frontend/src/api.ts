export type DemoRole = "patient" | "presenter" | "supervisor" | "clinician" | "nurse";

export interface Envelope<T> {
  success: boolean;
  data: T;
  error: { code: string; message: string } | null;
  correlation_id: string;
}

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export async function api<T>(
  path: string,
  role: DemoRole,
  options: { method?: string; body?: unknown } = {},
): Promise<T> {
  const correlationId = crypto.randomUUID();
  const response = await fetch(`${API_BASE}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      "X-Demo-Role": role,
      "X-Correlation-ID": correlationId,
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  let result: Envelope<T>;
  try {
    result = (await response.json()) as Envelope<T>;
  } catch {
    throw new Error(`The API returned an unreadable response (${response.status}).`);
  }
  if (!response.ok || !result.success) {
    throw new Error(result.error?.message ?? `The request failed (${response.status}).`);
  }
  return result.data;
}

export function newIdempotencyKey(): string {
  return crypto.randomUUID();
}


"use client";

import useSWR, { mutate as globalMutate } from "swr";
import type {
  AccountOut,
  AccountsOut,
  ActionKind,
  ActionOut,
  Alert,
  Application,
  CaptureOut,
  CatalogueOut,
  Consent,
  ConsentPreview,
  DuesOut,
  ExpiryOut,
  ForecastOut,
  FundingPlanOut,
  Lender,
  LogEvent,
  OrderOut,
  PassportOut,
  PauseOut,
  Pharmacy,
  PolicyOut,
  ShelfLifeCreditOut,
  TrimOut,
  ValueOut,
  VerifyOut,
} from "@/lib/types";

export const PID = "green-life";
const BASE = "/api/v1";

// ---------- session ----------

/** Fired on any 401 from an owner route: the PIN gate shows the PIN screen. */
export const LOCKED_EVENT = "lamp:locked";
/** Fired after a correct PIN: screens and the log stream reconnect. */
export const UNLOCKED_EVENT = "lamp:unlocked";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** Sandbox lender keys, published in contracts/plan_v3.md; the lender view sends them as X-Lender-Key. */
const LENDER_KEYS: Record<string, string> = {
  "wallet-lender": "wallet-lender-demo-key",
  "partner-bank": "partner-bank-demo-key",
};
const lenderHeaders = (lenderId: string) => ({ "X-Lender-Key": LENDER_KEYS[lenderId] ?? "" });

// ---------- transport ----------

async function liveFetch(method: string, path: string, body?: unknown, headers?: Record<string, string>): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    credentials: "include",
    headers: { ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    // Lock only when the session is missing or expired; a wrong PIN at approval is answered in its dialog.
    if (res.status === 401 && !path.startsWith("/lenders") && !text.includes("needs the owner PIN") && typeof window !== "undefined") {
      window.dispatchEvent(new Event(LOCKED_EVENT));
    }
    throw new ApiError(res.status, text || `${method} ${path} failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export async function apiGet<T>(path: string, headers?: Record<string, string>): Promise<T> {
  return liveFetch("GET", path, undefined, headers) as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown, headers?: Record<string, string>): Promise<T> {
  return liveFetch("POST", path, body, headers) as Promise<T>;
}

/** Unlock with the owner PIN. The API sets an HttpOnly session cookie. Throws ApiError(401) on a wrong PIN. */
export async function unlock(pin: string) {
  const res = await fetch(`${BASE}/pharmacies/${PID}/session`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin }),
  });
  if (!res.ok) throw new ApiError(res.status, res.status === 401 ? "Wrong PIN" : `Unlock failed (${res.status})`);
  window.dispatchEvent(new Event(UNLOCKED_EVENT));
  await refreshAll();
}

export async function apiDelete<T>(path: string): Promise<T> {
  return liveFetch("DELETE", path) as Promise<T>;
}

export async function uploadCapture(kind: "invoice" | "sales_page", file: File): Promise<CaptureOut> {
  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);
  const res = await fetch(`${BASE}/pharmacies/${PID}/captures`, { method: "POST", body: form, credentials: "include" });
  if (res.status === 401) window.dispatchEvent(new Event(LOCKED_EVENT));
  if (!res.ok) throw new ApiError(res.status, `Upload failed (${res.status})`);
  return res.json();
}

/** Live audit log over SSE. Reconnects after the owner unlocks (the stream needs the session). */
export function subscribeLogs(onEvent: (e: LogEvent) => void): () => void {
  let es: EventSource | null = null;
  const open = () => {
    es?.close();
    es = new EventSource(`${BASE}/logs/stream`, { withCredentials: true });
    es.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data) as LogEvent);
      } catch {
        /* ignore malformed events */
      }
    };
  };
  open();
  window.addEventListener(UNLOCKED_EVENT, open);
  return () => {
    window.removeEventListener(UNLOCKED_EVENT, open);
    es?.close();
  };
}

/** Re-fetch everything after a state change (approve, confirm, consent). */
export function refreshAll() {
  return globalMutate(() => true);
}

// ---------- hooks ----------

const ph = (p: string) => `/pharmacies/${PID}${p}`;
const get = <T,>(key: string) => apiGet<T>(key);

export const usePharmacy = () => useSWR<Pharmacy>(ph(""), get);
export const useAccounts = () => useSWR<AccountsOut>(ph("/accounts?period_days=30"), get);
export const useDues = () => useSWR<DuesOut>(ph("/dues"), get);
export const useForecast = () => useSWR<ForecastOut>(ph("/forecast?days=30"), get);
export const useAlerts = () => useSWR<Alert[]>(ph("/alerts"), get);
export const useExpiry = () => useSWR<ExpiryOut>(ph("/expiry?horizon_days=60"), get);
export const useOrders = () => useSWR<OrderOut[]>(ph("/orders"), get);
export const useTrim = (orderId?: string) => useSWR<TrimOut>(orderId ? ph(`/orders/${orderId}/trim`) : null, get);
export const useFundingPlan = () => useSWR<FundingPlanOut>(ph("/funding-plan"), (k: string) => apiPost<FundingPlanOut>(k, {}));
export const usePassport = () => useSWR<PassportOut>(ph("/passport"), get);
export const useActions = () => useSWR<ActionOut[]>(ph("/actions"), get);
export const useConsents = () => useSWR<Consent[]>(ph("/consents"), get);
export const useLenders = () => useSWR<Lender[]>("/lenders", get);
export const useApplications = (lenderId: string) =>
  useSWR<Application[]>(`/lenders/${lenderId}/applications`, (k: string) => apiGet<Application[]>(k, lenderHeaders(lenderId)));
export const useLogs = () => useSWR<LogEvent[]>("/logs", get);
export const useLogVerify = () => useSWR<VerifyOut>("/logs/verify", get);
export const useCatalogue = () => useSWR<CatalogueOut>(ph("/financing-catalogue"), get);
export const useShelfLifeCredit = () => useSWR<ShelfLifeCreditOut>(ph("/shelf-life-credit"), get);
export const usePause = () => useSWR<PauseOut>(ph("/pause"), get);
export const usePolicy = () => useSWR<PolicyOut>(ph("/policy"), get);
export const useAccount = () => useSWR<AccountOut>(ph("/account"), get);
export const useValue = () => useSWR<ValueOut>(ph("/value"), get);
export const useConsentPreview = (lenderId: string | null, scopes: string[]) =>
  useSWR<ConsentPreview>(lenderId ? ph(`/consents/preview?lender_id=${lenderId}&scopes=${scopes.join(",")}`) : null, get);

// ---------- mutations ----------

export async function proposeAction(kind: ActionKind, payload: ActionOut["payload"]) {
  const a = await apiPost<ActionOut>(ph("/actions"), { kind, payload, proposed_by: "owner" });
  await refreshAll();
  return a;
}

/** Approve or reject. Loan applications (requires_pin) need the owner PIN again. */
export async function decideAction(id: string, decision: "approve" | "reject", pin?: string) {
  const a = await apiPost<ActionOut>(ph(`/actions/${id}/${decision}`), pin ? { pin } : undefined);
  await refreshAll();
  return a;
}

/** Pause LaMP: the copilot and the scheduler can't propose, and their proposals can't be approved. */
export async function setPaused(paused: boolean) {
  const p = await apiPost<PauseOut>(ph("/pause"), { paused });
  await globalMutate(ph("/pause"), p, { revalidate: false });
  refreshAll();
  return p;
}

export async function grantConsent(lenderId: string, scopes: string[]) {
  await apiPost(ph("/consents"), { lender_id: lenderId, scopes });
  await refreshAll();
}

export async function withdrawConsent(consentId: string) {
  await apiDelete(ph(`/consents/${consentId}`));
  await refreshAll();
}

/** Send only the owner-corrected part (invoice or sales page); the API rejects anything else. */
export async function confirmCapture(id: string, extraction: CaptureOut["extraction"]) {
  const body = extraction.kind === "invoice" ? { invoice: extraction.invoice } : { sales_page: extraction.sales_page };
  await apiPost(ph(`/captures/${id}/confirm`), body);
  await refreshAll();
}

export async function lenderDecide(lenderId: string, appId: string) {
  await apiPost(`/lenders/${lenderId}/applications/${appId}/decide`, undefined, lenderHeaders(lenderId));
  await refreshAll();
}

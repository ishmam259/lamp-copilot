"use client";

import useSWR, { mutate as globalMutate } from "swr";
import type {
  AccountsOut,
  ActionKind,
  ActionOut,
  Alert,
  Application,
  CaptureOut,
  Consent,
  DuesOut,
  ExpiryOut,
  ForecastOut,
  FundingPlanOut,
  Lender,
  LogEvent,
  OrderOut,
  PassportOut,
  Pharmacy,
  TrimOut,
} from "@/lib/types";

export const PID = "green-life";
const BASE = "/api/v1";

// ---------- transport ----------

async function liveFetch(method: string, path: string, body?: unknown): Promise<unknown> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `${method} ${path} failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export async function apiGet<T>(path: string): Promise<T> {
  return liveFetch("GET", path) as Promise<T>;
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  return liveFetch("POST", path, body) as Promise<T>;
}

export async function apiDelete<T>(path: string): Promise<T> {
  return liveFetch("DELETE", path) as Promise<T>;
}

export async function uploadCapture(kind: "invoice" | "sales_page", file: File): Promise<CaptureOut> {
  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);
  const res = await fetch(`${BASE}/pharmacies/${PID}/captures`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return res.json();
}

export function subscribeLogs(onEvent: (e: LogEvent) => void): () => void {
  const es = new EventSource(`${BASE}/logs/stream`);
  es.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as LogEvent);
    } catch {
      /* ignore malformed events */
    }
  };
  return () => es.close();
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
export const useApplications = (lenderId: string) => useSWR<Application[]>(`/lenders/${lenderId}/applications`, get);
export const useLogs = () => useSWR<LogEvent[]>("/logs", get);

// ---------- mutations ----------

export async function proposeAction(kind: ActionKind, payload: ActionOut["payload"]) {
  const a = await apiPost<ActionOut>(ph("/actions"), { kind, payload, proposed_by: "owner" });
  await refreshAll();
  return a;
}

export async function decideAction(id: string, decision: "approve" | "reject") {
  const a = await apiPost<ActionOut>(ph(`/actions/${id}/${decision}`));
  await refreshAll();
  return a;
}

export async function grantConsent(lenderId: string, scopes: string[]) {
  await apiPost(ph("/consents"), { lender_id: lenderId, scopes });
  await refreshAll();
}

export async function withdrawConsent(consentId: string) {
  await apiDelete(`/consents/${consentId}`);
  await refreshAll();
}

/** Send only the owner-corrected part (invoice or sales page); the API rejects anything else. */
export async function confirmCapture(id: string, extraction: CaptureOut["extraction"]) {
  const body = extraction.kind === "invoice" ? { invoice: extraction.invoice } : { sales_page: extraction.sales_page };
  await apiPost(ph(`/captures/${id}/confirm`), body);
  await refreshAll();
}

export async function lenderDecide(lenderId: string, appId: string) {
  await apiPost(`/lenders/${lenderId}/applications/${appId}/decide`);
  await refreshAll();
}

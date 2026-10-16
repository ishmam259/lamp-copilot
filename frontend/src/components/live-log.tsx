"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { cn } from "cn";
import { subscribeLogs, useLogs } from "@/lib/api";
import { shortDate, timeOfDay } from "@/lib/format";
import type { LogEvent } from "@/lib/types";

// Tiers say who acted, not whether it went well, so the chips stay neutral.
// Only failed or blocked events use the alert colour.
const TIERS: { tier: LogEvent["tier"]; label: string }[] = [
  { tier: "T0", label: "Read-only" },
  { tier: "T1", label: "Owner & AI" },
  { tier: "T2", label: "Engines" },
  { tier: "T3", label: "Money" },
];

const isProblem = (e: LogEvent) => /blocked|failed|declined|rejected|suspicious/.test(e.event);

const money = (v: unknown) => `BDT ${Number(v).toLocaleString("en-US")}`;
const words = (v: unknown) => String(v ?? "").replaceAll("_", " ");

/** Known events in the owner's words; anything else falls back to the event name. */
function sentence(e: LogEvent): string {
  const d = e.data;
  switch (e.event) {
    case "shortfall_detected":
      return `Short ${money(d.amount)} on ${shortDate(String(d.date))}`;
    case "batches_at_risk":
      return `${d.batches} batches worth ${money(d.value)} expire soon`;
    case "action_proposed":
      return `Suggested a ${words(d.kind)}`;
    case "action_approved_by_owner":
      return `Owner approved a ${words(d.kind)}`;
    case "action_rejected":
      return "Owner declined a suggestion";
    case "order_trimmed":
      return `Order cut from ${money(d.from)} to ${money(d.to)}`;
    case "return_claim_sent":
      return `Return claim sent for ${money(d.amount)}`;
    case "extension_requested":
      return `Asked ${d.supplier} for ${d.days} more days`;
    case "set_aside_scheduled":
      return `Set aside ${money(d.amount)}`;
    case "consent_granted":
      return `Passport shared with ${d.lender}`;
    case "consent_withdrawn":
      return `Stopped sharing with ${d.lender}`;
    case "application_blocked_no_consent":
      return `Blocked: ${d.lender} has no permission to see the passport`;
    case "lock_acquired":
      return `Invoice ${d.invoice} locked so it can't be financed twice`;
    case "application_submitted":
      return `Loan application for ${money(d.amount)} sent`;
    case "application_approved":
      return "Lender approved the application";
    case "application_declined":
      return "Lender declined the application";
    case "document_read":
      return `Read a ${words(d.kind)}`;
    case "suspicious_text_flagged":
      return "Ignored instructions written inside a document";
    case "capture_confirmed":
      return "Owner confirmed a captured document";
    case "reset":
      return "Pharmacy data loaded";
    default:
      return words(e.event);
  }
}

function raw(data: Record<string, unknown>) {
  return Object.entries(data)
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(" ");
}

export function LiveLog({ compact = false }: { compact?: boolean }) {
  const { data } = useLogs();
  const [live, setLive] = useState<LogEvent[]>([]);
  const [filter, setFilter] = useState<LogEvent["tier"] | "all">("all");
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(() => subscribeLogs((e) => setLive((prev) => (prev.some((p) => p.id === e.id) ? prev : [...prev, e]))), []);

  const events = useMemo(() => {
    const seen = new Set<string>();
    const all = [...(data ?? []), ...live].filter((e) => (seen.has(e.id) ? false : (seen.add(e.id), true)));
    return all.filter((e) => filter === "all" || e.tier === filter);
  }, [data, live, filter]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  return (
    <section aria-label="Audit log" className="flex h-full min-h-0 flex-col">
      <div className="band band-ink">
        <span>Audit log</span>
        <span className="text-xs font-semibold tracking-normal normal-case">Updates as things happen</span>
      </div>
      <div className="flex flex-wrap gap-1.5 border-b border-rule px-3 py-2">
        {(["all", "T0", "T1", "T2", "T3"] as const).map((t) => (
          <button
            key={t}
            type="button"
            aria-pressed={filter === t}
            onClick={() => setFilter(t)}
            className={cn(
              "h-8 rounded-[var(--radius)] px-2.5 text-xs font-bold",
              filter === t ? "bg-ink text-board" : "bg-muted text-ink-2 hover:text-ink"
            )}
          >
            {t === "all" ? "All" : t}
          </button>
        ))}
      </div>
      <ol ref={listRef} className="min-h-0 flex-1 overflow-y-auto text-sm" aria-live="polite">
        {events.length === 0 && <li className="p-4 text-ink-2">No events yet. Actions you take appear here.</li>}
        {events.map((e) => (
          <li key={e.id} className="border-b border-rule px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="num font-board text-ink-2">{timeOfDay(e.ts)}</span>
              <span className="rounded-[2px] bg-muted px-1.5 text-xs font-bold text-ink">{e.tier}</span>
              <span className="text-xs font-bold text-ink-2">{e.component}</span>
            </div>
            <p className={cn("mt-0.5 font-semibold break-words", isProblem(e) ? "text-alert" : "text-ink")}>{sentence(e)}</p>
            {Object.keys(e.data).length > 0 && (
              <details className="text-xs text-ink-2">
                <summary className="cursor-pointer">Details</summary>
                <p className="font-board break-all">{raw(e.data)}</p>
              </details>
            )}
          </li>
        ))}
      </ol>
      {!compact && (
        <ul className="flex flex-wrap gap-3 border-t border-rule px-3 py-2 text-xs text-ink-2">
          {TIERS.map((t) => (
            <li key={t.tier} className="inline-flex items-center gap-1.5">
              <span className="rounded-[2px] bg-muted px-1.5 font-bold text-ink">{t.tier}</span>
              {t.label}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

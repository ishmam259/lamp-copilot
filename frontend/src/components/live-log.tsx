"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { cn } from "cn";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { subscribeLogs, useLogVerify } from "@/lib/api";
import { shortDate, timeOfDay } from "@/lib/format";
import type { LogEvent } from "@/lib/types";

// Tiers say who acted, not whether it went well, so the chips stay neutral.
// Only failed or blocked events use the alert colour.
const TIERS: { tier: LogEvent["tier"]; label: string }[] = [
  { tier: "T0", label: "Viewed" },
  { tier: "T1", label: "You & AI" },
  { tier: "T2", label: "Calculations" },
  { tier: "T3", label: "Money" },
];

/** The part of LaMP that wrote the event, in the owner's words. */
const PART: Record<string, string> = {
  DEV: "Demo",
  AUTH: "Sign-in",
  EXECUTOR: "Actions",
  REGISTRY: "Financing registry",
  FOLLOWUP: "Follow-up",
  NOTIFY: "Alert",
  CONSENT: "Sharing",
  EXPIRY: "Stock",
};
const part = (c: string) => PART[c] ?? c.charAt(0) + c.slice(1).toLowerCase();

const tierWord = (t: LogEvent["tier"]) => TIERS.find((x) => x.tier === t)?.label ?? t;

const isProblem = (e: LogEvent) => /blocked|failed|declined|rejected|refused|suspicious/.test(e.event);

const money = (v: unknown) => `BDT ${Number(v).toLocaleString("en-US")}`;
const words = (v: unknown) => String(v ?? "").replaceAll("_", " ");
const capital = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);

/** Action kinds with their article, as the owner would say them. */
const KIND: Record<string, string> = {
  return_claim: "a return claim",
  trim_order: "an order trim",
  extension_request: "a request for more days",
  loan_application: "a loan application",
  set_aside: "a set-aside",
};
const kind = (v: unknown) => KIND[String(v)] ?? `a ${words(v)}`;

/** Known events in the owner's words; anything else falls back to the event name. */
function sentence(e: LogEvent): string {
  const d = e.data;
  switch (e.event) {
    case "shortfall_detected":
      return `Short ${money(d.amount)} on ${shortDate(String(d.date))}`;
    case "batches_at_risk":
      return `${d.batches} batches worth ${money(d.value)} expire soon`;
    case "action_proposed":
      return `Suggested ${kind(d.kind)}`;
    case "action_approved_by_owner":
      return `Owner approved ${kind(d.kind)}`;
    case "action_executed":
      return `Carried out ${kind(d.kind)}`;
    case "action_failed":
      return `Couldn't carry out ${kind(d.kind)}: ${words(d.reason)}`;
    case "lock_rejected":
      return `Refused: invoice ${d.invoice} is already financed`;
    case "extension_declined":
      return `${d.supplier} said no to more days`;
    case "extension_accepted":
      return `${d.supplier} agreed to more days`;
    case "capture_created":
      return "Photo read; waiting for the owner to check it";
    case "forecast_updated":
      return "Cash forecast updated";
    case "inbox_viewed":
      return "A lender opened its inbox";
    case "chat_message":
      return "Owner asked LaMP a question";
    case "owner_locked":
      return "Owner locked the app";
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
    case "notify":
      return `Notified the ${d.audience}: ${d.title}`;
    case "owner_unlocked":
      return "Owner unlocked with the PIN";
    case "approval_pin_rejected":
      return "Wrong PIN at a loan approval";
    case "agent_paused":
      return "Owner paused LaMP";
    case "agent_resumed":
      return "Owner resumed LaMP";
    case "unlock_failed":
      return "Wrong PIN entered";
    case "consent_revoked":
      return `Stopped sharing with ${d.lender}`;
    case "followup_scheduled":
      return "Follow-up scheduled for the plan";
    case "followup_fired":
      return "Follow-up fired: the backup step is ready";
    case "followup_cancelled":
      return "Follow-up no longer needed";
    case "followup_held_paused":
      return "Follow-up held: LaMP is paused";
    case "proposal_refused_paused":
    case "approval_refused_paused":
      return "Refused: LaMP is paused";
    case "loan_refused_dbr":
      return "Refused: the loan breaks the borrowing ceiling";
    case "answer_blocked_untraced":
      return "Blocked a chat answer with an untraced money figure";
    case "sandbox_payout":
    case "wallet_credited":
      return `Wallet credited ${money(d.amount)}`;
    default:
      return capital(words(e.event));
  }
}

function raw(data: Record<string, unknown>) {
  return Object.entries(data)
    .map(([k, v]) => `${k}=${typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(" ");
}

export function LiveLog() {
  const { data: chain, mutate: recheck } = useLogVerify();
  const [live, setLive] = useState<LogEvent[]>([]);
  const [filter, setFilter] = useState<LogEvent["tier"] | "all">("all");
  const listRef = useRef<HTMLOListElement>(null);

  useEffect(
    () =>
      subscribeLogs(
        (e) => setLive((prev) => (prev.some((p) => p.id === e.id) ? prev : [...prev, e])),
        // Every (re)connect replays the whole log, and after a reset the ids restart: start again.
        () => setLive([])
      ),
    []
  );
  // Re-verify the hash chain whenever a new event arrives.
  useEffect(() => {
    if (live.length) recheck();
  }, [live.length, recheck]);

  const events = useMemo(() => {
    const seen = new Set<string>();
    const all = live.filter((e) => (seen.has(e.id) ? false : (seen.add(e.id), true)));
    return all.filter((e) => filter === "all" || e.tier === filter);
  }, [live, filter]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  return (
    <section aria-label="Audit log" className="flex h-full min-h-0 flex-col">
      <div className="band band-ink">
        <span>Audit log</span>
      </div>
      {chain && (
        <p
          role="status"
          title={chain.intact ? `Head hash ${chain.head_hash}` : `Chain broken at ${chain.first_bad_id}`}
          className={cn(
            "flex items-center gap-1.5 border-b border-rule px-3 py-1.5 text-xs font-semibold",
            chain.intact ? "text-stock" : "bg-alert-tint text-alert"
          )}
        >
          {chain.intact ? <ShieldCheck className="size-4 shrink-0" aria-hidden /> : <ShieldAlert className="size-4 shrink-0" aria-hidden />}
          {chain.intact ? (
            <span>
              Verified · <span className="num">{chain.count}</span> events, none changed
            </span>
          ) : (
            <span>The log was changed after it was written</span>
          )}
        </p>
      )}
      <div className="flex flex-wrap gap-1.5 border-b border-rule px-3 py-2">
        {(["all", ...TIERS.map((x) => x.tier)] as const).map((t) => (
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
            {t === "all" ? "All" : tierWord(t)}
          </button>
        ))}
      </div>
      <ol ref={listRef} className="min-h-0 flex-1 overflow-y-auto text-sm" aria-live="polite">
        {events.length === 0 && <li className="p-4 text-ink-2">No events yet. Actions you take appear here.</li>}
        {events.map((e) => (
          <li key={e.id} className="border-b border-rule px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="num font-board text-ink-2">{timeOfDay(e.ts)}</span>
              <span className="rounded-[2px] bg-muted px-1.5 text-xs font-bold text-ink" title={e.tier}>{tierWord(e.tier)}</span>
              <span className="text-xs font-bold text-ink-2">{part(e.component)}</span>
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
    </section>
  );
}

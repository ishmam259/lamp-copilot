"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { cn } from "cn";
import { subscribeLogs, useLogs } from "@/lib/api";
import { timeOfDay } from "@/lib/format";
import type { LogEvent } from "@/lib/types";

const TIERS: { tier: LogEvent["tier"]; label: string; cls: string }[] = [
  { tier: "T0", label: "T0 Read-only", cls: "bg-muted text-ink" },
  { tier: "T1", label: "T1 Owner & AI", cls: "bg-cash-tint text-cash" },
  { tier: "T2", label: "T2 Engines", cls: "bg-stock-tint text-stock" },
  { tier: "T3", label: "T3 Money", cls: "bg-alert-tint text-alert" },
];

const tierCls = (t: LogEvent["tier"]) => TIERS.find((x) => x.tier === t)?.cls ?? "";

function describe(data: Record<string, unknown>) {
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
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold tracking-normal normal-case">
          <span className="size-2 animate-pulse rounded-full bg-[#4ade80]" aria-hidden /> Live
        </span>
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
              filter === t ? "bg-ink text-white" : "bg-muted text-ink-2 hover:text-ink"
            )}
          >
            {t === "all" ? "All" : t}
          </button>
        ))}
      </div>
      <ol ref={listRef} className={cn("min-h-0 flex-1 overflow-y-auto", compact ? "text-xs" : "text-sm")} aria-live="polite">
        {events.length === 0 && <li className="p-4 text-ink-2">No events yet. Actions you take appear here.</li>}
        {events.map((e) => (
          <li key={e.id} className="border-b border-rule px-3 py-2">
            <div className="flex items-center gap-2">
              <span className="num font-stamp text-ink-2">{timeOfDay(e.ts)}</span>
              <span className={cn("rounded-[2px] px-1.5 font-bold", tierCls(e.tier))}>{e.tier}</span>
              <span className="font-bold text-ink">{e.component}</span>
            </div>
            <p className="mt-0.5 font-semibold break-words text-ink">{e.event.replaceAll("_", " ")}</p>
            {Object.keys(e.data).length > 0 && <p className="font-stamp break-all text-ink-2">{describe(e.data)}</p>}
          </li>
        ))}
      </ol>
      {!compact && (
        <ul className="flex flex-wrap gap-3 border-t border-rule px-3 py-2 text-xs text-ink-2">
          {TIERS.map((t) => (
            <li key={t.tier} className="inline-flex items-center gap-1.5">
              <span className={cn("rounded-[2px] px-1.5 font-bold", t.cls)}>{t.tier}</span>
              {t.label.slice(3)}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

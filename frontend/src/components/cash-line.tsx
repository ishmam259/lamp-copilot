"use client";

import { shortDate } from "@/lib/format";
import type { ForecastOut } from "@/lib/types";

/**
 * The next 30 days as a railway line on a true day scale.
 * Each large money move is a stop; the first day you'd be short is a red stop.
 */
export function CashLine({ forecast }: { forecast: ForecastOut }) {
  const days = forecast.days;
  const n = days.length;
  const W = 320;
  const pad = 10;
  const x = (i: number) => pad + (i / (n - 1)) * (W - pad * 2);
  const shortDate0 = forecast.shortfalls[0]?.date;
  const shortIdx = shortDate0 ? days.findIndex((d) => d.date === shortDate0) : -1;
  // Stops less than 2 days apart would overlap, so they merge into one stop.
  // Today, the last day and the short day always keep their own stop.
  const stops: { d: (typeof days)[number]; i: number; also: string[] }[] = [];
  days.forEach((d, i) => {
    const big = i === 0 || i === n - 1 || i === shortIdx || (d.items ? d.items.length > 0 : d.outflow >= 5000 || d.inflow >= 4000);
    if (!big) return;
    const prev = stops[stops.length - 1];
    const pinned = i === 0 || i === n - 1 || i === shortIdx;
    const prevPinned = prev && (prev.i === 0 || prev.i === n - 1 || prev.i === shortIdx);
    if (prev && i - prev.i < 2 && !(pinned && prevPinned)) {
      if (pinned) stops[stops.length - 1] = { d, i, also: [...prev.also, describeDay(prev.d)] };
      else prev.also.push(describeDay(d));
      return;
    }
    stops.push({ d, i, also: [] });
  });

  const label = shortDate0
    ? `Cash for the next 30 days. You run short on ${shortDate(shortDate0)}.`
    : "Enough cash for the next 30 days.";

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${W} 68`} className="block h-auto w-full" role="img" aria-label={label}>
        {/* track: green while cash holds, red from the first short day */}
        <line x1={x(0)} x2={shortIdx >= 0 ? x(shortIdx) : x(n - 1)} y1="30" y2="30" stroke="var(--cash)" strokeWidth="5" strokeLinecap="round" />
        {shortIdx >= 0 && <line x1={x(shortIdx)} x2={x(n - 1)} y1="30" y2="30" stroke="var(--alert)" strokeWidth="5" strokeDasharray="7 5" />}
        {stops.map(({ d, i, also }) => {
          const isShort = i === shortIdx;
          return (
            <g key={d.date}>
              <circle
                cx={x(i)}
                cy="30"
                r={isShort ? 9 : i === 0 ? 7 : 5.5}
                fill={isShort ? "var(--alert)" : "var(--board)"}
                stroke={isShort ? "var(--ink)" : i >= shortIdx && shortIdx >= 0 ? "var(--alert)" : "var(--cash)"}
                strokeWidth={isShort ? 2.5 : 3}
              >
                <title>{[describeDay(d), ...also].join("; ")}</title>
              </circle>
            </g>
          );
        })}
        <text x={x(0)} y="64" fontSize="13" fontWeight="600" fill="var(--ink-2)" fontFamily="var(--font-barlow)">
          Today
        </text>
        {shortIdx >= 0 && (
          <text x={x(shortIdx)} y="13" textAnchor="middle" fontSize="13" fontWeight="700" fill="var(--alert)" fontFamily="var(--font-barlow)">
            {shortDate(days[shortIdx].date)}
          </text>
        )}
        <text x={x(n - 1)} y="64" textAnchor="end" fontSize="13" fontWeight="600" fill="var(--ink-2)" fontFamily="var(--font-barlow)">
          {shortDate(days[n - 1].date)}
        </text>
      </svg>
    </figure>
  );
}

function describeDay(d: ForecastOut["days"][number]) {
  const what = d.items && d.items.length > 0
    ? d.items.map((x) => `${x.label} ${x.amount < 0 ? "−" : "+"}BDT ${Math.abs(x.amount).toLocaleString("en-US")}`).join(", ")
    : d.outflow > 0
      ? `pay BDT ${d.outflow.toLocaleString("en-US")}`
      : `receive BDT ${d.inflow.toLocaleString("en-US")}`;
  return `${shortDate(d.date)}: ${what}`;
}

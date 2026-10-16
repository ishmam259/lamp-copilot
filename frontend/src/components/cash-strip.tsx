"use client";

import { shortDate } from "@/lib/format";
import type { ForecastOut } from "@/lib/types";

/**
 * 30 days of closing balance, one bar per day on a true day scale.
 * Bars above the line are cash on hand; red bars below it are days you'd be short.
 */
export function CashStrip({ forecast, height = 72 }: { forecast: ForecastOut; height?: number }) {
  const days = forecast.days;
  const max = Math.max(...days.map((d) => Math.abs(d.balance)), 1);
  const w = 300;
  const gap = 2;
  const bw = (w - gap * (days.length - 1)) / days.length;
  const mid = height * 0.62;
  const upScale = (mid - 4) / max;
  const downScale = (height - mid - 4) / max;
  const firstShort = forecast.shortfalls[0]?.date;
  const label = firstShort
    ? `Cash for the next 30 days. You go below zero on ${shortDate(firstShort)}.`
    : "Cash for the next 30 days. It stays above zero every day.";

  return (
    <figure className="m-0">
      <svg viewBox={`0 0 ${w} ${height}`} className="block h-auto w-full" role="img" aria-label={label}>
        <line x1="0" x2={w} y1={mid} y2={mid} stroke="var(--rule)" strokeWidth="1" />
        {days.map((d, i) => {
          const x = i * (bw + gap);
          const neg = d.balance < 0;
          const h = Math.max(1.5, Math.abs(d.balance) * (neg ? downScale : upScale));
          return (
            <rect
              key={d.date}
              x={x}
              y={neg ? mid : mid - h}
              width={bw}
              height={h}
              rx="1"
              fill={neg ? "var(--alert)" : d.date === days[0].date ? "var(--ink)" : "var(--ink-2)"}
              opacity={neg ? 0.9 : d.date === days[0].date ? 1 : 0.45}
            >
              <title>{`${shortDate(d.date)}: BDT ${d.balance.toLocaleString("en-US")}`}</title>
            </rect>
          );
        })}
      </svg>
      <figcaption className="mt-1 flex justify-between text-xs font-semibold text-ink-2">
        <span>Today</span>
        {firstShort && <span className="text-alert">Short from {shortDate(firstShort)}</span>}
        <span>{shortDate(days[days.length - 1].date)}</span>
      </figcaption>
    </figure>
  );
}

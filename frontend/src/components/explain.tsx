"use client";

import { useState } from "react";
import { Calculator } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { bdt } from "@/lib/format";
import type { ExplainRow } from "@/lib/types";

const SIGN: Record<ExplainRow["op"], string> = {
  start: "",
  "+": "+",
  "-": "−",
  "=": "=",
};

/**
 * "Explain this number" (SHOULD-7): a small button beside a figure that opens a drawer with
 * the engine's own rows (start, + / − rows, = the figure). The rows come from the API as they
 * are; nothing is computed here.
 */
export function Explain({ rows, title, onBoard = false }: { rows?: ExplainRow[]; title: string; onBoard?: boolean }) {
  const [open, setOpen] = useState(false);
  if (!rows || rows.length < 2) return null;
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`inline-flex items-center gap-1 rounded-[var(--radius)] px-1.5 py-0.5 text-sm font-semibold hover:underline ${
          onBoard ? "sb-sub" : "text-cash"
        }`}
      >
        <Calculator className="size-4" aria-hidden /> How?
      </button>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent side="right" className="data-[side=right]:w-full data-[side=right]:sm:max-w-md">
          <SheetHeader className="border-b border-rule">
            <SheetTitle className="text-lg">{title}</SheetTitle>
            <SheetDescription>Worked out by LaMP&apos;s engines from your books. The chat never does this math.</SheetDescription>
          </SheetHeader>
          <ol className="num px-4">
            {rows.map((r, i) => (
              <li
                key={i}
                className={`grid grid-cols-[1.25rem_1fr_auto] items-baseline gap-2 py-2.5 ${
                  r.op === "=" ? "mt-1 border-t-2 border-ink font-bold text-ink" : "border-b border-rule text-ink"
                }`}
              >
                <span aria-hidden className="text-ink-2">
                  {SIGN[r.op]}
                </span>
                <span>
                  <span className="sr-only">{r.op === "-" ? "minus " : r.op === "+" ? "plus " : r.op === "=" ? "equals " : ""}</span>
                  {r.label}
                </span>
                <span className="text-right whitespace-nowrap">{bdt(r.amount)}</span>
              </li>
            ))}
          </ol>
        </SheetContent>
      </Sheet>
    </>
  );
}

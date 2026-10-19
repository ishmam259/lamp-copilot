"use client";

import { Check, ExternalLink, KeyRound, X } from "lucide-react";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { PauseToggle } from "@/components/pause";
import { ResetDemoButton } from "@/components/reset-demo";
import { usePolicy } from "@/lib/api";
import { bdt, num } from "@/lib/format";
import type { ActionKind } from "@/lib/types";

const KIND: Record<ActionKind, string> = {
  return_claim: "Return claims",
  extension_request: "Asking a supplier for more days",
  loan_application: "Loan applications",
  set_aside: "Daily set-asides",
  trim_order: "Trimming an order",
};

/** Read-only view of the rules LaMP enforces (CORE-07): Pause, the PIN, the borrowing ceiling. */
export default function RulesPage() {
  const { data: p, error } = usePolicy();
  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title="Rules" sub="What LaMP will and won't do. Pause is yours to switch; the other rules are enforced by the server and shown here as they are." />
      {error && <LoadError what="the rules" />}
      {!p && !error && <Skel className="h-96" />}
      {p && (
        <div className="space-y-4">
          <Carton tone={p.paused ? "warn" : "ink"} title="Pause" aside={p.paused ? "Paused" : "Running"}>
            <p className="text-ink">
              {p.paused
                ? "LaMP is paused. It can't suggest or follow up on anything, and its earlier suggestions can't be approved."
                : "LaMP can suggest actions and follow up on your plan. Nothing happens until you approve it."}
            </p>
            <div className="mt-3">
              <PauseToggle />
            </div>
          </Carton>

          <Carton tone="ink" title="Sandbox demo">
            <p className="text-ink">
              Everything here is a sandbox: no real money moves and no one is contacted. Reset puts the story back to the start for the next person.
            </p>
            <ResetDemoButton className="mt-3 inline-flex h-10 items-center gap-2 rounded-[var(--radius)] border border-rule px-3 font-semibold text-ink hover:bg-muted disabled:opacity-60" />
          </Carton>

          <Carton tone="ink" title="Your approval">
            <ul className="space-y-2 text-ink">
              {(Object.keys(KIND) as ActionKind[]).map((k) => {
                const pin = p.pin_required_for.includes(k);
                return (
                  <li key={k} className="flex items-center gap-2">
                    {pin ? <KeyRound className="size-4 shrink-0 text-warn" aria-hidden /> : <Check className="size-4 shrink-0 text-stock" aria-hidden />}
                    <span className="flex-1">{KIND[k]}</span>
                    <span className="text-sm text-ink-2">{pin ? "Your approval and your PIN again" : "Your approval"}</span>
                  </li>
                );
              })}
            </ul>
            <p className="mt-3 text-sm text-ink-2">The copilot can only read and suggest. It can never approve, pay or contact anyone.</p>
          </Carton>

          <Carton tone="ink" title="Borrowing ceiling" aside={`${num(p.dbr_cap_pct)}% of monthly net cash flow`}>
            <p className="text-ink">
              LaMP won&apos;t apply for a loan whose monthly repayment is more than {num(p.dbr_cap_pct)}% of your monthly net cash flow, which is{" "}
              <span className="num">{bdt(p.monthly_net_cash_flow)}</span>.
            </p>
            <ul className="mt-3 divide-y divide-rule border-t border-rule">
              {p.examples.map((e) => (
                <li key={e.label} className="flex items-start gap-3 py-3">
                  <span
                    className={`mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full ${e.ok ? "bg-stock-tint text-stock" : "bg-alert-tint text-alert"}`}
                    aria-label={e.ok ? "Allowed" : "Refused"}
                  >
                    {e.ok ? <Check className="size-4" aria-hidden /> : <X className="size-4" aria-hidden />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-ink">{e.label}</p>
                    <p className="num text-sm text-ink-2">
                      {bdt(e.amount)} over {e.months} months = {bdt(e.monthly_repayment)} a month = {num(e.dbr_pct, 1)}% of {bdt(e.monthly_net_cash_flow)}
                    </p>
                  </div>
                  <Stamp tone={e.ok ? "stock" : "alert"}>{e.ok ? "Allowed" : "Refused"}</Stamp>
                </li>
              ))}
            </ul>
            <details className="mt-2 text-sm text-ink-2">
              <summary className="cursor-pointer font-semibold text-cash">Where the {num(p.dbr_cap_pct)}% comes from</summary>
              <p className="mt-2">
                {p.source.issuer}, {p.source.title} ({p.source.edition}), page {p.source.page}: {p.source.clause}.
              </p>
              <p className="mt-1">{p.source.principle}.</p>
              <a href={p.source.url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 font-semibold text-cash hover:underline">
                Read the regulation <ExternalLink className="size-3.5" aria-hidden />
              </a>
            </details>
          </Carton>
        </div>
      )}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowRight, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { proposeAction, useActions, useFundingPlan } from "@/lib/api";
import { bdt, dayDate, num, stampDate } from "@/lib/format";
import type { ActionKind } from "@/lib/types";

export default function FundingPage() {
  const { data: plan, error } = useFundingPlan();
  const { data: actions } = useActions();
  const [busy, setBusy] = useState(false);

  const planKinds = new Set(plan?.plan.steps.map((s) => s.action_kind));
  const alreadyProposed = actions?.some((a) => planKinds.has(a.kind) && a.kind !== "return_claim" && a.status !== "rejected");

  async function proposePlan() {
    if (!plan) return;
    setBusy(true);
    try {
      for (const s of plan.plan.steps) {
        await proposeAction(s.action_kind as ActionKind, {
          summary: s.label,
          amount: s.amount,
          when: s.when,
          ...(s.action_kind === "loan_application" ? { lender_id: "wallet-lender", product_key: "wallet_loan", fallback: true } : {}),
        });
      }
      toast.success("Plan added to Actions. Approve each step there.");
    } catch {
      toast.error("Couldn't add the plan. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageTitle title="Funding" sub="Use money you already have first. Borrow only what's left, at the lowest cost." />
      {error && <LoadError what="your funding plan" />}
      {!plan && !error && <Skel className="h-96" />}
      {plan && (
        <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
          <section aria-labelledby="need-head" className="station-board lg:col-span-12">
            <h2 id="need-head" className="sb-head">
              <span className="num">{bdt(plan.need.amount)} to cover</span>
              <span className="sb-time">by {dayDate(plan.need.needed_by)}</span>
            </h2>
            <p className="sb-sub mt-1.5 text-[1.0625rem] font-medium">Left after trimming the slow mover from Supplier A&apos;s order.</p>
          </section>
          <div className="lg:col-span-12">
            <Carton tone="ink" title="Recommended plan" aside={`Costs ${bdt(plan.plan.total_cost_bdt)} if Supplier A agrees`}>
              <ol className="space-y-3 lg:grid lg:grid-cols-3 lg:gap-4 lg:space-y-0">
                {plan.plan.steps.map((s, i) => (
                  <li key={s.label} className="flex gap-3">
                    <span className="num flex size-8 shrink-0 items-center justify-center rounded-full bg-muted font-bold text-ink">{i + 1}</span>
                    <div className="min-w-0">
                      <p className="font-semibold text-ink">{s.label}</p>
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        <Stamp>{s.fallback_for ? `If needed ${stampDate(s.when)}` : `Now ${stampDate(s.when)}`}</Stamp>
                        <span className="num text-sm text-ink-2">{bdt(s.amount)}</span>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="mt-4 rounded-[var(--radius)] bg-stock-tint p-3 text-ink">
                Borrowing the full BDT 19,000 straight away would cost <span className="num font-bold">{bdt(plan.naive_cost_bdt)}</span> in interest, and you&apos;d
                still hold stock that expires. This plan costs <span className="num font-bold">BDT 0–182</span>.
              </div>
              <Button size="lg" className="mt-4 w-full sm:w-auto" disabled={busy || !!alreadyProposed} onClick={proposePlan}>
                {alreadyProposed ? "Plan is in Actions" : "Add this plan to Actions"}
              </Button>
              {alreadyProposed && (
                <Link href="/actions" className="mt-2 inline-flex items-center gap-1 font-semibold text-cash hover:underline sm:ml-3">
                  Go to Actions <ArrowRight className="size-4" aria-hidden />
                </Link>
              )}
              <p className="mt-2 text-sm text-ink-2">Nothing happens until you approve each step.</p>
            </Carton>
          </div>

          <div className="lg:col-span-12">
            <Carton tone="ink" title="All options" aside="Cheapest first" bodyClassName="p-0">
              <ul className="divide-y divide-rule lg:grid lg:grid-cols-2 lg:divide-y-0">
                {plan.options.map((o) => (
                  <li key={o.key} className={`p-4 lg:border-b lg:border-rule ${o.eligible ? "" : "opacity-75"}`}>
                    <div className="flex items-start gap-3">
                      <span
                        className={`mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full ${o.eligible ? "bg-stock-tint text-stock" : "bg-muted text-ink-2"}`}
                        aria-label={o.eligible ? "Available" : "Not available"}
                      >
                        {o.eligible ? <Check className="size-4" aria-hidden /> : <X className="size-4" aria-hidden />}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-ink">{o.label}</p>
                        <p className="text-sm text-ink-2">
                          {o.provider} · {o.speed}
                          {o.certainty === "uncertain" ? " · not guaranteed" : ""}
                        </p>
                        <p className="mt-1 text-sm text-ink">{o.reason}</p>
                      </div>
                      <div className="text-right">
                        <p className="num font-bold text-ink">{o.cost_bdt === null ? "—" : o.cost_bdt === 0 ? "Free" : bdt(o.cost_bdt)}</p>
                        {o.apr_pct !== null && <p className="num text-xs text-ink-2">{num(o.apr_pct, 1)}% a year</p>}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </Carton>
            <p className="mt-3 text-sm text-ink-2">
              Lenders see your record only if you share it.{" "}
              <Link href="/passport" className="font-semibold text-cash hover:underline">
                Your credit passport
              </Link>
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

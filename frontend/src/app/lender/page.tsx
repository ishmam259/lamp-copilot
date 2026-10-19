"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Carton, PageTitle, Skel, Stamp } from "@/components/carton";
import { lenderDecide, useApplications, useLenders, useShelfLifeCredit } from "@/lib/api";
import { bdt, num, shortDate } from "@/lib/format";
import type { ShelfLifeCreditOut } from "@/lib/types";

export default function LenderPage() {
  const { data: lenders } = useLenders();
  const [lenderId, setLenderId] = useState("wallet-lender");
  const { data: apps } = useApplications(lenderId);
  const [busy, setBusy] = useState<string | null>(null);

  async function decide(appId: string) {
    setBusy(appId);
    try {
      await lenderDecide(lenderId, appId);
      toast.success("Decision recorded.");
    } catch {
      toast.error("Couldn't record the decision.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageTitle title="Lender view" sub="The lender's inbox. Only pharmacies that shared their passport with this lender appear here." />
      <div role="tablist" aria-label="Lender" className="mb-4 inline-flex rounded-[var(--radius)] border border-rule bg-board p-1">
        {lenders?.map((l) => (
          <button
            key={l.id}
            role="tab"
            aria-selected={lenderId === l.id}
            onClick={() => setLenderId(l.id)}
            className={`h-10 rounded-[3px] px-4 font-semibold ${lenderId === l.id ? "bg-primary text-primary-foreground" : "text-ink-2 hover:text-ink"}`}
          >
            {l.name}
          </button>
        ))}
      </div>

      {!apps ? (
        <Skel className="h-48" />
      ) : apps.length === 0 ? (
        <Carton tone="ink" title="No applications">
          <p className="text-ink">
            Nothing yet. A pharmacy appears here after it switches on sharing in its Passport and approves a loan application in Actions.
          </p>
        </Carton>
      ) : (
        <div className="space-y-4">
          <ShelfLifeCard />
          {apps.map((a) => (
            <Carton
              key={a.id}
              tone={a.status === "approved" ? "stock" : a.status === "declined" ? "alert" : "warn"}
              title={`${a.pharmacy_name} · ${a.id}`}
              aside={a.status === "pending" ? "Waiting for decision" : a.status === "approved" ? "Approved" : "Declined"}
            >
              <div className="grid gap-4 lg:grid-cols-2">
                <dl className="num grid grid-cols-2 gap-3">
                  <div>
                    <dt className="text-sm text-ink-2">Amount</dt>
                    <dd className="text-xl font-bold text-ink">{bdt(a.amount)}</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-2">On-time record</dt>
                    <dd className="text-xl font-bold text-ink">
                      {a.passport.paid_on_time} / {a.passport.invoices_total}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-2">Default risk</dt>
                    <dd className="text-xl font-bold text-ink">{num(a.passport.default_probability * 100, 1)}%</dd>
                  </div>
                  <div>
                    <dt className="text-sm text-ink-2">Advance rate</dt>
                    <dd className="text-xl font-bold text-ink">{num(a.passport.advance_rate_pct, 1)}%</dd>
                  </div>
                </dl>
                <div>
                  <h3 className="text-sm font-semibold text-ink-2">Evidence (latest invoices)</h3>
                  <table className="num mt-1 w-full text-sm">
                    <thead className="text-left text-ink-2">
                      <tr>
                        <th className="py-1 font-semibold">Invoice</th>
                        <th className="py-1 font-semibold">Supplier</th>
                        <th className="py-1 text-right font-semibold">Paid</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-rule">
                      {a.passport.evidence.slice(-5).map((e) => (
                        <tr key={e.invoice_no}>
                          <td className="py-1.5 text-ink">{e.invoice_no}</td>
                          <td className="py-1.5 text-ink">{e.supplier}</td>
                          <td className={`py-1.5 text-right font-semibold ${e.on_time ? "text-stock" : "text-alert"}`}>{e.on_time ? "On time" : "Late"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              {a.status === "pending" ? (
                <Button className="mt-4" disabled={busy === a.id} onClick={() => decide(a.id)}>
                  Run decision rule
                </Button>
              ) : (
                <div className="mt-4 space-y-1">
                  <p className="text-ink">{a.decision?.reason}</p>
                  {a.decision?.payout_ref && <Stamp tone="stock">Payout {a.decision.payout_ref}</Stamp>}
                </div>
              )}
            </Carton>
          ))}
        </div>
      )}
    </div>
  );
}

/** Shelf-life credit (CORE-11): one number decides both what to lend and what to order. */
function ShelfLifeCard() {
  const { data: s, error } = useShelfLifeCredit();
  if (error || !s || !s.order_id) return null;
  return (
    <Carton tone="ink" title="Shelf-life credit" aside={`Order ${s.order_id} · needed by ${shortDate(s.needed_by)}`}>
      <ShelfLifeBody s={s} />
    </Carton>
  );
}

function ShelfLifeBody({ s }: { s: ShelfLifeCreditOut }) {
  const fewer = s.batches.reduce((n, b) => n + (b.qty_ordered - b.sellable_qty), 0);
  const cut = s.batches.filter((b) => b.unsellable_value > 0);
  return (
    <>
      <dl className="num grid grid-cols-3 divide-x divide-rule">
        <div className="pr-3">
          <dt className="text-sm text-ink-2">Purpose-blind lender</dt>
          <dd className={`text-xl font-bold text-ink-2 ${s.not_financed > 0 ? "line-through decoration-1" : ""}`}>{bdt(s.counterfactual_purpose_blind)}</dd>
        </div>
        <div className="px-3">
          <dt className="text-sm text-ink-2">Won&apos;t sell before expiry</dt>
          <dd className={`text-xl font-bold ${s.not_financed > 0 ? "text-alert" : "text-ink"}`}>{bdt(s.not_financed)}</dd>
        </div>
        <div className="pl-3">
          <dt className="text-sm text-ink-2">LaMP finances at most</dt>
          <dd className="text-xl font-bold text-stock">{bdt(s.financeable)}</dd>
        </div>
      </dl>
      <p className="mt-3 text-ink">
        {s.not_financed > 0 ? (
          <>
            A lender that ignores the shelf would lend {bdt(s.counterfactual_purpose_blind)} (a computed comparison). {bdt(s.not_financed)} of this order
            won&apos;t sell before it expires, so LaMP finances at most {bdt(s.financeable)}
            {fewer > 0 && <>, and the owner orders {fewer} fewer boxes</>}. One number, two decisions.
          </>
        ) : (
          <>{s.reason} LaMP finances only stock that sells before it expires.</>
        )}
      </p>
      {cut.length > 0 && (
        <ul className="mt-2 space-y-1 text-sm text-ink-2">
          {cut.map((b) => (
            <li key={b.product}>
              {b.product}: {b.sellable_qty} of {b.qty_ordered} boxes sell in time; {bdt(b.unsellable_value)} not financed.
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

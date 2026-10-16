"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Carton, PageTitle, Skel, Stamp } from "@/components/carton";
import { lenderDecide, useApplications, useLenders } from "@/lib/api";
import { bdt, num } from "@/lib/format";

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
      <PageTitle title="Lender view" sub="A simulated lender's inbox. Only pharmacies that shared their passport with this lender appear here." />
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

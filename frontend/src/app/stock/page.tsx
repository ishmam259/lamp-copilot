"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { proposeAction, useActions, useExpiry, useOrders, useTrim } from "@/lib/api";
import { bdt, num, stampDate } from "@/lib/format";

export default function StockPage() {
  const { data: expiry, error } = useExpiry();
  const { data: orders } = useOrders();
  const order = orders?.[0];
  const { data: trim } = useTrim(order?.id);
  const { data: actions } = useActions();
  const [busy, setBusy] = useState<string | null>(null);

  const claimPending = actions?.some((a) => a.kind === "return_claim" && (a.status === "proposed" || a.status === "executed"));
  const trimDone = actions?.some((a) => a.kind === "trim_order" && a.status === "executed");
  const trimPending = actions?.some((a) => a.kind === "trim_order" && a.status === "proposed");

  async function propose(kind: "return_claim" | "trim_order", payload: Record<string, unknown> & { summary: string; amount: number }) {
    setBusy(kind);
    try {
      await proposeAction(kind, payload);
      toast.success("Added to Actions. Approve it there when you're ready.");
    } catch {
      toast.error("Couldn't add it. Try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageTitle title="Stock" />
      <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
        <div className="lg:col-span-7">
          <Carton tone="warn" title="Expiring in 60 days" aside={expiry ? `${expiry.batches.length} batches` : undefined}>
            {error && <LoadError what="expiring stock" />}
            {!expiry && !error && <Skel className="h-64" />}
            {expiry && (
              <>
                <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1">
                  <p>
                    <span className="num text-[1.75rem] font-bold text-ink">{bdt(expiry.at_risk_value)}</span>
                    <span className="ml-2 text-ink-2">at risk</span>
                  </p>
                  <p>
                    <span className="num text-[1.5rem] font-bold text-stock">{bdt(expiry.return_eligible_value)}</span>
                    <span className="ml-2 text-ink-2">can go back</span>
                  </p>
                </div>
                <ul className="mt-4 divide-y divide-rule">
                  {expiry.batches.map((b) => (
                    <li key={b.batch_no} className="flex items-start gap-3 py-3">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-ink">{b.product}</p>
                        <p className="text-sm text-ink-2">
                          {b.supplier} · {b.qty} boxes
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1.5">
                          <Stamp tone={b.days_left <= 14 ? "alert" : "warn"}>Exp {stampDate(b.expiry_date)}</Stamp>
                          <Stamp>Batch {b.batch_no}</Stamp>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="num text-lg font-bold text-ink">{num(b.cost_value)}</p>
                        <p className={`text-sm font-semibold ${b.return_eligible ? "text-stock" : "text-ink-2"}`}>
                          {b.return_eligible ? "Can return" : "Sell first"}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
                <Button
                  size="lg"
                  className="mt-2 w-full sm:w-auto"
                  disabled={!!claimPending || busy !== null}
                  onClick={() =>
                    propose("return_claim", {
                      summary: `Return ${expiry.batches.filter((b) => b.return_eligible).map((b) => `${b.product.split(",")[0]} (${b.batch_no})`).join(" and ")}`,
                      amount: expiry.return_eligible_value,
                    })
                  }
                >
                  {claimPending ? "Return claim is in Actions" : `Draft return claims for ${bdt(expiry.return_eligible_value)}`}
                </Button>
                <p className="mt-2 text-sm text-ink-2">Returns come back as supplier credit, usually within 1–2 weeks.</p>
              </>
            )}
          </Carton>
        </div>

        <div className="lg:col-span-5">
          <Carton
            tone="ink"
            title={order ? `${order.supplier} order` : "Next order"}
            aside={order ? <>Due {stampDate(order.due_date)}</> : undefined}
          >
            {!trim || !order ? (
              <Skel className="h-64" />
            ) : (
              <>
                <ul className="divide-y divide-rule">
                  {trim.lines.map((l) => {
                    const cut = l.suggested_qty < l.qty && !trimDone;
                    return (
                      <li key={l.product} className={`py-2.5 ${cut ? "-mx-4 bg-warn-tint px-4" : ""}`}>
                        <div className="flex items-start justify-between gap-3">
                          <p className="font-semibold text-ink">{l.product}</p>
                          <p className="num text-right font-bold whitespace-nowrap text-ink">
                            {trimDone && l.suggested_qty < l.qty ? l.suggested_qty : l.qty} × {num(l.unit_cost)}
                          </p>
                        </div>
                        {cut && (
                          <p className="mt-1 text-sm text-ink">
                            Sells about 1 box every {Math.round(1 / l.sales_rate_per_day)} days. Only{" "}
                            <span className="font-bold">{l.sellable_qty}</span> of {l.qty} will sell before expiry.{" "}
                            <span className="font-bold text-warn">{bdt(l.at_risk_value)} at risk.</span>
                          </p>
                        )}
                      </li>
                    );
                  })}
                </ul>
                <div className="num mt-2 flex justify-between border-t-2 border-ink pt-2 font-bold text-ink">
                  <span>Order total</span>
                  <span>
                    {trimDone ? (
                      bdt(trim.suggested_total)
                    ) : (
                      <>
                        <s className="mr-2 text-ink-2">{num(trim.original_total)}</s>
                        {bdt(trim.suggested_total)}
                      </>
                    )}
                  </span>
                </div>
                {trimDone ? (
                  <div className="mt-3">
                    <Stamp approved>Trimmed · saves {bdt(trim.saving)}</Stamp>
                  </div>
                ) : (
                  <Button
                    size="lg"
                    variant="outline"
                    className="mt-3 w-full"
                    disabled={!!trimPending || busy !== null}
                    onClick={() =>
                      propose("trim_order", {
                        summary: `Cut ${trim.lines.find((l) => l.at_risk_value > 0)?.product.split(",")[0]} from ${trim.lines.find((l) => l.at_risk_value > 0)?.qty} to ${trim.lines.find((l) => l.at_risk_value > 0)?.suggested_qty} boxes on ${order.supplier}'s order`,
                        amount: trim.saving,
                        order_id: order.id,
                      })
                    }
                  >
                    {trimPending ? "Trim is in Actions" : `Trim the order, save ${bdt(trim.saving)}`}
                  </Button>
                )}
              </>
            )}
          </Carton>
        </div>
      </div>
    </div>
  );
}

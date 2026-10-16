"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { decideAction, useActions } from "@/lib/api";
import { bdt, stampDate } from "@/lib/format";
import type { ActionOut } from "@/lib/types";

const KIND_LABEL: Record<ActionOut["kind"], string> = {
  return_claim: "Return claim",
  extension_request: "Ask supplier for more days",
  loan_application: "Loan application",
  set_aside: "Daily set-aside",
  trim_order: "Trim an order",
};

export default function ActionsPage() {
  const { data: actions, error } = useActions();
  const [busy, setBusy] = useState<string | null>(null);
  const waiting = actions?.filter((a) => a.status === "proposed") ?? [];
  const done = actions?.filter((a) => a.status !== "proposed") ?? [];

  async function decide(a: ActionOut, decision: "approve" | "reject") {
    setBusy(a.id);
    try {
      const res = await decideAction(a.id, decision);
      if (res.status === "failed") toast.error(String(res.result?.summary ?? "It didn't go through."));
      else if (decision === "approve") toast.success(String(res.result?.summary ?? "Approved."));
      else toast("Declined. Nothing was done.");
    } catch {
      toast.error("Couldn't reach LaMP. Try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title="Actions" sub="Nothing that touches money or a supplier happens until you approve it here." />
      {error && <LoadError what="your actions" />}
      {!actions && !error && <Skel className="h-64" />}
      {actions && (
        <div className="space-y-4">
          <Carton tone="warn" title="Waiting for you" aside={`${waiting.length}`}>
            {waiting.length === 0 ? (
              <p className="text-ink-2">You&apos;re all caught up. When you or LaMP suggest something, it appears here for approval.</p>
            ) : (
              <ul className="divide-y divide-rule">
                {waiting.map((a) => (
                  <li key={a.id} className="py-3 first:pt-0 last:pb-0">
                    <p className="text-sm font-semibold text-ink-2">
                      {KIND_LABEL[a.kind]} · suggested by {a.proposed_by === "agent" ? "LaMP" : "you"}
                    </p>
                    <p className="mt-0.5 text-lg font-semibold text-ink">{a.payload.summary}</p>
                    {(a.payload.amount !== undefined || typeof a.payload.when === "string") && (
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {a.payload.amount !== undefined && <span className="num font-bold text-ink">{bdt(Number(a.payload.amount))}</span>}
                        {typeof a.payload.when === "string" && <Stamp>{`On ${stampDate(a.payload.when)}`}</Stamp>}
                      </div>
                    )}
                    <div className="mt-3 flex gap-2">
                      <Button className="flex-1 sm:flex-none" disabled={busy === a.id} onClick={() => decide(a, "approve")}>
                        Approve
                      </Button>
                      <Button variant="outline" className="flex-1 sm:flex-none" disabled={busy === a.id} onClick={() => decide(a, "reject")}>
                        Decline
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Carton>

          <Carton tone="ink" title="Done" aside={`${done.length}`}>
            {done.length === 0 ? (
              <p className="text-ink-2">Approved and declined actions are kept here with their results.</p>
            ) : (
              <ul className="divide-y divide-rule">
                {done.map((a) => (
                  <li key={a.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-ink">{a.payload.summary}</p>
                      {a.result?.summary && <p className="text-sm text-ink-2">{String(a.result.summary)}</p>}
                    </div>
                    {a.status === "executed" && <Stamp approved>Approved</Stamp>}
                    {a.status === "rejected" && <Stamp>Declined</Stamp>}
                    {a.status === "failed" && <Stamp tone="alert">Not done</Stamp>}
                  </li>
                ))}
              </ul>
            )}
          </Carton>
        </div>
      )}
    </div>
  );
}

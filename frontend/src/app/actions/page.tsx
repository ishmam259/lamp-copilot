"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { PinPrompt } from "@/components/pin-gate";
import { ApiError, decideAction, errorDetail, useActions, usePause, useValue } from "@/lib/api";
import { bdt, stampDate } from "@/lib/format";
import type { ActionOut } from "@/lib/types";

const KIND_LABEL: Record<ActionOut["kind"], string> = {
  return_claim: "Return claim",
  extension_request: "Ask supplier for more days",
  loan_application: "Loan application",
  set_aside: "Daily set-aside",
  trim_order: "Trim an order",
};

const PROPOSER: Record<ActionOut["proposed_by"], string> = {
  owner: "suggested by you",
  agent: "suggested by LaMP",
  "lamp-scheduler": "LaMP follow-up",
};

/** The action's own description: owner proposals carry `summary`, the copilot's carry `reason`. */
function title(a: ActionOut): string {
  const p = a.payload as Record<string, unknown>;
  return String(p.summary ?? p.reason ?? KIND_LABEL[a.kind]);
}

export default function ActionsPage() {
  const { data: actions, error } = useActions();
  const [busy, setBusy] = useState<string | null>(null);
  const [pinFor, setPinFor] = useState<ActionOut | null>(null);
  const paused = !!usePause().data?.paused;
  const { data: value } = useValue();
  /** While paused, what LaMP proposed can't be approved (the API refuses it too). */
  const held = (a: ActionOut) => paused && a.proposed_by !== "owner";
  const waiting = actions?.filter((a) => a.status === "proposed") ?? [];
  const done = actions?.filter((a) => a.status !== "proposed") ?? [];

  /** Returns false for a wrong PIN and the message for a PIN lockout, so the PIN prompt can say so. */
  async function decide(a: ActionOut, decision: "approve" | "reject", pin?: string): Promise<boolean | string> {
    if (decision === "approve" && a.requires_pin && !pin) {
      setPinFor(a);
      return true;
    }
    setBusy(a.id);
    try {
      const res = await decideAction(a.id, decision, pin);
      setPinFor(null);
      if (res.status === "failed") toast.error(String(res.result?.summary ?? "It didn't go through."));
      else if (decision === "approve") toast.success(String(res.result?.summary ?? "Approved."));
      else toast("Declined. Nothing was done.");
      return true;
    } catch (e) {
      if (pin && e instanceof ApiError && e.status === 401) return false;
      if (pin && e instanceof ApiError && e.status === 429) return errorDetail(e, "Too many wrong PINs. Try again later.");
      setPinFor(null);
      toast.error(e instanceof ApiError && e.status === 409 ? errorDetail(e, "LaMP refused this action.") : "Couldn't reach LaMP. Try again.");
      return true;
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title="Actions" />
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
                      {KIND_LABEL[a.kind]} · {PROPOSER[a.proposed_by]}
                      {a.requires_pin && " · needs your PIN"}
                    </p>
                    <p className="mt-0.5 text-lg font-semibold text-ink">{title(a)}</p>
                    {(a.payload.amount !== undefined || typeof a.payload.when === "string") && (
                      <div className="mt-1 flex flex-wrap items-center gap-2">
                        {a.payload.amount !== undefined && <span className="num font-bold text-ink">{bdt(Number(a.payload.amount))}</span>}
                        {typeof a.payload.when === "string" && <Stamp>{`On ${stampDate(a.payload.when)}`}</Stamp>}
                      </div>
                    )}
                    <div className="mt-3 flex gap-2">
                      <Button className="flex-1 sm:flex-none" disabled={busy === a.id || held(a)} onClick={() => decide(a, "approve")}>
                        Approve
                      </Button>
                      <Button variant="outline" className="flex-1 sm:flex-none" disabled={busy === a.id} onClick={() => decide(a, "reject")}>
                        Decline
                      </Button>
                    </div>
                    {held(a) && <p className="mt-2 text-sm text-ink-2">LaMP is paused. Resume it to approve this suggestion.</p>}
                  </li>
                ))}
              </ul>
            )}
          </Carton>

          <Dialog open={!!pinFor} onOpenChange={(open) => !open && setPinFor(null)}>
            <DialogContent showCloseButton={false} className="max-w-sm">
              <DialogHeader>
                <DialogTitle>Approve with your PIN</DialogTitle>
              </DialogHeader>
              {pinFor && (
                <PinPrompt
                  title={`${title(pinFor)}${pinFor.payload.amount !== undefined ? ` · ${bdt(Number(pinFor.payload.amount))}` : ""}. Loan applications need your PIN again.`}
                  onSubmit={(pin) => decide(pinFor, "approve", pin)}
                  onCancel={() => setPinFor(null)}
                />
              )}
            </DialogContent>
          </Dialog>

          <Carton tone="ink" title="Done" aside={`${done.length}`}>
            {done.length === 0 ? (
              <p className="text-ink-2">Approved and declined actions are kept here with their results.</p>
            ) : (
              <ul className="divide-y divide-rule">
                {done.map((a) => (
                  <li key={a.id} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-ink">{title(a)}</p>
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

          {value && value.items.length > 0 && (
            <Carton tone="stock" title="What your approvals saved" aside={bdt(value.total)}>
              <ul className="divide-y divide-rule">
                {value.items.map((v) => (
                  <li key={`${v.action_id}-${v.kind}`} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-ink">{v.label}</p>
                      <p className="text-sm text-ink-2">{v.basis}</p>
                      <p className="text-sm text-ink-2">Without it: {v.counterfactual}</p>
                    </div>
                    <span className="num font-bold text-stock">{bdt(v.amount)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-3 border-t border-rule pt-3 text-sm text-ink-2">
                Total <span className="num font-bold text-ink">{bdt(value.total)}</span>
              </p>
            </Carton>
          )}
        </div>
      )}
    </div>
  );
}

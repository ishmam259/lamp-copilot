"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Check, X } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { grantConsent, useConsents, useLenders, usePassport, withdrawConsent } from "@/lib/api";
import { num, shortDate } from "@/lib/format";

const SCOPES = ["passport.summary", "passport.evidence"];

export default function PassportPage() {
  const { data: passport, error } = usePassport();
  const { data: lenders } = useLenders();
  const { data: consents } = useConsents();
  const [busy, setBusy] = useState<string | null>(null);

  async function toggle(lenderId: string, on: boolean) {
    setBusy(lenderId);
    try {
      if (on) {
        await grantConsent(lenderId, SCOPES);
        toast.success("Shared. This lender can now see your passport.");
      } else {
        const c = consents?.find((x) => x.lender_id === lenderId);
        if (c) await withdrawConsent(c.id);
        toast("Stopped sharing. The lender can no longer see your passport.");
      }
    } catch {
      toast.error("Couldn't change sharing. Try again.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div>
      <PageTitle title="Credit passport" sub="Your record of paying suppliers, turned into evidence a lender can trust. You decide who sees it." />
      {error && <LoadError what="your passport" />}
      {!passport && !error && <Skel className="h-80" />}
      {passport && (
        <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
          <div className="space-y-4 lg:col-span-7">
            <Carton tone="stock" title="Your record" aside="Last 3 months">
              <p className="text-ink">
                You paid <span className="num text-[1.75rem] font-bold">{passport.paid_on_time}</span>
                <span className="text-ink-2"> of </span>
                <span className="num font-bold">{passport.invoices_total}</span> supplier invoices on time.
              </p>
              <ol className="mt-3 flex flex-wrap gap-1" aria-label="Each invoice, oldest first">
                {passport.evidence.map((e) => (
                  <li
                    key={e.invoice_no}
                    title={`${e.invoice_no} · ${e.supplier} · due ${shortDate(e.due_date)} · ${e.on_time ? "on time" : "late"}`}
                    className={`size-5 rounded-[3px] ${e.on_time ? "bg-stock" : "bg-alert"}`}
                  >
                    <span className="sr-only">{`${e.invoice_no} ${e.on_time ? "on time" : "late"}`}</span>
                  </li>
                ))}
              </ol>
              <p className="mt-2 text-sm text-ink-2">Each square is one invoice, oldest first. All {num(passport.confirmed_share * 100)}% were confirmed by the supplier.</p>
            </Carton>

            <Carton tone="ink" title="What a lender would offer">
              <dl className="grid grid-cols-2 divide-x divide-rule">
                <div className="pr-4">
                  <dt className="text-sm text-ink-2">Advance on an order</dt>
                  <dd className="num text-[1.75rem] font-bold text-ink">{num(passport.advance_rate_pct, 1)}%</dd>
                </div>
                <div className="pl-4">
                  <dt className="text-sm text-ink-2">Default risk</dt>
                  <dd className="num text-[1.75rem] font-bold text-ink">{num(passport.default_probability * 100, 1)}%</dd>
                </div>
              </dl>
              <details className="mt-3 text-sm text-ink">
                <summary className="cursor-pointer font-semibold text-cash">How this is worked out</summary>
                <p className="mt-2">
                  LaMP takes a cautious view of your on-time record: with {passport.paid_on_time} of {passport.invoices_total} on time, it&apos;s at least{" "}
                  <span className="num font-semibold">{num(passport.theta_low_5pct, 3)}</span> on a 0 to 1 scale (95% sure). Combined with a{" "}
                  {num(passport.default_probability * 100, 1)}% default risk, that gives a score of <span className="num font-semibold">{num(passport.score, 3)}</span>.
                </p>
                <p className="mt-2">
                  Advance = 60% + 30% × score. The supplier or a guarantee scheme covers {num(passport.partner_share_pct, 1)}% of any loss; that share shrinks
                  as your record grows. Every on-time payment raises your terms.
                </p>
              </details>
            </Carton>
          </div>

          <div className="lg:col-span-5">
            <Carton tone="warn" title="Who can see it">
              <p className="text-sm text-ink-2">Nobody sees your passport unless you switch them on. You can stop sharing at any time.</p>
              <ul className="mt-3 divide-y divide-rule">
                {lenders?.map((l) => {
                  const on = !!consents?.some((c) => c.lender_id === l.id);
                  return (
                    <li key={l.id} className="flex items-start gap-3 py-3">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-ink">{l.name}</p>
                        <p className="text-sm text-ink-2">{l.products.map((p) => p.label).join(", ")}</p>
                        {on && <Stamp tone="stock" className="mt-1.5">Sharing</Stamp>}
                      </div>
                      <Switch
                        checked={on}
                        disabled={busy === l.id}
                        onCheckedChange={(v: boolean) => toggle(l.id, v)}
                        aria-label={`Share passport with ${l.name}`}
                      />
                    </li>
                  );
                })}
              </ul>
              <h3 className="mt-3 text-sm font-semibold text-ink">What they see</h3>
              <ul className="mt-1 space-y-1 text-sm text-ink">
                <li className="flex gap-2">
                  <Check className="mt-0.5 size-4 shrink-0 text-stock" aria-hidden /> Your on-time record, score and terms
                </li>
                <li className="flex gap-2">
                  <Check className="mt-0.5 size-4 shrink-0 text-stock" aria-hidden /> Invoice numbers, dates and suppliers behind it
                </li>
                <li className="flex gap-2">
                  <X className="mt-0.5 size-4 shrink-0 text-ink-2" aria-hidden /> Never your patients, or what anyone bought
                </li>
              </ul>
            </Carton>
          </div>
        </div>
      )}
    </div>
  );
}

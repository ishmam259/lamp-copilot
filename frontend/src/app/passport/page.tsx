"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Check, X } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { grantConsent, useConsentPreview, useConsents, useLenders, usePassport, withdrawConsent } from "@/lib/api";
import { num, shortDate } from "@/lib/format";

const SUMMARY = ["passport.summary"];
const FULL = ["passport.summary", "passport.evidence"];

export default function PassportPage() {
  const { data: passport, error } = usePassport();
  const { data: lenders } = useLenders();
  const { data: consents } = useConsents();
  const [busy, setBusy] = useState<string | null>(null);
  const [withEvidence, setWithEvidence] = useState(true);
  const [previewFor, setPreviewFor] = useState<string | null>(null);
  const scopes = withEvidence ? FULL : SUMMARY;
  const previewLender = previewFor ?? lenders?.[0]?.id ?? null;
  const { data: preview } = useConsentPreview(previewLender, scopes);

  async function toggle(lenderId: string, on: boolean) {
    setBusy(lenderId);
    try {
      if (on) {
        await grantConsent(lenderId, scopes);
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
      <PageTitle title="Credit passport" />
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
              <p className="mt-2 text-sm text-ink-2">Each square is one invoice, oldest first.</p>
            </Carton>

            <Carton tone="ink" title="What a lender would offer">
              <dl className="grid grid-cols-2 divide-x divide-rule">
                <div className="pr-4">
                  <dt className="text-sm text-ink-2">A lender would pay</dt>
                  <dd className="num text-[1.75rem] font-bold text-ink">{num(passport.advance_rate_pct, 1)}%</dd>
                  <dd className="text-sm text-ink-2">of each order</dd>
                </div>
                <div className="pl-4">
                  <dt className="text-sm text-ink-2">Chance of not repaying</dt>
                  <dd className="num text-[1.75rem] font-bold text-ink">{num(passport.default_probability * 100, 1)}%</dd>
                </div>
              </dl>
              <details className="mt-3 text-sm text-ink">
                <summary className="cursor-pointer font-semibold text-cash">How this is worked out</summary>
                <p className="mt-2">
                  You paid {passport.paid_on_time} of {passport.invoices_total} supplier invoices on time. LaMP counts this carefully, so a few good
                  weeks can&apos;t make it look better than it is.
                </p>
                <p className="mt-2">
                  The better your record, the more of an order a lender will pay and the lower the chance of not repaying. Every on-time payment
                  improves both.
                </p>
              </details>
            </Carton>
          </div>

          <div className="lg:col-span-5">
            <Carton tone="warn" title="Who can see it">
              <p className="text-sm text-ink-2">Nobody sees your passport until you switch a lender on below. You can stop sharing at any time.</p>
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
              <fieldset className="mt-3 border-t border-rule pt-3">
                <legend className="float-left w-full text-sm font-semibold text-ink">What a lender sees</legend>
                <div className="clear-left grid gap-2 pt-2 sm:grid-cols-2">
                  {[
                    { v: false, label: "Summary only", sub: "Your on-time count and the offer" },
                    { v: true, label: "Summary and invoices", sub: "Plus each invoice and when you paid it" },
                  ].map((o) => (
                    <label
                      key={o.label}
                      className={`cursor-pointer rounded-[var(--radius)] border p-2.5 text-sm ${withEvidence === o.v ? "border-cash bg-muted" : "border-rule"}`}
                    >
                      <input type="radio" name="scope" className="sr-only" checked={withEvidence === o.v} onChange={() => setWithEvidence(o.v)} />
                      <span className="block font-semibold text-ink">{o.label}</span>
                      <span className="block text-ink-2">{o.sub}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              <div className="mt-3 flex flex-wrap items-baseline gap-x-2">
                <h3 className="text-sm font-semibold text-ink">What this lender will see</h3>
                {lenders && lenders.length > 1 && (
                  <select
                    aria-label="Lender to preview"
                    value={previewLender ?? ""}
                    onChange={(e) => setPreviewFor(e.target.value)}
                    className="h-8 rounded-[var(--radius)] border border-rule bg-board px-2 text-sm text-ink"
                  >
                    {lenders.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <ul className="mt-1 space-y-1 text-sm text-ink">
                {preview?.shares.map((t) => (
                  <li key={t} className="flex gap-2">
                    <Check className="mt-0.5 size-4 shrink-0 text-stock" aria-hidden /> {t}
                  </li>
                ))}
                {preview?.withholds.map((t) => (
                  <li key={t} className="flex gap-2 text-ink-2">
                    <X className="mt-0.5 size-4 shrink-0" aria-hidden /> Not shared: {t}
                  </li>
                ))}
                <li className="flex gap-2 text-ink-2">
                  <X className="mt-0.5 size-4 shrink-0" aria-hidden /> Never your patients, or what anyone bought
                </li>
              </ul>
              {preview && (
                <p className="mt-2 text-xs text-ink-2">
                  {preview.passport.evidence.length > 0
                    ? `This lender would see ${preview.passport.evidence.length} invoices.`
                    : "This lender would see the summary only."}
                </p>
              )}
            </Carton>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useRef, useState } from "react";
import { toast } from "sonner";
import { Camera, CircleAlert, CircleCheck, ShieldAlert } from "lucide-react";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { Carton, PageTitle } from "@/components/carton";
import { confirmCapture, uploadCapture } from "@/lib/api";
import { dayDate, num } from "@/lib/format";
import type { CaptureOut, ExtractionLine, ExtractionResult } from "@/lib/types";

type SalesDay = NonNullable<ExtractionResult["sales_page"]>["days"][number];

type Kind = "invoice" | "sales_page";

export default function CapturePage() {
  const [kind, setKind] = useState<Kind>("invoice");
  const [capture, setCapture] = useState<CaptureOut | null>(null);
  const [reading, setReading] = useState(false);
  const [saved, setSaved] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function onFile(file: File | undefined) {
    if (!file) return;
    setReading(true);
    setSaved(false);
    try {
      setCapture(await uploadCapture(kind, file));
    } catch {
      toast.error("LaMP couldn't read that photo. Try again in better light.");
    } finally {
      setReading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageTitle title="Capture" />

      {!capture && (
        <Carton tone="ink" title="What are you photographing?">
          <div role="radiogroup" aria-label="Document type" className="grid grid-cols-2 gap-2">
            {(
              [
                ["invoice", "Supplier invoice"],
                ["sales_page", "Sales book page"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                role="radio"
                aria-checked={kind === k}
                onClick={() => setKind(k)}
                className={cn(
                  "h-14 rounded-[var(--radius)] border-2 font-semibold",
                  kind === k ? "border-cash bg-cash-tint text-cash" : "border-rule text-ink hover:border-ink-2"
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <input
            ref={fileRef}
            id="photo"
            type="file"
            accept="image/*"
            capture="environment"
            className="sr-only"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
          <Button size="lg" className="mt-4 w-full" disabled={reading} onClick={() => fileRef.current?.click()}>
            <Camera className="size-5" aria-hidden />
            {reading ? "Reading the photo…" : "Take or choose a photo"}
          </Button>
          <p className="mt-3 text-sm text-ink-2">Lay the page flat, fill the frame, avoid shadows. LaMP reads printed and handwritten English.</p>
        </Carton>
      )}

      {capture && capture.extraction.invoice && (
        <Review
          capture={capture}
          saved={saved}
          onConfirm={async (lines) => {
            const ex = structuredClone(capture.extraction);
            ex.invoice!.lines = lines;
            try {
              await confirmCapture(capture.id, ex);
              setSaved(true);
              toast.success("Saved to your accounts.");
            } catch {
              toast.error("Couldn't save it. Check the highlighted fields and try again.");
            }
          }}
          onAnother={() => {
            setCapture(null);
            setSaved(false);
          }}
        />
      )}

      {capture && capture.extraction.sales_page && (
        <SalesReview
          capture={capture}
          saved={saved}
          onConfirm={async (days) => {
            const ex = structuredClone(capture.extraction);
            ex.sales_page!.days = days;
            try {
              await confirmCapture(capture.id, ex);
              setSaved(true);
              toast.success("Saved to your accounts.");
            } catch {
              toast.error("Couldn't save it. Check the highlighted fields and try again.");
            }
          }}
          onAnother={() => {
            setCapture(null);
            setSaved(false);
          }}
        />
      )}
    </div>
  );
}

function SuspiciousBanner({ capture, what }: { capture: CaptureOut; what: string }) {
  const suspicious = capture.extraction.suspicious_text;
  if (suspicious.length === 0) return null;
  return (
    <div role="alert" className="flex gap-3 rounded-[8px] border border-alert/40 bg-alert-tint p-4 text-ink">
      <ShieldAlert className="mt-0.5 size-5 shrink-0 text-alert" aria-hidden />
      <div>
        <p className="font-semibold text-alert">This photo contained instructions to the AI. LaMP ignored them.</p>
        <p className="mt-1 text-sm">
          Found: <q>{suspicious[0]}</q>. Nothing was approved or changed. Only the {what} below were read.
        </p>
      </div>
    </div>
  );
}

/** Failed plain-code checks, listed so the owner knows what to look at. */
function FailedChecks({ capture }: { capture: CaptureOut }) {
  const failed = capture.extraction.checks.filter((c) => !c.passed);
  if (failed.length === 0) return null;
  return (
    <ul className="mt-3 space-y-1.5" aria-label="Checks that failed">
      {failed.map((c) => (
        <li key={c.name} className="flex items-start gap-2 rounded-[var(--radius)] bg-warn-tint p-3 text-sm text-ink">
          <CircleAlert className="size-5 shrink-0 text-warn" aria-hidden />
          <span>
            <span className="font-semibold">{c.name}:</span> {c.detail}
          </span>
        </li>
      ))}
    </ul>
  );
}

function Review({
  capture,
  saved,
  onConfirm,
  onAnother,
}: {
  capture: CaptureOut;
  saved: boolean;
  onConfirm: (lines: ExtractionLine[]) => Promise<void>;
  onAnother: () => void;
}) {
  const inv = capture.extraction.invoice!;
  const [lines, setLines] = useState(inv.lines);
  const conf = capture.extraction.field_confidence;
  const low = (path: string) => (conf[path] ?? 1) < 0.6;
  const linesTotal = lines.reduce((s, l) => s + l.qty * l.unit_cost, 0);
  const matches = Math.abs(linesTotal - inv.total) < 1;

  function setLine(i: number, field: "qty" | "unit_cost", value: string) {
    const n = Number(value.replace(/[^0-9.]/g, ""));
    setLines((prev) => prev.map((l, j) => (j === i ? { ...l, [field]: n, line_total: field === "qty" ? n * l.unit_cost : l.qty * n } : l)));
  }

  return (
    <div className="space-y-4">
      <SuspiciousBanner capture={capture} what="invoice details" />

      <Carton tone={saved ? "stock" : "warn"} title={saved ? "Saved" : "Check what LaMP read"} aside={`${inv.supplier_name} · ${inv.invoice_no}`}>
        <p className="text-sm text-ink-2">Fields LaMP wasn&apos;t sure about are highlighted. Correct them, then save.</p>
        <FailedChecks capture={capture} />
        <ul className="mt-3 divide-y divide-rule">
          {lines.map((l, i) => (
            <li key={l.batch_no} className="py-3">
              <p className="font-semibold text-ink">{l.product}</p>
              <p className="text-sm text-ink-2">
                Batch {l.batch_no} · expires {l.expiry_date}
              </p>
              <div className="mt-2 grid grid-cols-3 items-end gap-2">
                <NumberField label="Boxes" value={l.qty} unsure={low(`invoice.lines[${i}].qty`)} disabled={saved} onChange={(v) => setLine(i, "qty", v)} />
                <NumberField
                  label="Price per box"
                  value={l.unit_cost}
                  unsure={low(`invoice.lines[${i}].unit_cost`)}
                  disabled={saved}
                  onChange={(v) => setLine(i, "unit_cost", v)}
                />
                <p className="num pb-2.5 text-right font-bold text-ink">{num(l.qty * l.unit_cost)}</p>
              </div>
            </li>
          ))}
        </ul>
        <div
          className={cn(
            "mt-2 flex items-start gap-2 rounded-[var(--radius)] p-3 text-sm",
            matches ? "bg-stock-tint text-ink" : "bg-warn-tint text-ink"
          )}
        >
          {matches ? <CircleCheck className="size-5 shrink-0 text-stock" aria-hidden /> : <CircleAlert className="size-5 shrink-0 text-warn" aria-hidden />}
          <p>
            Lines add up to <span className="num font-bold">BDT {num(linesTotal)}</span>. The invoice says{" "}
            <span className="num font-bold">BDT {num(inv.total)}</span>.
            {matches ? " They match." : " Check the highlighted prices."}
          </p>
        </div>
        {!saved ? (
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <Button size="lg" disabled={!matches} onClick={() => onConfirm(lines)}>
              Save to accounts
            </Button>
            <Button size="lg" variant="ghost" onClick={onAnother}>
              Retake photo
            </Button>
          </div>
        ) : (
          <Button size="lg" variant="outline" className="mt-4" onClick={onAnother}>
            Capture another
          </Button>
        )}
      </Carton>
    </div>
  );
}

const SALES_FIELDS = [
  ["cash_sales", "Cash sales"],
  ["credit_sales", "Credit sales"],
  ["dues_collected", "Dues collected"],
  ["expenses", "Expenses"],
] as const;

function SalesReview({
  capture,
  saved,
  onConfirm,
  onAnother,
}: {
  capture: CaptureOut;
  saved: boolean;
  onConfirm: (days: SalesDay[]) => Promise<void>;
  onAnother: () => void;
}) {
  const [days, setDays] = useState(capture.extraction.sales_page!.days);
  const conf = capture.extraction.field_confidence;
  const low = (path: string) => (conf[path] ?? 1) < 0.6;
  const total = days.reduce((s, d) => s + d.cash_sales + d.credit_sales, 0);

  function setField(i: number, field: (typeof SALES_FIELDS)[number][0], value: string) {
    const n = Number(value.replace(/[^0-9.]/g, ""));
    setDays((prev) => prev.map((d, j) => (j === i ? { ...d, [field]: n } : d)));
  }

  return (
    <div className="space-y-4">
      <SuspiciousBanner capture={capture} what="sales figures" />
      <Carton tone={saved ? "stock" : "warn"} title={saved ? "Saved" : "Check what LaMP read"} aside={`Sales book · ${days.length} days`}>
        <p className="text-sm text-ink-2">Fields LaMP wasn&apos;t sure about are highlighted. Correct them, then save.</p>
        <FailedChecks capture={capture} />
        <ul className="mt-3 divide-y divide-rule">
          {days.map((d, i) => (
            <li key={`${d.date}-${i}`} className="py-3">
              <p className="font-semibold text-ink">{dayDate(d.date)}</p>
              <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {SALES_FIELDS.map(([field, label]) => (
                  <NumberField
                    key={field}
                    label={label}
                    value={d[field]}
                    unsure={low(`sales_page.days[${i}].${field}`)}
                    disabled={saved}
                    onChange={(v) => setField(i, field, v)}
                  />
                ))}
              </div>
            </li>
          ))}
        </ul>
        <p className="mt-2 rounded-[var(--radius)] bg-board p-3 text-sm text-ink">
          Sales on this page: <span className="num font-bold">BDT {num(total)}</span> over {days.length} days.
        </p>
        {!saved ? (
          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <Button size="lg" onClick={() => onConfirm(days)}>
              Save to accounts
            </Button>
            <Button size="lg" variant="ghost" onClick={onAnother}>
              Retake photo
            </Button>
          </div>
        ) : (
          <Button size="lg" variant="outline" className="mt-4" onClick={onAnother}>
            Capture another
          </Button>
        )}
      </Carton>
    </div>
  );
}

function NumberField({
  label,
  value,
  unsure,
  disabled,
  onChange,
}: {
  label: string;
  value: number;
  unsure: boolean;
  disabled: boolean;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block text-xs font-semibold text-ink-2">
      {label}
      {unsure && <span className="ml-1 text-warn">· check</span>}
      <input
        inputMode="decimal"
        value={String(value)}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className={cn(
          "num mt-1 h-11 w-full rounded-[var(--radius)] border bg-board px-2.5 text-base font-semibold text-ink",
          unsure ? "border-warn bg-warn-tint" : "border-input"
        )}
      />
    </label>
  );
}

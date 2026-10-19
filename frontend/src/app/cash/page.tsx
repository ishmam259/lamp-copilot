"use client";

import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { CashLine } from "@/components/cash-line";
import { dayAmount, dayLabel, isNamedMove } from "@/lib/forecast";
import { useAccounts, useDues, useForecast } from "@/lib/api";
import { bdt, dayDate, num, signed, shortDate, stampDate } from "@/lib/format";

export default function CashPage() {
  const { data: forecast, error } = useForecast();
  const { data: dues } = useDues();
  const { data: accounts } = useAccounts();

  const events = forecast?.days.filter(isNamedMove) ?? [];
  const first = forecast?.days[0]?.date;
  const last = forecast?.days[forecast.days.length - 1]?.date;

  return (
    <div>
      <PageTitle title="Cash" />
      <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
        <div className="space-y-4 lg:col-span-7">
          <Carton tone="cash" title="Next 30 days" aside={first && last ? `${shortDate(first)} – ${shortDate(last)}` : undefined}>
            {error && <LoadError what="the forecast" />}
            {!forecast && !error && <Skel className="h-24" />}
            {forecast && (
              <>
                <CashLine forecast={forecast} />
                <p className="mt-3 text-sm text-ink-2">
                  You have <span className="num font-semibold text-ink">{bdt(forecast.start_cash)}</span> today.
                </p>
              </>
            )}
          </Carton>

          <Carton tone="cash" title="Money in and out" bodyClassName="p-0">
            {!forecast ? (
              <Skel className="m-4 h-40" />
            ) : (
              <table className="w-full text-left">
                <caption className="sr-only">Named payments and receipts in the next 30 days, with the cash balance at the end of each day</caption>
                <thead className="bg-board text-sm font-semibold text-ink-2">
                  <tr className="border-b border-rule">
                    <th scope="col" className="px-4 py-2 font-semibold">Day</th>
                    <th scope="col" className="px-2 py-2 text-right font-semibold">Amount</th>
                    <th scope="col" className="px-4 py-2 text-right font-semibold">Cash left</th>
                  </tr>
                </thead>
                <tbody className="num">
                  {events.map((d) => {
                    const net = dayAmount(d);
                    const neg = d.balance < 0;
                    return (
                      <tr key={d.date} className={neg ? "bg-alert-tint" : "even:bg-shelf/40"}>
                        <th scope="row" className="px-4 py-2.5 font-semibold whitespace-nowrap text-ink">
                          {dayDate(d.date)}
                          <span className="block text-sm font-normal whitespace-normal text-ink-2">
                            <KeepCode text={dayLabel(d, dues?.items.find((x) => x.due_date === d.date)?.supplier)} />
                          </span>
                        </th>
                        <td className={`px-2 py-2.5 text-right font-semibold whitespace-nowrap ${net < 0 ? "text-ink" : "text-stock"}`}>{signed(net)}</td>
                        <td className={`px-4 py-2.5 text-right font-bold whitespace-nowrap ${neg ? "text-alert" : "text-ink"}`}>{num(d.balance)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </Carton>
        </div>

        <div className="space-y-4 lg:col-span-5">
          <Carton tone="cash" title="Supplier bills" aside={dues ? `${dues.items.length} invoices` : undefined}>
            {!dues ? (
              <Skel className="h-40" />
            ) : (
              <>
                <ul className="divide-y divide-rule">
                  {dues.items.map((d) => (
                    <li key={d.invoice_no} className="flex items-start gap-3 py-3 first:pt-0">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold text-ink">{d.supplier}</p>
                        <p className="text-sm text-ink-2">Invoice {d.invoice_no}</p>
                        <Stamp tone={d.status === "overdue" ? "alert" : d.status === "due_soon" ? "warn" : undefined} className="mt-1.5">
                          Due {stampDate(d.due_date)}
                        </Stamp>
                      </div>
                      <span className="num text-right text-lg font-bold text-ink">{num(d.amount)}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-2 flex justify-between border-t-2 border-ink pt-2 font-bold text-ink">
                  <span>Total due</span>
                  <span className="num">{bdt(dues.total_due)}</span>
                </div>
              </>
            )}
          </Carton>

          <div id="accounts">
            <Carton tone="ink" title="Accounts" aside="Last 30 days">
              {!accounts ? (
                <Skel className="h-56" />
              ) : (
                <>
                  <dl className="num divide-y divide-rule">
                    {[
                      ["Sales", accounts.sales, ""],
                      [`Profit on goods sold (${accounts.gross_margin_pct}%)`, accounts.gross_profit, ""],
                      ["Rent, salaries, utilities", -accounts.overheads, ""],
                    ].map(([label, value]) => (
                      <div key={String(label)} className="flex justify-between py-2">
                        <dt className="text-ink-2">{label}</dt>
                        <dd className="font-semibold text-ink">{signed(Number(value)).replace("+ ", "")}</dd>
                      </div>
                    ))}
                    <div className="flex justify-between border-t-2 border-ink py-2 text-lg font-bold">
                      <dt className="text-ink">You kept</dt>
                      <dd className="text-stock">{bdt(accounts.net_profit)}</dd>
                    </div>
                  </dl>
                  <dl className="mt-3 grid grid-cols-2 divide-x divide-rule border-t border-rule pt-3 text-sm">
                    <div className="pr-4">
                      <dt className="text-ink-2">Stock on shelves</dt>
                      <dd className="num font-bold text-ink">{bdt(accounts.stock_value)}</dd>
                      <dd className="text-ink-2">{accounts.stock_days} days of stock</dd>
                    </div>
                    <div className="pl-4">
                      <dt className="text-ink-2">Patients owe you</dt>
                      <dd className="num font-bold text-ink">{bdt(accounts.patient_dues)}</dd>
                      <dd className="text-ink-2">{accounts.patient_due_days} days of sales</dd>
                    </div>
                  </dl>
                  <h3 className="mt-4 font-semibold text-ink">Who you buy from</h3>
                  <p className="text-xs text-ink-2">{accounts.active_suppliers} suppliers. The biggest five:</p>
                  <ul className="mt-2 space-y-1.5">
                    {accounts.top_suppliers.map((s) => (
                      <li key={s.name} className="grid grid-cols-[96px_1fr_44px] items-center gap-2 text-sm">
                        <span className="font-semibold text-ink">{s.name}</span>
                        <span className="h-2.5 rounded-full bg-muted" aria-hidden>
                          <span className="block h-full rounded-full bg-ink-2" style={{ width: `${(s.share_pct / 20) * 100}%` }} />
                        </span>
                        <span className="num text-right text-ink">{s.share_pct}%</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </Carton>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Keeps the last word (an invoice code such as "D-20931") on one line instead of breaking at its hyphen. */
function KeepCode({ text }: { text: string }) {
  const cut = text.lastIndexOf(" ");
  if (cut < 0) return <span className="whitespace-nowrap">{text}</span>;
  return (
    <>
      {text.slice(0, cut + 1)}
      <span className="whitespace-nowrap">{text.slice(cut + 1)}</span>
    </>
  );
}

"use client";

import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { CashStrip } from "@/components/cash-strip";
import { useAccounts, useDues, useForecast } from "@/lib/api";
import { bdt, dayDate, num, signed, shortDate, stampDate } from "@/lib/format";

export default function CashPage() {
  const { data: forecast, error } = useForecast();
  const { data: dues } = useDues();
  const { data: accounts } = useAccounts();

  const events = forecast?.days.filter((d) => d.outflow > 0 || d.inflow > 2000) ?? [];
  const first = forecast?.days[0]?.date;
  const last = forecast?.days[forecast.days.length - 1]?.date;

  return (
    <div>
      <PageTitle title="Cash" sub="What comes in, what goes out, and where it runs short." />
      <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
        <div className="space-y-4 lg:col-span-7">
          <Carton tone="cash" title="Next 30 days" aside={first && last ? `${shortDate(first)} – ${shortDate(last)}` : undefined}>
            {error && <LoadError what="the forecast" />}
            {!forecast && !error && <Skel className="h-24" />}
            {forecast && (
              <>
                <CashStrip forecast={forecast} height={96} />
                <p className="mt-3 text-sm text-ink-2">
                  Starts from <span className="num font-semibold text-ink">{bdt(forecast.start_cash)}</span> today. Each day adds normal sales and takes out
                  normal restocking; the rows below are the bigger moves.
                </p>
              </>
            )}
          </Carton>

          <Carton tone="cash" title="Money in and out" bodyClassName="p-0">
            {!forecast ? (
              <Skel className="m-4 h-40" />
            ) : (
              <table className="w-full text-left">
                <caption className="sr-only">Large cash movements in the next 30 days with the balance after each</caption>
                <thead className="sticky top-14 bg-board text-xs font-semibold tracking-wide text-ink-2 uppercase lg:top-[57px]">
                  <tr className="border-b border-rule">
                    <th scope="col" className="px-4 py-2 font-semibold">Day</th>
                    <th scope="col" className="px-2 py-2 text-right font-semibold">In / out</th>
                    <th scope="col" className="px-4 py-2 text-right font-semibold">Balance</th>
                  </tr>
                </thead>
                <tbody className="num">
                  {events.map((d) => {
                    const net = d.inflow - d.outflow;
                    const neg = d.balance < 0;
                    return (
                      <tr key={d.date} className={neg ? "bg-alert-tint" : "even:bg-shelf/40"}>
                        <th scope="row" className="px-4 py-2.5 font-semibold whitespace-nowrap text-ink">
                          {dayDate(d.date)}
                        </th>
                        <td className={`px-2 py-2.5 text-right font-semibold ${net < 0 ? "text-ink" : "text-stock"}`}>{signed(net)}</td>
                        <td className={`px-4 py-2.5 text-right font-bold ${neg ? "text-alert" : "text-ink"}`}>{num(d.balance)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </Carton>
        </div>

        <div className="space-y-4 lg:col-span-5">
          <Carton tone="cash" title="Supplier dues" aside={dues ? `${dues.items.length} invoices` : undefined}>
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
                      [`Gross profit at ${accounts.gross_margin_pct}%`, accounts.gross_profit, ""],
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
                  <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div className="rounded-[var(--radius)] bg-shelf p-3">
                      <dt className="text-ink-2">Stock on shelves</dt>
                      <dd className="num font-bold text-ink">{bdt(accounts.stock_value)}</dd>
                      <dd className="text-ink-2">{accounts.stock_days} days of buying</dd>
                    </div>
                    <div className="rounded-[var(--radius)] bg-shelf p-3">
                      <dt className="text-ink-2">Patients owe you</dt>
                      <dd className="num font-bold text-ink">{bdt(accounts.patient_dues)}</dd>
                      <dd className="text-ink-2">{accounts.patient_due_days} days of sales</dd>
                    </div>
                  </dl>
                  <h3 className="mt-4 text-sm font-bold tracking-wide text-ink-2 uppercase">Where your buying goes</h3>
                  <p className="text-xs text-ink-2">{accounts.active_suppliers} active suppliers. Top five:</p>
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

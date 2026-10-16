"use client";

import Link from "next/link";
import { ArrowRight, BadgeCheck, Landmark, ScrollText } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Carton, LoadError, Skel, Stamp } from "@/components/carton";
import { CashLine } from "@/components/cash-line";
import { useAccounts, useActions, useAlerts, useDues, useExpiry, useForecast, usePharmacy } from "@/lib/api";
import { bdt, dayDate, daysBetween, inDays, num, shortDate, signed, stampDate, weekday } from "@/lib/format";

export default function TodayPage() {
  const { data: pharmacy } = usePharmacy();
  const { data: forecast, error: fErr } = useForecast();
  const { data: dues } = useDues();
  const { data: expiry } = useExpiry();
  const { data: accounts } = useAccounts();
  const { data: actions } = useActions();
  const { data: alerts } = useAlerts();

  const asOf = pharmacy?.settings.as_of_date;
  const short = forecast?.shortfalls[0];
  const pending = actions?.filter((a) => a.status === "proposed") ?? [];
  const suspicious = alerts?.find((a) => a.kind === "suspicious_document");
  const first = forecast?.days[0]?.date;
  const last = forecast?.days[forecast.days.length - 1]?.date;
  const balanceBefore = short && forecast ? forecast.days[forecast.days.findIndex((d) => d.date === short.date) - 1]?.balance : undefined;

  return (
    <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
      <h1 className="sr-only">Today</h1>

      {suspicious && (
        <p role="alert" className="rounded-[var(--radius)] border border-alert/40 bg-alert-tint p-3 font-semibold text-alert lg:col-span-12">
          {suspicious.title}. {suspicious.detail}
        </p>
      )}

      {/* Cash: the first thing the owner reads, on the station board */}
      <div className="space-y-4 lg:col-span-7">
        {!forecast && !fErr && <Skel className="h-72" />}
        {fErr && <LoadError what="your cash forecast" />}
        {forecast && (
          <>
            <section aria-labelledby="board-head" className="station-board">
              {short ? (
                <>
                  <p className="sb-kicker">
                    Next stop · {dayDate(short.date)}
                    {asOf ? ` · ${inDays(daysBetween(asOf, short.date))}` : ""}
                  </p>
                  <h2 id="board-head" className="sb-head num">
                    Short {bdt(short.amount)}
                  </h2>
                  <p className="sb-sub mt-1.5 text-[1.0625rem] font-medium">
                    {short.cause}
                    {balanceBefore !== undefined && <> · you&apos;ll have {bdt(balanceBefore)}</>}
                  </p>
                </>
              ) : (
                <>
                  <p className="sb-kicker">Next 30 days</p>
                  <h2 id="board-head" className="sb-head">
                    Cash holds
                  </h2>
                </>
              )}
            </section>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              {short && (
                <Link href="/funding" className={buttonVariants({ size: "lg", className: "w-full sm:w-auto" })}>
                  See the fix <ArrowRight className="size-5" aria-hidden />
                </Link>
              )}
              <Link href="/cash" className="inline-flex h-11 items-center justify-center gap-1 font-semibold text-cash hover:underline sm:px-2">
                Cash, day by day <ArrowRight className="size-4" aria-hidden />
              </Link>
            </div>
            <Carton tone="ink" title="Upcoming money" aside={first && last ? `${shortDate(first)} – ${shortDate(last)}` : undefined}>
              <CashLine forecast={forecast} />
              <ul className="mt-3 divide-y divide-rule">
                {forecast.days
                  .filter((d) => d.outflow >= 5000 || d.inflow >= 4000)
                  .slice(0, 5)
                  .map((d) => {
                    const neg = d.balance < 0;
                    const due = dues?.items.find((x) => x.due_date === d.date);
                    return (
                      <li key={d.date} className={`grid grid-cols-[64px_1fr_auto] items-center gap-3 py-2.5 ${neg ? "-mx-4 bg-alert-tint px-4" : ""}`}>
                        <span className="font-board leading-tight font-bold text-ink">
                          {shortDate(d.date)}
                          <span className="block text-xs font-semibold text-ink-2">{weekday(d.date)}</span>
                        </span>
                        <span className="min-w-0 truncate text-ink">
                          {due ? due.supplier : d.inflow > d.outflow ? "Patient dues collected" : d.outflow === 18000 ? "Shop rent" : d.outflow === 15000 ? "Salaries" : "Bills"}
                          {neg && <span className="ml-2 text-sm font-semibold text-alert">short</span>}
                        </span>
                        <span className={`num text-right font-bold ${d.inflow > d.outflow ? "text-stock" : "text-ink"}`}>
                          {signed(d.inflow > d.outflow ? d.inflow - 1650 : -d.outflow)}
                        </span>
                      </li>
                    );
                  })}
              </ul>
            </Carton>
          </>
        )}
      </div>

      <div className="space-y-4 lg:col-span-5">
        {/* Waiting for the owner */}
        {pending.length > 0 && (
          <Carton tone="warn" title="Waiting for you" aside={`${pending.length} to approve`}>
            <ul className="space-y-2">
              {pending.slice(0, 3).map((a) => (
                <li key={a.id} className="text-ink">
                  <span className="font-semibold">{a.payload.summary ?? a.kind.replaceAll("_", " ")}</span>
                  <span className="text-sm text-ink-2"> · suggested by {a.proposed_by === "agent" ? "LaMP" : "you"}</span>
                </li>
              ))}
            </ul>
            <Link href="/actions" className={buttonVariants({ variant: "outline", className: "mt-3 w-full" })}>
              Review and approve
            </Link>
          </Carton>
        )}

        {/* Expiring stock */}
        <Carton tone="ink" title="Expiring stock" aside="Next 60 days">
          {!expiry ? (
            <Skel className="h-24" />
          ) : (
            <>
              <p className="num text-[1.75rem] font-bold text-ink">{bdt(expiry.at_risk_value)}</p>
              <p className="mt-1 text-ink">
                {expiry.batches.length} batches. <span className="num font-bold text-stock">{bdt(expiry.return_eligible_value)}</span> can still go back to suppliers.
              </p>
              <div className="mt-2">
                <Stamp>EXP ≤ {stampDate(expiry.batches.reduce((m, b) => (b.expiry_date > m ? b.expiry_date : m), expiry.batches[0].expiry_date))}</Stamp>
              </div>
              <Link href="/stock" className={buttonVariants({ variant: "outline", className: "mt-3 w-full" })}>
                Recover {bdt(expiry.return_eligible_value)}
              </Link>
            </>
          )}
        </Carton>
      </div>

      {/* This month */}
      <div className="lg:col-span-12">
        <Carton tone="ink" title="Last 30 days" aside={accounts ? `${num(accounts.gross_margin_pct)}% margin` : undefined}>
          {!accounts ? (
            <Skel className="h-16" />
          ) : (
            <dl className="grid grid-cols-3 gap-3">
              <div>
                <dt className="text-sm text-ink-2">Sales</dt>
                <dd className="num text-xl font-bold text-ink">{num(accounts.sales)}</dd>
              </div>
              <div>
                <dt className="text-sm text-ink-2">Costs and stock</dt>
                <dd className="num text-xl font-bold text-ink">{num(accounts.sales - accounts.net_profit)}</dd>
              </div>
              <div>
                <dt className="text-sm text-ink-2">You kept</dt>
                <dd className="num text-xl font-bold text-stock">{num(accounts.net_profit)}</dd>
              </div>
            </dl>
          )}
          <Link href="/cash#accounts" className="mt-3 inline-flex items-center gap-1 font-semibold text-cash hover:underline">
            Full accounts <ArrowRight className="size-4" aria-hidden />
          </Link>
        </Carton>
      </div>

      {/* Phone: the screens that aren't in the tab bar */}
      <nav aria-label="More" className="grid grid-cols-3 gap-2 lg:hidden">
        {[
          { href: "/passport", label: "Passport", icon: BadgeCheck },
          { href: "/lender", label: "Lender view", icon: Landmark },
          { href: "/log", label: "Audit log", icon: ScrollText },
        ].map(({ href, label, icon: Icon }) => (
          <Link key={href} href={href} className="flex h-16 flex-col items-center justify-center gap-1 rounded-[var(--radius)] border border-rule bg-board text-sm font-semibold text-ink">
            <Icon className="size-5 text-ink-2" aria-hidden />
            {label}
          </Link>
        ))}
      </nav>
      {asOf && <p className="text-center text-xs text-ink-2 lg:col-span-12">Figures as of {shortDate(asOf)} 2026</p>}
    </div>
  );
}

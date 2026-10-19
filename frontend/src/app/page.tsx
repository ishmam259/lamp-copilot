"use client";

import Link from "next/link";
import { ArrowRight, BadgeCheck, Check, ChevronRight, CreditCard, Landmark, ScrollText, ShieldCheck } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Carton, LoadError, Skel, Stamp } from "@/components/carton";
import { CashLine } from "@/components/cash-line";
import { dayAmount, dayLabel, isNamedMove } from "@/lib/forecast";
import { useAccount, useAccounts, useActions, useAlerts, useDues, useExpiry, useForecast, usePharmacy } from "@/lib/api";
import { bdt, dayDate, daysBetween, inDays, num, shortDate, signed, stampDate, weekday } from "@/lib/format";
import { waitingOn } from "@/lib/waiting";

export default function TodayPage() {
  const { data: pharmacy } = usePharmacy();
  const { data: forecast, error: fErr } = useForecast();
  const { data: dues } = useDues();
  const { data: expiry } = useExpiry();
  const { data: accounts } = useAccounts();
  const { data: actions } = useActions();
  const { data: alerts } = useAlerts();
  const { data: account } = useAccount();
  const waiting = waitingOn(actions, account);

  const asOf = pharmacy?.settings.as_of_date;
  const short = forecast?.shortfalls[0];
  const pending = actions?.filter((a) => a.status === "proposed") ?? [];
  const suspicious = alerts?.find((a) => a.kind === "suspicious_document");
  const last = forecast?.days[forecast.days.length - 1]?.date;
  const moves = forecast?.days.filter(isNamedMove) ?? [];
  const shown = moves.slice(0, 5);
  const moreCount = moves.length - shown.length;
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
                  {waiting.covered && (
                    <p className="sb-sub mb-1.5 flex items-center gap-1.5 text-sm font-semibold">
                      <Check className="size-4" aria-hidden /> First shortfall covered. Next one:
                    </p>
                  )}
                  <h2 id="board-head" className="sb-head">
                    <span className="num">Short {bdt(short.amount)}</span>
                    <span className="sb-time">
                      {dayDate(short.date)}
                      {asOf ? ` · ${inDays(daysBetween(asOf, short.date))}` : ""}
                    </span>
                  </h2>
                  <p className="sb-sub mt-1.5 text-[1.0625rem] font-medium">
                    {short.cause}
                    {balanceBefore !== undefined && <> · you&apos;ll have {bdt(balanceBefore)}</>}
                  </p>
                </>
              ) : (
                <h2 id="board-head" className="sb-head">
                  <span>Cash holds for 30 days</span>
                </h2>
              )}
            </section>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
              {short && (
                <Link href="/funding" className={buttonVariants({ size: "lg", className: "w-full sm:w-auto" })}>
                  See the fix <ArrowRight className="size-5" aria-hidden />
                </Link>
              )}
              {waiting.loan && (
                <Link href="/funding" className="text-sm font-semibold text-warn hover:underline sm:px-2">
                  Loan applied, waiting for the lender
                </Link>
              )}
              <Link href="/cash" className="inline-flex h-11 items-center justify-center gap-1 font-semibold text-cash hover:underline sm:px-2">
                Cash, day by day <ArrowRight className="size-4" aria-hidden />
              </Link>
            </div>
            <Carton
              tone="ink"
              title="Upcoming money"
              aside={shown.length > 0 ? `${shortDate(shown[0].date)} – ${shortDate(shown[shown.length - 1].date)}` : undefined}
            >
              <CashLine forecast={forecast} />
              <ul className="mt-3 divide-y divide-rule">
                {shown.map((d) => {
                  // The engine's own shortfall for this day, so the row matches the board.
                  const gap = forecast.shortfalls.find((x) => x.date === d.date);
                  const neg = !!gap || d.balance < 0;
                  const amount = dayAmount(d);
                  return (
                    <li key={d.date} className={`grid grid-cols-[64px_1fr_auto] items-center gap-3 py-2.5 ${neg ? "-mx-4 bg-alert-tint px-4" : ""}`}>
                      <span className="font-board leading-tight font-bold text-ink">
                        {shortDate(d.date)}
                        <span className="block text-xs font-semibold text-ink-2">{weekday(d.date)}</span>
                      </span>
                      <span className="min-w-0 truncate text-ink">
                        {dayLabel(d, dues?.items.find((x) => x.due_date === d.date)?.supplier)}
                      </span>
                      <span className="text-right">
                        <span className={`num block font-bold ${amount > 0 ? "text-stock" : "text-ink"}`}>{signed(amount)}</span>
                        {gap && (
                          <span className="num block text-sm font-semibold whitespace-nowrap text-alert">
                            {gap.date === short?.date ? `Short ${num(gap.amount)}` : `${num(gap.amount)} more short`}
                          </span>
                        )}
                      </span>
                    </li>
                  );
                })}
              </ul>
              {moreCount > 0 && last && (
                <Link href="/cash" className="mt-1 flex items-center justify-between gap-2 border-t border-rule pt-3 font-semibold text-cash hover:underline">
                  <span>
                    {moreCount} more to {shortDate(last)}
                  </span>
                  <ArrowRight className="size-4" aria-hidden />
                </Link>
              )}
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
                  <span className="font-semibold">{String(a.payload.summary ?? (a.payload as Record<string, unknown>).reason ?? a.kind.replaceAll("_", " "))}</span>
                  <span className="text-sm text-ink-2"> · {a.proposed_by === "owner" ? "suggested by you" : a.proposed_by === "lamp-scheduler" ? "LaMP follow-up" : "suggested by LaMP"}</span>
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
                <Stamp>All by {stampDate(expiry.batches.reduce((m, b) => (b.expiry_date > m ? b.expiry_date : m), expiry.batches[0].expiry_date))}</Stamp>
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
      <nav aria-label="More" className="carton lg:hidden">
        <ul className="divide-y divide-rule">
          {[
          { href: "/passport", label: "Credit passport", icon: BadgeCheck },
          { href: "/wallet", label: "Wallet", icon: CreditCard },
          { href: "/rules", label: "Rules", icon: ShieldCheck },
          { href: "/lender", label: "Lender view", icon: Landmark },
          { href: "/log", label: "Audit log", icon: ScrollText },
          ].map(({ href, label, icon: Icon }) => (
            <li key={href}>
              <Link href={href} className="flex min-h-12 items-center gap-3 px-4 py-2 text-ink hover:bg-muted">
                <Icon className="size-5 shrink-0 text-ink-2" aria-hidden />
                <span className="min-w-0 flex-1 font-semibold">{label}</span>
                <ChevronRight className="size-5 shrink-0 text-ink-2" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      {asOf && <p className="text-center text-xs text-ink-2 lg:col-span-12">Figures as of {shortDate(asOf)} 2026</p>}
    </div>
  );
}

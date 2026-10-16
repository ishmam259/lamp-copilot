"use client";

import Link from "next/link";
import { ArrowRight, BadgeCheck, Landmark, ScrollText } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { Carton, LoadError, Skel, Stamp } from "@/components/carton";
import { CashStrip } from "@/components/cash-strip";
import { useAccounts, useActions, useAlerts, useDues, useExpiry, useForecast, usePharmacy } from "@/lib/api";
import { bdt, daysBetween, inDays, num, shortDate, stampDate } from "@/lib/format";

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
  const balanceBefore = short && forecast ? forecast.days[forecast.days.findIndex((d) => d.date === short.date) - 1]?.balance : undefined;

  return (
    <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
      <h1 className="sr-only">Today</h1>

      {suspicious && (
        <p role="alert" className="rounded-[var(--radius)] border border-alert/40 bg-alert-tint p-3 font-semibold text-alert lg:col-span-12">
          {suspicious.title}. {suspicious.detail}
        </p>
      )}

      {/* Cash: the first thing the owner reads */}
      <div className="lg:col-span-7">
        {!forecast && !fErr && <Skel className="h-72" />}
        {fErr && <LoadError what="your cash forecast" />}
        {forecast && (
          <Carton
            tone={short ? "alert" : "stock"}
            title={short ? "Cash alert" : "Cash holds"}
            aside={short && asOf ? inDays(daysBetween(asOf, short.date)) : "Next 30 days"}
          >
            {short ? (
              <>
                <p className="num text-[2.5rem] leading-none font-extrabold text-ink lg:text-[3rem]">Short {bdt(short.amount)}</p>
                <p className="mt-2 text-lg text-ink">
                  {short.cause} is due.{" "}
                  {balanceBefore !== undefined && (
                    <>
                      You&apos;ll have about <span className="num font-bold">{bdt(balanceBefore)}</span> that day.
                    </>
                  )}
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Stamp tone="alert">Due {stampDate(short.date)}</Stamp>
                </div>
              </>
            ) : (
              <p className="text-lg text-ink">Your cash stays above zero for the next 30 days.</p>
            )}
            <div className="mt-5">
              <CashStrip forecast={forecast} />
            </div>
            <div className="mt-5 flex flex-col gap-2 sm:flex-row">
              {short && (
                <Link href="/funding" className={buttonVariants({ size: "lg", className: "w-full sm:w-auto" })}>
                  See the fix <ArrowRight className="size-5" aria-hidden />
                </Link>
              )}
              <Link href="/cash" className={buttonVariants({ size: "lg", variant: "outline", className: "w-full sm:w-auto" })}>
                Cash, day by day
              </Link>
            </div>
          </Carton>
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

        {/* Next payments */}
        <Carton tone="cash" title="Next payments" aside={dues ? `${bdt(dues.total_due)} due` : undefined}>
          {!dues ? (
            <Skel className="h-28" />
          ) : (
            <ul className="divide-y divide-rule">
              {dues.items.slice(0, 3).map((d) => (
                <li key={d.invoice_no} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold text-ink">{d.supplier}</p>
                    <Stamp tone={d.status === "overdue" ? "alert" : d.status === "due_soon" ? "warn" : "cash"} className="mt-1">
                      Due {stampDate(d.due_date)}
                    </Stamp>
                  </div>
                  <span className="num text-right text-lg font-bold text-ink">{num(d.amount)}</span>
                </li>
              ))}
            </ul>
          )}
          <Link href="/cash" className="mt-3 inline-flex items-center gap-1 font-semibold text-cash hover:underline">
            All payments <ArrowRight className="size-4" aria-hidden />
          </Link>
        </Carton>

        {/* Expiring stock */}
        <Carton tone="stock" title="Expiring stock" aside="Next 60 days">
          {!expiry ? (
            <Skel className="h-24" />
          ) : (
            <>
              <p className="num text-3xl font-extrabold text-ink">{bdt(expiry.at_risk_value)}</p>
              <p className="mt-1 text-ink">
                {expiry.batches.length} batches. <span className="num font-bold text-stock">{bdt(expiry.return_eligible_value)}</span> can still go back to suppliers.
              </p>
              <div className="mt-2">
                <Stamp tone="stock">EXP ≤ {stampDate(expiry.batches.reduce((m, b) => (b.expiry_date > m ? b.expiry_date : m), expiry.batches[0].expiry_date))}</Stamp>
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

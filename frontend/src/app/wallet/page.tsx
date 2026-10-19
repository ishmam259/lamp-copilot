"use client";

import { Carton, LoadError, PageTitle, Skel, Stamp } from "@/components/carton";
import { useAccount } from "@/lib/api";
import { bdt, num, signed, stampDate } from "@/lib/format";
import type { AccountOut, MatchStatus } from "@/lib/types";

const STATUS: Record<MatchStatus, { label: string; tone?: "alert" | "warn" | "stock" }> = {
  matched: { label: "Matched", tone: "stock" },
  duplicate: { label: "Paid twice", tone: "alert" },
  unmatched: { label: "No bill", tone: "warn" },
  missing_from_statement: { label: "Not on statement", tone: "warn" },
};

const ORDER: MatchStatus[] = ["duplicate", "unmatched", "missing_from_statement", "matched"];

const TXN_KIND: Record<string, string> = { loan_payout: "Loan payout" };

export default function WalletPage() {
  const { data: account, error } = useAccount();
  return (
    <div>
      <PageTitle title="Wallet" sub="Your sandbox wallet, and its statement checked against your books." />
      {error && <LoadError what="your wallet" />}
      {!account && !error && <Skel className="h-96" />}
      {account && <Wallet a={account} />}
    </div>
  );
}

function Wallet({ a }: { a: AccountOut }) {
  const problems = a.matches.filter((m) => m.status !== "matched");
  const rows = [...a.matches].sort((x, y) => ORDER.indexOf(x.status) - ORDER.indexOf(y.status) || x.date.localeCompare(y.date));
  return (
    <div className="space-y-4 lg:grid lg:grid-cols-12 lg:gap-5 lg:space-y-0">
      <div className="space-y-4 lg:col-span-5">
        <Carton tone="cash" title="Balance">
          <p className="num text-[2rem] leading-tight font-bold text-ink">{bdt(a.balance)}</p>
          <p className="text-sm text-ink-2">
            Opening balance <span className="num">{bdt(a.opening_balance)}</span>
          </p>
          {a.transactions.length === 0 ? (
            <p className="mt-3 text-sm text-ink-2">No wallet transactions yet. An approved loan pays out here.</p>
          ) : (
            <ul className="mt-3 divide-y divide-rule border-t border-rule">
              {a.transactions.map((t) => (
                <li key={t.ref} className="flex items-start gap-3 py-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-ink">{TXN_KIND[t.kind] ?? t.kind.replaceAll("_", " ")}</p>
                    <p className="font-board text-xs break-all text-ink-2">{t.ref}</p>
                  </div>
                  <div className="text-right">
                    <p className={`num font-bold ${t.amount >= 0 ? "text-stock" : "text-ink"}`}>{signed(t.amount)}</p>
                    <Stamp>{stampDate(t.date)}</Stamp>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Carton>

        <Carton tone={problems.length ? "warn" : "stock"} title="What to do" aside={problems.length ? `${problems.length} to check` : "All clear"}>
          {a.recommendations.length === 0 ? (
            <p className="text-ink">Every payment on the statement matches a bill in your books.</p>
          ) : (
            <ul className="space-y-2 text-ink">
              {a.recommendations.map((r) => (
                <li key={r} className="flex gap-2">
                  <span aria-hidden className="mt-2 size-1.5 shrink-0 rounded-full bg-warn" />
                  {r}
                </li>
              ))}
            </ul>
          )}
        </Carton>
      </div>

      <div className="lg:col-span-7">
        <Carton
          tone="ink"
          title="Statement vs books"
          aside={ORDER.filter((s) => a.counts[s])
            .map((s) => `${a.counts[s]} ${STATUS[s].label.toLowerCase()}`)
            .join(" · ")}
          bodyClassName="p-0"
        >
          <div className="overflow-x-auto">
            <table className="num w-full text-sm">
              <thead className="text-left text-ink-2">
                <tr className="border-b border-rule">
                  <th className="hidden px-4 py-2 font-semibold sm:table-cell">Date</th>
                  <th className="py-2 pr-2 pl-4 font-semibold sm:pl-2">Paid to</th>
                  <th className="px-2 py-2 text-right font-semibold">Amount</th>
                  <th className="hidden px-4 py-2 font-semibold sm:table-cell">Check</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-rule">
                {rows.map((m) => (
                  <tr key={m.ref} className={m.status === "matched" ? "" : "bg-warn-tint/40"}>
                    <td className="hidden px-4 py-2 whitespace-nowrap text-ink sm:table-cell">{stampDate(m.date)}</td>
                    <td className="py-2 pr-2 pl-4 text-ink sm:pl-2">
                      <span className="block text-xs text-ink-2 sm:hidden">{stampDate(m.date)}</span>
                      {m.supplier ?? m.payee}
                      {m.invoice_no && <span className="whitespace-nowrap text-ink-2"> · {m.invoice_no}</span>}
                      {m.status !== "matched" && <p className="text-xs text-ink-2">{m.note}</p>}
                    </td>
                    <td className="py-2 pr-4 pl-2 text-right align-top font-semibold sm:pr-2 whitespace-nowrap text-ink sm:align-middle">
                      {signed(m.amount)}
                      <span className="mt-1 block sm:hidden">
                        <Stamp tone={STATUS[m.status].tone}>{STATUS[m.status].label}</Stamp>
                      </span>
                    </td>
                    <td className="hidden px-4 py-2 sm:table-cell">
                      <Stamp tone={STATUS[m.status].tone}>{STATUS[m.status].label}</Stamp>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Carton>
        <p className="mt-2 text-sm text-ink-2">Sandbox statement: {num(a.matches.length)} lines. Money out has a minus sign.</p>
      </div>
    </div>
  );
}

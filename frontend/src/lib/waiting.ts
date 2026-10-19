import type { AccountOut, ActionOut } from "./types";

/**
 * What LaMP is waiting on from someone else, and what has already been covered.
 * The owner API has no application status, so a loan application counts as waiting
 * until the wallet shows a payout for it (lenders pay out in the order they decide).
 */
export function waitingOn(actions: ActionOut[] | undefined, account: AccountOut | undefined) {
  const applied = (actions ?? []).filter((a) => a.kind === "loan_application" && a.status === "executed");
  const payouts = account?.transactions.filter((t) => t.kind === "loan_payout").length ?? 0;
  const loan = account && applied.length > payouts ? applied[applied.length - 1] : undefined;
  const extensions = (actions ?? []).filter((a) => a.kind === "extension_request" && a.status === "executed");
  const extension = extensions.find((a) => a.result?.status === "awaiting_supplier");
  // Money that arrived or a due date that moved: an earlier shortfall has been dealt with.
  const covered = payouts > 0 || extensions.some((a) => a.result?.status === "accepted");
  return { loan, extension, covered };
}

/** The action's own one-line summary from the executor, if it wrote one. */
export const resultSummary = (a: ActionOut | undefined): string | undefined =>
  typeof a?.result?.summary === "string" ? a.result.summary : undefined;

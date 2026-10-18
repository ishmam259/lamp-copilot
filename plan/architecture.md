# Architecture delta and decisions (re-plan v3, final)

The base architecture stays as in `docs/PLAN.md` §2: Next.js app → FastAPI → deterministic engines → PostgreSQL, with OpenAI called only from `backend/app/agents/`. This page lists only what the re-plan adds and the decisions behind it, revised after judge rounds 1 and 2. Round 1: authentication added, dev clock dropped, tracing logic moved into the engines, catalogue and shelf-life credit added. Round 2: the session now covers reads, the chat and the log stream; cost disclosure corrected; wallet and reconciliation merged; borrowing-base curve made conditional; deadline moved to Thursday. No new services.

## What changes (new parts in bold)

```
 Browser (owner phone / laptop, lender, admin)
 ┌───────────────────────────────────────────────────────────────┐
 │ Next.js app                                                   │
 │  **PIN unlock → owner session**                               │
 │  Today · Capture (+ **sales-page review**) · Cash · Stock ·   │
 │  Funding (**APR, tenor, cost of gap; catalogue at B**) ·     │
 │  Actions ·                                                    │
 │  Passport · Lender (**shelf-life credit card; curve at C**) · │
 │  **Pause** (rules view at C) · **Value** (B) ·               │
 │  **Reconciliation results**                                   │
 │  Chat drawer: **plan checklist**, **"N of N traced" badge**   │
 │  **Service worker → OS notifications** (owner / admin)        │
 └───────────────┬───────────────────────────────────────────────┘
                 │ REST (**owner session / lender key**) · SSE (log +
                 │ **notify events**) · chat stream
 ┌───────────────▼───────────────────────────────────────────────┐
 │ FastAPI /api/v1   **owner-session dependency (HttpOnly cookie)│
 │   on every /pharmacies/{pid}/* route, /chat and /logs*;       │
 │   lender key on /lenders/***                                  │
 │  agents/chat: read tools + **share_plan** + **get_policy**    │
 │     + propose_action → calls **engines.fidelity** on output   │
 │  engines: accounts · dues · forecast · alerts · expiry ·      │
 │   orders · passport (**+ shelf-life credit**) ·               │
 │   funding (**+ cost disclosure; catalogue at B**) ·           │
 │   lenders · actions · registry ·                              │
 │   **auth** · **policy** (tiers, PIN, cash-flow ceiling,       │
 │   Pause) · **followups** · **wallet** · **reconcile** ·       │
 │   **value** · **fidelity** · logbus (**hash chain**, notify)  │
 │  /dev/* (reset, supplier-reply incl. **"no reply"**)          │
 │        **mounted only when DEV_MODE=true**                    │
 └───────────────┬───────────────────────────────────────────────┘
                 ▼
            PostgreSQL (+ tables: session, followup, wallet_txn,
            statement_line, policy_version; audit_log gains
            prev_hash, hash; lender products gain source, source_date)
```

## New components

| Component | Responsibility | Inputs → outputs | Enforced where | Requirement |
|---|---|---|---|---|
| `engines/auth.py` + a **router-level** dependency | Owner session issued after the PIN (hash in pharmacy settings; test PIN in the seed file), carried in an **HttpOnly cookie** so `EventSource` works; lender keys; caller identity → `proposed_by`; PIN re-entered at Tier-3 approval (re-authentication, not a second factor) | PIN → session cookie; request → caller {owner, lender, agent (in-process), scheduler (in-process)} | **Every `/pharmacies/{pid}/*` route (reads and writes), `POST /chat` (`agents/router.py`, M1's file) and `/logs*`**; lender endpoints need the key and an active consent; `proposed_by` never read from the request | CORE-13 |
| `config.py` / `main.py` changes | `/dev/*` mounted only when `DEV_MODE=true`; no default `registry_key` (startup refuses the placeholder unless `DEV_MODE=true`) | env → routes | App start-up | CORE-13 |
| `engines/policy.py` | Level A: Pause, and which action kinds need the PIN at approval (loan applications). Level C: a cash-flow ceiling **from a sourced norm** (e.g. repayment as a share of projected net cash flow over the tenor) and a read-only rules view; until then the matrix calls the ceiling "designed, not built" | action, amount, context → {approval, allowed, reason} | At propose (Pause) and at approve (PIN) | CORE-08, CORE-13, CORE-07 (C) |
| `engines/followups.py` | Conditional steps of an approved plan; deadline **Thu 22 Oct** (needed_by − 4, D-16) | approved plan → follow-up rows; a supplier outcome ("declined" or "no reply by the deadline") → fallback proposal (`proposed_by="lamp-scheduler"`) + notify event | Deterministic; obeys Pause; survives restarts | CORE-04 (Level A) |
| `engines/wallet.py` + `engines/reconcile.py` (**merged in v3**) | Sandbox account (opening balance = seed `cash_on_hand`; payouts credited at decision time and counted by the forecast) **and** its statement plus ~20 seeded external lines matched to invoices and payments (payee alias, amount, date ±3 days) | executed actions → account transactions; statement → matched / needs review + recommendation | Only executors write; matching is read-only; no new action kind | CORE-05 (Level B) |
| `engines/passport.py` (extended): **shelf-life credit** | The ineligible-inventory rule computed per batch: financeable amount for a need = need − unsellable value of the order it pays for (19,000 − 10,800 = 8,200), with the purpose-blind amount returned as `counterfactual_purpose_blind`. The borrowing-base curve (advance rate × sellable stock value) only at Level C, and only if it binds in the simulation (on Green Life ≈ 137,700 → 130,900, so it never binds) | passport, expiry, trim → {counterfactual_purpose_blind, financeable, not_financed, reason} | Deterministic; new golden numbers appended to PLAN §6 | CORE-11 (A), CORE-11b (C) |
| `engines/funding.py` + `lenders.py` (extended) | **Level A (CORE-15):** each option returns `apr_pct` on the amount financed, `amount_financed`, `tenor_days`, `cost_of_gap_bdt`, `cost_of_gap_pct_of_need` and its horizon (supplier credit: APR 12.2% on 49,200 for 30 days; 492 = 6.0% of the 8,200 gap). **Level B (CORE-14):** 6+ archetypes with source, date, permitted purpose and eligibility reasons | need, history, catalogue → ranked options, "N matched, K eligible" | Terms from the sources; a test reports whether the golden plan still holds; if not, the team decides (D-07) | CORE-15 (A), CORE-14 (B) |
| `engines/value.py` | Value ledger with basis and counterfactual per item | executed actions → items, total | Engine numbers only | CORE-10 |
| `engines/fidelity.py` | Pure function: answer text + this turn's tool outputs → traced / untraced **money figures** (BDT amounts and rates, label-bound); counts and dates reported separately; the funding-plan tool returns the derived values the answer uses (boxes trimmed, extension days, fallback date) | text, outputs → result | Called by `chat.py`; tested on the exact recorded answers | CORE-03 |
| `engines/logbus.py` (extended) | `hash = sha256(prev_hash + canonical event)`; notify events (owner/admin) | events → chained rows, SSE | Every write; `GET /logs/verify`, `scripts/verify_trace.py` | CORE-09, CORE-06 |
| `agents/chat.py` (extended) | Honest "not recorded" reply in replay; `share_plan`; `get_policy`; calls `engines.fidelity`; badge data part | — | Tool list asserted by the security test | CORE-01/02/03 |
| Frontend service worker | OS notifications from notify events; a click deep-links | SSE → `showNotification()` | No notification action approves | CORE-06 |

## Decisions

| ID | Decision | Why | Alternatives rejected |
|---|---|---|---|
| D-01 | Follow-ups are deterministic engine code, not the LLM | "The AI can't act" stays true; reproducible | The agent scheduling its own tasks |
| D-02 | Notifications never carry approval power | A lock screen is not a safe place to spend | Approve buttons in the notification |
| D-03 | Notification text is a template filled with engine numbers | No untraced figure on the lock screen | LLM-written notifications |
| D-04 (v3) | The owner PIN issues the session cookie and is **re-entered at Tier-3 approval**: re-authentication at the point of approval, **not** a second factor (stated in the security report) | Cheapest real identity; honest naming | Calling it step-up 2FA; full OIDC, device binding or OTP (SHOULD-6) |
| D-05 (v3) | Level A policy is code (Pause; PIN for loan approvals). The versioned policy file, the cash-flow ceiling (sourced norm) and the read-only view are Level C | Re-sequenced so the spike lands first | Building the ceiling with a tuned parameter |
| D-06 | Hash chain, not blockchain; anchored by the head hash published outside our database | Tamper evidence without breaking the team rule; the limit is stated (R-20) | Ledger, token or on-chain anchor (team rule) |
| D-07 | New data is additive; existing golden numbers are frozen; new numbers (shelf-life credit, APR and cost-of-gap figures, ledger, reconciliation findings) appended to PLAN §6 and asserted | The deck, video and docs quote them | Re-tuning the seed |
| D-08 | An untraced figure blocks the answer (safe message, log, admin notified) | A money figure not from the engines must never reach the owner | Footnote warnings |
| D-09 | `share_plan` (no-op) and `get_policy` (read) are the only new chat tools; the security test asserts the exact list | Keeps "read-only tools plus propose_action" | A planner sub-agent with tools |
| D-10 | Video chat scenes run live in `record` mode, then replay; unrecorded questions in replay get an honest message | Authentic output, reproducible retakes, no fake-AI impression | The regex script answering silently |
| D-11 (v2) | **No dev clock.** The follow-through is triggered through the existing supplier-reply simulator with a new outcome, "no reply by the deadline"; engines keep `as_of_date` | Screens stay consistent; less attack surface (judge weak 8) | Moving the follow-up date or `as_of_date` |
| D-12 | Reconciliation evidence is shown next to the passport score, not inside θ | Keeps θ = 0.826 | Re-weighting θ now |
| D-13 (v2) | `/dev/*` exists only with `DEV_MODE=true`; the submitted default config has it off; the recording machine turns it on | An ungated reset that drops every table is an obvious finding | Leaving dev routes open |
| D-14 (v2) | The tracing logic lives in `engines/fidelity.py` (M2's folder) and `chat.py` (M1's) only calls it | Pure, testable, and rebalances the work within `CLAUDE.md` ownership | All in `chat.py` |
| D-16 (v3) | Follow-up deadline **Thu 22 Oct** (needed_by − 4) instead of Fri 23 Oct; changes one golden date (the fallback step's `when`), so it is a **team decision** recorded in PLAN §6 | Friday is the weekly holiday; supplier offices and banks are closed | Keeping Friday |
| D-17 (v3) | **Router-level** session dependency instead of per-endpoint checks; HttpOnly cookie | Cheaper than per-write checks and closes reads, chat and the log stream in one place | Per-write checks only (v2) |
| D-18 (v3) | Cost disclosure = APR on the amount financed + tenor + cost of this gap in BDT and as % of the need; tenors stated when they differ | Matches how disclosure rules quote cost; fixes the v2 mislabel | "Effective annual cost on the money needed" (v2) |
| D-15 (v2) | Catalogue rows are archetypes "anchored on" a dated, sourced real offer, never presented as that lender's live terms | Honest; avoids implying partnerships | Unsourced rates |

## Contract changes (engine owner publishes first, at G1)

New schemas and examples in `contracts/examples/` (Level A items first):
- `SessionOut` (sets the HttpOnly cookie) and `ApprovalRequirement` (on `ActionOut`: whether the PIN is needed);
- `ShelfLifeCreditOut`: `counterfactual_purpose_blind`, `financeable`, `not_financed`, `reason` (the curve only at Level C);
- `FundingOption` gains `apr_pct`, `amount_financed`, `tenor_days`, `cost_of_gap_bdt`, `cost_of_gap_pct_of_need` (Level A), and `source`, `source_date`, `permitted_purpose`, `ineligible_reason` (Level B);
- `FollowUpOut`, `VerifyOut`, a `notify` SSE event shape;
- `AccountOut` with statement matches, `ValueOut` (Level B);
- `PolicyOut` (Level C).

Endpoints:
- `POST /pharmacies/{pid}/session` (PIN → cookie);
- `POST /pharmacies/{pid}/pause`;
- `GET /pharmacies/{pid}/followups`, `GET …/shelf-life-credit`;
- `GET …/account` (balance, transactions, statement matches) and `GET …/value` (Level B);
- `GET /logs/verify` (owner session);
- `GET …/policy` (Level C).

Changed:
- Every `/pharmacies/{pid}/*` route, `POST /chat` and `/logs*` need the owner session cookie.
- Lender endpoints need the lender key and an active consent.
- The supplier-reply simulator accepts the outcome `no_reply`.
- `POST …/actions/{aid}/approve` re-asks the PIN for loan applications.
- `proposed_by` is no longer accepted from the request.
- `/dev/*` exists only with `DEV_MODE=true`.

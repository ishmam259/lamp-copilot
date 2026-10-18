# Farhan: Engines & API for the win plan (61% of the product work)

Hi Farhan. The approved win plan (v3, 18 Oct) makes the product's safety story real: the API is closed, the agent follows through on its own plans, every money figure is traced, and the log can't be edited unnoticed. Almost all of that is backend, so you own most of it. Ishmam builds the screens on top of your contract, so **your first job (A0) unblocks him. Do it before anything else.**

Read first, in this order:
1. [../plan-summary.md](../plan-summary.md): the approved plan on one page
2. [../architecture.md](../architecture.md): new components, decisions D-01 to D-18, contract changes
3. [../requirements.md](../requirements.md): acceptance check for every ID below
4. This file

**Your folders:** as in `CLAUDE.md`: `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/schemas/`, `backend/app/db/`, `backend/app/engines/`, `backend/app/api/`, `backend/app/agents/llm.py`, `agents/extraction.py`, `contracts/`, `seed/`, `tests/engines/`, `tests/api/`, `tests/agents/test_llm.py`, `tests/agents/test_extraction.py`, `eval/`, `scripts/`, `logs/`, `docker-compose.yml`, `.env.example`.
**Don't edit:** `agents/chat.py`, `agents/tools.py`, `agents/router.py`, `agents/permissions.py`, `agents/prompts/chat_*.md`, `tests/agents/test_chat.py`, `tests/agents/test_security.py`, `frontend/`, `docs/`.

**Rules:** commit every ~10 minutes and push (`git pull --rebase` first). Plain commit messages like `engines: add follow-ups`. No AI attribution lines. Existing golden numbers stay frozen; new numbers are appended to PLAN §6 (D-07) and asserted in `test_golden.py`.

---

## Your share, broken down

| # | Work item | Plan IDs | Level | Share |
|---|---|---|---|---|
| A0 | **Contract first:** schemas, endpoints and example JSON for every new endpoint | (G1b) | A | 2% |
| A1 | **Close the API:** owner session, lender key, caller identity, PIN at approval, dev routes off, 10 HTTP tests | CORE-13 | A | 9% |
| A2 | Cost disclosure on every funding option | CORE-15 | A | 1% |
| A3 | Pause LaMP | CORE-08 | A | 2% |
| A4 | Hash-chained audit log + verify | CORE-09 | A | 4% |
| A5 | Money-figure tracing function | CORE-03 | A | 6% |
| A6 | Shelf-life credit figures | CORE-11 | A | 2% |
| A7 | Follow-through: the agent's plan acts on its own fallback | CORE-04 | A | 6% |
| A8 | Notify events on the SSE stream | CORE-06 | A | 1% |
| B1 | Sourced financing catalogue | CORE-14 | B | 6% |
| B2 | Sandbox wallet + statement reconciliation | CORE-05 | B | 11% |
| B3 | Value ledger | CORE-10 | B | 3% |
| C1 | Consent scopes enforced for lenders | CORE-16 | C | 4% |
| C2 | Cash-flow borrowing ceiling | CORE-07 | C | 4% |
| | **Total** | | | **61%** (≈ 21 of ≈ 35 product hours) |

Order: A0 → A1 → A2 … A8, then B, then C. All of Level A must land; B and C follow in order.

---

## Tech choices

- Same stack: FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL, pytest + `TestClient`.
- **Session:** a FastAPI dependency at **router level** (D-17), reading an **HttpOnly cookie**, so the browser's `EventSource` on `/logs/stream` keeps working. Sessions in a new `session` table (random token, pharmacy id, role, expiry).
- **PIN:** hashed in pharmacy settings (`hashlib.scrypt` or `pbkdf2_hmac`, salt per pharmacy); the test PIN goes in the seed file only.
- **Log hashing:** `hashlib.sha256` over canonical JSON of the event (`sort_keys=True`, no whitespace).
- No new services. No LLM calls in engines.

---

## A0: Contract first (by 19 Oct, 09:00 BDT)

Publish in `contracts/examples/` and `backend/app/schemas/`, then tell Ishmam in the group chat with the commit hash:
- `SessionOut` (sets the cookie) and `ApprovalRequirement` on `ActionOut` (whether the PIN is needed)
- `FundingOption` gains `apr_pct`, `amount_financed`, `tenor_days`, `cost_of_gap_bdt`, `cost_of_gap_pct_of_need`
- `ShelfLifeCreditOut`: `counterfactual_purpose_blind`, `financeable`, `not_financed`, `reason`
- `FollowUpOut`, `VerifyOut`, and the `notify` SSE event shape
- Level B shapes when you reach them: `AccountOut` (balance, transactions, statement matches), `ValueOut`, catalogue fields `source`, `source_date`, `permitted_purpose`, `ineligible_reason`

Endpoints: `POST /pharmacies/{pid}/session` · `POST /pharmacies/{pid}/pause` · `GET …/followups` · `GET …/shelf-life-credit` · `GET /logs/verify` · Level B: `GET …/account`, `GET …/value`. Re-export `contracts/openapi.json`.

---

## A1: Close the API (CORE-13), the most important item

Today anyone can approve a loan or wipe the database with one HTTP call. Fix all of it in one place:
- **Owner session:** `POST /pharmacies/{pid}/session {pin}` sets an HttpOnly cookie. A router-level dependency requires it on **every** `/pharmacies/{pid}/*` route (reads **and** writes) and on `/logs*`. Ishmam adds the same check to `POST /chat` in `agents/router.py`; give him the dependency to import.
- **Lender key:** lender endpoints need `X-Lender-Key`; lenders see a pharmacy only through their own endpoints and only with an active consent.
- **Caller identity:** `proposed_by` is never read from the request. Owner session → `"owner"`; the chat's in-process call → `"agent"`; the follow-up runner → `"lamp-scheduler"`.
- **PIN at approval:** `POST …/actions/{aid}/approve` re-asks the PIN for loan applications (Tier 3). It's re-authentication, not a second factor (D-04).
- **Dev routes:** `/dev/*` mounted only when `DEV_MODE=true`. No default `registry_key`: startup refuses the placeholder unless `DEV_MODE=true`.
- **Tests (`tests/api/test_auth.py`), the 10 direct-HTTP cases:**
  1. passport without a session → 401
  2. lender key on an owner read → 403
  3. chat without a session → 401 (once Ishmam's part lands)
  4. log stream without a session → 401
  5. approve without a session → 401
  6. approve with a lender key → 403
  7. consent without a session → 401
  8. lender decide without a key → 401
  9. `/dev/reset` with `DEV_MODE=false` → 404
  10. spoofed `proposed_by` → recorded as the real caller
- Update the existing API tests and `scripts/demo_run.py` to log in first.

---

## A2: Cost disclosure (CORE-15)

Every funding option returns, from the engine:
- `apr_pct` on the **amount actually financed**, `amount_financed`, `tenor_days`
- `cost_of_gap_bdt` and `cost_of_gap_pct_of_need`: what covering this gap costs
- **Golden:** supplier credit: APR 12.2% on 49,200 for 30 days; covering the 8,200 gap costs 492 = 6.0% of the gap for 30 days. Wallet loan: APR 9% on 8,200 for 90 days; 181.97 = 2.2% of the gap over 90 days.
- No "effective annual cost" label anywhere. Different tenors are stated, not hidden.

---

## A3: Pause LaMP (CORE-08)

- `POST /pharmacies/{pid}/pause {paused: true|false}` (owner session).
- While paused: agent and scheduler proposals are refused, and agent-proposed actions can't be approved. Log `agent_paused` / `agent_resumed`.
- The chat can read the state but can't change it.

---

## A4: Hash-chained audit log (CORE-09)

- `audit_log` gains `prev_hash` and `hash`; `hash = sha256(prev_hash + canonical_event)`. The first row uses a fixed genesis value.
- `GET /logs/verify` (owner session) → `{intact, count, head_hash, first_bad_id}`.
- `scripts/verify_trace.py logs/sandbox_execution_trace.log` checks an exported trace the same way; the export carries the hashes.
- **Done when:** changing one character in one event fails verification at exactly that line.

---

## A5: Money-figure tracing (CORE-03)

Pure function in `engines/fidelity.py`; Ishmam's `chat.py` calls it on every answer:
- Input: the answer text and this turn's tool outputs. Output: traced and untraced **money figures** (BDT amounts and rates), each bound to the label next to it ("cost", "APR", "shortfall"…). Counts and dates are reported separately, never blocked.
- The funding-plan tool also returns its derived values (18 boxes trimmed, 20 extension days, the fallback date), so those count as engine outputs too.
- **Tests:** the guard passes the exact recorded demo answers, and fails a variant that attaches 421.64 to the wrong option.

---

## A6: Shelf-life credit (CORE-11)

The ineligible-inventory rule, computed per batch from the photographed invoices before the purchase:
- `GET …/shelf-life-credit` → `counterfactual_purpose_blind` = 19,000 (a lender who ignores the shelf), `not_financed` = 10,800 (stock in the order that won't sell before expiry), `financeable` = 8,200, plus `reason`.
- All from existing engines (forecast, expiry, trim). Append the three numbers to PLAN §6 (ask Ishmam, it's his file) and assert them in `test_golden.py`.

---

## A7: Follow-through (CORE-04)

The agent's plan keeps working after the owner approves it:
- Approving a plan with a fallback stores a row in a new `followup` table (`engines/followups.py`), deadline **Thu 22 Oct** (needed_by − 4; D-16, because Friday is the weekly holiday). This changes one golden date, so confirm with Ishmam first.
- The supplier-reply simulator gains a `no_reply` outcome. On `declined` or `no_reply`, the runner creates the fallback proposal (wallet loan 8,200, cost 181.97) with `proposed_by="lamp-scheduler"` and one notify event.
- Engines keep `as_of_date` (no dev clock, D-11). The runner obeys Pause and survives a restart.
- `GET …/followups` lists them with status.

---

## A8: Notify events (CORE-06, backend part)

- `logbus` emits `notify` events on the SSE stream: `{audience: "owner"|"admin", title, body, link}`.
- Text is a template filled with engine numbers only (D-03). Notifications never carry approval power (D-02).
- Emit for: a follow-up firing (owner), an untraced chat answer blocked (admin), a suspicious photo (owner).

---

## B1: Sourced financing catalogue (CORE-14)

- At least 6 product archetypes, each anchored on a dated, sourced Bangladeshi offer: `source`, `source_date`, `permitted_purpose`, eligibility rules and the A2 disclosure.
- The funding planner reports "N matched, K eligible, cheapest first" and why each other option doesn't fit (`ineligible_reason`).
- **Terms come from the sources, never tuned to protect the golden plan.** A test reports whether the golden plan still holds; if not, the team decides (D-07).

---

## B2: Sandbox wallet + reconciliation (CORE-05)

- `engines/wallet.py`: a sandbox account (opening balance = seed `cash_on_hand`). Payouts are credited when the lender decides, and the forecast counts them.
- `engines/reconcile.py`: the account statement plus ~20 seeded external lines, matched to invoices and payments (payee alias, amount, date ±3 days) → matched / needs review (duplicate, unmatched, missing deposit), with a recommendation line.
- `GET …/account` → balance, transactions, matches. No new action kind.
- **Done when:** the payout adds 8,200 and the board flips to "Cash holds"; exactly the one seeded duplicate payment is found; golden tests still pass.

---

## B3: Value ledger (CORE-10)

- `engines/value.py`, `GET …/value`: one line per executed action with its basis and counterfactual: return claim 9,200 · stock not bought that would expire 10,800 · interest saved 239.67 (421.64 − 181.97).
- Totals from engine numbers only.

---

## C1: Consent scopes (CORE-16)

- Lender endpoints return only the fields in the consented scopes (for example `passport.summary` vs `passport.evidence`).
- An endpoint for the "what this lender will see" preview Ishmam shows.

## C2: Cash-flow borrowing ceiling (CORE-07)

- In `engines/policy.py`: loan proposals above a ceiling are refused. The ceiling comes from a **sourced** responsible-lending norm (for example repayment as a share of projected net cash flow over the tenor), not a number tuned to keep 8,200 eligible.
- If no source is found, don't build it.

---

## Done means
- [ ] A0 contract published and announced before Ishmam starts the new screens
- [ ] All 10 direct-HTTP cases pass; the demo script and existing tests log in
- [ ] Every funding option shows APR, tenor and cost of the gap; golden figures asserted
- [ ] Pause blocks agent and scheduler proposals
- [ ] `GET /logs/verify` and `verify_trace.py` catch a one-character edit
- [ ] Tracing passes the recorded demo answers and fails the wrong-option variant
- [ ] Shelf-life credit returns 19,000 / 10,800 / 8,200, asserted in `test_golden.py`
- [ ] "No reply by Thu 22 Oct" → one wallet-loan proposal (181.97) and one notify event
- [ ] Level B: catalogue ≥ 6 sourced options; wallet payout and the seeded duplicate found; value ledger totals match
- [ ] `pytest` green, including every golden number

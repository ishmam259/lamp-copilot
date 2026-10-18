# Farhan: Engines & API, plus photo reading (49% of the project)

Hi Farhan. You own the backbone: the database, the deterministic money logic, the REST API, the seed pharmacy, tests and Docker. The other two build on your contract, so **your first job (M1) unblocks everyone. Do it before anything else.**

Read first, in this order:
1. [../IDEA_AND_PROBLEM.md](../IDEA_AND_PROBLEM.md): what we're building and why (15 minutes, worth it)
2. [../PLAN.md](../PLAN.md): architecture, contract, golden numbers, rules
3. This file

**Your folders:** `backend/pyproject.toml`, `backend/app/main.py`, `backend/app/config.py`, `backend/app/schemas/`, `backend/app/db/`, `backend/app/engines/`, `backend/app/api/`, `contracts/`, `seed/` (now including `seed/images/`), `tests/engines/`, `tests/api/`, `scripts/`, `logs/`, `docker-compose.yml`, `.env.example`, the "Run it" section of `README.md`, and from Pritom's part: `backend/app/agents/__init__.py`, `agents/llm.py`, `agents/extraction.py`, `agents/prompts/extraction_*.md`, `tests/agents/test_llm.py`, `tests/agents/test_extraction.py`, `eval/`.
**Don't edit:** `agents/chat.py`, `agents/tools.py`, `agents/router.py`, `agents/permissions.py`, `agents/prompts/chat_*.md`, `tests/agents/test_chat.py`, `tests/agents/test_security.py`, `docs/`, `frontend/`, `deck/`, `video/`.

**Rules:** commit every ~10 minutes and push (`git pull --rebase` first). Plain commit messages like `engines: add forecast`. No AI attribution lines.

---

## Your share, broken down

| # | Work item | Share |
|---|---|---|
| F1 | **M1 contract:** schemas, stub endpoints, example JSON, OpenAPI export, Docker skeleton | 8% (with F0 seed shape) |
| F2 | Accounts, dues calendar, 30-day forecast, alerts | 8% |
| F3 | Expiry engine, sales-rate inference, order trimming | 6% |
| F4 | Credit passport and funding planner | 6% |
| F5 | Duplicate-financing registry, actions + approvals + sandbox executor, audit log + SSE | 4% |
| F6 | Tests, Docker Compose, README run section, demo script, trace export | 2% |
| F7 | *(from Pritom's P1)* LLM client: OpenAI Responses API, live/record/replay modes, budget guard, image resizing | (inside F8) |
| F8 | *(from P2)* Photo extraction: invoices and sales-book pages, checks, confidence | 10% |
| F9 | *(from P4)* Image-injection defence and its test | 2% |
| F10 | *(from P5)* Evaluation set, accuracy table, demo photos | 3% |
| | **Total** | **49%** |

---

## Tech choices

- **Python 3.12** (use 3.12 in Docker even if your machine has a newer one)
- FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync is fine), `psycopg[binary]`, uvicorn
- SciPy (`scipy.stats.beta.ppf`) for the passport math
- pytest + FastAPI `TestClient`
- PostgreSQL 16 in Docker Compose
- SSE: FastAPI `StreamingResponse` with `text/event-stream`, or `sse-starlette`
- **LLM calls only in `backend/app/agents/`.** Your engines and API never call OpenAI; your new `agents/llm.py` and `agents/extraction.py` are the only code of yours that does.

---

## F1: M1 contract first (deadline 16 Oct, 23:59 Bangladesh time)

Goal: Pritom and @ishmam259 can build against real shapes within hours.

1. `backend/pyproject.toml`, `backend/app/main.py` (FastAPI app, `/api/v1` prefix, CORS for `http://localhost:3000`), `config.py` (reads `.env`).
2. `backend/app/schemas/`: every model in PLAN section 4.3, exactly those field names. Split by area: `accounts.py`, `cash.py`, `expiry.py`, `orders.py`, `funding.py`, `passport.py`, `actions.py`, `captures.py`, `logs.py`, `lenders.py`.
3. **Stub endpoints** for every row in PLAN section 4.1. Each returns a hand-written example that already uses the golden numbers, so the UI shows real-looking data from minute one.
4. `contracts/examples/<endpoint>.json`: the same examples as files (Ishmam's mock layer reads them). `contracts/openapi.json`: export with a small script `scripts/export_openapi.py`.
5. **Stub `agents` interface** so you aren't blocked by Pritom. If `app.agents.extraction` can't be imported, fall back to returning `contracts/examples/capture_invoice.json`. Mount `app.agents.router.router` if it exists.
6. `docker-compose.yml`: `db` (postgres:16), `backend` (uvicorn on 8000), `frontend` (Next.js on 3000, can be added later by Ishmam's Dockerfile). `.env.example` stays the source of truth for variables.
7. Post in the group chat: "M1 done", with the commit hash.

---

## F0 + F2: Seed pharmacy and core accounts

### The fixed "today"
**Engines must never use the real clock.** Each pharmacy has `settings.as_of_date = "2026-10-16"` and every calculation is relative to it. That keeps golden numbers stable whenever the demo is run.

### Seed design (`seed/green_life.json`)
Build the seed so the golden numbers in PLAN section 6 come out exactly. Suggested shape:
- `pharmacy`: id `green-life`, name "Green Life Pharmacy", city "Bogura", settings `{gross_margin_pct: 12, cash_buffer: 0, expiry_buffer_days: 30, as_of_date: "2026-10-16"}`.
- **23 suppliers** with at least one invoice in the last 90 days. Name them generically ("Supplier A", "Supplier B", …, or neutral made-up company names; **don't use real company names**). Give each a `return_cutoff_days`.
- **41 invoices** in the 90 days before `as_of_date`, with payments: 38 paid on or before the due date, 3 late. All `supplier_confirmed: true`.
- **30 `sales_day` rows** summing to cash + credit sales = 412,500.
- **Expenses** in the last 30 days summing to 36,000 (for example rent 18,000, salaries 15,000, utilities 3,000), plus `expense_schedule` rows so the forecast knows when they recur.
- **Stock batches** with total cost value 210,000. Among them: 6 batches expiring within 60 days, total cost 18,400, of which 9,200 is return-eligible (days_left ≥ that supplier's `return_cutoff_days`).
- **Patient dues** totalling 38,000. Labels like "Customer 014". No medicine names.
- **Planned order** from Supplier A due `as_of + 10` days, total 60,000, including the slow-mover line (30 boxes × 600, expiry 90 days after `as_of`). Its past invoices should show about 0.2 boxes/day: for example 6 boxes bought every 30 days over 90 days, so 18 boxes / 90 days = 0.2/day.
- **Starting cash and flows** chosen so the forecast balance on `as_of + 10`, before paying the order, is exactly 41,000.
- **Lenders and products** (all simulated):
  - "Wallet Lender" mobile-wallet loan: 500–30,000, 9% a year, 90 days, cost borne by the pharmacy
  - "Partner Bank" supplier credit: 1% per 30 days on the order total, minimum 10 invoices of history
  - "Partner Bank" small-business loan: minimum 200,000, 12+ months of history

### Demo captures
During the demo, the owner photographs 2 invoices and 1 sales-book page. **Golden numbers hold after those three are confirmed.**
- Put their exact content in `seed/demo_captures/*.json`. You now also make the photos matching them (F10).
- `POST /dev/reset?with_demo_captures=true` loads the seed plus the confirmed demo captures (used by tests and by the scripted run).
- `POST /dev/reset` loads only the seed (used before a live demo, where the owner captures them).

### Engine formulas (F2)
Use `as_of_date` and a 30-day window unless noted.
- `sales` = Σ (cash_sales + credit_sales)
- `gross_profit` = sales × gross_margin_pct; `overheads` = Σ expenses; `net_profit` = gross_profit − overheads
- `cogs_30` = sales × (1 − margin) = 363,000; `stock_days` = stock_value / (cogs_30 / 30), rounded to 1 decimal → 17.4
- `patient_due_days` = patient_dues / (sales / 30) → 2.8
- `active_suppliers` = suppliers with an invoice in the last 90 days → 23
- `top_suppliers` = share of last-90-day purchases
- `slow_movers` = products whose sellable_qty < qty held (uses F3)
- `expiring_value_60d` = from F3 → 18,400

**Dues calendar:** unpaid invoices sorted by due date; `status` = `overdue`, `due_soon` (≤ 7 days) or `upcoming`.

**30-day forecast**, day by day from `as_of_date`:
- Inflow: average daily cash receipts = avg(cash_sales + dues_collected) over the last 30 days
- Outflows:
  - routine restock at average daily cost of sales
  - each unpaid supplier invoice on its due date
  - scheduled expenses on their day of month
  - planned orders on their due date
- `shortfalls`: each day where balance before an outflow would drop below `cash_buffer`. Record the amount and cause (e.g. "Supplier A order 60,000"). **Golden: the first shortfall is 19,000 on `as_of + 10`.**

**Alerts** (generated, not stored, unless simple to store):
- `shortfall` (from forecast)
- `expiry` (batches ≤ 60 days)
- `return_window` (eligible batches whose cutoff is ≤ 14 days away)
- `patient_dues` (any due older than 30 days)
- `suspicious_document` (when a capture has `suspicious_text`)

---

## F3: Expiry and order trimming

- **Sales rate per product:** total qty purchased in the last 90 days ÷ 90. This assumes stock levels are roughly stable; write that assumption in a docstring, because it goes into the technical doc.
- `sellable_days` = days_to_expiry − `expiry_buffer_days` (30), minimum 0.
- `sellable_qty` = floor(min(qty, rate × sellable_days)).
- `at_risk_value` = (qty − sellable_qty) × unit_cost.
- **Trim suggestion:** `suggested_qty` = sellable_qty for any line with at-risk value > 0. **Golden:** slow mover 30 → 12, at risk 10,800; order 60,000 → 49,200.
- **Expiry view:** batches with days_left ≤ horizon; `return_eligible` = days_left ≥ supplier.return_cutoff_days; totals 18,400 and 9,200.

---

## F4: Credit passport and funding planner

### Passport
- Use the invoices of the last 90 days. Weight is 1.0 if `supplier_confirmed`, otherwise 0.5. `s` = weighted on-time count, `f` = weighted late count.
- Posterior: Beta(1 + s, 1 + f). `theta_mean` = (1+s)/(2+s+f). `theta_low_5pct` = `scipy.stats.beta.ppf(0.05, 1+s, 1+f)` → **0.826** for Beta(39, 4).
- **Default probability** (placeholder lender model; the doc says so):
  `p = 1 / (1 + exp(-(-3.915 + 6.0 * late_share)))`, where `late_share = f / (s + f)`. For 3/41 this gives **0.030**.
- `score` = clip((theta_low − 0.50) / 0.45, 0, 1) × max(0, 1 − p / 0.10) → **0.507**
- `advance_rate_pct` = 60 + 30 × score → **75.2**; `partner_share_pct` = 100 − 90 × score → **54.4**
- `evidence` = list of invoice ids, dates, on-time flags and confirmed flags.

### Funding planner
Input: a need `{amount, needed_by}`. Default: the first forecast shortfall *after* applying suggested trims → 8,200 on `as_of + 10`.

Build these options:
| key | How | Eligible when | Cost |
|---|---|---|---|
| `trim_order` | from F3 | at-risk value > 0 | 0 (it reduces the need) |
| `return_claims` | from F3 | return-eligible value > 0 | 0; arrives as supplier credit, **not counted as cash before `needed_by`** |
| `supplier_extension` | ask the order's supplier for more days | supplier verified and on-time share ≥ 0.85 | 0; `certainty: "uncertain"` |
| `wallet_loan` | Wallet Lender | amount within 500–30,000 | amount × 0.09 × 90/365 → **181.97** for 8,200 |
| `bank_supplier_credit` | Partner Bank | ≥ 10 invoices of history | 1% × order total per 30 days → **492.00** on 49,200 |
| `bank_sme_loan` | Partner Bank | amount ≥ 200,000 and 12 months of history | — (**ineligible** here; give the reason) |

- **Plan rule:** cheapest certain-enough path. Free options first; if the cheapest is uncertain, add the cheapest certain option as a **fallback** with `when = needed_by − 3 days`.
- **Golden plan:** `trim_order` → `supplier_extension` → fallback `wallet_loan` 8,200 on `as_of + 7`. `total_cost_bdt` = 0 if the extension is accepted, else 181.97.
- `naive_cost_bdt` = wallet-loan cost on the *untrimmed* shortfall (19,000) → **421.64**.

---

## F5: Registry, actions, audit log

### Duplicate-financing registry
- `commitment` = hex HMAC-SHA256(`REGISTRY_KEY` from env, `"{supplier_id}|{invoice_no}|{pharmacy_id}|{total:.2f}|{invoice_date}"`).
- Lock = `INSERT INTO registry_lock ... ON CONFLICT (commitment) DO NOTHING RETURNING id`. No row back means already locked: the action fails with reason `duplicate_financing` and a log event.
- Lock when a `loan_application` or `bank_supplier_credit` action executes, for every invoice it finances.

### Actions (the only way anything "happens")
- States: `proposed → approved → executed` (or `failed`), or `proposed → rejected`.
- `proposed_by`: `"owner"` (UI button) or `"agent"` (the copilot chat). **Only the HTTP approve endpoint can approve. There is no Python function for the agent to approve.**
- The executor is deterministic and sandbox-only. On approve:
  - `trim_order`: update the planned order lines.
  - `return_claim`: create a claim record; result `{claim_id, expected_credit}`.
  - `extension_request`: status `executed`, result `{status: "awaiting_supplier"}`. Add `POST /dev/simulate/supplier-reply {action_id, accepted}` for the demo.
  - `loan_application`: requires an active consent for that lender, then the registry lock, then creates an `application` visible in the lender inbox.
  - `set_aside`: store a schedule.
- **Lender decide** (simulated rule): approve if `default_probability ≤ 0.05` and the amount is within limits; payout = sandbox reference string `SANDBOX-<LENDER>-<date>-<n>`.

### Audit log and live stream
- `engines/logbus.py`: `log(tier, component, event, **data)` writes to `audit_log` and pushes to an in-memory queue for SSE subscribers.
- Tiers:
  - T0 regulator/read-only views
  - T1 owner and extraction
  - T2 engines
  - T3 lender and financial execution
- Log every endpoint that changes state, every action transition, every registry lock or rejection, and every capture (including suspicious-text flags).
- Text format for export, one line per event:
  `[2026-10-16T14:05:00Z] [T3:REGISTRY] lock_acquired commitment=8f9c… application=APP-0001`

---

## F6: Tests, Docker, README, demo script, trace export

- `tests/engines/test_golden.py`: load seed + demo captures and assert **every** golden number (PLAN section 6). This is the most important test in the project.
- `tests/engines/`: unit tests per engine (edge cases: no history, zero sales, expired batches, empty orders).
- `tests/api/`: TestClient round trips per endpoint; approval flow; consent required; **registry race** (two threads lock the same commitment, exactly one wins).
- `scripts/demo_run.py`: calls the API in demo order (reset → confirm captures → accounts → expiry → propose and approve return claims → trim → funding plan → approve extension and fallback → consent → loan application → lender decide → log export). Deterministic, and uses replay mode for any agent call.
- `scripts/export_trace.py` → `logs/sandbox_execution_trace.log` (**submission item 6**).
- `README.md`: write the "Run it" section (`cp .env.example .env`, `docker compose up`, URLs, how to run tests, how to run the demo script, replay vs live mode).

---

## F7–F10: Pritom's AI work, now yours

Pritom left on 17 Oct. The full spec is in [pritom-agents-docs.md](pritom-agents-docs.md): read P1, P2, P4 and P5 there. Your capture endpoint already falls back to a stored draft when `app.agents.extraction` is missing, so nothing breaks while you build.

| # | What | Spec | Latest by (BDT) |
|---|---|---|---|
| F7 | `agents/llm.py`: `LLM_MODE` live/record/replay, sha256 cache key, recordings in `eval/replay/`, budget guard writing `eval/spend.log` and refusing live calls past `LLM_DAILY_BUDGET_USD`, EXIF fix + resize to 1,600 px + JPEG 85 + strip metadata. Add `openai`, `pillow` and `pydantic-ai` to `pyproject.toml` (the chat needs `pydantic-ai`). | P1 | 18 Oct, 12:00 |
| F8 | `agents/extraction.py`: `extract(image, kind) -> ExtractionResult` with structured output, plain-code checks, confidence 0.95 / 0.5 / 0.3, prompt in `agents/prompts/extraction_v1.md` | P2 | 18 Oct, 23:59 |
| F9 | Regex screen + model flag for instruction-like text; matches removed from fields, listed in `suspicious_text`, logged. Test with an injection image: flagged, alert raised, no action created, normal fields still read. | P4 item 1 | 18 Oct, 23:59 |
| F10 | `seed/images/`: 2 invoices + 1 sales page that extract to exactly `seed/demo_captures/*.json`, plus 1 injection invoice. `eval/`: 20–30 photos with ground truth and `eval/run_eval.py` (record once, then replay). Send the results table and total spend to @ishmam259 for the technical doc. | P5 | 19 Oct, 18:00 |

**Interface for the chat:** @ishmam259 builds the chat on PydanticAI. Expose a small helper in `llm.py` that records a live call's cost in `eval/spend.log` and says whether today's budget allows another live call, and tell @ishmam259 its name.

**Budget:** the team limit is still $20. Record the demo photos and the eval set once in `record` mode; everything after that runs in `replay`.

## Done means
- [x] M1 posted to the group by 16 Oct 23:59 BDT
- [x] `pytest` green, including `test_golden.py`
- [x] `docker compose up` brings up db + backend (+ frontend once Ishmam adds it) on a clean machine
- [x] `scripts/demo_run.py` runs end to end and exports `logs/sandbox_execution_trace.log`
- [ ] README "Run it" works for a judge who has never seen the project
- [x] Every engine function has a docstring stating its formula and assumptions (they are quoted in the technical doc)
- [x] `extract()` works live on the demo photos, and replay recordings are committed
- [x] `pytest tests/agents/test_llm.py tests/agents/test_extraction.py` passes with no API key set
- [x] The injection photo is flagged, raises an alert and creates no action
- [x] Eval table and total live spend sent to @ishmam259 by 19 Oct 18:00 BDT

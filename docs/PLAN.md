# LaMP-Copilot: master build plan

Everyone reads this. Read [IDEA_AND_PROBLEM.md](IDEA_AND_PROBLEM.md) first for what we're building and why. Your own detailed task list is in [docs/tasks/](tasks/).

| Person | Part | Share of total work | Task file |
|---|---|---|---|
| **Farhan** | Engines & API, plus LLM client, photo reading and evaluation | 49% | [tasks/farhan-engines-api.md](tasks/farhan-engines-api.md) |
| **@ishmam259** (team lead) | Frontend & pitch, plus copilot chat, permissions and documents | 51% | [tasks/ishmam259-frontend-pitch.md](tasks/ishmam259-frontend-pitch.md) |

**Pritom left the team on 17 Oct 2026.** His AI work (P1–P6) is split between the two of us; the original spec stays in [tasks/pritom-agents-docs.md](tasks/pritom-agents-docs.md), and each task file says which parts are yours.

**Hard deadline: 20 Oct 2026, 23:59 Beijing time = 21:59 Bangladesh time.** Our internal freeze is **20 Oct, 18:00 Bangladesh time**, leaving time to submit calmly.

---

## 1. Team rules

1. **Commit every ~10 minutes and push each time.** Small commits, never a day's work in one. Before every push: `git pull --rebase`.
2. **Work only in your own folders** (table in section 3). If you need a change in someone else's folder, ask them in the group chat; don't edit it yourself. `eval/replay/` holds recordings from both people's code; never edit them by hand.
3. **Everyone commits to `main`.** Folder ownership keeps us out of each other's way, so no branches or pull requests are needed. If a rebase conflict ever happens, stop and ask.
4. **Commit messages are plain and human:** `engines: add forecast shortfall detection`, `frontend: funding plan table`. No "Co-Authored-By" or AI attribution lines. Your Claude Code sessions are told this in [CLAUDE.md](../CLAUDE.md).
5. **Never commit secrets.** The OpenAI key lives only in `.env`, which git ignores.
6. **The contract is shared law.** Once `contracts/` and `backend/app/schemas/` are frozen (milestone M1), changes need a message to the whole team first.
7. **The golden numbers (section 6) must match everywhere:** engine output, tests, UI, deck, video and docs.

---

## 2. Architecture

```
            Phone / laptop browser
   ┌──────────────────────────────────────────┐
   │ Next.js app (frontend/)                  │
   │  Owner views · Lender view · Live log    │
   │  Chat drawer (AI SDK useChat)            │
   └───────────────┬──────────────────────────┘
                   │ REST JSON + SSE + chat stream
   ┌───────────────▼──────────────────────────┐
   │ FastAPI (backend/app/main.py)            │
   │                                          │
   │  api/ (Farhan)        agents/ (both)     │
   │   REST routers  ◄────  extraction        │
   │        │               chat orchestrator │
   │        ▼                    │ tools      │
   │  engines/ (Farhan) ◄────────┘ (read-only │
   │   accounts · dues · forecast · expiry    │
   │   orders · credit · funding · registry   │
   │   actions · logbus                       │
   │        │                                 │
   └────────┼─────────────────────────────────┘
            ▼
       PostgreSQL            OpenAI Responses API
       (db/, seed/)          (gpt-6-luna, called only from agents/)
```

**Key design rules:**
- **All money math is in `engines/`**, which is plain Python and deterministic. The LLM never computes money.
- **The LLM is called only from `agents/`.** Its two jobs: read photos into structured data, and run the chat.
- **The chat agent's tools are read-only, plus `propose_action`.** The agent can't approve or execute anything. Only the owner can, through the app (`POST /actions/{id}/approve`), and then `engines/actions.py` executes deterministically in the sandbox.
- **Every important event goes to `logbus`.** It's stored in `audit_log` and streamed to the UI by Server-Sent Events. This is our execution evidence.

---

## 3. Repo layout and ownership

```
lamp-copilot/
├── CLAUDE.md                      team rules for Claude Code sessions   (@ishmam259)
├── README.md                      overview + run instructions           (Farhan writes run section)
├── docker-compose.yml             postgres + backend + frontend         (Farhan)
├── .env.example                                                        (Farhan)
├── contracts/
│   ├── openapi.json               exported from FastAPI                 (Farhan)
│   └── examples/*.json            one sample response per endpoint      (Farhan)
├── seed/
│   ├── green_life.json            the demo pharmacy                     (Farhan)
│   └── images/                    demo photos (invoices, sales pages)   (Farhan)
├── backend/
│   ├── pyproject.toml                                                  (Farhan)
│   └── app/
│       ├── main.py  config.py                                          (Farhan)
│       ├── schemas/               shared Pydantic models (the contract) (Farhan)
│       ├── db/                    SQLAlchemy models, session, seed load (Farhan)
│       ├── engines/               deterministic money logic             (Farhan)
│       ├── api/                   REST routers                          (Farhan)
│       └── agents/                llm + extraction (Farhan); chat, tools, router, permissions (@ishmam259)
├── tests/
│   ├── engines/  api/                                                  (Farhan)
│   └── agents/                    test_llm, test_extraction (Farhan); test_chat, test_security (@ishmam259)
├── eval/                          photo test set + accuracy script      (Farhan)
├── logs/                          exported sandbox trace for submission (Farhan)
├── docs/
│   ├── IDEA_AND_PROBLEM.md  PLAN.md  tasks/  LaMP_Idea_Brief.md        (@ishmam259)
│   ├── technical/                 technical documentation (item 1)      (@ishmam259)
│   └── security/                  security self-assessment (item 5)     (@ishmam259)
├── frontend/                      Next.js app                           (@ishmam259)
├── deck/                          10-minute presentation (item 2)       (@ishmam259)
└── video/                         demo video script + link (item 3)     (@ishmam259)
```

---

## 4. The contract

Farhan turns this into real code first (milestone M1): Pydantic models in `backend/app/schemas/`, stub endpoints returning the example JSON, and `contracts/openapi.json` plus `contracts/examples/`. Everyone else builds against it immediately.

All endpoints are under `/api/v1`. Money is in BDT, as numbers with 2 decimals. Dates are ISO `YYYY-MM-DD`; timestamps are ISO UTC. The demo pharmacy id is `green-life`.

### 4.1 HTTP endpoints (used by the frontend)

| Method & path | Purpose | Owner |
|---|---|---|
| `GET /health` | Liveness | Farhan |
| `POST /dev/reset` | Wipe and reload the seed pharmacy (demo reset button) | Farhan |
| `GET /pharmacies/{pid}` | Profile and settings (margin, buffers) | Farhan |
| `POST /pharmacies/{pid}/captures` | Upload photo (`multipart`: `file`, `kind` = `invoice` or `sales_page`) → extraction draft for review | Farhan (calls `agents.extraction.extract`) |
| `GET /pharmacies/{pid}/captures/{cid}` | Get a capture and its draft | Farhan |
| `POST /pharmacies/{pid}/captures/{cid}/confirm` | Owner submits corrected draft → saved as invoice or sales day | Farhan |
| `GET /pharmacies/{pid}/accounts?period_days=30` | P&L, margin, stock days, patient-due days, supplier concentration, slow movers, expiring value | Farhan |
| `GET /pharmacies/{pid}/dues` | Supplier-dues calendar | Farhan |
| `GET /pharmacies/{pid}/forecast?days=30` | Daily cash balance series + shortfall events | Farhan |
| `GET /pharmacies/{pid}/alerts` | Current alerts | Farhan |
| `GET /pharmacies/{pid}/expiry?horizon_days=60` | Batches at risk, return-eligible value | Farhan |
| `GET /pharmacies/{pid}/orders` | Upcoming orders | Farhan |
| `GET /pharmacies/{pid}/orders/{oid}/trim` | Sellable value per line + suggested quantities | Farhan |
| `POST /pharmacies/{pid}/funding-plan` | Body optional `{amount, needed_by}`; default = first forecast shortfall after suggested trims. Returns ranked options + recommended plan | Farhan |
| `GET /pharmacies/{pid}/passport` | Credit passport: record, posterior, default probability, terms, evidence | Farhan |
| `GET /pharmacies/{pid}/actions` | Proposed / approved / executed actions | Farhan |
| `POST /pharmacies/{pid}/actions` | Propose an action (UI buttons can also propose) | Farhan |
| `POST /pharmacies/{pid}/actions/{aid}/approve` · `/reject` | Owner decision; approve triggers sandbox execution | Farhan |
| `GET /pharmacies/{pid}/consents` · `POST` · `DELETE /consents/{id}` | Per-lender consent | Farhan |
| `GET /lenders` | Simulated lenders and products | Farhan |
| `GET /lenders/{lid}/applications` | Lender inbox (only consented pharmacies) | Farhan |
| `POST /lenders/{lid}/applications/{appid}/decide` | Simulated lender decision (deterministic rule) | Farhan |
| `GET /logs?since=` · `GET /logs/stream` (SSE) | Audit log, live | Farhan |
| `POST /chat` | Copilot chat, AI SDK UI message stream | **@ishmam259** (router mounted by Farhan) |

### 4.2 Python interfaces between the engines and the agents

The chat (@ishmam259) calls Farhan's engines in-process, and the capture endpoint calls Farhan's extraction. Signatures (in `backend/app/...`):

```python
# Farhan provides (agents/extraction.py)
async def extract(image: bytes, kind: Literal["invoice", "sales_page"]) -> ExtractionResult

# @ishmam259 provides (agents/router.py)
router: fastapi.APIRouter            # exposes POST /api/v1/chat; Farhan mounts it in main.py

# Farhan provides (engines/*.py) — all take a DB session first
get_accounts(db, pid, period_days=30) -> AccountsOut
get_dues(db, pid) -> DuesOut
get_forecast(db, pid, days=30) -> ForecastOut
get_alerts(db, pid) -> list[Alert]
get_expiry(db, pid, horizon_days=60) -> ExpiryOut
list_orders(db, pid) -> list[OrderOut]
get_trim(db, pid, order_id) -> TrimOut
get_funding_plan(db, pid, need: FundingNeed | None = None) -> FundingPlanOut
get_passport(db, pid) -> PassportOut
propose_action(db, pid, proposal: ActionProposal, proposed_by: str) -> ActionOut
log(tier: str, component: str, event: str, **data) -> None     # engines/logbus.py
```

Until the real thing exists, each side uses a stub returning the example JSON, so nobody waits.

### 4.3 Key schemas (field names are binding)

```text
ExtractionResult
  kind: "invoice" | "sales_page"
  invoice?: { supplier_name, invoice_no, invoice_date, due_date, total,
              lines: [{ product, strength?, pack?, batch_no, expiry_date, qty, unit_cost, line_total }] }
  sales_page?: { days: [{ date, cash_sales, credit_sales, dues_collected, expenses }] }
  field_confidence: { "<json path>": 0..1 }       # e.g. "invoice.lines[2].qty": 0.62
  checks: [{ name, passed, detail }]               # arithmetic, date sanity, duplicates
  suspicious_text: [string]                        # instruction-like text found in the image (never obeyed)
  model: string, prompt_version: string, mode: "live" | "replay"

AccountsOut   { period_days, sales, gross_margin_pct, gross_profit, overheads, net_profit,
                stock_value, stock_days, patient_dues, patient_due_days,
                active_suppliers, top_suppliers:[{name, share_pct}], slow_movers:[...], expiring_value_60d }
DuesOut       { items:[{ supplier, invoice_no, amount, due_date, days_left, status }] , total_due }
ForecastOut   { start_cash, days:[{ date, inflow, outflow, balance, items:[{ label, amount }] }], shortfalls:[{ date, amount, cause }] }
              # items = named moves that day (supplier invoice, rent, salaries, patient dues), signed; routine daily sales not listed
Alert         { id, kind: "shortfall"|"expiry"|"return_window"|"patient_dues"|"suspicious_document",
                severity, title, detail, created_at }
ExpiryOut     { horizon_days, batches:[{ product, batch_no, expiry_date, days_left, qty, cost_value,
                return_eligible, supplier }], at_risk_value, return_eligible_value }
TrimOut       { order_id, lines:[{ product, qty, unit_cost, sales_rate_per_day, sellable_days,
                sellable_qty, suggested_qty, at_risk_value }], original_total, suggested_total, saving }
FundingPlanOut{ need:{ amount, needed_by }, options:[{ key, label, provider, amount, cost_bdt, apr_pct,
                eligible, reason, speed, certainty }], plan:{ steps:[{ action_kind, label, amount, when, fallback_for? }],
                total_cost_bdt }, naive_cost_bdt }
PassportOut   { invoices_total, paid_on_time, confirmed_share, theta_mean, theta_low_5pct,
                default_probability, score, advance_rate_pct, partner_share_pct, evidence:[...] }
ActionOut     { id, kind: "return_claim"|"extension_request"|"loan_application"|"set_aside"|"trim_order",
                status: "proposed"|"approved"|"rejected"|"executed"|"failed",
                payload, proposed_by, created_at, decided_at?, result? }
LogEvent      { id, ts, tier: "T0"|"T1"|"T2"|"T3", component, event, data }
```

---

## 5. Data model (PostgreSQL)

Farhan owns it. Tables:
- `pharmacy`: id, name, city, settings (json: `gross_margin_pct`, `cash_buffer`, `expiry_buffer_days`)
- `supplier`: id, name, verified, `return_cutoff_days` (claims must be filed at least this many days before expiry)
- `invoice`, `invoice_line`: as `ExtractionResult.invoice`, plus status, `supplier_confirmed`, `capture_id`
- `payment`: supplier, invoice, amount, paid_on (on time if paid_on ≤ due_date)
- `sales_day`: date, cash_sales, credit_sales, dues_collected, expenses
- `patient_dues`: label (alias only), amount, since. **No medicine names, ever.**
- `expense_schedule`: category, amount, day_of_month
- `stock_batch`: product, batch_no, expiry_date, qty, unit_cost, supplier (derived from invoice lines)
- `planned_order`, `planned_order_line`
- `lender`, `lender_product`: kind, min/max amount, apr, fee_pct, tenor_days, min_history_invoices, cost_bearer
- `consent`, `application`
- `registry_lock`: `commitment` (unique), application_id, created_at
- `action`, `capture`, `audit_log`

---

## 6. Golden numbers (must reproduce exactly)

Farhan designs `seed/green_life.json` so the engines output these. Tests assert them. The frontend, deck, video and docs quote them.

| Quantity | Value |
|---|---|
| Sales, last 30 days | 412,500 |
| Gross margin (setting) | 12% → gross profit 49,500 |
| Overheads, 30 days | 36,000 |
| Net profit, 30 days | 13,500 |
| Stock value / stock days | 210,000 / 17.4 days (on purchases at cost: 363,000 per 30 days) |
| Patient dues / days | 38,000 / 2.8 days |
| Active suppliers | 23 |
| Invoices last 3 months / paid on time | 41 / 38 (all supplier-confirmed in seed) |
| Batches expiring ≤ 60 days | 6 batches, cost value 18,400 |
| Return-eligible value | 9,200 |
| Supplier A order | 60,000, due in 10 days |
| Forecast cash on that day | 41,000 → shortfall 19,000 |
| Slow-mover line | 30 boxes × 600; rate 0.2/day; 90 days to expiry; 30-day buffer → 60 sellable days → 12 sellable; at risk 10,800 |
| Trimmed order / new shortfall | 49,200 / 8,200 |
| Option: supplier extension (20 days) | cost 0, uncertain |
| Option: mobile-wallet loan 8,200 @ 9%, 90 days | 181.97 |
| Option: bank-funded supplier credit 1% on 49,200 | 492.00 |
| Option: bank small-business loan | ineligible (minimum 200,000) |
| Naive: mobile-wallet loan 19,000 @ 9%, 90 days | 421.64 |
| Passport θ lower bound (5th pct of Beta(39, 4)) | 0.826 |
| Default probability (lender model) | 0.030 |
| Score S | 0.507 |
| Advance rate / partner share | 75.2% / 54.4% |

---

## 7. Milestones

| Milestone | What "done" means | Latest by (Bangladesh time) |
|---|---|---|
| **M1 Contract frozen** | Schemas, stub endpoints with example JSON, `contracts/` exported, seed file loads, `docker compose up` runs. **Blocks the others, so Farhan does this first.** | 16 Oct, 23:59 |
| **M2 Parts work alone** | Engines pass golden-number tests; extraction and chat work in replay mode; frontend complete on mock data | 18 Oct, 23:59 |
| **M3 Integrated** | Frontend on the live API; the full demo story runs end to end; the sandbox trace exports | 19 Oct, 23:59 |
| **M4 Submitted** | Docs PDFs, deck, video, repo, logs, registration email all sent | 20 Oct, 18:00 (freeze) |

---

## 8. Submission checklist

| # | Item | Owner | Where |
|---|---|---|---|
| 1 | Technical documentation (architecture, algorithms, security design) | @ishmam259 (eval table from Farhan) | `docs/technical/` → PDF |
| 2 | Presentation deck (≤ 10 min) | @ishmam259 | `deck/` → PDF + PPTX |
| 3 | Demo video (≤ 5 min) | @ishmam259 | `video/` + link |
| 4 | Source code: README, GitHub link, deployment instructions, test cases | Farhan (README run section, tests), everyone | repo |
| 5 | Security self-assessment (permission tiers, known-risk list) | @ishmam259 | `docs/security/` → PDF |
| 6 | Execution evidence: sandbox logs + demo video | Farhan (log export), @ishmam259 (video) | `logs/sandbox_execution_trace.log` |
| — | Registration form and submission email to fintechathon@ican-x.com | @ishmam259 | email |

**The repo is private.** Before submitting, decide with the team whether to make it public or add the judges. The rules ask for a GitHub repository link.

---

## 9. OpenAI budget rules ($20 hard limit)

- Set the project's monthly budget to **$20** in the OpenAI dashboard, with an email alert at **$5**.
- **One key per person** under the same OpenAI project.
- **Tests never call the API.** They use replay mode (`LLM_MODE=replay`), which serves saved responses.
- **Agent loop cap:** at most 5 tool calls per chat message.
- **Photos are resized** to 1,600 px on the long side before sending.
- **Reasoning effort:** `low` for chat, `medium` for extraction.
- If a day costs more than about $1, stop and find the leak.

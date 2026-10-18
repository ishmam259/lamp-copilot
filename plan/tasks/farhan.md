# Farhan: tasks from the approved win plan (v3)

Approved 18 Oct 2026. Full detail and acceptance checks for each ID: `plan/requirements.md`. Work in rank order: all of Level A, then Level B, then Level C. Stay inside your folders in `CLAUDE.md`; where a task touches one of Ishmam's files, do your part and hand over.

**You are the contract owner.** At G1b (19 Oct, 09:00), publish the schemas and examples for the new endpoints in `contracts/` (session cookie, approval PIN, follow-ups, notify events, log verify, shelf-life credit, cost-disclosure fields, wallet, value ledger, catalogue) and tell Ishmam.

## Level A (≈ 11 h)

| # | ID | Task | Your part | Hours | Done when |
|---|---|---|---|---|---|
| 1 | SUB-02 | Secrets scan of the full git history before the repo goes public; README "Run it" kept current | Scan + run section | 0.25 | Scan report clean |
| 2 | **CORE-13** | **Close the API, reads included.** Owner session (HttpOnly cookie after the PIN) on every `/pharmacies/{pid}/*` route and `/logs*`; lender key for lender endpoints; `proposed_by` from the caller; PIN re-asked at Tier-3 approval; `/dev/*` only with `DEV_MODE=true`; no default `registry_key`. New `engines/auth.py` | `api/`, `main.py`, `config.py`, `engines/auth.py`, tests | 3.25 | The 10 direct-HTTP cases in `requirements.md` pass |
| 3 | CORE-15 | Correct cost disclosure: APR on the amount financed, tenor, cost of covering the gap (BDT and % of need) for every option | Engine fields + tests | 0.25 | Engine returns the figures; the 73% label is gone |
| 4 | CORE-08 | Pause LaMP: while paused, agent and scheduler proposals are refused, agent-proposed actions can't be approved | Engine + API | 0.5 | `agent_paused` logged; tests |
| 5 | CORE-09 | Hash-chained audit log, `scripts/verify_trace.py`, `GET /logs/verify` | `engines/logbus.py`, scripts | 1.5 | One changed character fails at that line |
| 6 | CORE-03 | Money-figure tracing: pure function `engines/fidelity.py` (amounts and rates bound to the field they name; counts and dates separate); the funding-plan tool returns its derived values | `engines/fidelity.py` + tests | 2 | Recorded scene-3 answer passes; wrong-option variant fails |
| 7 | CORE-11 | Shelf-life credit figures (19,000 purpose-blind counterfactual → 8,200 financed, 10,800 ineligible); add to PLAN §6 via Ishmam | Engine + endpoint | 0.75 | Engine confirms every figure |
| 8 | CORE-04 | Follow-through: approving a plan with a fallback stores a follow-up; supplier "declined" / "no reply by Thu 22 Oct" makes the runner propose the 8,200 wallet loan (`lamp-scheduler`) and emit a notify event | Engines + API | 2 | "No reply" → one proposal (181.97) and one notify event |
| 9 | CORE-06 | Notify events on the SSE stream for the desktop notifications (owner and admin audiences) | Event shape + stream | 0.5 | Ishmam's notification fires from it |

## Level B (≈ 17 h)

| # | ID | Task | Your part | Hours |
|---|---|---|---|---|
| 10 | PROOF-04 | Shelf-life credit simulation: ≥200 perturbed pharmacies through the real engines; purpose-blind vs shelf-life; `eval/shelf_life_sim.md` with seed and assumptions | Script + table | 2.5 |
| 11 | CORE-14 | Sourced financing catalogue: ≥6 archetypes from dated Bangladeshi offers, eligibility reasons, cost disclosure; a test reports whether the golden plan still holds | Seed + engines | 2 |
| 12 | PROOF-03 | Real-photo extraction eval: printed invoices, team-handwritten sales pages, two phones, 2 injection prints; `eval/results_real.md` | Photos + record once | 2 |
| 13 | CORE-05 | Sandbox wallet (payouts credited, counted by the forecast) + statement matcher (~20 seeded lines; matched / duplicate / unmatched / missing deposit) | Engines + API + seed | 4 |
| 14 | CORE-10 | Value ledger with basis and counterfactual per line (9,200 return + 10,800 + 239.67) | Engine + API | 1 |
| 15 | PROOF-01 | Red-team: ≥15 cases incl. the 10 HTTP cases; 2–3 outside testers; table by category | HTTP + engine cases | 1.75 |
| 16 | PROOF-02 | Intent eval harness in `eval/`, 20 questions (≥8 written outside the team) | Harness | 1 |
| 17 | DOC-04 | Unit economics: AI cost per pharmacy per month, with assumptions | Figures | 0.5 |
| 18 | SUB-07 | Export the trace and head hash from the one continuous video run | Run + export | 0.5 |
| 19 | SUB-03/04 | Draft the algorithm, eval and red-team sections (in `eval/`) for Ishmam's docs | Drafts | 2 |

## Level C (≈ 7.5 h)

CORE-16 consent scopes in lender endpoints (1.5) · CORE-07 cash-flow ceiling from a sourced norm (1.5) · PROOF-05 wider evidence (3.5) · CORE-11b borrowing-base curve, only if it binds in PROOF-04 (1).

## Proposed additions (not in the approved plan; decide tomorrow)

Raised after review because the time limit was lifted: true Web Push so notifications reach a closed app (SHOULD-3, needs a `pyproject.toml` dependency), a system-health alert to the admin when a component fails, and a live judge URL running the real model under a daily budget cap (SHOULD-8).

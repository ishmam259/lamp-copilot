# Requirements (re-plan v3, final, after judge round 2)

Derived from the demo story (`demo-flow.md`) and the hard requirements (`problem.md`), revised twice from the judge's reports (`judge-review.md`). Nothing here is assigned to a person. **Split** shows the estimated hours per ownership area under `CLAUDE.md` (M1 = Ishmam's folders, M2 = Farhan's folders), so the team can assign at `/assign` and see the balance.

- **Priority:** MUST · SHOULD · COULD. **Class:** **Spike** = the one feature built properly (safe agency: "it can plan for a week, but it can't spend a taka", the security & compliance criterion) · **Story** = what the demo story needs, built thin · **Proof** = measurement · **Coverage** = the thinnest version that covers a word of the topic · **Deliverable**.
- **Rubric:** TC = Task completion 40% · SC = Security & compliance 30% · II = Innovation & interaction 30%. Capabilities: **IU** intent understanding · **TP** task planning · **SE** safe execution · **UC** user control · **MV** measurable value.
- **Cost:** S (<1 h) · M (1–2 h) · L (>2 h), with an hour estimate. **Rank:** points per effort among MUST rows, using the judge's estimates where it gave them. **NC** = never cut.
- **Level:** the scope-ladder step. **v3 re-sequenced the ladder** (judge round 2, change 2), so that the round-1 fixes and the follow-through land in Levels A + B, and the never-cut list and Level A agree.

**MVP line:** every MUST row, about **72 h** (M1 ≈ 36, M2 ≈ 36). **Recommended commitment: Level A in full, then Level B in rank order** (A + B ≈ 61 h: M1 ≈ 33, M2 ≈ 28). The judge expects A plus about two-thirds of B by the freeze.

## Precondition: tonight (survival, not points)

| Step | What | Who decides / does | Status |
|---|---|---|---|
| P-1 | Registration confirmed **with the two-member roster** (Pritom left on 17 Oct). With two members the team is at the minimum size, and the ≥60% rule means both must be non-Chinese nationals. Ask the organisers how to submit (channel) | Team lead | TODO |
| P-2 | Plan approved (G0) and **scope level committed** tonight | Team | TODO |
| P-3 | **Challenge bonus decision** (team rule "no blockchain"; cost in `win-plan.md` §1) | Team | TODO |
| P-4 | **README ownership:** `CLAUDE.md` gives Farhan only the "Run it" section; Ishmam (owner of `CLAUDE.md`) assigns the rest before SUB-02 and DOC-01 start | Ishmam | TODO |
| P-5 | **`plan/` stays off the judge path** (untracked today; it holds rival scenarios and award odds). Never rewrite git history to hide how the entry was built | Team | TODO |

## Already built (keep, verified by tests in the repo)

| ID | What exists | Evidence | Note |
|---|---|---|---|
| K-01 | Deterministic engines with every golden number in PLAN §6 | `tests/engines/test_golden.py`, `test_engine_edges.py` | Frozen (except D-16, a team decision) |
| K-02 | Photo extraction with checks, confidence, injection screen, replay | `tests/agents/test_extraction.py`, `eval/results.md` | 27 clean synthetic images only |
| K-03 | Chat agent: read-only tools plus `propose_action`; 5-call cap; budget guard | `tests/agents/` | No chat recordings; replay answers through the regex `_script` |
| K-04 | Actions: propose → approve/reject → sandbox executor in a savepoint | `tests/api/test_flows.py` | **Every route open, reads included; `/chat` and `/logs/stream` open; `proposed_by` from the query** |
| K-05 | Consent, 2 simulated lenders with 3 products, inbox, decision rule | `seed/green_life.json` | Scopes not enforced |
| K-06 | Duplicate-financing registry | `tests/engines/test_registry.py` | Default `registry_key` in `config.py` |
| K-07 | Audit log with tiers, SSE, export, scripted demo, trace | `logs/` | Not tamper-evident; 38 events within one second; `model=none` for the sales page |
| K-08 | Frontend: nine screens plus the chat drawer, PWA manifest | `frontend/src/app/*` | No service worker; no sales-page review |
| K-09 | Docker Compose, README run section, OpenAPI contract | `docker-compose.yml`, `contracts/` | `/dev/reset` drops every table, ungated |
| K-10 | Tech doc, security report, 25-slide deck, video script | `docs/`, `deck/`, `video/` | Deck reuses BCOLBD photos, cut-outs and icons with no recorded licence |

## Level A: submission-safe, honest, and the spike in place (≈ 29.5 h · M1 18.5 / M2 11)

| ID | Class | Description | Rubric | Cost | Split | Rank | Acceptance check |
|---|---|---|---|---|---|---|---|
| SUB-01 | Deliverable | = P-1 | Hard req. | S (0.5) | M1 0.5 | 1 | Confirmation names the two current members |
| SUB-10 | Deliverable | **Deck image licences:** replace BCOLBD photos, cut-outs and icons with app screenshots or images with a recorded licence; remove the BCOLBD lines from `deck/README.md` (moved to Level A by the judge) | Hard req. (licensing) | S (1) | M1 1 | 2 | Every image in the deck has a recorded source and licence, or is our own screenshot |
| SUB-02 | Deliverable | **Secrets scan of the full history**, then repo public (or reviewer access); README judge-first (three-line pitch, video link, judge's guide, 5-minute run, real vs sandbox); internal material (49%/51% shares, "Pritom left", team rules) off the first screen; `plan/` not in the public repo (P-5) | TC | M (1.5) | M1 1.25 · M2 0.25 | 3 | Logged-out browser: first screen shows the video and the guide; the scan report is clean |
| DOC-01 | Deliverable | Judge's guide: five capabilities and three criteria → timestamp, slide, file, number (README top, tech doc p1) | all | S (1) | M1 1 | 4 | Every capability has a timestamp and a number |
| CORE-13 | **Spike** | **Close the API, reads included.** One router-level owner-session dependency on every `/pharmacies/{pid}/*` route (reads and writes), on `POST /chat` and on `/logs*`, carried in an **HttpOnly cookie** so the SSE `EventSource` keeps working; the session is issued after the owner's PIN. Lenders read only consented data, through the lender endpoints, with their key. `proposed_by` comes from the authenticated caller (owner → "owner"; the chat's in-process call → "agent"; the runner → "lamp-scheduler"). **Tier-3 approvals re-ask the PIN**, which is re-authentication at the point of approval, not a second factor (stated in the security report). `/dev/*` mounted only with `DEV_MODE=true`; no default `registry_key` | SC · SE, UC | L (4.5) | M2 3.25 (`api/`, `main.py`, `config.py`, `engines/auth.py`) · M1 1.25 (`agents/router.py`, PIN screen, frontend credentials) | 5 | **10 direct-HTTP cases:** passport without a session → 401; a lender key on an owner read → 403; chat without a session → 401; log stream without a session → 401; approve without a session → 401; approve with a lender key → 403; consent without a session → 401; lender decide without a key → 401; `/dev/reset` with `DEV_MODE=false` → 404; spoofed `proposed_by` → recorded as the caller |
| FIX-01 | Coverage | Capture screen reviews a sales-book page | TC | S (1) | M1 1 | 6 | Demo sales page reviewed and saved |
| SUB-08 | Deliverable | Consistency pass (73 / 91 / 98 tests; "to be filled"; "in progress"; the README's stale "stored draft" line) | TC, SC | M (1) | M1 1 | 7 | Grep agrees everywhere |
| CORE-01 | Story | Real chat recorded live and replayed; free-form goals live; clarifying questions; replay answers an unrecorded question honestly ("not recorded: set `LLM_MODE=live`") | II · IU | M (2) | M1 2 | 8 | Video questions served from `eval/replay/chat/`; unrecorded → honest message |
| CORE-15 | **Spike** (compliance) | **Correct cost disclosure on every option** (judge change 3). Each option shows: APR on the amount financed, its tenor, and the cost of covering this gap in BDT and as a % of the need. Supplier credit: "APR 12.2% on 49,200 for 30 days; covering the 8,200 gap costs 492 = 6.0% of the gap for 30 days". Wallet loan: "APR 9% on 8,200 for 90 days; 181.97 = 2.2% of the gap over 90 days". Options are compared over the same horizon, or the difference in tenor is stated. Engine to confirm every figure | SC, TC · MV | S (0.5) | M2 0.25 · M1 0.25 | 9 | Funding page and deck show APR, tenor and cost-of-gap per option; no "effective annual cost" label on the 73% figure |
| CORE-08 | **Spike** | Pause LaMP (owner session required); while paused, agent and scheduler proposals are refused and agent-proposed actions can't be approved | SC · UC | S (0.75) | M2 0.5 · M1 0.25 | 10 | Paused → `agent_paused` logged |
| CORE-09 | **Spike** | Hash-chained audit log; `verify_trace.py`; `GET /logs/verify` (owner session); anchoring limit stated (R-20) | SC, TC · SE | M (1.75) | M2 1.5 · M1 0.25 | 11 | One changed character fails verification at that line |
| CORE-03 | **Spike** | **Money-figure tracing, safe for scene 3** (judge change 5). "Figures" means BDT amounts and rates, label-bound to the field they name; counts and dates are reported separately. The funding-plan tool returns the derived values the answer uses (18 boxes trimmed, 20 extension days, the fallback date), so they are engine outputs too. Pure function in `engines/fidelity.py` (M2); `chat.py` (M1) calls it, shows "N of N money figures traced to LaMP's engines", and blocks an answer with an untraced money figure (safe message, log, admin notified). **A test runs the guard on the exact recorded answers before G3** | SC, II · SE, IU | L (3) | M2 2 · M1 1 | 12 | The recorded scene-3 answer passes; a variant attaching 421.64 to the wrong option fails |
| CORE-11 | Story / Innovation | **Shelf-life credit card, framed honestly.** "A purpose-blind lender would lend 19,000 for the full gap (computed counterfactual, not a request in the log). Applying the ineligible-inventory rule asset-based lenders use, computed per batch from the photographed invoices before the purchase: 10,800 of Supplier A's order won't sell before expiry, so LaMP finances at most 8,200, and the owner orders 18 fewer boxes. One number, two decisions." Engine confirms; appended to PLAN §6 | II, TC · MV | M (1.5) | M2 0.75 · M1 0.75 | 13 | Lender view shows the card with "computed counterfactual" on the 19,000 |
| DOC-03 | **Spike** (compliance) | Financial-regulation matrix: lending rules, AML/KYC (the lender performs KYC), credit information, **cost disclosure (CORE-15)**, responsible lending (the cash-flow ceiling shown as "**designed, not built**" unless CORE-07 lands with a sourced norm), licensing, record retention, model risk, PDPO consent, and **a row on the retail nano-loan used for a business bill** (City Bank–bKash nano-loans are retail loans to individuals: the owner borrows personally, so the product's permitted purpose must be checked). Every citation checked or marked "to verify" | SC | M (2) | M1 2 | 14 | Every row: control, repo evidence, citation status |
| CORE-04 | Story | **Thin follow-through** (moved to Level A). Approving a plan with a fallback stores a follow-up; the simulator's outcomes "declined" and "no reply by the deadline" make the runner create the fallback proposal (`lamp-scheduler`) and a notify event; engines keep `as_of_date`. Deadline **Thu 22 Oct** (needed_by − 4; D-16, a team decision, because Friday is the weekly holiday) | TC, II · TP, UC | M (2) | M2 2 | 15 | "No reply" → wallet-loan proposal for 8,200 (181.97) and one notify event |
| CORE-06 | Story | **Desktop notifications** (service worker plus `showNotification` from SSE notify events, owner and admin audiences; the tab must be open; a click opens the approval). **Never say "lock screen" unless SHOULD-3 (Web Push) is built** | II, SC · UC | M (2) | M1 1.5 · M2 0.5 | 16 | Background tab → OS notification → approval still needs the PIN |
| SUB-06a | Deliverable | Insurance video: today's story recorded as reusable scene clips and assembled into a ≤5:00 v1 (G2) | all | L (2.5) | M1 2.5 | NC | v1 plays logged out |
| SUB-09 | Deliverable | Early v1 sent once the channel is known | Hard req. | S (0.5) | M1 0.5 | 17 | Sent and acknowledged |
| FIX-02 | Coverage | Funding page text from the API | TC | S (0.5) | M1 0.5 | 18 | No hard-coded 19,000 / 0–182 |

## Level B: the account, the matching and the proof (≈ 32 h · M1 14.5 / M2 17.25)

| ID | Class | Description | Rubric | Cost | Split | Rank | Acceptance check |
|---|---|---|---|---|---|---|---|
| PROOF-04 | Proof / Innovation | **Shelf-life credit simulation** (judge change 4): ≥200 perturbed pharmacies run through the **real engines**, comparing purpose-blind lending with shelf-life credit. Reports the share of cases where the financed amount changes, financed stock that expires unsold (median, P10–P90), interest, and need left unfinanced. Seed published; labelled synthetic | TC, II · MV | L (3) | M2 2.5 · M1 0.5 | 19 | `eval/shelf_life_sim.md` with the table, assumptions and seed |
| CORE-14 | Coverage | **Sourced catalogue**: 6+ archetypes anchored on dated, sourced Bangladeshi offers, each with eligibility reasons and the CORE-15 disclosure; "N matched, K eligible, cheapest first, why the rest don't fit". **Terms come from the sources, never chosen to protect the golden plan**: if a sourced product beats it, the team updates the golden numbers everywhere (decision logged), not the product | TC, SC · MV | L (2.5) | M2 2 · M1 0.5 | 20 | ≥6 options with source, date and reasons; a test reports whether the golden plan holds |
| PROOF-03 | Proof | Real-photo extraction eval: eval invoices printed; 5 sales pages **handwritten by the team** (said so); two phones, shop light; 2 injection prints; per-image rows next to the synthetic table | TC · IU | M (2) | M2 2 | 21 | `eval/results_real.md` |
| CORE-05 | Story / Coverage | **Sandbox account with a statement and a matcher** (merged CORE-05 + CORE-12, judge change 2): a sandbox wallet (opening balance = seed `cash_on_hand`), payouts credited at decision time and counted by the forecast; its statement plus seeded external lines (~20) matched to invoices and payments (payee alias, amount, date ±3 days) → matched / needs review (duplicate, unmatched, missing deposit) with a recommendation line; no new action kind | TC · MV | L (5) | M2 4 · M1 1 | 22 | Payout → +8,200, board flips; exactly the seeded duplicate found; golden tests pass |
| CORE-10 | Story | Value ledger with basis and counterfactual per item. The click script **approves the 9,200 return claim**, so the ledger contains it | TC · MV | M (1.5) | M2 1 · M1 0.5 | 23 | 9,200 + 10,800 + 239.67 with bases; totals match the engine |
| PROOF-01 | Proof | Red-team, **≥15 cases including all 10 direct-HTTP cases**, plus chat and image injection and approval-path cases; 2–3 testers from outside the team, their attempts logged; table by category | SC · SE | L (3) | M2 1.75 · M1 1.25 | 24 | "0 of N changed state, including 10 direct HTTP calls" |
| CORE-02 | Story | **Thin visible plan**: `share_plan` (no data, no state) rendered as a checklist | II · TP | M (1.5) | M1 1.5 | 25 | Checklist before the tool chips |
| PROOF-02 | Proof | Intent eval, **20 questions, ≥8 written outside the team**; harness in `eval/` | II · IU | M (1.5) | M2 1 · M1 0.5 | 26 | `eval/intent_results.md` |
| DOC-02 | Proof | OWASP LLM Top 10 mapping (current version) + model card + PDPO table | SC | M (1.5) | M1 1.5 | 27 | Each item: control, test, residual |
| DOC-04 | Proof | Unit economics: AI cost per pharmacy per month, with assumptions | TC · MV | S (0.75) | M2 0.5 · M1 0.25 | 28 | Figure with assumptions |
| SUB-05 | Deliverable | Deck revised to the `pitch.md` outline (reorder, relabel, replace slides; not a full rebuild); spoken ≤10:00 | all | L (3) | M1 3 | NC | Notes ≤10:00; numbers consistent |
| SUB-06b + SUB-07 | Deliverable | Final video from **one continuous run** (caption: "hook filmed after the captures, same session"); trace and head hash from that run | all | L (3) | M1 2.5 · M2 0.5 | NC | Trace ids match the screen; `verify_trace` intact |
| SUB-03/04 | Deliverable | Tech doc and security report updated (M2 drafts algorithm, eval and red-team sections in `eval/`); PDFs | TC, SC | L (3.5) | M1 1.5 · M2 2 | NC | No stale rows; tiers with enforcement points |

## Level C: depth after A + B (≈ 11 h · M1 3.5 / M2 7.5)

| ID | Description | Rubric | Cost | Split | Rank |
|---|---|---|---|---|---|
| CORE-16 | Consent scopes enforced in the lender endpoints, plus a "what the lender will see" preview (moved up from SHOULD-5: backs the consent claim) | SC · UC | M (2) | M2 1.5 · M1 0.5 | 29 |
| CORE-07 | Cash-flow ceiling from a **sourced norm** (e.g. repayment as a share of projected net cash flow over the tenor) plus a read-only rules view; otherwise it stays "designed, not built" | SC · UC | L (2.5) | M2 1.5 · M1 1 | 30 |
| PROOF-05 | Wider evidence: naive vs LaMP across the simulated shops (interest, expiry loss, days short), the forecast's error on simulated sales, intent eval to 30 questions, red-team to 40 cases | TC, SC | L (4) | M2 3.5 · M1 0.5 | 31 |
| CORE-11b | Borrowing-base curve and a 10-second animation, **only if the curve binds somewhere in PROOF-04** (on Green Life it never does: ≈ 137,700 → 130,900 against needs of 8,200–19,000); otherwise dropped | II | L (2.5) | M2 1 · M1 1.5 | 32 |

## SHOULD (Level D, in order) and parallel non-code work

| ID | Description | Rubric | Cost |
|---|---|---|---|
| SHOULD-9 | **Parallel, non-code, any level:** 3–5 real owner conversations (consent, no patient data), including the Bangla and Friday-trading questions. Only if real | TC · MV | M (2) |
| SHOULD-3 | True Web Push (app closed) plus PWA install; only then may the video say "lock screen". Needs a dependency in `pyproject.toml` | II · UC | L (2.5) |
| SHOULD-4 | Generative cards with inline approval (session and PIN) | II | L (3–4) |
| SHOULD-10 | Telegram channel (alerts and questions, never approvals) | II · UC | L (3–4) |
| SHOULD-8 | Live judge URL, live mode under a daily budget cap, rate limit, hourly reset | TC | L (2–4) |
| SHOULD-7 | "Explain this number" drawer | II, SC | L (3–5) |
| SHOULD-6 | Full multi-tenant auth, device binding or OTP for step-up | SC | L (3–4) |

## COULD (round 2 or roadmap)

COULD-1 what-if tool · COULD-2 uncertainty band and backtest on a public dataset · COULD-3 federated credit-model simulation (labelled synthetic) · COULD-4 morning briefing · COULD-6 voice · COULD-7 dues scheduler · COULD-8 third-party payment sandbox.

## Build order (points per effort)

Tonight: P-1 → P-5. Then: SUB-01 → SUB-10 → SUB-02 → DOC-01 → **CORE-13** → FIX-01 → SUB-08 → CORE-01 → CORE-15 → CORE-08 → CORE-09 → CORE-03 → CORE-11 → DOC-03 → CORE-04 → CORE-06 → SUB-09 → FIX-02 | PROOF-04 → CORE-14 → PROOF-03 → CORE-05 → CORE-10 → PROOF-01 → CORE-02 → PROOF-02 → DOC-02 → DOC-04 | Level C in rank order. SUB-06a by G2; SUB-03/04/05/06b/07 close at G4. **Contract first:** at G1 M2 publishes schemas and examples for CORE-13/04/05/10/11/14/15.

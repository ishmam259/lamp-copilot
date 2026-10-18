# Judge review

## Plan review: round 1 (re-plan v1), 18 Oct 2026, evening (Bangladesh time)

Written by the judge agent in plan review mode (fresh context, full documents in `plan/`, official sources in `Problem Statement & Starter Files/`). I read every file in `plan/` in full (every requirements row, the whole cut list), both PDFs page by page and the website capture, and checked the plan's claims about the current product against the repo. Nothing was run.

**Verdict in one line.** The plan is coherent and honest, and its safety story is genuinely distinctive. But it is a breadth plan with a DEPTH label. It leaves the biggest security hole (no authentication) below the line while planning to publish "0 of N attacks changed anything". And its promise of "measured, not claimed" depends on items that sit on the cut list. Against the strongest rival it is roughly a coin flip. With the five changes below it leads.

**Source check.** `plan/problem.md` is faithful to both PDFs and the website: 40/30/30, the six deliverables, the three Topic E wordings, the deadline, the award names, conflicts C1 to C8. I found no errors in it.

**Repo claims I verified.** Every one I checked is true:
- 98 `def test_` functions; the deck notes say "73 automated tests" (slide 16), and the tech doc and security report say 91.
- The tech doc's eval table still says "to be filled", and the security report's injection-image row says "In progress".
- `eval/replay/` holds extraction recordings only, so replay-mode chat runs the regex `INTENTS` / `_script` in `chat.py`.
- `capture/page.tsx` renders a review only when `extraction.invoice` exists.
- `funding/page.tsx` hard-codes "BDT 19,000" and "BDT 0–182".
- The extraction eval scores 100% on 27 synthetic images.
- The committed trace (16 Oct) logs the sales page with `model=none`, and all 38 of its events carry two consecutive timestamps (11:56:38–39Z).

The plan doesn't mention several further repo facts. They are listed under "What's missing".

### Strongest rival team, concretely

A team of 4–5 strong engineers using the whole window from 31 Aug, building an "SME CFO agent" for, say, Indonesian warungs or Singapore food stalls.
- **Task completion.** A multi-agent orchestrator (planner, cash flow, reconciliation, financing, compliance) with a visible plan graph. It ingests bank-statement CSVs and invoice OCR, and **reconciliation is a core screen** with an exceptions queue. The cash forecast is backtested on a public retail dataset, with a MAPE. The financing matcher covers 15–25 real, sourced loan products, with eligibility reasons and an effective APR. Payments are "executed" through a real third-party sandbox (a payment provider's test mode), so the operation logs come from an external system. Value is measured across 100+ simulated SMEs against a naive baseline. There is a live URL with a demo login.
- **Security & compliance.** JWT roles (owner, accountant, lender), amount thresholds with OTP step-up, a guardrail model, an automated red-team run with an attack-success rate, PII redaction, an OWASP LLM Top 10 table, a risk register and a consent screen.
- **Innovation & interaction.** Generative UI cards, a WhatsApp or Telegram bot for alerts and questions (the organisers' "channels such as apps and IM" taste), voice input and a polished persona video.
- **Its weak spots.** A generic SME with little domain insight. Safety that rests on prompts and thresholds. No run-time check of the figures the LLM says. No tamper evidence. An agent that answers only when asked.

### Scores (plan as written, every MUST delivered)

| Criterion | Weight | Our plan /5 | Rival /5 | Gap and why |
|---|---|---|---|---|
| Task completion | 40% | **3.5** | **4.0** | **Rival ahead.** Every number we show comes from one synthetic shop whose seed was built to reproduce the golden numbers. The things that would prove generality all sit below the MVP line and on the cut list: the value simulation (SHOULD-2, cut #8), real-photo extraction (SHOULD-1, cut #9) and a forecast backtest (COULD-2). Financing-option matching, the *first* function in the PDF wording of Topic E and WeBank's own business, is 2 simulated lenders with 3 products, and the plan doesn't touch it. Reconciliation is minimal (20 seeded lines). Every counterparty is our own simulation. **Ours ahead** on the coherence of the end-to-end story, the deterministic test-asserted numbers and a conditional plan carried out over a simulated week. |
| Security & compliance | 30% | **4.0** (at risk of 3.5) | **3.5** | **Ours ahead on design:** an agent with no capability to act, policy as code with a PIN step-up, a kill switch, a run-time number check, a hash chain and a red-team suite. **Behind on basics.** The API has **no authentication at all**: anyone can approve as the owner, grant consent to a lender, or decide as the lender. `proposed_by` is a client-supplied query parameter. `POST /dev/reset` drops every table and is not gated. `registry_key` has a committed default. The planned "0 of N attacks changed anything" is therefore false for the simplest attack, a direct HTTP call to approve a Tier 1–2 action. "Compliance" covers OWASP and privacy only. Nothing maps to financial regulation (lending rules, KYC/AML, cost disclosure, credit-intermediation licensing), which is what a WeBank panel means by compliance. |
| Innovation & interaction | 30% | **3.5** | **3.5** | **Ours ahead** on domain insight and on the follow-through with no power to spend. The plan checklist and the verified badge only reach parity. **Behind** on channels and modality: the rival has IM, voice and generative cards, and we have in-tab notifications. Our headline innovation number doesn't hold up. The expiry-aware limit, 36,998 vs 45,120, is just 75.2% × the trimmed order vs 75.2% × the untrimmed order, and both exceed the 8,200 loan, so it never changes a decision. The app is English-only for owners who keep their books in Bangla, and the pitch Q&A doesn't address it. |

**Weighted totals** (score / 5 × weight): **ours 73 / 100 · rival 74 / 100.**
- Realistic delivery by the 20 Oct 18:00 freeze (Level A plus most of Level B): **ours ≈ 66.**
- With the five changes below and the precondition: **ours ≈ 79.**

### Five-capability check (website brief)

| Capability | Our plan's proof | Rival's proof | Verdict |
|---|---|---|---|
| Intent understanding | One free-form goal recorded live; a clarifying question; an intent eval of ≥30 questions the team wrote itself; extraction 100% on synthetic images | Multi-turn chat; OCR accuracy on real receipts | Par. Behind on real-world input unless SHOULD-1 is done |
| Task planning | The `share_plan` checklist plus a dated conditional fallback that fires later | A multi-agent plan graph | **Ahead**: planning over time is rare |
| Safe execution | No action tools for the agent, PIN tier, fidelity guard, hash chain, red-team | Thresholds, OTP, guardrail model, attack-success rate | **Ahead**, except that there is no authentication |
| User control | Per-step approval, conditional approval, PIN, Pause, consent preview | Approve buttons, thresholds, settings | **Ahead** |
| Measurable value | One shop: 0–182 vs 422; ledger ≈ 20,240 | 100+ simulated SMEs vs a baseline; a backtest MAPE | **Behind** unless SHOULD-2 is done |

### What's weak in the plan as written

1. **DEPTH label, breadth plan.** `win.md` says DEPTH means "few features, each solid", and that a second big feature is never started before the first is excellent. The MVP has 12 CORE items, including at least five new big features: follow-through with a dev clock, the sandbox wallet, a policy engine with an editable rules screen, reconciliation with a new action kind, and notifications. About 44 clock hours remain, which is SPEED territory under the kit's own rule ("one spike, never two"). The plan names three "core differentiators" plus two supporting ones.
2. **The load is infeasible, and it falls on one person.** By my count M1 (Ishmam) carries about 40 of the 59 MUST hours: two video recordings (the insurance and the final cut), the deck rebuild, both PDFs, the README, the judge's guide, CORE-01/02/03, PROOF-02, and the UI for about eight new features. That is inside 44 clock hours. G3 ("the whole new story runs on main") is about 26 hours away. Level B is the realistic ceiling, and the plan should say so now rather than at G2.
3. **The plan's own method check passes only on cut items.** §4b says the value simulation "compares LaMP against a naive policy" and that extraction is measured "on held-out real photos", and it claims to "Beat" the rival on measured value. Both are SHOULD items, and both are on the cut list.
4. **The innovation number doesn't bind** (see the scores table). A banker will read "advance rate × a smaller order" as trivial.
5. **"7 of 7 figures verified" overclaims.** CORE-03 checks that each number *appears* in this turn's tool outputs, not that it is attached to the right quantity: "the loan costs 421.64" for the wrong option would pass. A derived ratio ("≈ 1.5 months of net profit") is LLM arithmetic unless an engine returns it. Say "figures traced to engine results", and match label plus value where you can.
6. **The value ledger's framing.** 9,200 of returned stock is cash recovered, not profit. The 10,800 counts as a loss avoided only against a stated counterfactual (the owner would have bought all 30 boxes). "≈ 1.5 months of net profit" invites the question.
7. **The trace won't be the video's session.** The setup checklist resets per scene, and `load_seed` runs `drop_all`, which wipes `audit_log` and so restarts the hash chain. "Trace exported from the recorded session, head hash on the closing card" will cover only the last take. A reviewer who compares the trace with the video will see different action ids and the resets.
8. **The demo clock contradicts the engines.** Under D-11 the banner says Fri 23 Oct while every engine still reports as of 16 Oct, so relative text ("due in 10 days") is wrong on screen. The clock also adds R-12 attack surface.
9. **The video is too dense.** It packs about 16 distinct beats into 4:50 (photo, sales page, goal, plan, approvals, rules, clock, notification, consent, PIN, payout, board, duplicate, reconciliation, ledger, injection, jailbreak, red-team table, terminal) for reviewers who are mostly non-native English speakers. Reconciliation and the terminal shot will rush.
10. **The live URL contradicts itself.** SHOULD-8 is "replay mode, no API key on the server". A judge who types their own question gets the regex `_script`, which is exactly the "fake AI" impression CORE-01 exists to remove.
11. **The hash chain is anchored only by the published head hash.** Anyone with write access to the database can recompute the chain. Say this in the risk list.

### What's missing

1. **Authentication and authorization** (most serious). There is no identity on any endpoint. `proposed_by` is chosen by the caller. Consent, approve, lender decide and `dev/reset` are all open, and the registry key has a default in `config.py`. The plan leaves auth as SHOULD-6 (cut #4) while the security report already rates risk 12 High. With a bank panel scoring security at 30%, and a red-team table claiming 0 of N, this is the single most likely place for a reviewer to mark the entry down for overclaiming.
2. **Evidence beyond one golden shop** (serious). No value distribution, no real-world photo, no forecast accuracy and no real user input (there is no owner conversation anywhere in the repo) sits above the MVP line. Academics will read the evidence as "a tuned seed, self-graded 100%". The intent eval and red-team cases are also written by the team itself, with no public attack corpus and no testers from outside the team.
3. **Compliance as financial regulation, and financing matching** (serious). There is no control mapping to Bangladesh Bank rules on digital and small-business lending, AML/KYC (who does KYC: the lender), credit-information sharing, cost disclosure (an effective annual cost on every option), responsible lending (a ceiling tied to cash flow, not a fixed figure) or credit-intermediation licensing. Separately, financing-option matching, the first function of Topic E in the PDFs, stays at 3 products.
4. **The registration roster after Pritom left on 17 Oct.** If the registration lists three members, tell the organisers now. Compliance screening is on 21 Oct. Two members is still within the allowed 2–5, and the at-least-60% non-Chinese rule still has to hold.
5. **The 0–5 challenge bonus is forgone without a priced decision.** The PDFs say "choosing the on-chain topic does not affect scoring" and list the bonus under the unified scoring, so it plausibly applies to any topic. Up to 5 points is larger than the whole gap to the rival. The duplicate-financing registry, whose own risk row says it "needs a shared registry", is the natural on-chain case, and a Topic E rival may take it. The team rule (no blockchain) stands unless the team changes it; re-confirm it knowing the cost.
6. **Hard Q&A rows that are missing:** the Bangla question (the users, the sales books, the English-only app); "when does expiry-awareness change a decision"; "is the trace the video's session"; "how accurate is the forecast"; "who does KYC". See below.
7. **An honest replay fallback.** In replay mode, a question with no recording should say "not recorded: set `LLM_MODE=live` to ask freely". Today it silently answers with regex templates. This matters for any judge who runs `docker compose up`, since replay is the default.
8. **Unit economics as a measurable number.** The AI cost per pharmacy per month can be computed from `eval/spend.log` and the per-turn chat cost. It is cheap to add, and bankers like it.
9. **A real external sandbox for execution** (optional). Logs from a public payment sandbox would beat logs from our own simulator on item 06. It isn't needed to win, but the rival may have it.

### Top 5 changes (points per hour of work)

**Precondition: cut to one spike and rebalance.** This costs about 0 points, frees about 6 hours, and makes the MUST line deliverable.
- Trigger the follow-through from the existing supplier-reply simulator ("no reply by Friday", simulated) instead of a new dev clock. That removes the `as_of_date` mismatch and R-12 (−1.5 h).
- Reconciliation: keep the matcher and its results table (they cover the website's wording). Drop the new `payment_query` action kind and the live part of video scene 6 (−2.5 h).
- Policy: keep the PIN on Tier 3, the ceiling and Pause. Show the policy file and drop the editable Safety rules screen (−1.5 h).
- Move work off M1 within the `CLAUDE.md` ownership rules: the number check becomes a pure function in `backend/app/engines/` (Farhan) that `chat.py` calls, and the intent-eval harness and table go in `eval/` (Farhan). That saves M1 about 3 h.
- Record the insurance video as scene clips the final cut can reuse.
- Do one continuous run of the whole story, after the scene-1 reset, to export the trace and head hash.

| # | Change | Hours | Points gained (weighted /100) | Points / h | Owner (per `CLAUDE.md`) |
|---|---|---|---|---|---|
| 1 | **Make the expiry-aware limit bind, and reframe it as a borrowing base.** Show the decision it changes, using golden numbers: a naive lender would fund the full 19,000 gap, but the expiry-aware check refuses to finance the 10,800 of stock that won't sell before expiry, so at most 8,200 is financeable. Or compute a borrowing base over the whole stock book from the expiry engine. Plot it (expiry curve → sellable value → credit line), name it, have the engine confirm it, and append it to PLAN §6 | +0.5 over CORE-11 | ≈ +1.5 (II +0.25), plus better Best Innovation odds | **≈ 3** | Farhan (`engines/passport.py`, `expiry.py`) + Ishmam (lender view, consent card) |
| 2 | **Thin authentication and an honest threat model.** An owner session token issued after the PIN (reuse CORE-07's PIN hash), required on every owner write (approve, reject, consent, capture confirm, owner proposals, Pause, policy). A lender key on lender endpoints. `proposed_by` taken from the caller, not a query parameter. `/dev/*` mounted only with `DEV_MODE=true`, off in the submitted config. No default `registry_key`. Add about 6 direct-HTTP cases to PROOF-01 and re-rate risk 12 | 3 | ≈ +3 (SC +0.5), and avoids ≈ −3 if a reviewer catches the gap | **1–2** | Farhan (`api/`, `config.py`, `tests/api/`) + Ishmam (PIN/login screen, security report) |
| 3 | **A financial-regulation compliance matrix, plus an affordability rule.** Each control mapped to the rule it serves (digital and small-business lending rules, AML/KYC and who performs it, credit-information consent, cost disclosure, responsible lending, licensing, record retention, model-risk labelling of the placeholder default model). The borrowing ceiling expressed as a share of 30-day net cash flow. Verify every citation's current name and status, and mark anything unverified | 2 | ≈ +2 (SC +0.25–0.5) | **≈ 1–1.5** | Ishmam (`docs/security/`) + Farhan (policy rule, 0.5 h) |
| 4 | **Financing-option matching with a real catalogue.** Add 5–7 product archetypes, each anchored on a real Bangladeshi offer with a source per row: an MFS nano-loan, distributor trade credit, bank supplier finance, an MFI small-business loan, a refinance scheme, and an informal lender for contrast. Show eligibility reasons and an effective annual cost, and display "N matched, K eligible, cheapest first, why the rest don't fit". Keep it additive: the new products must be costlier or ineligible, so a test proves the golden plan (0 / 181.97 / 492 / ineligible; naive 421.64) is unchanged | 2.5 | ≈ +2 (TC +0.25) | **≈ 0.8–1** | Farhan (`seed/`, `engines/funding.py`, `lenders.py`) + Ishmam (funding page) |
| 5 | **A real-photo extraction eval (SHOULD-1), promoted above reconciliation's extras.** Print the eval invoices, handwrite 5 sales pages, photograph them on two phones in shop light, and add 2 printed injection pages. Put per-image rows next to the synthetic table, whatever the accuracy turns out to be. API cost < $0.02 | 2 | ≈ +1.5 (TC method credibility) | **≈ 0.75** | Farhan (`eval/`) |

**Runners-up, in order:**
- (6) The honest replay fallback, 0.5 h, Ishmam (`chat.py`).
- (7) Three to five real pharmacy-owner conversations (SHOULD-9, real only), about 2 h and no code, about +1 to +1.5.
- (8) The value simulation (SHOULD-2), 5 h, about +3, but only once 1–5 are done.
- (9) "Figures traced" wording with a label-bound check in CORE-03.

### Best Innovation / Creative Award

**As planned, the shot is low: about 1 in 10.** There is one award for the whole International Track, across six topics. Topic F is the organisers' "signature topic", where "ambitious ideas are encouraged"; autonomous agents are the natural creativity winners.

Our three innovations fall into categories judges don't usually reward as creative:
- **Safety engineering** (fidelity guard, an agent with no capability to act, the hash chain) reads as good engineering, not creativity.
- **Follow-through** ("proactive agent") is a crowded claim in 2026.
- **Expiry-aware credit** is the most original idea, but its on-screen number doesn't bind (see the scores table).

**How to raise it:**
1. Make one invention the headline, and make it binding and visual. "Shelf-life credit" fits: a credit line computed from photographed paper, which shrinks as stock ages and triggers return proposals before the return window closes. It joins the expiry engine, the passport and the follow-through in one loop. Give it a 20-second animated beat in the video and its own deck slide with before and after numbers.
2. Name the design pattern ("an agent that can plan for a week but can't spend a taka"), with the fidelity guard as its run-time proof.
3. Frame the HMAC registry honestly: lenders can detect double financing without seeing invoices, through keyed commitments, with PSI as the next step. This fits WeBank's interest in privacy-preserving computation without overclaiming federated learning.
4. Use the departures-board visual consistently across the deck and the video. It is the most memorable design asset.

### Deadline risks to flag now

- **Registration:** confirmation (UNK-001) and the roster after Pritom left. Both must happen today.
- **G2, 19 Oct 12:00:** the insurance video is about 14 hours away, overnight, and M1 makes it alone. Start it before any new feature.
- **G3, 19 Oct 23:59:** the full new story isn't achievable with the current split. Commit to Level B plus the precondition cuts at G1, not at G2.
- **The trace:** take it from one continuous run (see item 7 under "What's weak"), and state in the README which run it is.
- **Going public:** `.env` is ignored and has never been committed (I checked the history), but scan the history anyway. Move the "shares" table, "Pritom left" and the team rules out of the README's first screen. The README still says capture "returns a stored draft until the extraction agent is in place".
- **Links:** test every link logged out, keep a mirror, and attach the MP4 and PDFs if the channel allows. The 24-hour bilingual reminder is the last checkpoint.

### Hard judge questions the plan's Q&A doesn't yet answer

| Question | Honest answer the team needs (after the changes) |
|---|---|
| "Your approve endpoint has no authentication. How is 'only the owner approves' enforced against anyone except the LLM?" | Today it isn't. After change 2: an owner session issued after the PIN, a lender key, dev routes off, and a test for each case |
| "Your 36,998 and 45,120 limits both exceed the 8,200 loan. When does expiry-awareness ever change a lending decision?" | After change 1: it refuses to finance the 10,800 of stock that won't sell, with the number on screen |
| "'7 of 7 figures verified': verified that the number appears in a tool output, or that it is the right number for the right thing?" | Traced, not verified, unless the label is checked too; say which |
| "Bogura owners keep their books in Bangla. The app, the chat and the sales-book eval are English. Who is the real user?" | English for this competition; Bangla UI and handwriting are next; the engines are language-neutral |
| "Is the submitted log the same session as the video? The old trace's 38 events span about one second" | One continuous run, its head hash published; the scripted trace is labelled as such |
| "How accurate is your cash forecast?" | It is a deterministic dues calendar plus average sales; no backtest yet (COULD-2); this is a known limit |
| "Who does KYC and AML on the borrower? Is LaMP a credit intermediary?" | The lender does KYC; licensing is risk 10; the compliance matrix from change 3 shows the rest |

---

## Product review

Written by the judge agent. Rows come from the **official rubric in `plan/problem.md`**, never from a generic list. Only verified, demo-visible evidence counts.

### Review — `<time>`, gate `<G?>`

| Criterion (from problem.md) | Weight | Evidence judges would see | Score /5 | Gap / likely question |
|---|---|---|---|---|
| — | — | — | — | — |

### Likely judge questions

| Question | Our answer | Proof to show |
|---|---|---|
| — | — | — |

### Top 3 fixes (points gained per hour, within the current gate)

1. —
2. —
3. —

---

## Plan review — round 2 (re-plan v2), 18 Oct 2026, late evening (Bangladesh time)

Written by the judge agent in plan review mode, in a fresh context. I read every file in `plan/` in full (all 33 MUST rows, the 8 SHOULD and 7 COULD rows, the whole cut list, win-plan §9), both PDFs (text extracted page by page), the website capture and the round-1 section above. I scored v2 on its own first, then checked each round-1 finding against it, and checked the repo wherever a claim depends on it. Nothing was run. The one figure I computed myself (the borrowing base) replicates the engine formulas on the seed and is marked approximate.

**Verdict in one line.** v2 adopts every round-1 change on paper and removes most of the overclaims. But it does this by adding about 15 net hours to a plan that was already over capacity, and the items that answer round 1's method concerns now sit at Level C, beyond the A + B the plan itself recommends. At the level the team can reach, it scores about where v1 did: **73 vs the rival's 74.** Three changes put it clearly ahead: close the read path, re-sequence the ladder so that reconciliation, the visible plan and the intent eval land at A + B, and give shelf-life credit a number of its own.

**Source check.** `plan/problem.md` is still faithful. It records one fact that the plan doesn't use: the prizes are per track, not per topic. There is one First, Second and Third Prize and one Best Innovation Award for the whole International Track (PDF A p4, PDF B §7). LaMP competes with the best entry from all six topics, including Topic F entries that can earn the 0–5 on-chain bonus.

**Repo facts I checked this round.** Nothing from v2 is built yet: the last commit (`7074b8f`) predates the plan, and G0 is still open.
- `tests/` still has 98 `def test_` functions. There is no service worker in `frontend/`.
- `backend/app/api/routes.py`: **every route is open, reads included.** That covers `GET /pharmacies/{pid}/accounts`, `/forecast`, `/passport`, `/captures/{cid}` and `/consents`, plus `/logs`, `/logs/export` and `/logs/stream`. In `backend/app/agents/router.py`, `POST /chat` accepts any `pharmacy_id` with no identity and can run every read tool plus `propose_action`. **CORE-13 as written protects writes and lender endpoints only.**
- `config.py` still ships `registry_key = "dev-registry-key-change-me"`. `/dev/reset` is still ungated, and `proposed_by` still comes from the query string.
- The golden "Short 19,000" exists only after three captures. The committed trace shows 14,380 at reset, 20,580 after invoices F and H, and 19,000 after the sales page. The plan handles this by filming the hook after scene 2, but the video order and the trace order will then differ.
- Shelf-life arithmetic: the 10,800 is the trim engine's output, (30 − 12) × 600. The sales rate behind it is 90-day purchases / 90, a purchase proxy documented in `expiry.py`. "Financeable 8,200" is the trimmed shortfall, 19,000 − 10,800.
- **The borrowing base never binds.** I replicated `sales_rates` and `sellable_qty` on the seed's stock batches. 75.2% × sellable value is about 137,700 today and about 130,900 from day 30 to day 90 (approximate; the two captured invoices add a little). It never comes near the 8,200 or 19,000 needs, so the curve the plan wants to animate changes no decision.
- `deck/README.md` says the photos and cut-outs "come from BCOLBD" and that the icons in `assets/bc/` are reused from it. No licences are recorded.
- The seed's `as_of_date` (16 Oct 2026) and the follow-up deadline (23 Oct) are both Fridays, the weekly holiday in Bangladesh.
- `CLAUDE.md` gives Farhan the README's "Run it" section but assigns the rest of `README.md` to nobody. `agents/router.py`, where `/chat` would get its auth dependency, is Ishmam's file, not Farhan's.

### Strongest rival, concretely

**Rival E (the best Topic E entry).** I keep round 1's rival because it is still the right benchmark: 4–5 strong engineers working since late August on an "SME CFO agent" for warungs or food stalls.
- Reconciliation is a core screen with an exceptions queue; it reads bank-statement CSVs and receipts.
- 15–25 sourced loan products with APR.
- Payments go through a third-party test-mode sandbox.
- A forecast backtested on a public retail dataset (MAPE), and value measured across 100+ simulated SMEs.
- A live URL with a demo login.
- JWT roles, OTP above a threshold, a guardrail model and an attack-success rate.
- An IM bot, generative cards and voice.

Its weak spots: a generic domain, safety that rests on prompts and thresholds, no run-time check of the model's figures, and no tamper evidence.

**Rival F (the best entry track-wide; illustrative).** A Topic F wallet agent on a public testnet:
- a smart account whose session keys and on-chain spending limits are its permission tiers;
- intent → plan → transaction simulation → user signature;
- real transaction hashes as its execution evidence (item 06's on-chain wording);
- a 2–4 point challenge bonus.

It is the organisers' "signature topic", where "ambitious ideas are encouraged", so it is also the natural Best Innovation candidate.

### Scores

Each column assumes the team builds exactly that level of the plan and claims only what it built.

| Criterion | Weight | Ours: full MUST (A+B+C) | Ours: A+B (recommended) | Ours: A only | Rival E | Gap and why |
|---|---|---|---|---|---|---|
| Task completion | 40% | **4.0** | **3.5** | 3.25 | **4.0** | **Full MUST: parity.** Ours is ahead on a coherent, verifiable sandbox week (one-run trace, hash chain) and on domain depth, and the catalogue and real photos close two round-1 gaps. Ours is behind on external counterparties (every lender, supplier and payout is our own simulator), on a live URL (Level D) and on any backtest on real data. **At A+B it drops half a point.** Reconciliation (one of the three functions in the website's Topic E wording), the visible plan, the intent eval and the value simulation are all Level C, so "measured beyond one shop" rests on real photos alone. **At A** there is no follow-through, wallet or catalogue, and the video is the insurance cut of today's story |
| Security & compliance | 30% | **4.0** | **4.0** | 3.5 | **3.5** | **Ahead on design:** an agent with no capability to act, auth on writes, the PIN, Pause, traced figures, the hash chain, a red-team that includes direct HTTP calls, and a financial-regulation matrix. **Not the strategist's 4.5:** (1) the read path stays open, so "the lender sees only what the owner shares" (scene 6) is false at the API; (2) consent scopes still don't filter fields (risk 6, SHOULD-5); (3) the PIN that opens the session is also the step-up; (4) the matrix is a desk mapping with "to verify" rows; (5) the cost-disclosure row rests on a mislabelled "effective annual cost". With change 1 below it reaches 4.25. **At A** there is no red-team table and no PIN tier |
| Innovation & interaction | 30% | **3.75** | **3.5** | 3.0 | **3.5** | **Ahead** on domain insight, and on proactivity without any power to spend. **Held back:** the headline number restates the trim already shown in scene 3; the borrowing-base curve never binds; the wow's "lock-screen notification" needs Web Push (SHOULD-3, Level D); there is no IM, voice or generative cards at any MUST level. **At A+B** the plan checklist is missing too. **At A** the deck is the old 25-slide one |
| **Weighted /100** | | **78.5** | **73** | **65** | **74** | |

**Rival F, for the ranking:** TC 4.0, SC 3.75, II 4.0 gives 78.5, plus a 2–4 point bonus, so about 80–82. It is a guess, but it shows that the benchmark for First Prize is the whole track, not the topic.

**What score is realistic:**
- **The strategist's expected 83–85 (full MUST) and 81 (A+B) are 5–8 points high.** The differences: SC 4.0, not 4.5; II 3.75 (3.5 at A+B), not 4.0; TC 3.5 at A+B, not 3.75.
- **A + B is the ceiling, not the expectation** (see capacity below). By the 20 Oct 18:00 freeze the team can realistically deliver Level A plus about two-thirds of B: **≈ 70–72**.
- **With the five changes below:** ≈ 78 if A + B lands (TC 3.75, SC 4.25, II 3.75). The changes cost about 5 hours more than A + B, 4 of them Farhan's, and Farhan has the slack at A + B (≈ 26 h vs Ishmam's ≈ 32 h). At the realistic two-thirds of B, they still lift the score to ≈ 74–75, because they move score-dense items forward.

**Mode, honestly.** Counted from tonight, this is a 43-hour build, which is SPEED territory under the kit's own rule. The plan's de facto spike is security & compliance, and that is the right choice: it is the 30% criterion where the plan clearly beats the rival, while task completion's 40% can't be won outright against external sandboxes. Spend the spike's hours on closing the read path before the wallet and the ceiling.

### Five-capability check (website brief), at Level A + B

| Capability | Our proof at A+B | Rival E's proof | Verdict |
|---|---|---|---|
| Intent understanding | Recorded live chats; the honest offline message; the real-photo eval (PROOF-03) | Multi-turn chat; OCR on real receipts | **Par.** The intent eval (PROOF-02) is Level C, so there is no intent number |
| Task planning | The fallback planned on day 0 and carried out on the simulated supplier event (CORE-04) | A plan graph | **Ahead** on planning over time, but there is no visible checklist (CORE-02 is Level C) |
| Safe execution | Auth on writes, PIN, Pause, traced figures, hash chain, red-team including HTTP | Thresholds, OTP, a guardrail model, an attack-success rate | **Ahead**, except for the open read path |
| User control | Per-step approval, conditional approval, PIN, Pause, consent | Approve buttons, settings | **Ahead** |
| Measurable value | 0–182 vs 422; 10,800 not financed; ledger ≈ 20,240 with counterfactuals; unit economics. All from one shop | 100+ SMEs vs a baseline; MAPE | **Behind**: the value simulation is Level C |

### Round-1 findings: fixed, or only reworded?

| Round-1 finding | v2's answer | Verdict |
|---|---|---|
| Precondition: one spike, rebalance, free ≈ 6 h | Clock dropped, reconciliation thinned, rules view read-only (≈ −5.5 h); every MUST classed as Core, Proof, Coverage or Deliverable | **Reworded, not fixed.** MUST grew from 59 h to 74 h. The classes are labels: Core still holds three new features (wallet, notifications, policy). The deep feature's own pieces (CORE-04/05/06/07) rank 18–21, at Level B. So at Level A the one deep feature doesn't exist, although the cut list calls the follow-through and the Tier-3 PIN "never cut" |
| Weak 2: load on M1 | M1 ≈ 38 h, M2 ≈ 36 h; A+B ≈ 32 / 26 (30 / 28 with M2 drafting) | **Improved, but still over capacity.** About 43.5 clock hours remain from tonight to the freeze, two nights included. 30–32 productive hours for M1 leave no slack for integration or for a restarted continuous run (R-23). Some of M1's work isn't costed at all: the 20-second shelf-life animation, the outside-tester sessions and the owner conversations planned for "today" |
| Top change 1: make the expiry limit bind | Shelf-life credit (requested 19,000 → financeable 8,200 → refused 10,800) plus the borrowing-base curve | **Partly.** It now changes a number, but: (a) it is the trim restated, with the same 10,800 and 8,200 in scene 3 and again in scene 4; (b) nobody requests 19,000 in the run, so "Requested" is a computed counterfactual and must be labelled that way; (c) the curve never binds (≈ 137,700 → 130,900 against needs of 8,200–19,000); (d) not lending against stock that won't sell before expiry is standard asset-based lending practice ("ineligible inventory"), so calling it an "invention" invites a deflating question from a WeBank expert. What is new is the data source and the timing, and the plan should say so |
| Top change 2: thin auth | CORE-13, Level A, rank 8; ≥ 6 HTTP cases | **Partly.** Writes and lender endpoints are covered. Reads, `/chat` and the log stream are not, so the consent story and "only the owner" are still false for a plain GET. Also, "reusing CORE-07's PIN hash" inverts the dependency, because CORE-07 is Level B |
| Top change 3: regulation matrix plus an affordability rule | DOC-03 (Level A); a cash-flow ceiling in CORE-07 | **Mostly.** The matrix is right. But the ceiling's parameter is "set by the team; must keep the golden 8,200 eligible". That is tuning, not a lending norm. And cut-list row 14 can drop the ceiling while the matrix still cites it. Name a sourced norm (e.g. repayment as a share of projected net cash flow over the tenor), or present the ceiling as "designed, not built" |
| Top change 4: sourced catalogue | CORE-14, Level B | **Fixed in the plan, with one new error.** The "1% ≈ 73% a year" figure is labelled "effective annual cost" and used as the cost-disclosure control. Disclosure rules quote APR on the amount financed, which is 12.2% here (492 on 49,200 for 30 days); 73% is the annualised cost of covering only the 8,200 gap. Show both, with the tenor (the wallet loan runs 90 days, the supplier credit 30). Also, the rule "new products must be costlier or ineligible" must follow from each product's real terms, never be chosen to protect the golden plan |
| Top change 5: real-photo eval | PROOF-03, Level B | **Fixed.** Say that the team handwrote the sales pages |
| Missing 1: authentication | CORE-13 | **Partly** (see top change 2) |
| Missing 2: evidence beyond one shop | PROOF-03/04 made MUST; outside testers | **Partly.** At A+B, only the real photos and the outside red-team testers land; PROOF-02 and PROOF-04 are Level C. PROOF-04 is also still on the cut list (row 9), even though the cut list's header says the proof items left it |
| Missing 3: financial regulation and financing matching | DOC-03, CORE-14 | **Fixed in the plan**, apart from the 73% caveat |
| Missing 4: the roster | SUB-01, UNK-015, R-19, G1 | **Fixed as an action, still open in fact.** Do it tonight |
| Missing 5: the challenge bonus | A priced team decision at G1 | **Accepted as a decision, but priced against the wrong rival.** The bonus matters because Topic F entries compete for the same track-wide prizes |
| Missing 6: hard Q&A rows | Seven rows added | **Fixed.** New hard questions are below |
| Missing 7: honest replay | CORE-01, Level A | **Fixed** |
| Missing 8: unit economics | DOC-04, Level A | **Fixed** |
| Missing 9: external sandbox | Declined (COULD-8) | **Acceptable**, and stated as a known gap |
| Weak 5: "verified" | "Traced", label-bound | **Fixed in wording, with a new risk.** The scene-3 answer's "18 boxes" (30 − 12), "20 days" and "Fri 23 Oct" are not engine outputs, and D-08 blocks any answer with an untraced figure. Define what counts as a figure, and test the guard on the exact recorded answers |
| Weak 6: ledger framing | A basis and a counterfactual per line | **Fixed, with one hole.** The run sheet never approves the 9,200 return claim (scene 5 approves only the trim and the extension), so `GET /value` won't contain it. Add it to scene 5 or to the click script |
| Weak 7: the trace isn't the video's session | One continuous run | **Fixed.** Add a caption saying the hook was filmed after the captures |
| Weak 8: the dev clock | Dropped | **Fixed** |
| Weak 9: video density | 10 scenes, ≤ 13 beats | **Partly.** Scene 4 still packs the card, a 10-second animation, the curve, the catalogue and the cost line into 35 seconds; scene 6 packs nine steps into 50 seconds |
| Weak 10: the live URL | Live mode under a daily cap | **Fixed in the plan**, at Level D |
| Weak 11: hash-chain anchoring | R-20; head hash published | **Fixed** |

### What is still weak

1. **The ladder contradicts the never-cut list.** The follow-through and the Tier-3 PIN are "never cut", yet both sit at Level B behind 17 other items, while Level A spends about 7 hours on documents. If the team stops at A, the product has no deep feature.
2. **Scope grew instead of shrinking.** v2 added about 21 hours and removed 5.5. The ladder is honest, but the deck, video and docs are written for the full MUST, and each needs a version that claims only A + B.
3. **The headline invention has no number of its own.** Every figure it shows is either the trim's or comes from a curve that never binds (see change 4).
4. **The wow depends on a Level D item.** The plan promises a "lock-screen and desktop notification", but a phone lock screen needs Web Push (SHOULD-3), and level-1 notifications only work while the page is alive. The plan's own rule is "never fake a notification", so say "desktop notification" unless SHOULD-3 lands.
5. **The step-up uses the same factor as the login.** The PIN that issues the session is the PIN re-entered at approval. That is re-authentication at the point of approval, not a second factor, and the security report should say so.
6. **Domain details a Bangladeshi reviewer would notice:**
   - Both the as-of date and the supplier deadline fall on a Friday.
   - City Bank–bKash nano-loans are retail loans to individuals (about BDT 3,000 on average, per the idea brief), so using one to pay a pharmacy's supplier bill needs a sentence in the matrix and a Q&A row.

### What is missing

1. **Authorisation on reads, the chat and the log stream** (the most serious gap). One router-level dependency on `/pharmacies/{pid}/*`, `/chat` and `/logs*` is cheaper than the per-write checks the plan describes. Use an HttpOnly cookie so that the SSE `EventSource` keeps working.
2. **The track-wide view.** The rival analysis, the bonus price and the Best Innovation odds all consider Topic E only, but all six topics compete for the First Prize and the Innovation Award.
3. **Reconciliation at the level the team will actually reach.** It is one of the three functions in the newest Topic E wording, and it sits at rank 26.
4. **A measured number for shelf-life credit across many shops:** how often it changes the financed amount, and how much financed stock would have expired.
5. **Image licensing at Level A.** It is now folded into the deck rebuild (Level B). If the team stops at A, the submitted deck still carries photos and cut-outs whose licences aren't recorded.
6. **An owner for the README.** `CLAUDE.md` assigns only its "Run it" section. Ishmam owns `CLAUDE.md` and should assign the rest before SUB-02 and DOC-01 start.
7. **A decision on `plan/` before the repo goes public.** The folder is untracked today, and it holds rival scenarios and award odds (this review included). Keep it off the judge path, and never rewrite history to hide how the entry was built.

### Top 5 changes (points per hour of work)

**Precondition, tonight (survival, not points):**
- **Registration:** confirmed with the two-member roster. With two members the team is at the minimum size, and the 60% rule means both must be non-Chinese nationals.
- **Channel:** ask the organisers how to submit.
- **Licensing:** replace the BCOLBD photos, cut-outs and icons with app screenshots or images with a recorded licence, and remove the lines in `deck/README.md` (about 1 h, moved to Level A).
- **Secrets:** scan the history before the repo goes public.

| # | Change | Hours | Points gained (weighted /100) | Points / h | Owner (per `CLAUDE.md`) |
|---|---|---|---|---|---|
| 1 | **Close the read path.** Require the owner session on every `/pharmacies/{pid}/*` route (read or write), on `/chat` and on `/logs*`. Lenders read only consented data, through the lender endpoints, with their key. Add four HTTP cases: passport without a session → 401; a lender key on an owner read → 403; chat without a session → 401; the log stream without a session → 401 | +0.5 over CORE-13 | ≈ +1.5 (SC +0.25), and avoids ≈ −1.5 to −3 if a reviewer runs one GET after hearing the consent line | **3–6** | Farhan (`api/`, `main.py`, `tests/api/`) + Ishmam (`agents/router.py`, frontend credentials) |
| 2 | **Re-sequence the ladder** to match the never-cut list and the topic wording. Into Level A: a thin CORE-04 ("declined" → scheduler proposal) and the PIN at approve. In Level B: merge CORE-05 and CORE-12 into one "sandbox account with a statement and a matcher" (about 5 h instead of 7), and add a thin CORE-02 and a 20-question PROOF-02 (at least 8 questions from outside the team). Down to Level C: the cash-flow ceiling, the rules view, the borrowing-base curve and its animation, and red-team cases beyond 15 | ≈ +1 net | ≈ +3.5 (TC +0.25, II +0.25) | **≈ 2–3** | Ishmam (gatekeeper, plan) with Farhan |
| 3 | **Fix the cost disclosure.** Every option shows APR on the amount financed, its tenor, and the cost of covering this gap in BDT and as a % of the need. The 73% line becomes "6.0% of the 8,200 gap for 30 days", shown next to "APR 12.2% on 49,200". Compare the options over the same horizon, or say that they differ | 0.5 | ≈ +0.75, and avoids a banker finding that the cost-disclosure control is misstated | **≈ 1.5** | Farhan (`engines/funding.py`, `schemas/`) + Ishmam (funding page, deck) |
| 4 | **Give shelf-life credit a number of its own, and frame it honestly.** Add a Level B value simulation focused on it: ≥ 200 perturbed pharmacies through the real engines, purpose-blind lending vs shelf-life credit. Report the share of cases where the financed amount changes, the financed stock that expires unsold (median and P10–P90), interest, and the need left unfinanced. Publish the seed and label it synthetic. **Framing:** "the ineligible-inventory rule asset-based lenders use, computed per batch from photographed invoices before the purchase, with one number shared by owner and lender". Show the curve only if it binds somewhere in the simulation | ≈ 3 | ≈ +3 (TC +0.25, II +0.25), plus better Innovation Award odds | **≈ 1** | Farhan (`eval/`, `engines/passport.py`) + Ishmam (slide 8, scene 4) |
| 5 | **Make scene 3 safe from its own guard.** "Figures" means BDT amounts and rates, label-bound; counts and dates are named separately ("7 of 7 money figures traced"). The funding-plan tool returns the derived counts the answer uses (18 boxes). A test runs the guard on the exact recorded answers before G3 | 0.5 | ≈ +0.5 (protects scene 3, the badge and the red-team's untraced-figure row) | **≈ 1** | Farhan (`engines/fidelity.py`, engine outputs) + Ishmam (`chat.py`, `test_chat.py`) |

**Runners-up, in order:**
- (6) Real owner conversations (SHOULD-9): about 2 h, +1 to +1.5, and only if they are real.
- (7) Web Push (SHOULD-3): 2.5 h plus a dependency Farhan must add; about +0.5, and it makes the lock-screen claim true.
- (8) Move the follow-up deadline to Thursday 22 Oct (needed_by − 4 days): minutes.
- (9) One matrix row and one Q&A row on using a retail nano-loan for a business bill.

### Best Innovation / Creative Award

**As planned: about 1 in 8** (round 1: 1 in 10). v2 does what round 1 asked: one named invention, one named pattern and one visual language. Three things hold it back:
- **The invention's numbers are the trim's numbers.** A reviewer who watched scene 3 sees nothing new in scene 4, and a banker recognises the ineligible-inventory rule.
- **The award is track-wide.** Topic F entries are told that "ambitious ideas are encouraged", and an autonomous on-chain agent looks more creative than any safety design.
- **The most creative part of the entry is undersold.** One per-batch shelf-life number drives two decisions from the same photographed paper: the owner orders 18 fewer boxes, and the lender lends 10,800 less. That loop, measured across simulated shops (change 4), is the creative claim. "We invented credit that refuses expiring stock" is not.

**With change 4 and the honest framing: about 1 in 6.**

### Hard judge questions the plan still doesn't answer

| Question | Honest answer the team needs |
|---|---|
| "Your consent screen says the lender sees only what the owner shares. Why does `GET /pharmacies/green-life/passport` answer anyone?" | After change 1: every pharmacy read needs the owner's session, and lenders see only consented data, through their own endpoints |
| "Isn't shelf-life credit the ineligible-inventory haircut every asset-based lender applies?" | The concept, yes. What's new is computing it per batch from photographed paper, before the purchase, for shops with no stock system, so the owner and the lender see the same number. The simulation shows how often it changes the loan |
| "Who requested 19,000? I don't see it in your log." | Nobody in the run. It is the loan a purpose-blind lender would make for the full gap, computed and labelled as such |
| "1% supplier credit at 73% a year? That isn't an APR." | After change 3: the APR is 12.2% on the 49,200 financed; 73% is the annualised cost of covering only the 8,200 gap |
| "Your 9% loan runs 90 days and the supplier credit 30. Why compare their costs in taka?" | After change 3: costs over the same horizon, or the difference stated |
| "City Bank–bKash nano-loans are retail products. Is it responsible lending to pay a pharmacy's supplier bill with one?" | This needs a researched answer, and a matrix row, before the deck is final |
| "How did you choose the cash-flow ceiling's parameter?" | From a sourced norm, or "designed, not built". Never "so that our demo loan passes" |
| "The PIN that opens the session is the same PIN you ask for at approval. Where is the second factor?" | There isn't one. It is re-authentication at the point of approval; device binding or an OTP is the production step (R-22) |
| "Was the app open when the lock-screen notification arrived?" | Honestly yes, unless Web Push (SHOULD-3) is built. Otherwise show only the desktop notification |

### Things that could endanger the submission or the screening

- **Registration and roster** (UNK-001, UNK-015): still open. Two members is the minimum team size, and under the 60% rule both must be non-Chinese nationals. Do it tonight, not at G1.
- **Licensing:** the deck reuses photos, cut-outs and icons, and a public README names where they came from. Move the fix to Level A.
- **Repo access and hygiene:**
  - The repo is private.
  - The README's first screen is still internal (shares of 49% / 51%, "Pritom left", the team rules).
  - `plan/` is untracked.

  Scan for secrets, then make the repo public or give reviewers access, and keep `plan/` off the judge path.
- **The continuous run:** if it breaks mid-way (R-23), label the trace "scripted", as planned. Never present a stitched run as one session.
- **Timing:** nothing from v2 is built yet, G0 is still open, and about 43.5 hours remain to the freeze. Approve the plan and commit to a level tonight, not at 09:00 tomorrow.

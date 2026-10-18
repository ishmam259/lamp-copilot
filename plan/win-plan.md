# Win plan (full re-plan of LaMP-Copilot), v3 final, after judge round 2

> Written by the strategist on 18 Oct 2026 as a full re-plan from first principles of an entry that already works, then revised twice from the independent judge's reports (`judge-review.md`, rounds 1 and 2). Per the team's instruction the plan is **not cut to fit the build time**. Every item carries an honest cost, a points-per-effort rank and a scope-ladder level, so the team chooses. Event facts come from `plan/problem.md` only; team facts from the repo.

**Status:** APPROVED (after two judge rounds) · **Approved by / time:** Farhan, 18 Oct 2026

Companion files: `plan-summary.md` (the one-page approval page), `problem.md`, `requirements.md` (ladder and ranks), `demo-flow.md`, `pitch.md`, `cut-list.md`, `risks.md`, `architecture.md`, `task-board.md`, `judge-review.md`.

---

## 1. How this event is won (decoded from the sources)

| Item | What the sources say | Source |
|---|---|---|
| **Event mode** | **SPEED, with one spike** (changed in v3). The event runs over weeks, but counted from tonight the build is about **43.5 hours, two nights included**, which is SPEED territory under the kit's rule. The judge called v1 and v2 "a breadth plan with a DEPTH label", and it was right. **The spike is security & compliance, as "safe agency": it can plan for a week, but it can't spend a taka.** That is the 30% criterion where we clearly beat the strongest Topic E rival, while task completion's 40% can't be won outright against rivals using external sandboxes. The spike is built properly and proven from outside: a closed API (reads, chat and log stream included), PIN re-entry at approval, Pause, money figures traced by code, a hash-chained one-run trace, correct cost disclosure, a financial-regulation matrix and red-team results that include direct HTTP calls. Everything else is thin: the follow-through, shelf-life credit, the account with its matcher, the catalogue | problem.md; judge rounds 1–2 |
| Rubric | Task completion **40%** · Security & compliance **30%** · Innovation & interaction **30%** · challenge bonus 0–5 for "on-chain exploration". **Bonus: forgone by the team's rule "no blockchain". Cost, stated plainly: up to 5 points if it applies to Topic E (UNKNOWN, plausible). Prizes are per track, so Topic F on-chain entries compete for the same First Prize and Innovation Award; the judge prices an illustrative Topic F rival at ≈ 78.5 plus 2–4 bonus points. Keeping or changing the rule is the team's decision, tonight** | PDF A p2, p4; PDF B §3, §7 |
| When judges first see the product | Online review from 23 Oct (screening 21 Oct), package only. **Deadline 20 Oct, 21:59 Bangladesh time** | WEB, PDF A |
| Judging format | Asynchronous review by "WeBank industry experts and university scholars"; some open the code; finalists defend on 22 Nov | PDF A p4, WEB |
| What judges look for | "intent understanding, task planning, safe execution, user control and measurable value"; "AI as a Financial Participant"; "completing real tasks"; "permission-tier implementation and known-risk list"; "simulated-account/sandbox operation logs and demo video" | WEB, PDF A |
| Hard requirements | Registration with a correct roster (two members is the minimum, and the 60% rule then means both are non-Chinese nationals); six deliverables; English; properly licensed assets; no changes after the deadline; one finalist attends | PDF A/B |
| Emphasis | Agency; safety and proof (3 of 6 deliverables); Topic E: financing matching first (PDFs), plus reconciliation and operational recommendations (website); the organisers' "safety + experience" and "apps and IM" taste | PDF A/B, WEB |
| Provided systems | None. Leverage is the wording, the schedule and the reviewers' interests | problem.md |

**Decoding conclusions**

1. **The five capabilities are the scoring script.** Every scene, slide and doc section is labelled with the one it proves; a one-page judge's guide maps each to a timestamp, a slide, a file and a number.
2. **The video, deck and docs are the product, and reviewers open the code.** Every claim must survive a plain GET, a read of the code and a look at the trace.
3. **"Participant", not "assistant".** It follows up over time and reaches the owner, without any power to spend.
4. **Measured beyond one shop**, with honest labels (synthetic, team-handwritten, outside testers).
5. **For a bank panel, compliance means financial regulation**, and cost disclosure must be stated the way disclosure rules state it (APR on the amount financed, tenor).
6. **Financing matching is Topic E's first function**; reconciliation is in the newest wording.
7. **The benchmark is track-wide.** Topic F entries (signature topic, on-chain evidence, a bonus) compete for the same prizes.

---

## 2. The win thesis

**Average Topic E entry:** a GPT chat over a statement CSV for a generic shop, often doing arithmetic itself; a dashboard and rule-matched loans; a system prompt and an Approve button; mock data.

**Rival E, the strongest Topic E entry** (judge's version): 4–5 engineers since late August on an "SME CFO agent". Reconciliation is a core screen; 15–25 sourced loan products with APR; payments through a third-party test sandbox; a backtested forecast; value across 100+ simulated SMEs; a live URL; JWT, OTP thresholds, a guardrail model, an attack-success rate; an IM bot, generative cards, voice. **Weak spots:** a generic domain, safety resting on prompts and thresholds, no run-time check of the model's figures, no tamper evidence.

**Rival F, the strongest track-wide entry** (illustrative): a Topic F wallet agent on a public testnet. Its permission tiers are session keys and on-chain spending limits; it runs intent → plan → simulation → user signature, submits real transaction hashes as execution evidence, and earns a 2–4 point bonus. It is the natural Best Innovation candidate. **We can't out-blockchain it under the team rule.** We beat it, if at all, on real-world grounding (a real SME problem, measured value) and on safety you can check from outside without a chain.

**Our visible differentiators:**
1. **The spike, safe agency: "it can plan for a week, but it can't spend a taka."**
   - The API answers nothing without the owner's session, reads included; lenders see the passport only through their own endpoints after consent.
   - Loans need the PIN re-entered at approval.
   - Pause stops all agent and scheduler proposals.
   - Every money figure in the copilot's answer is traced by code to the engine field it names.
   - The trace is hash-chained and comes from the video's own session.
   - The red-team table includes 10 direct HTTP calls and attempts by outside testers.
   - Cost disclosure is correct, and a financial-regulation matrix maps each control to its rule.
   - *SC; SE, UC.*
2. **The demo story: follow-through.** The fallback planned on day 0 is carried out when the supplier doesn't answer by Thu 22 Oct: a desktop notification, then an approval with consent and the PIN, a sandbox payout, and the board flips. *TP, UC.*
3. **The idea: shelf-life credit, framed honestly.** It is the ineligible-inventory rule asset-based lenders use, now computed per batch from photographed invoices, before the purchase, for shops with no stock system. **One number drives two decisions:** the owner orders 18 fewer boxes, and the lender lends 10,800 less than a purpose-blind lender would (a computed counterfactual of 19,000, labelled as such). At Level B a simulation across ≥200 perturbed pharmacies gives the idea its own number: how often it changes the financed amount, and how much financed stock would have expired unsold. *II, MV.*
4. *Supporting:* honest prices (APR, tenor and the cost of covering this gap for every option), a sourced catalogue at B, and the sandbox account with statement matching at B.
5. *Supporting:* evidence beyond one shop: real phone photos (sales pages handwritten by the team, said so), intent questions and attacks from outside the team, and the shelf-life simulation.

**Best Innovation / Creative Award** (judge: about 1 in 8 for v2, about 1 in 6 with the simulation and the honest framing). The creative claim is the loop, not a rule: one per-batch shelf-life number, from the same photographed paper, drives the owner's order and the lender's limit, and the simulation measures it. Add the named pattern ("plans for a week, can't spend a taka") and the departures-board visual throughout. The award is track-wide, so this is a long shot; the plan doesn't depend on it.

**Product / promise / persona:**
- **LaMP-Copilot**: "An AI finance officer for neighbourhood pharmacies. It finds the cheapest money, starting with the cash you already have, and it never moves a taka without you."
- Persona: Green Life Pharmacy, Bogura (fictional, illustrative).
- **Story:** "A lender that doesn't look at the shelf would have lent Green Life 19,000, 10,800 of it against medicine that won't sell in time. LaMP lent nothing against that stock, and when the supplier didn't answer, it came back with a BDT 182 fallback that only the owner's PIN could release."

**The "wow" moment:**
1. "Simulated supplier event: no reply from Supplier A by Thu 22 Oct."
2. A **desktop notification**. The phone lock screen appears only if Web Push (SHOULD-3) is built.
3. One click: consent and PIN.
4. The sandbox payout lands, and the board flips red → green (the account flip is Level B; Level A shows the payout reference and log line).

---

## 3. Demo story (video ≤5:00, one continuous run; full run sheet in `demo-flow.md`)

1. **Hook (0:00–0:15):** "Short BDT 19,000 · Mon 26 Oct", captioned "filmed after the captures, same session".
2. **INTENT UNDERSTANDING (0:15–0:45):** photo → a field corrected → totals checked → saved.
3. **INTENT UNDERSTANDING → TASK PLANNING (0:45–1:35):** free-form goal → answer (trim 18 boxes = 10,800 → 8,200; extension free; fallback 181.97 vs 421.64) → "N of N money figures traced"; checklist at B.
4. **SHELF-LIFE CREDIT (1:35–2:05):** the card (counterfactual 19,000 → financeable 8,200; one number, two decisions); cost lines (APR 12.2% on 49,200 for 30 days, 6.0% of the gap; APR 9% on 8,200 for 90 days); simulation result at B.
5. **USER CONTROL (2:05–2:35):** approve the return claim, the trim and the extension request; fallback "only if no reply by Thu 22 Oct · PIN"; Pause.
6. **Follow-through (2:35–3:35):** simulated "no reply" → desktop notification → consent and PIN → payout → board flips (B).
7. **MEASURABLE VALUE (3:35–3:55, B):** ledger with bases; statement matching found a duplicate payment.
8. **SAFE EXECUTION under attack (3:55–4:25):** injection photo; `GET passport` and `POST approve` without a session → 401; duplicate financing refused; red-team table (B); chain intact.
9. **PROOF (4:25–4:42):** delivered numbers only; real vs sandbox.
10. **Close (4:42–4:50).**

---

## 4. Criterion-by-criterion strategy

| Criterion | Weight | Top score looks like | What we show | Proof on screen | What we say | Cost | Risk |
|---|---|---|---|---|---|---|---|
| **Task completion** | 40% | A working agent completing real tasks end to end in a sandbox, covering the topic, measured beyond one case | Photo → books; goal → plan → executed sandbox steps over a simulated week; honest prices; shelf-life credit; account and matcher (B); catalogue (B) | One-run hash-chained trace; tests; real-photo eval (B); shelf-life simulation (B); ledger (B); unit economics (B) | "Every step ran in the sandbox in one session; here is the log and how to verify it" | L | External counterparties are all simulated (vs Rival E's third-party sandbox); stated as a known gap |
| **Security & compliance (the spike)** | 30% | Identity on every route; approval that can't be bypassed; attack testing with a rate; consent; audit integrity; honest risks; regulatory mapping | Closed API (reads, chat, log stream); PIN re-entered at approval; Pause; traced money figures; registry; hash chain; correct cost disclosure; regulation matrix | 401/403 overlays; 10 HTTP tests; red-team table (B); `verify_trace`; tier table with enforcement points; matrix; OWASP (B) | "No anonymous path to any data or action; the AI holds no tool that moves money; every money figure is traced; here is each control's rule" | M–L | Demo-grade auth (single owner; same factor at approval), stated |
| **Innovation & interaction** | 30% | Something new that changes outcomes; natural interaction; proactivity | Shelf-life credit's loop (one number, two decisions); follow-through with a notification; traced badge; checklist (B); departures board | The card; the simulation's share of changed decisions (B); the notification | "An old lending rule, finally computable for a paper-based shop, before the purchase" | M | No IM, voice or generative cards at A or B (SHOULD) |

### The five capabilities at the recommended level (A + B)

| Capability | Scene | Proof | Verdict vs Rival E (judge round 2, updated for v3) |
|---|---|---|---|
| Intent understanding | 2, 3 | Recorded live chats; honest offline message; real-photo eval; intent eval with 20 questions (≥8 outside) at B | Par → slightly ahead once the intent eval lands at B |
| Task planning | 3, 6 | Fallback carried out on the simulated event (A); checklist (B) | Ahead (planning over time) |
| Safe execution | 5, 6, 8 | Closed API incl. reads; PIN; Pause; traced figures; hash chain; HTTP red-team | Ahead, now including the read path |
| User control | 5, 6 | Per-step approval; conditional approval; PIN; Pause; consent | Ahead |
| Measurable value | 3, 4, 7 | 0–182 vs 422; 10,800 not financed; shelf-life simulation (B); ledger (B) | Closer: a simulation focused on our own idea vs their 100+ SME study |

## 4b. Find what's missing (final)

**Free leverage.** All rows from v2 still hold. Changes in v3:
- the per-track prize rule now shapes the rival analysis and the bonus price;
- cost disclosure follows disclosure practice (APR on the amount financed, tenor);
- the "simulated-account" wording is met by the sandbox account at B;
- the brief's "user control" now includes Pause and re-entering the PIN at approval;
- reconciliation lands at B (merged with the account), not C.

**Proof on screen** (criteria ≥15%):

| Criterion | Ours (A + B) | Rival E | Match or beat? |
|---|---|---|---|
| Task completion 40% | One-run verifiable trace; honest prices; catalogue; real photos; shelf-life simulation; statement matching; ledger | External sandbox; 15–25 products; MAPE; 100+ SMEs; live URL | **Behind by about half a point** (external counterparties, live URL, broad value study at C) |
| Security & compliance 30% | Closed API incl. reads; PIN at approval; Pause; traced figures; HTTP red-team; hash chain; matrix | JWT, OTP, guardrails, attack rate, OWASP | **Beat** |
| Innovation & interaction 30% | Shelf-life loop with its own number; follow-through; traced badge; checklist | Cards, IM bot, voice, plan graph | **Par to slightly ahead** (domain insight vs channels) |

**Method check.**
- Task completion: measured on held-out real photos and ≥200 simulated pharmacies (B), with the counterfactual stated and the synthetic label on.
- Security & compliance: tiers with an enforcement point each, plus bypass tests at the HTTP level (A), an attack table (B), a regulation matrix with citation status (A) and the anchoring limit stated.
- Innovation & interaction: shelf-life credit measured by how often it changes the decision (B); an intent eval with outside questions (B).

**Cheap, high-scoring changes from round 2** (all adopted):
1. Close the read path (+0.5 h, 3–6 points/h).
2. Re-sequence the ladder (≈ +1 h).
3. Fix cost disclosure (0.5 h).
4. Shelf-life simulation and honest framing (≈ 3 h).
5. Make scene 3 safe from the figure guard (0.5 h).

## 4c. Audit of the existing product

Real today: engines with golden numbers; extraction with replay; the chat agent; the approval path with a savepoint executor; consent; registry; audit log; Docker; 98 test functions. Simulated: lenders, suppliers, payouts, the fixed as-of date.

**Defects** (all verified in the repo by the strategist or the judge):

| # | Defect | Fix |
|---|---|---|
| 1 | **Every route open, reads included; `/chat` and `/logs/stream` open**; `proposed_by` from the query; `/dev/reset` ungated; default `registry_key` | CORE-13 v3 |
| 2 | No chat recordings, so replay answers through the regex script | CORE-01 |
| 3 | Sales-page review renders nothing | FIX-01 |
| 4 | Stale numbers (73 / 91 / 98 tests; "to be filled"; "in progress"; README "stored draft") | SUB-08 |
| 5 | 100% on 27 synthetic images only | PROOF-03 |
| 6 | Deck reuses BCOLBD photos, cut-outs and icons with no recorded licence | SUB-10 (Level A) |
| 7 | Funding page hard-codes "BDT 19,000" and "BDT 0–182" | FIX-02 |
| 8 | Trace: 38 events within one second; `model=none` for the sales page | SUB-07 (one continuous run) |
| 9 | Thin catalogue (2 lenders, 3 products) | CORE-14 |
| 10 | No reconciliation | CORE-05 (merged, B) |
| 11 | Alerts on screen only | CORE-06 |
| 12 | As-of date and the planned deadline fall on Fridays | D-16 (Thursday) |
| 13 | README ownership unassigned beyond "Run it"; `plan/` untracked | P-4, P-5 |

## 4d. Differentiator ranking (final, points per effort)

Rank order of the MUST rows is in `requirements.md`. In brief:
- **Level A:** closed API, image licences, judge's guide, chat honesty, cost disclosure, Pause, hash chain, money-figure tracing, shelf-life card, regulation matrix, thin follow-through, desktop notifications.
- **Level B:** shelf-life simulation, catalogue, real photos, account with statement matching, ledger, red-team table, checklist, intent eval, OWASP, unit economics, final video and deck.
- **Level C:** consent scopes, sourced cash-flow ceiling and rules view, wider evidence, and the borrowing-base curve (only if it binds).

**Verdict on the team's notification idea (final).** It is a commodity on its own. It earns its place as the delivery channel of the follow-through and of fail-loud safety, built by deterministic code with no approval power. It is shown as a **desktop** notification unless Web Push is built.

---

## 5. Scope

- **MVP line:** every MUST row, about **72 h** (M1 ≈ 36, M2 ≈ 36), against about 43.5 clock hours to the freeze.
- **Recommended commitment (final): Level A in full, then Level B in rank order.**
  - A ≈ 29.5 h (M1 18.5 / M2 11).
  - B ≈ 32 h (M1 14.5 / M2 17.25).
  - A + B ≈ 61 h is the ceiling. The judge expects A plus about two-thirds of B by the freeze.
- **Level A is a complete, honest submission with the spike in place.** It has the closed API, the follow-through, the shelf-life card, correct disclosure, the matrix and traced figures. It lacks the account flip, the simulation, the catalogue, real photos and the red-team table.
- **Level C** (≈ 11 h) and **Level D** (SHOULD) only after A + B. Owner conversations (SHOULD-9) run in parallel at any level, if real.
- **Claim only what was built.** The deck, video and docs carry level markers (see `pitch.md`, `demo-flow.md`).
- **Not building:** real lender APIs; Bangla (roadmap); native apps; blockchain (team rule); autonomous execution; learned forecasts; per-visitor sandboxes; a supplier portal.
- **Round-2 track (if finalists):** Web Push on a real phone; Telegram; consent scopes; the sourced ceiling; wider evidence; an FL simulation (labelled).

---

## 6. Talk track

- **Hook:** "Last month Green Life Pharmacy in Bogura sold BDT 412,500 of medicine and kept 13,500. On Monday it will be 19,000 short for its biggest supplier. A lender that doesn't look at the shelf would lend it all 19,000, 10,800 of it against medicine that won't sell before it expires. LaMP won't."
- **Key messages:**
  1. It can plan for a week, but it can't spend a taka.
  2. Shelf-life credit: an old lending rule, finally computable for a paper-based shop. One number, two decisions.
  3. AI reads and proposes; code calculates and traces every money figure; only the owner approves.
  4. Honest prices: APR, tenor and the real cost of covering the gap.
  5. Every claim has a number, and you can verify the log yourself.
- **Rubric words:** task completion, end to end, sandbox execution, simulated account, permission tiers, authentication, re-authentication at approval, least privilege, human in the loop, responsible lending, cost disclosure, APR, KYC by the lender, known risks, residual risk, audit trail, tamper-evident, consent, data minimisation, intent understanding, task planning, safe execution, user control, measurable value.
- **Closing line:** "Every pharmacy already has a credit history. LaMP puts it to work, finances only what will sell, and never moves a taka without the owner."
- **Q&A:** `pitch.md` (26 questions, including the judge's round-2 questions).

---

## 7. Risks to winning (top 3; full list in `risks.md`)

1. **Scope versus the clock** (A + B ≈ 61 h; about 43.5 clock hours). Mitigation: the re-sequenced ladder puts the spike and the follow-through in A; commit tonight; G3 freeze; claim only what was built.
2. **A reviewer finds an overclaim**: the open read path, the 73% "effective annual cost", the borrowing-base curve, "lock screen", "second factor", "requested 19,000". All are fixed or re-labelled in v3; each claim is tied to a delivered level.
3. **Screening and licensing:** registration and roster (two members, both non-Chinese nationals), the channel, the deck images, the secrets scan, `plan/` off the judge path. All are tonight's precondition or Level A.

**Gates** (Bangladesh time):

| Gate | Condition | Deadline |
|---|---|---|
| G0 | Plan approved | 18 Oct, tonight |
| G1a | Registration and roster; channel question; level committed; bonus rule decided; README owner; `plan/` off the judge path | 18 Oct, tonight |
| G1b | Level A contract published; secrets scan; deck images replaced or licensed | 19 Oct, 09:00 |
| G2 | Insurance clips and v1; README judge-first; consistency; CORE-13 merged or on track | 19 Oct, 12:00 |
| G3 | Level A complete on `main`, plus the B items reached; guard tested on the recorded answers; dry run done. No new features after | 19 Oct, 23:59 |
| G4 | Final video from one run; deck; PDFs; verified trace; claims match the level | 20 Oct, 14:00 |
| G5 | Submitted (freeze) | 20 Oct, 18:00 (hard 21:59) |

---

## 8. Team split

Follows `CLAUDE.md` ownership: what judges **see** (M1) and what makes it **true** (M2).

| Member | Workstream | MUST hours (A / B / C) | Why this fits |
|---|---|---|---|
| M1 Ishmam (leader) | Video, deck, docs (incl. the regulation matrix), judge's guide, README (once assigned), image licences; UI for the PIN unlock, notifications, shelf-life card, cost lines, ledger, account; chat (recordings, honest offline message, checklist, calling the tracing function, the `agents/router.py` session dependency) | ≈ 36 (18.5 / 14.5 / 3.5) | Owns every artifact judges see and the agent's voice |
| M2 Farhan | Router-level auth, dev gating, keys; cost disclosure; shelf-life credit; follow-ups; account and matcher; hash chain; tracing function; ledger; catalogue; proof pack (real photos, shelf-life simulation, intent harness, HTTP and image red-team cases, unit economics); one-run trace; contract; drafts doc sections in `eval/` | ≈ 36 (11 / 17.25 / 7.5) | Money, state and security logic belong in the engines and API |

At Level A, M1 carries more (18.5 vs 11 h). M2 starts Level B items (simulation, catalogue, account) as soon as auth, tracing and the follow-through are done. Demo and presentation: M1 · Contract: M2 · Submission: M1 · Gatekeeper: M1.

---

## 9. Plan review (independent judge)

### Judge rounds (the judge's scores, not the strategist's)

| Criterion | Round 1 (v1, every MUST) | Rival E | Round 2 (v2): full MUST / A+B / A only | Rival E | What changed in v3 |
|---|---|---|---|---|---|
| Task completion (40%) | 3.5 | 4.0 | 4.0 / **3.5** / 3.25 | 4.0 | Ladder re-sequenced: reconciliation (merged with the account), the checklist, a 20-question intent eval and a shelf-life simulation now at Level B; real photos at B |
| Security & compliance (30%) | 4.0 (at risk 3.5) | 3.5 | 4.0 / **4.0** / 3.5 | 3.5 | Read path, chat and log stream closed (router-level session, HttpOnly cookie); 10 HTTP cases; cost disclosure corrected; PIN described as re-authentication; ceiling "designed, not built" unless sourced; nano-loan purpose row; image licences at A |
| Innovation & interaction (30%) | 3.5 | 3.5 | 3.75 / **3.5** / 3.0 | 3.5 | Shelf-life credit framed as the ineligible-inventory rule made computable; its own number from the simulation; curve only if it binds; checklist at B; "desktop notification" (no lock-screen claim) |
| **Weighted /100** | **73** | **74** | **78.5 / 73 / 65** | **74** | Rival F (track-wide, illustrative): ≈ 78.5 + 2–4 bonus ≈ 80–82 |

The judge's realistic delivery for v2: Level A plus about two-thirds of B ≈ 70–72. With its five round-2 changes: ≈ 78 if A + B lands (TC 3.75, SC 4.25, II 3.75), ≈ 74–75 at A plus two-thirds of B.

### Round-2 findings and responses

| Judge finding (round 2) | Response in v3 |
|---|---|
| Read path, `/chat` and `/logs/stream` open; "lender sees only what the owner shares" false at the API | **Fixed:** CORE-13 v3, a router-level session on all pharmacy routes, chat and logs (HttpOnly cookie); 4 more HTTP cases (10 in total); D-17 |
| The ladder contradicts the never-cut list; the deep feature at B; scope grew | **Fixed:** thin follow-through, PIN at approval, notifications and the shelf-life card moved to Level A; account and reconciliation merged (≈ 5 h instead of 7); thin checklist and a 20-question intent eval in B; ceiling, rules view, curve and red-team beyond 15 moved to C; MUST now ≈ 72 h, down from 74 |
| Cost-disclosure error ("73% effective annual cost") | **Fixed:** CORE-15 at Level A: APR on the amount financed (12.2% on 49,200, 30 days), tenor, cost of the gap (492 = 6.0% of 8,200 for 30 days); tenors stated; D-18 |
| Shelf-life credit: trim restated, "requested" uncosted, curve never binds, "invention" deflatable | **Fixed:** honest framing (ineligible-inventory rule, computed per batch before the purchase; one number, two decisions); 19,000 labelled a computed counterfactual; PROOF-04 simulation gives it its own number at B; the curve only if it binds (C) |
| Scene 3 would be blocked by the figure guard | **Fixed:** money figures (BDT, rates) label-bound; counts and dates separate; the tool returns the derived values; guard tested on the exact recorded answers before G3 |
| Catalogue rule "costlier or ineligible to protect the golden plan" | **Fixed:** terms come from the sources; if a sourced product beats the golden plan, the team updates the golden numbers (R-07) |
| Value ledger misses the 9,200 (return claim never approved) | **Fixed:** the click script approves it (scene 5) |
| PIN at approval is the same factor as the login | **Fixed in wording:** "re-authentication at the point of approval", not a second factor; OTP or device binding later (D-04, R-22) |
| Lock-screen claim needs Web Push | **Fixed:** "desktop notification" unless SHOULD-3 is built; "never fake" rule in `demo-flow.md` |
| Fridays (as-of date and deadline) | **Partly:** deadline moved to Thu 22 Oct (D-16, a team decision because it changes one golden date); the as-of date stays (moving it shifts every golden number); Q&A row added |
| Retail nano-loan for a business bill | **Fixed as a disclosure:** matrix row, Q&A row, catalogue field `permitted_purpose`; if business use isn't permitted, the archetype becomes ineligible (team decision, R-28) |
| Ceiling parameter is tuning | **Fixed:** sourced norm or "designed, not built" |
| Rival analysis Topic-E only; bonus priced against the wrong rival | **Fixed:** Rival F added; bonus decision re-priced against track-wide competition; the decision stays the team's |
| Image licensing at Level A | **Fixed:** SUB-10, rank 2 |
| README owner; `plan/` before going public | **Fixed as decisions:** P-4, P-5 |
| Hook order vs trace order | **Fixed:** caption "filmed after the captures, same session" |
| Video density (scenes 4 and 6) | **Fixed:** scene 4 is a card plus cost lines (no animation unless the curve binds); scene 6 is 60 s; the duplicate refusal moved to scene 8 |
| Mode: SPEED territory; the de facto spike is security | **Adopted:** mode set to SPEED with the security & compliance spike |
| Strategist's 83–85 / 81 were 5–8 points high | **Accepted:** the final expectation below uses the judge's numbers |

### Final expected score (judge's numbers as the baseline)

| Scenario | TC | SC | II | Weighted /100 | vs Rival E (74) | vs Rival F (≈ 80–82, illustrative) |
|---|---|---|---|---|---|---|
| **Realistic: Level A + about two-thirds of B, with v3's changes** | ≈ 3.5–3.75 | ≈ 4.25 | ≈ 3.5–3.75 | **≈ 74–75** | Level to slightly ahead | Behind |
| **Ceiling: Level A + B fully landed** | 3.75 | 4.25 | 3.75 | **≈ 78** | Ahead by about 4 | Behind by about 2–4 |
| Full MUST (A + B + C) | ≈ 4.0 | ≈ 4.25 | ≈ 3.75–4.0 | ≈ 80 (strategist's extrapolation from the judge's 78.5, not judged) | Ahead | About level |
| Level A only | — | — | — | below 74 (the judge scored v2's Level A at 65; v3 moves the spike and follow-through into A, so expect higher, but it hasn't been judged) | Behind | Behind |

No criterion is expected below 3/5 at any level from A upwards. **Biggest remaining risk:** delivering B; every B item that doesn't land lowers task completion first.

---

## 10. Re-plan log

| Time | Trigger | What changed |
|---|---|---|
| 18 Oct 2026 | Full re-plan requested | v1: DEPTH, the safe follow-through loop; follow-through, notifications, fidelity guard, policy tiers, kill switch, hash chain, wallet, reconciliation, ledger, expiry-aware limit, evals, judge's guide, OWASP |
| 18 Oct, evening | Judge round 1: 73 vs 74 | v2: thin auth, sourced catalogue, regulation matrix, unit economics, real photos and value simulation promoted, outside testers, honest replay, roster; shelf-life credit; "traced"; ledger counterfactuals; one-run trace; video cut to 10 scenes; dev clock dropped; reconciliation and rules screen thinned; work rebalanced |
| 18 Oct, late evening | Judge round 2: v2 at A + B = 73 vs 74; Rival F ≈ 80–82 | v3 (final): **mode SPEED with the security & compliance spike**; read path, chat and log stream closed; ladder re-sequenced (spike, follow-through, notifications and shelf-life card in A; account and matcher merged; checklist and 20-question intent eval in B; ceiling, rules view, curve and wide evidence in C); cost disclosure corrected (APR, tenor, cost of gap); shelf-life credit framed honestly, with its own simulation at B; scene 3 made guard-safe; 9,200 approved in the run; PIN called re-authentication; desktop notification only; Thursday deadline (team decision); nano-loan purpose row; Rival F and per-track prizes; image licences and secrets scan at A; README owner and `plan/` decisions; MUST ≈ 72 h |

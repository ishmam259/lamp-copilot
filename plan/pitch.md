# Pitch (re-plan v3, final)

Round 1: judges **read** the deck as a PDF and **watch** the video; the spoken script must fit 10:00 for the finals. Keep the existing style (Poppins, green panels), use the **departures board** as the recurring visual, and only images we own or whose licence is recorded (SUB-10). Lead with **shelf-life credit**, framed honestly, and **"it can plan for a week, but it can't spend a taka"**. Label every slide with the capability it proves. **Claim only what the delivered level built:** each slide below notes the level its content needs.

## Slide outline (target 9:20 spoken; hard limit 10:00)

| # | Slide | Content | Level | Time |
|---|---|---|---|---|
| 1 | Title | LaMP-Copilot: an AI finance officer for neighbourhood pharmacies. "It finds the cheapest money, starting with the cash you already have, and it never moves a taka without you." | A | 0:15 |
| 2 | Hook | Green Life, Bogura: sold 412,500, kept 13,500; Monday: 19,000 short. "A purpose-blind lender would lend all 19,000, 10,800 of it against medicine that won't sell before it expires." | A | 0:25 |
| 3 | The problem | 173,500 licensed pharmacies; 10–50 suppliers each on short credit, on paper; 10–15% margins; expiry; no lender can read paper (sources) | A | 0:35 |
| 4 | The insight | "Every pharmacy already has a credit history, scattered on paper." "The cheapest money is the cash you already have." One line each on PulseTech, TallyKhata, Shelf Life | A | 0:30 |
| 5 | A financial participant | The loop: read → understand → plan → propose → **owner approves** → sandbox executes → follows up → measures, tagged with the five capabilities. "It can plan for a week, but it can't spend a taka." | A | 0:35 |
| 6 | Demo 1: reading paper (INTENT UNDERSTANDING) | Invoice capture with a highlighted field; the sales-page review; extraction accuracy (synthetic; real photos at B, with "sales pages handwritten by the team") | A/B | 0:25 |
| 7 | Demo 2: a goal, a plan, traced money figures (INTENT UNDERSTANDING · TASK PLANNING) | Chat answer; "N of N money figures traced"; checklist (B); 19,000 → trim 10,800 → 8,200; extension free; fallback 181.97 vs 421.64 | A/B | 0:40 |
| 8 | **Shelf-life credit** (MEASURABLE VALUE) | "The ineligible-inventory rule asset-based lenders use, computed per batch from photographed invoices **before the purchase**, for shops with no stock system. One number, two decisions: the owner orders 18 fewer boxes; the lender lends 10,800 less." The purpose-blind 19,000 labelled "computed counterfactual". At B: the simulation across ≥200 pharmacies (share of cases where the financed amount changes; financed stock expiring unsold, median and P10–P90; need left unfinanced; labelled synthetic). The curve appears only if it binds in the simulation (C) | A/B | 0:45 |
| 9 | Demo 3: the owner decides, LaMP follows through (USER CONTROL · TASK PLANNING) | Approvals; fallback "only if no reply by Thu 22 Oct"; simulated event; **desktop notification** (phone only with Web Push); consent plus PIN; the board flips (B) | A/B | 0:40 |
| 10 | Financing matched with honest prices; value kept (MEASURABLE VALUE) | Each option: **APR on the amount financed, tenor, cost of covering this gap** (supplier credit: APR 12.2% on 49,200 for 30 days, 492 = 6.0% of the 8,200 gap; wallet loan: APR 9% on 8,200 for 90 days, 181.97). Catalogue "N matched, K eligible" (B); value ledger with bases (B); reconciliation result (B) | A/B | 0:35 |
| 11 | What is new | (1) Shelf-life credit's loop: one per-batch number from photographed paper drives the owner's order and the lender's limit. (2) The pattern "plans for a week, can't spend a taka", with traced money figures as its run-time proof. (3) Double financing detected without lenders seeing invoices (keyed commitments; PSI next). (4) Neutral across every supplier | A | 0:25 |
| 12 | Architecture and permission tiers (SAFE EXECUTION · USER CONTROL) | AI only in reading and chat; engines; **every pharmacy route, the chat and the log stream behind the owner's session** (HttpOnly cookie after the PIN); lender key; PIN re-entered at Tier-3 approval (re-authentication, not a second factor); Pause; executor; hash-chained log | A | 0:35 |
| 13 | Security proof | 401/403 on direct calls (incl. reads, chat, log stream); traced figures; injection photo; registry refusal; `verify_trace`; red-team table (B, incl. outside testers); OWASP coverage (B); top residual risks (single-owner demo-grade auth; hash chain anchored by the published head; collusion) | A/B | 0:35 |
| 14 | Measured beyond one shop | Only delivered rows: tests; extraction real (B) and synthetic; intent eval (B); shelf-life simulation (B); AI cost per pharmacy per month (B) | A/B | 0:35 |
| 15 | Compliance, the banker's way | Financial-regulation matrix: KYC/AML by the lender; cost disclosure (APR, tenor, cost of the gap); responsible lending (cash-flow ceiling "designed, not built" unless built at C with a sourced norm); **retail nano-loan used for a business bill: permitted purpose to check**; credit information; licensing; record retention; model risk; PDPO consent. Citations verified or "to verify" | A | 0:30 |
| 16 | Real vs sandbox, and limits | Real: reading, maths, chat, auth, approvals, log. Sandbox: lenders, suppliers, payouts. English only now, Bangla next | A | 0:15 |
| 17 | Business model and competition | Free for the pharmacy; lender origination fee; distributor programmes; no loan book | A | 0:25 |
| 18 | Roadmap | Pilot (20 pharmacies, one lender, one distributor) → Bangla, more lenders → bank supplier-credit product; shared risk model with federated learning (roadmap) | A | 0:20 |
| 19 | Close and ask | "Every pharmacy already has a credit history. LaMP puts it to work, finances only what will sell, and never moves a taka without the owner." Ask: one lender and one distributor for a pilot | A | 0:15 |
| A1 | Appendix: judge's guide | Capabilities and criteria → timestamp, slide, file, number | A | — |
| A2 | Appendix: Green Life numbers | Golden numbers plus the engine-confirmed new ones | A | — |
| A3 | Appendix: screenshots | Every video scene | A | — |

## Speaking roles (finals)

| Member | Part | Also does |
|---|---|---|
| M1 Ishmam | Opening, problem, the loop, shelf-life credit, close | Q&A lead; timekeeper |
| M2 Farhan | Live demo; architecture, security, measured results | Q&A on engines, security, evals, regulation |

## Script

- **Hook:** "Last month Green Life Pharmacy in Bogura sold BDT 412,500 of medicine and kept 13,500. On Monday it will be 19,000 short for its biggest supplier. A lender that doesn't look at the shelf would lend it all 19,000, 10,800 of it against medicine that won't sell before it expires. LaMP won't."
- **Handovers:** "Let me show you what happens when the owner just asks." → "Here's the number a lender usually can't see." → "Now watch what happens when the supplier doesn't answer." → "None of this matters if anyone could make it move money, so here's why no one can: not the AI, and not a stranger calling our API."
- **Close:** "Every pharmacy already has a credit history. LaMP puts it to work, finances only what will sell, and never moves a taka without the owner."

## Key messages

1. **Shelf-life credit:** the old ineligible-inventory rule, finally computable for a paper-based shop: one number, two decisions.
2. **It can plan for a week, but it can't spend a taka.**
3. AI reads and proposes; code calculates and traces every money figure; only the owner approves.
4. Honest prices: APR, tenor and the real cost of covering the gap, for every option.
5. Every claim has a number, and you can verify the log yourself.

## Q&A prep (WeBank industry experts and academics)

| Question | Short, honest answer | Who answers |
|---|---|---|
| What is real and what is simulated? | Real: photo reading, every money calculation, the chat and its tools, authentication, approvals, consent, the registry, the hash-chained log, the sandbox executor. Simulated: lenders and their decisions, supplier replies and confirmations, payouts. No real money moves. The default-probability formula is a placeholder, labelled as such | Farhan |
| Your consent screen says the lender sees only what the owner shares. Why would `GET /pharmacies/green-life/passport` answer anyone? | It doesn't any more: every pharmacy route, read or write, plus the chat and the log stream, needs the owner's session; lenders see the passport only through their own endpoints, with their key, and only after consent. Our HTTP tests try each case. Field-level scopes are next (Level C) | Farhan |
| Isn't shelf-life credit just the ineligible-inventory haircut every asset-based lender applies? | The concept, yes, and we say so. What's new is computing it per batch, from photographed paper, before the purchase, for shops with no stock system, so the owner and the lender see the same number. [At B:] across 200 simulated pharmacies it changed the financed amount in X% of cases and cut financed stock expiring unsold from A to B | Ishmam |
| Who requested 19,000? I don't see it in your log. | Nobody in the run. It's the loan a purpose-blind lender would make for the full gap, computed and labelled "counterfactual" on screen | Farhan |
| "1% supplier credit at 73% a year": that isn't an APR. | Right, and we no longer show it that way. The APR is 12.2% on the 49,200 financed (1% per 30 days). Covering only the 8,200 gap with it costs 492, which is 6.0% of the gap for 30 days. Both are on screen | Farhan |
| Your wallet loan runs 90 days and the supplier credit 30. Why compare their costs in taka? | We show each option's APR and tenor next to its taka cost, and state that the tenors differ. In taka, the plan is about what this shortfall costs the owner | Farhan |
| City Bank–bKash nano-loans are retail loans to individuals. Is paying a pharmacy's supplier bill with one responsible lending? | Good question, and it's in our compliance matrix: the owner would borrow personally, so the product's permitted purpose must be checked with the provider before any pilot. If it isn't permitted, that archetype becomes ineligible for business use and the plan moves to the next option | Ishmam |
| How did you choose the cash-flow ceiling's parameter? | [If built at C:] from a sourced norm, repayment as a share of projected net cash flow over the tenor. [Otherwise:] it's designed, not built, and the matrix says so. Never "so that our demo loan passes" | Ishmam |
| The PIN that opens the session is the same PIN you ask for at approval. Where's the second factor? | There isn't one. It's re-authentication at the point of approval. Device binding or an OTP is the production step, and the security report says so | Farhan |
| Was the app open when the notification arrived? | Yes. It's a desktop notification from the open app. [If Web Push is built:] the phone lock-screen one arrives with the app closed | Ishmam |
| Your deadline was a Friday? | No: we moved the supplier deadline to Thursday 22 Oct, because Friday is the weekly holiday and supplier offices and banks are closed | Ishmam |
| "N of N figures": verified, or just found somewhere in a tool output? | Traced: every money figure must match the engine field it is labelled with (cost, shortfall, saving, rate); counts and dates are checked separately. A failing answer is blocked. We say "traced", not "verified" | Ishmam |
| Is the submitted log the same session as the video? | Yes, one continuous run after one reset; the head hash on the closing card matches the log; the hook was filmed after the captures in the same session, and the caption says so | Farhan |
| How accurate is your forecast? | A dues calendar plus average daily sales; no backtest on real data yet. [At C: error on simulated sales is X% MAPE, labelled synthetic.] Known limit | Farhan |
| Who does KYC and AML? Is LaMP a credit intermediary? | The lender does KYC and AML; we pass consented data only. Licensing needs legal review (risk 10) | Ishmam |
| Bogura owners keep books in Bangla. Who is the real user? | English for this competition. Invoices are mostly English, sales books often aren't; the engines are language-neutral; Bangla UI and handwriting are first on the roadmap | Ishmam |
| Why use an LLM if engines do the maths? | Reading messy paper, and understanding the owner's goal in their own words; code is the accountant and the gatekeeper | Ishmam |
| Your extraction accuracy was 100%. | On 27 clean synthetic images, labelled so. [At B:] on real phone photos, with sales pages handwritten by the team, it's X%. The owner confirms every field anyway | Farhan |
| Isn't one tuned demo shop just a tuned seed? | Its golden numbers are illustrative. [At B:] the shelf-life simulation runs the same engines on ≥200 perturbed pharmacies; real photos and outside testers check the rest | Farhan |
| How do you stop fake invoices inflating the passport? | Half weight for unconfirmed invoices; cautious 5th-percentile score; registry; statement matching (B). Collusion remains a Medium risk; the lender sees the evidence and decides | Farhan |
| The default model is a placeholder. Why trust the score? | Trust the evidence, not our score; the lender applies its own model; a federated model across lenders is roadmap | Ishmam |
| Your registry: privacy-preserving how? | It stores keyed commitments only, so "already financed" is learned without seeing the invoice; one key holder today; PSI next. Not FL, not a blockchain | Farhan |
| Why no on-chain bonus? | The team decided against any blockchain component, knowing the bonus could be worth up to 5 points and that Topic F entries compete for the same prizes | Ishmam |
| What happens if OpenAI is down? | Engines, plans, approvals and the log keep working; capture falls back to manual entry; the chat says honestly it can't answer live | Farhan |
| PDPO 2025 and photos sent abroad? | Minimised (no patient data, resized, metadata stripped); a DPA and residency review are needed for production | Ishmam |
| What was hardest, and what's next? | Making an agent useful over time while keeping it unable to act alone. Next: a pilot with real invoices, Bangla, lender partners | Ishmam |

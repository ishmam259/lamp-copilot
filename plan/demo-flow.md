# Demo flow (re-plan v3, final)

Round 1 is an online review: judges never see a live demo. **The demo is the video (≤5:00)**, backed by the deck (≤10:00 spoken), the docs and the hash-chained trace. At the finals (22 Nov) the same story runs live. Every step is planned behaviour; Verified stays NO until it passes on `main`. Each scene notes the **Level** it needs, and the rule is: **show only what was built.**

## Demo story

- **One-sentence story:** Green Life Pharmacy is 19,000 short for Monday. A purpose-blind lender would lend all of it, 10,800 against medicine that won't sell before expiry. LaMP reads the shop's paper, plans the cheapest fix, finances only what will sell, gets the owner's approval step by step, and carries out its fallback when the supplier doesn't answer. Neither the AI nor a stranger calling its API can move a taka.
- **The "wow" moment:** "Simulated supplier event: no reply from Supplier A by Thu 22 Oct." A **desktop notification** appears ("Your fallback is ready: BDT 8,200 wallet loan, 90 days, APR 9%, cost BDT 181.97. Review."); the phone lock screen is shown **only if Web Push (SHOULD-3) is built**. The click opens the approval: share the passport with Wallet Lender, re-enter the PIN. The sandbox payout lands in the sandbox account, and the red departures board flips to "Cash holds".
- **Where judges see it:** the video (primary), deck slides 6–10, the tech doc, optionally a live URL (SHOULD-8).
- **Slot length and demo share:** video 5:00, of which about 4:25 is the product; deck 10:00 spoken, of which about 3:05 shows the product.

## How it is filmed: one continuous run

1. One reset at the start (seed only, `DEV_MODE=true` on the recording machine only).
2. PIN unlock (not filmed).
3. Every scene in story order, following a written click script, with no further resets.
4. Export the trace, run `verify_trace.py`, and put the head hash on the closing card and in the README.

Notes on the run:
- The hook is filmed right after the captures and moved to the front in editing, with the caption "filmed after the captures, same session".
- The click script also **approves the 9,200 return claim** (off camera or in scene 5), so the value ledger contains it.
- Only scenes with no state change may be retaken. If the run breaks after an approval, restart it, or label the trace "scripted run". Never stitch runs and call the result one session.

## Run sheet (target 4:50, hard limit 5:00; 10 scenes)

| # | Time | Chapter label | Level | Action / input | What judges see | Rubric | Talking point (voice-over) | Fallback | Verified |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0:00–0:15 | — | A | Title card, then Today | Departures board "Short BDT 19,000 · Mon 26 Oct"; caption "filmed after the captures, same session" | Hook · II | "Green Life Pharmacy in Bogura sold BDT 412,500 last month and kept 13,500. On Monday it will be 19,000 short for its biggest supplier. LaMP is an AI finance officer that can plan for a week, but can't spend a taka on its own." | Screenshot | NO |
| 2 | 0:15–0:45 | INTENT UNDERSTANDING · reading paper | A | Capture invoice F → one low-confidence field highlighted → correct → "lines add up, they match" → save (invoice H and the sales page are captured in the same run, off camera) | Highlighted field; totals check; log `T1:CAPTURE … model=gpt-6-luna` | TC · IU | "The owner photographs supplier invoices and the sales book. The model reads them, code checks every total, and the owner fixes the one figure it wasn't sure of." | Replay recordings | NO |
| 3 | 0:45–1:35 | INTENT UNDERSTANDING → TASK PLANNING | A (checklist: B) | Free-form goal "Supplier A's rep comes Monday. Can I take his full order?" (live in `record` mode) | Plan checklist (Level B; tool chips at Level A); answer: short 19,000 → trim 18 slow boxes, saving 10,800 → 8,200 left → ask for 20 more days (free), fallback wallet loan 181.97 (vs 421.64 for borrowing all 19,000); badge **"N of N money figures traced to LaMP's engines"** | II, SC · IU, TP, SE | "It understood the goal, made a plan and checked the real figures, and every money figure was traced by code to LaMP's own calculations before the owner saw it." | Recorded conversation | NO |
| 4 | 1:35–2:05 | SHELF-LIFE CREDIT | A (simulation: B) | Lender-side card, then the cost-disclosure lines on the funding page | **"A purpose-blind lender would lend 19,000 (computed counterfactual). Ineligible inventory, per batch, from the photographed invoices: 10,800 won't sell before expiry → finance at most 8,200. Same number, two decisions: the owner orders 18 fewer boxes, the lender lends 10,800 less."** Level B adds "Across 200 simulated pharmacies: financed amount changed in X%; financed stock expiring unsold, median A → B". Cost lines: "Supplier credit: APR 12.2% on 49,200 for 30 days; covering the gap costs 492 = 6.0% of 8,200 for 30 days" vs "Wallet loan: APR 9% on 8,200 for 90 days; 181.97" | II, TC, SC · MV | "Lenders don't lend against stock that won't sell. That's an old rule. What's new is computing it per batch, from photographed paper, before the purchase, so the owner and the lender see the same number. And every option shows its real yearly rate and what covering this gap actually costs." | Screenshot | NO |
| 5 | 2:05–2:35 | USER CONTROL | A | Actions: approve the return claim (9,200, one tap), the trim (one tap) and the extension request; the fallback appears as scheduled; Pause toggle shown | "Scheduled: only if Supplier A hasn't agreed by Thu 22 Oct · Tier 3 · needs your PIN"; Pause in the header | SC · UC, SE | "Nothing that touches money or a supplier happens until the owner approves. Borrowing needs the PIN again, at the moment of approval. And the owner can pause LaMP at any time." | Screenshots | NO |
| 6 | 2:35–3:35 | TASK PLANNING · follow-through | A (account flip: B) | Simulated supplier event "no reply by Thu 22 Oct" → desktop notification (+ phone only with SHOULD-3) → click → approval screen: share passport with Wallet Lender + PIN → executed: registry lock, application, sandbox lender approves → payout into the sandbox account → board flips to "Cash holds" | Caption "Simulated supplier event"; notification; consent and PIN on one screen; log `T3:REGISTRY lock_acquired`, `T3:PAYOUT sandbox_payout`; account +8,200 and red → green (Level B; at Level A the payout reference and log line) | TC, SC, II · TP, UC, SE | "We simulate Thursday: the supplier never answered. LaMP remembered its plan, and it doesn't borrow: it asks. The lender sees the passport only because the owner shared it, and the money moves only after the owner's PIN. Monday is covered." | "Declined" outcome | NO |
| 7 | 3:35–3:55 | MEASURABLE VALUE | B | Value ledger; reconciliation result from the sandbox account's statement | "Kept in the business this week vs the naive path: 9,200 supplier credit claimed · 10,800 of stock not bought that would likely expire · 239.67 interest avoided", each with its basis; "Matched 19 of 20 lines · 1 duplicate payment" | TC · MV | "About BDT 20,000 kept in the business in one week, each line saying against what, and reconciliation caught a double payment." | Screenshot | NO |
| 8 | 3:55–4:25 | SAFE EXECUTION · under attack | A (table: B) | Injection invoice → flagged, owner and admin notified, nothing changes. Overlays: `GET …/passport` with no session → **401**; `POST …/approve` with no session → **401**; a second application for the same order → refused "duplicate financing". Red-team table (Level B). "verify_trace: chain intact · N events · head …" | Warning banner; three overlays; table "0 of N attacks changed state, including 10 direct HTTP calls"; chain overlay | SC · SE | "Text in a photo is data, never a command. The chat has no tool that moves money, the API answers nothing without the owner's session, and the same order can't be financed twice. People outside our team tried to break it. And the log is hash-chained." | Screenshots | NO |
| 9 | 4:25–4:42 | PROOF | A | Proof slide | Only delivered numbers: extraction (real photos if B, synthetic), intent eval (if B), traced figures, red-team (if B), tests, shelf-life simulation (if B), AI cost per pharmacy (if B); "Real: reading, maths, chat, auth, approvals, log. Sandbox: lenders, suppliers, payouts." | TC, SC | "Every claim has a number, and every number is in the repo." | — | NO |
| 10 | 4:42–4:50 | — | A | Close card | "Every pharmacy already has a credit history. LaMP puts it to work, safely."; repo URL; head hash | II | Closing line | — | NO |

**Never fake.** No staged screen, no edited-in notification, no lock screen without Web Push, no "requested 19,000" without the "computed counterfactual" label, no number from a level that wasn't built.

## Five-capability coverage map

| Capability | Video scene(s) | Deck slide(s) | Proof number (level) |
|---|---|---|---|
| Intent understanding | 2, 3 | 6, 7 | Real-photo extraction (B); intent eval, 20 questions with ≥8 from outside the team (B); synthetic extraction (A) |
| Task planning | 3, 6 | 7, 9 | Fallback carried out on the simulated event, in the trace (A); checklist (B) |
| Safe execution | 5, 6, 8 | 12, 13 | 10 direct-HTTP cases (A tests, B table); figures traced (A); `verify_trace` (A); registry refusal (A) |
| User control | 5, 6 | 9, 12 | Approve/decline per step, PIN at approval, Pause, consent (A) |
| Measurable value | 3, 4, 7, 9 | 8, 10, 14 | 0–182 vs 422; 10,800 not financed (A); shelf-life simulation (B); ledger ≈ 20,240 (B); AI cost per pharmacy (B) |

## Rubric coverage map

| Criterion | Weight | Demo step or slide | Proof shown |
|---|---|---|---|
| Task completion | 40% | Video 2–4, 6, 7, 9; slides 6–10, 14 | One-run sandbox week with a verifiable trace; catalogue with correct disclosure; tests; eval tables; ledger; reconciliation; shelf-life simulation |
| Security & compliance | 30% | Video 5, 6, 8; slides 12, 13, 15 | Closed API (401/403 incl. reads, chat, log stream); PIN at approval; Pause; traced figures; red-team; registry; `verify_trace`; OWASP, financial-regulation and PDPO tables |
| Innovation & interaction | 30% | Video 3, 4, 6; slides 7, 8, 9, 11 | Shelf-life credit (one number, two decisions; simulation); follow-through notification; checklist and traced badge; departures-board UI |

## Demo controls

- [x] Reset (`POST /dev/reset`): exists; after CORE-13 only with `DEV_MODE=true`
- [x] Seed data; extraction replay: exist
- [ ] Chat recordings and the honest "not recorded" message (CORE-01)
- [x] Supplier-reply simulator: exists; **add the outcome "no reply by the deadline" (CORE-04)**
- [ ] PIN unlock (HttpOnly session cookie) and PIN re-entry at Tier-3 approval; test PIN from the seed file, never spoken or shown (CORE-13)
- [ ] Pause (CORE-08)
- [ ] Desktop notifications pre-allowed in the recording profile (CORE-06); phone mirrored only with SHOULD-3
- [ ] Seeded statement lines (CORE-05, Level B)
- [ ] Written click script for the continuous run, including the 9,200 return-claim approval
- [ ] Trace export with head hash (SUB-07)

## Setup checklist

- [ ] Tagged commit; `DEV_MODE=true` on the recording machine only; health OK
- [ ] `LLM_MODE=record` for the chat scene's first take; the guard test passed on the recorded answer (CORE-03)
- [ ] 1920×1080, zoom 110%, clean profile, notifications allowed for localhost
- [ ] OBS 1080p30; captions from the voice-over
- [ ] After the run: export, `verify_trace.py`, head hash onto the closing card, the README and the submission message

## Insurance video (gate G2)

Today's working story as reusable scene clips (hook, capture, chat question, approvals, passport and lender, injection), with chapter labels, assembled into a ≤5:00 v1 by 19 Oct 12:00 Bangladesh time. The final cut replaces clips with ones from the continuous run.

## Rehearsal log

| # | Time | Who | Duration | What broke | Fixed? |
|---|---|---|---|---|---|
| 1 | — | — | — | — | — |

# Plan summary (final approval page)

> One page for the team's approval (gate G0, **tonight**). Written by the strategist on 18 Oct 2026 after two independent judge reviews (re-plan v3, final). Details: `win-plan.md`, `requirements.md` (ladder and ranks), `demo-flow.md`, `pitch.md`, `risks.md`, `judge-review.md`.

**Plan version:** v3 final · **Status:** APPROVED 18 Oct 2026 · **Mode:** **SPEED with one spike.** About 43.5 build hours remain from tonight. The spike is **security & compliance as "safe agency": it can plan for a week, but it can't spend a taka.** It is the 30% criterion where we clearly beat the best Topic E rival; everything else is built thin.

## The problem and how it's judged
- **Problem:** Topic E, SME Finance Copilot: a working financial agent for small-business owners (financing matching, cash flow with alerts, analysis; the website adds reconciliation and operational recommendations). Ours: Bangladeshi neighbourhood pharmacies on paper, 10–50 suppliers, expiring stock.
- **Rubric:** Task completion 40% · Security & compliance 30% · Innovation & interaction 30%. The brief's checklist: intent understanding, task planning, safe execution, user control, measurable value.
- **Prizes are per track:** Topic F on-chain entries compete for the same prizes and may earn a 0–5 bonus.
- **Judges first see the product:** online review from 23 Oct (screening 21 Oct), package only. **Deadline 20 Oct, 21:59 Bangladesh time.** Defence 22 Nov.

## How we win
- **Win thesis:** Every claim survives a reviewer who opens the code. The spike makes the AI and the API structurally unable to move money or leak data, and that is proven from outside: 401s on direct calls, traced money figures, a hash-chained one-run trace, correct cost disclosure and a regulation matrix. The story shows an agent that follows through over time. The idea, **shelf-life credit**, is the ineligible-inventory rule made computable per batch from photographed paper: one number drives two decisions, the owner's order and the lender's limit.
- **"Wow" moment:** a simulated supplier event ("no reply by Thu 22 Oct"), then a **desktop notification** with the BDT 8,200 fallback (APR 9%, 90 days, cost 181.97 vs 421.64). One click: consent and the PIN. The sandbox payout lands and the board flips to "Cash holds". The phone lock screen appears only if Web Push is built.
- **Demo story** (≤5:00, one continuous run):
  1. Hook.
  2. Photo → books.
  3. Free-form goal → answer, "N of N money figures traced".
  4. Shelf-life card (19,000 counterfactual → 8,200) with honest prices.
  5. Approvals (return claim, trim, extension) and Pause.
  6. Follow-through.
  7. Value ledger and statement matching (B).
  8. Attacks: injection, 401s, duplicate refused, red-team (B), chain intact.
  9. Proof.
  10. Close.

## What we build
- **MUST ≈ 72 h** (M1 ≈ 36, M2 ≈ 36). **Final recommendation: Level A in full, then Level B in rank order.**
  - **Level A (≈ 29.5 h), a complete, honest submission with the spike:** registration and roster; deck image licences; secrets scan and a judge-first README; judge's guide; **closed API including reads, chat and log stream**; recorded chat with an honest offline message; correct cost disclosure; Pause; hash chain; money-figure tracing; shelf-life card; regulation matrix; thin follow-through with desktop notifications; insurance clips.
  - **Level B (≈ 32 h):** shelf-life simulation (≥200 pharmacies); sourced catalogue; real-photo eval; sandbox account with statement matching (reconciliation); value ledger; red-team table (≥15 incl. 10 HTTP, outside testers); checklist; 20-question intent eval; OWASP; unit economics; final video, deck and docs.
  - **Level C (≈ 11 h):** consent scopes; sourced cash-flow ceiling and rules view; wider evidence; borrowing-base curve (only if it binds).
- **Team split:** M1 Ishmam (leader): what judges see (video, deck, docs, README, UI, chat). M2 Farhan: what makes it true (auth, engines, simulation, proof pack, contract). The split follows `CLAUDE.md` ownership.

## What we cut or demoted, and why

| Item | Now | Reason |
|---|---|---|
| DEPTH mode (v1–v2) | SPEED with one spike | 43.5 h left; judge: "breadth plan with a DEPTH label" |
| Dev clock; reconciliation action kind; editable rules screen | Dropped; matcher merged with the account; read-only view at C | Thinness; consistency |
| "Expiry-aware limit"; shelf-life "invention"; borrowing-base curve headline | Honest framing; its own simulation number; curve only if it binds (it doesn't on Green Life) | A banker knows the rule; the curve never changes a decision |
| "73% effective annual cost" | APR on the amount financed + tenor + cost of the gap | Mislabelled disclosure |
| "Figures verified"; "lock screen"; "second factor"; Friday deadline; ledger "1.5 months of profit" | "Money figures traced"; "desktop notification"; "re-authentication"; Thursday; basis per line | Overclaims and domain errors |
| Problem-heavy slides; regex chat in the video; FL as a capability | Merged; test-only; roadmap | Time; honesty |
| Cash-flow ceiling, consent scopes, wider evidence | Level C | After the spike and the story |
| Web Push, Telegram, generative cards, live URL, provenance, full auth | SHOULD (D) | Polish after A + B |
| Real lender APIs, Bangla, blockchain (team rule), native app, autonomous execution | Never start | Rules, safety thesis, no rubric value |

## Independent judge review
- **Round 1 (v1):** ours **73** vs Rival E **74**.
- **Round 2 (v2):** full MUST **78.5**, **Level A + B 73**, Level A only 65, vs Rival E **74**; illustrative Topic F rival ≈ 80–82 including the bonus. The judge's realistic delivery for v2 was ≈ 70–72.
- **Top 3 round-2 concerns and what v3 did:**
  1. **The read path, the chat and the log stream were open**, so the consent story was false for a plain GET. → Router-level owner session (HttpOnly cookie) on every pharmacy route, `/chat` and `/logs*`; lenders read only through their endpoints after consent; 10 direct-HTTP tests; Level A.
  2. **A + B scored only 73**, because the deep feature and the method items sat at B and C, against the never-cut list. → Ladder re-sequenced: follow-through, PIN, notifications and the shelf-life card in A; reconciliation merged with the account, plus checklist, intent eval and simulation in B; ceiling, curve and wide evidence down to C; MUST cut from 74 to 72 h.
  3. **Shelf-life credit had no number of its own and a deflatable "invention" claim, and the 73% cost figure was mislabelled.** → Honest framing (an old rule made computable; one number, two decisions); a ≥200-pharmacy simulation at B; correct APR and tenor disclosure at A.
  - Also fixed: scene 3 made safe from the figure guard; the 9,200 claim approved in the run; image licences and the secrets scan at A; Thursday deadline; the nano-loan purpose row; Rival F added.
- **Honest expected score (judge's numbers as the baseline):**

| Scenario | Ours | Rival E | Rival F (illustrative) |
|---|---|---|---|
| Realistic (A + about two-thirds of B) | **≈ 74–75** | 74 | ≈ 80–82 |
| Ceiling (A + B fully landed) | **≈ 78** | 74 | ≈ 80–82 |

  So we are likely level with, or ahead of, the best Topic E entry, and behind a strong Topic F entry for First Prize unless B lands in full. No criterion is expected below 3/5.

## Gates, risk, decisions
- **Gates (Bangladesh time):**

| Gate | What | When |
|---|---|---|
| G0 | Plan approved | **tonight** |
| G1a | Registration and roster; channel question; level committed; bonus decided; README owner; `plan/` off the judge path | **tonight** |
| G1b | Contract; secrets scan; images | 19 Oct 09:00 |
| G2 | Insurance clips, v1, README, CORE-13 | 19 Oct 12:00 |
| G3 | Level A complete; guard tested on the recorded answers; no new features after | 19 Oct 23:59 |
| G4 | Final video from one run; verified trace; claims match the level | 20 Oct 14:00 |
| G5 | Submitted | 20 Oct 18:00 (hard deadline 21:59) |

- **Biggest remaining risk:** delivering Level B. Each B item that doesn't land costs task completion first, and the claims that depend on it must come out.
- **Decisions the team must make tonight:**
  1. **Registration and roster:** confirmed with two members (both non-Chinese nationals)? Ask the organisers for the submission channel.
  2. **Commit to "Level A in full, then B in rank order"?**
  3. **Challenge bonus:** keep the no-blockchain rule, knowing it may cost up to 5 points while Topic F entries compete for the same prizes?
  4. **Thursday deadline (D-16):** accept the change of one golden date (the fallback moves from 23 to 22 Oct)?
  5. **README ownership** beyond "Run it" (Ishmam assigns it in `CLAUDE.md`), and **keep `plan/` out of the public repo** (never rewrite history to hide how the entry was built)?
  6. **Nano-loan purpose:** if business use of the retail nano-loan isn't permitted, accept that the archetype becomes ineligible and the golden plan changes?
  7. **People:** who are the 2–3 outside testers and the ≥8 outside intent-question writers? Can we reach 3–5 real pharmacy owners (only real conversations count)?

# Cut list (re-plan v3, final)

The plan is not cut for time (team instruction). The scope ladder in `requirements.md` already orders the work. **Cutting means stopping at a level and removing every claim that needs the unbuilt items.** v3 aligns this list with the ladder: everything on the never-cut list is in Level A.

## Never cut (all in Level A or the tonight precondition)

- Registration with the two-member roster; the channel question; the six deliverables in English with links that open logged out.
- **Deck image licences** (SUB-10) and the **secrets scan** before the repo goes public (SUB-02).
- The video (insurance clips by G2).
- **Closed API, reads included** (CORE-13): every pharmacy route, the chat and the log stream behind the owner's session; PIN re-entered at Tier-3 approval; dev routes off; no default key.
- Real recorded chat with the honest offline message (CORE-01).
- Money-figure tracing, tested on the exact recorded answers (CORE-03).
- Correct cost disclosure (CORE-15).
- Pause (CORE-08) and the hash chain (CORE-09).
- The shelf-life credit card with honest framing (CORE-11).
- Thin follow-through (CORE-04) with desktop notifications (CORE-06).
- Financial-regulation matrix (DOC-03), judge's guide (DOC-01), consistency (SUB-08).
- Existing golden numbers and `test_golden.py` (D-16's deadline change only by team decision).

## Cut order (first to go at the top)

| # | Capability | Requirement | Cut trigger | How to remove safely | What to say instead |
|---|---|---|---|---|---|
| 1 | COULD items | COULD-1…8 | Always, for round 1 | Don't start | Roadmap slide |
| 2 | SHOULD items except owner conversations | SHOULD-3…8, 10 | Any Level A or B item still open | Don't start | "Desktop notification" (never "lock screen"); "one command runs it" |
| 3 | Borrowing-base curve and animation | CORE-11b | It doesn't bind in PROOF-04, or Level B is unfinished | Drop it | Nothing; the card and the simulation carry the idea |
| 4 | Wider evidence | PROOF-05 | Level B unfinished | Drop; keep the shelf-life simulation if done | Report only what was measured |
| 5 | Cash-flow ceiling and rules view | CORE-07 | Level B unfinished | Matrix shows the ceiling as "designed, not built" | Honest row |
| 6 | Consent scopes | CORE-16 | Level B unfinished | Risk 6 stays; the consent claim is "the lender sees the passport only after the owner shares it" (true with CORE-13) | Honest residual risk |
| 7 | Unit economics; OWASP table | DOC-04, DOC-02 | Behind at G3 | Leave out; the security report keeps the tier table and the matrix | — |
| 8 | Intent eval | PROOF-02 | Behind at G3 | Cut to 12 questions (≥5 from outside), or drop and remove the intent number | — |
| 9 | Visible plan | CORE-02 | Behind at G3 | Tool chips stay | — |
| 10 | Red-team table | PROOF-01 | Behind at G3 | Keep the 10 HTTP tests in CI (Level A); drop the outside-tester sessions and the table; scene 8 shows the overlays only | "Direct HTTP calls are tested in CI" |
| 11 | Value ledger | CORE-10 | Behind at G3 | Scene 7 shows the plan's 0–182 vs 422 only | — |
| 12 | Sandbox account with statement and matcher | CORE-05 | Not working by 19 Oct 18:00 | Scene 6 shows the payout reference and log line; reconciliation goes to the roadmap slide. **Never staged** | "Reconciliation is next" |
| 13 | Real-photo eval | PROOF-03 | No photos by G3 | Keep the synthetic table, labelled so | — |
| 14 | Catalogue size | CORE-14 | Behind at G3 | Keep ≥4 sourced archetypes with the CORE-15 disclosure, or the existing 3 options | — |
| 15 | Shelf-life simulation | PROOF-04 | Not started by 19 Oct 14:00 | Slide 8 and scene 4 show the card only | "Measured on one illustrative shop" |

## Demoted (from the existing entry, v1 and v2)

| Item | Now | Reason |
|---|---|---|
| Problem-heavy deck slides; feasibility; dense competition table | Merged or appendix | Time to the loop and proof |
| Regex chat as the demo source | Test fallback only; honest offline message | Fake-AI impression |
| v1 dev clock | Dropped (simulated supplier event) | Date mismatch; attack surface |
| v1 reconciliation action kind | Matcher only, merged with the sandbox account (v3) | Thinness; saves about 2 h |
| v1 editable rules screen | Read-only view at Level C | Thinness |
| v1 "expiry-aware limit 36,998 vs 45,120" | Shelf-life credit card | Never changed a decision |
| v2 "shelf-life credit, the invention" | "The ineligible-inventory rule, computed per batch from paper": one number, two decisions | A banker knows the rule (judge round 2) |
| v2 borrowing-base curve as a headline | Level C, only if it binds | It never binds on Green Life (≈ 137,700 vs 8,200–19,000) |
| v2 "effective annual cost ≈ 73%" | APR on the amount financed (12.2%), tenor, cost of the gap (6.0% for 30 days) | Mislabelled disclosure (judge round 2) |
| v2 "7 of 7 figures verified" | "N of N money figures traced", counts and dates separate | Guard would have blocked scene 3 |
| v2 "lock-screen notification" | "Desktop notification" unless Web Push is built | Never fake |
| v2 Friday 23 Oct deadline | Thursday 22 Oct (team decision on the golden fallback date) | Friday is the weekly holiday |
| v2 auth on writes only | Router-level session on all pharmacy routes, chat and logs | Read path was open |
| v2 PIN as a "step-up" second factor | Described as re-authentication at approval | Same factor as login |
| v2 ladder (follow-through and PIN at Level B) | Both in Level A | Matched the never-cut list (judge round 2) |
| v2 value simulation (general) at Level C | Shelf-life-focused simulation at Level B; the general one at C | Gives the idea its own number |
| Federated learning as a capability | Roadmap | Overclaiming |
| Set-aside action | Not shown | Adds nothing |

## Never start

| Idea | Why not |
|---|---|
| Real lender, bank or wallet APIs | Partnerships; a sandbox meets the rules |
| Bangla UI or handwriting | Team rule: English only now; first roadmap item |
| Any blockchain or on-chain component (incl. the 0–5 bonus) | **The team's rule**; its cost is stated in `win-plan.md` §1, including Topic F competition |
| Autonomous execution without the owner | Breaks the safety thesis |
| Any approve, execute, transfer, consent or contact tool for the chat agent | Team rule |
| Native apps; learned forecast models; per-visitor sandboxes; a supplier portal; barcodes; a lender portfolio; refactors | No rubric value for the cost |

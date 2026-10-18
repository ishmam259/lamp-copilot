# Ishmam: tasks from the approved win plan (v3)

Approved 18 Oct 2026. Full detail and acceptance checks for each ID: `plan/requirements.md`. Work in rank order: all of Level A, then Level B, then Level C. Stay inside your folders in `CLAUDE.md`. You are the leader, gatekeeper, demo owner and submission owner. Farhan is the contract owner and publishes the new endpoint contracts at G1b (19 Oct, 09:00).

## Tonight (precondition)

P-1 registration with the two-member roster and the submission-channel question · P-3 challenge-bonus decision · P-4 assign ownership of the rest of the README in `CLAUDE.md` · P-5 decide whether `plan/` stays in the public repo.

## Level A (≈ 18.5 h)

| # | ID | Task | Your part | Hours |
|---|---|---|---|---|
| 1 | SUB-01 | Registration confirmed with the two current members | All | 0.5 |
| 2 | SUB-10 | Deck image licences: replace BCOLBD photos, cut-outs and icons; fix `deck/README.md` | All | 1 |
| 3 | SUB-02 | README judge-first (pitch, video, judge's guide, 5-minute run, real vs sandbox); internal material off the first screen | README top | 1.25 |
| 4 | DOC-01 | Judge's guide: five capabilities and three criteria → timestamp, slide, file, number | All | 1 |
| 5 | CORE-13 | Closed API, your side: session check on `/chat` in `agents/router.py`, PIN screen, frontend sends credentials | Router + UI | 1.25 |
| 6 | FIX-01 | Capture screen reviews a sales-book page | All | 1 |
| 7 | SUB-08 | Consistency pass (73 / 91 / 98 tests, "to be filled", stale README lines) | All | 1 |
| 8 | CORE-01 | Real chat recorded live and replayed; honest message for an unrecorded question | All | 2 |
| 9 | CORE-15 | Cost disclosure shown on the funding page and deck | UI | 0.25 |
| 10 | CORE-08 | Pause switch in the UI | UI | 0.25 |
| 11 | CORE-09 | Show the chain status / head hash | UI | 0.25 |
| 12 | CORE-03 | Call Farhan's `fidelity` function in `chat.py`; show "N of N money figures traced"; block untraced answers | Chat + UI | 1 |
| 13 | CORE-11 | Shelf-life credit card in the lender view ("computed counterfactual" on 19,000) | UI | 0.75 |
| 14 | DOC-03 | Financial-regulation matrix, every citation checked or "to verify" | All | 2 |
| 15 | CORE-06 | Desktop notifications: service worker + `showNotification` from SSE notify events; click opens the approval (PIN still needed). Never say "lock screen" unless Web Push is built | Frontend | 1.5 |
| 16 | SUB-06a | Insurance video v1 (≤5:00) from scene clips by G2 | All | 2.5 |
| 17 | SUB-09 | Early v1 sent once the channel is known | All | 0.5 |
| 18 | FIX-02 | Funding page text from the API, no hard-coded figures | All | 0.5 |

## Level B (≈ 14.5 h)

PROOF-04 simulation shown on a slide (0.5) · CORE-14 catalogue UI (0.5) · CORE-05 wallet and matching screen (1) · CORE-10 value ledger UI (0.5) · PROOF-01 chat and approval-path red-team cases (1.25) · CORE-02 visible plan checklist via `share_plan` (1.5) · PROOF-02 intent questions (0.5) · DOC-02 OWASP LLM Top 10, model card, PDPO table (1.5) · DOC-04 unit economics in the docs (0.25) · SUB-05 deck revised to `plan/pitch.md`, ≤10:00 (3) · SUB-06b final video from one continuous run (2.5) · SUB-03/04 tech doc and security report updated, PDFs (1.5).

## Level C (≈ 3.5 h)

CORE-16 "what the lender will see" preview (0.5) · CORE-07 rules view (1) · PROOF-05 (0.5) · CORE-11b curve animation, only if it binds (1.5).

## Proposed additions (not in the approved plan; decide tomorrow)

True Web Push to a closed app (SHOULD-3), a system-health alert to the admin, and a live judge URL with the real model under a budget cap (SHOULD-8). Each needs work on your side too.

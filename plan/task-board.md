# Task board (re-plan v3, final)

## Gates

> G0 is always "win plan approved". Deadlines count back from the submission deadline (20 Oct, 23:59 UTC+8 = **21:59 Bangladesh time**), because judges first see the product in the online review after compliance screening on 21 Oct. All times are Bangladesh time (UTC+6). The team's own freeze (20 Oct 18:00) comes from `docs/PLAN.md`.

| Gate | Condition (what must be true) | Forbids after passing | Deadline | Status | Evidence |
|---|---|---|---|---|---|
| G0 | Win plan APPROVED by the team (`plan/win-plan.md`, `plan/plan-summary.md`) | Until it passes: no new code from this plan, no task assignment | **18 Oct, tonight** | PASSED | Approved 18 Oct; tasks in `plan/tasks/` |
| G1a | **Tonight (precondition P-1…P-5):** registration confirmed with the two-member roster (both non-Chinese nationals under the 60% rule); channel question sent; **scope level committed** (recommended: Level A in full, then B in rank order); challenge-bonus rule re-confirmed or changed by the team; README ownership assigned in `CLAUDE.md`; `plan/` kept off the judge path | — | **18 Oct, tonight** | OPEN | — |
| G1b | Contract for the Level A endpoints published (session cookie, approval requirement, shelf-life credit, cost-disclosure fields, follow-ups, notify, verify); secrets scan of the history done; deck images replaced or licensed (SUB-10) | Contract changes without telling the team | 19 Oct, 09:00 | OPEN | — |
| G2 | **Insurance:** today's story as reusable scene clips, assembled into a ≤5:00 v1 with chapter labels; README judge-first; consistency pass; v1 sent if the channel allows; CORE-13 (closed API incl. reads) merged or on track | Re-recording without a better full take | 19 Oct, 12:00 | OPEN | — |
| G3 | **Level A complete on `main`** and the Level B items reached so far merged; `pytest` green incl. golden numbers and the 10 HTTP cases; chat recordings committed; the figure guard passes on the exact recorded answers; a full dry run of the continuous recording done | **No new features.** Only fixes, docs, deck and video | 19 Oct, 23:59 | OPEN | — |
| G4 | Final video from one continuous run, uploaded and tested logged out; deck PDF/PPTX; tech doc and security PDFs; trace from that run; `verify_trace.py` passes; head hash in the README and on the closing card; **every claim matches the delivered level** | Code changes except critical fixes | 20 Oct, 14:00 | OPEN | — |
| G5 | Submission sent (team freeze) and acknowledged | Everything; only resubmission of the same package | 20 Oct, 18:00 (hard deadline 21:59) | OPEN | — |
| R2-a | Finalists announced; rules on post-submission changes and the defence format clarified (UNK-006) | — | 31 Oct | OPEN | — |
| R2-b | Finals build (round-2 track) frozen; live demo rehearsed on the venue setup | New features | UNKNOWN (before 20 Nov check-in) | OPEN | — |

**Current gate:** G1a tonight (G0 passed).

## Team

### Team skills (from the repo history)

| Member | Strong at | Can also do | Avoid |
|---|---|---|---|
| M1 Ishmam (@ishmam259, leader) | Frontend (Next.js), design, chat agent (PydanticAI), deck, docs, video | Security tests | Engine and seed changes (Farhan's folders) |
| M2 Farhan | Engines, API, database, seed, photo extraction, evaluation, Docker, scripts | LLM client and budget guard | Frontend, deck, docs (Ishmam's folders) |

### Roles for this event (copied from the approved win plan §8 at `/assign`)

| Member | Workstream | Owns (folders / files) |
|---|---|---|
| M1 | Leader + "what judges see" (video, deck, docs incl. regulation matrix, judge's guide, loop UI, chat agent): ≈ 36 MUST hours (A + B ≈ 33) | Per `CLAUDE.md` |
| M2 | "What makes it true" (auth, shelf-life credit, catalogue, policy, follow-ups, wallet, hash chain, tracing function, value, reconciliation; proof pack; contract): ≈ 36 MUST hours (A + B ≈ 28) | Per `CLAUDE.md` |

Demo & presentation owner: M1 · Contract owner: M2 · Submission owner: M1 · Gatekeeper: M1

## Tasks

Created only after the team approves the plan (`/assign`). States: TODO → DOING → DONE, or BLOCKED.

Per-person lists, in rank order with hours: **`plan/tasks/farhan.md`** and **`plan/tasks/ishmam.md`**. Shared items are split by folder ownership; each person does their part. Work Level A in full, then Level B, then Level C.

| Level | Farhan (M2) | Ishmam (M1) | Shared (split by folder) |
|---|---|---|---|
| A | CORE-04 follow-through, CORE-09 hash chain | SUB-01, SUB-10, DOC-01, FIX-01, SUB-08, CORE-01, DOC-03, SUB-06a, SUB-09, FIX-02 | SUB-02, **CORE-13**, CORE-15, CORE-08, CORE-03, CORE-11, CORE-06 |
| B | PROOF-03 real-photo eval, DOC-04 figures, SUB-07 trace | CORE-02 visible plan, DOC-02, SUB-05 deck | PROOF-04, CORE-14, CORE-05, CORE-10, PROOF-01, PROOF-02, SUB-06b, SUB-03/04 |
| C | — | — | CORE-16, CORE-07, PROOF-05, CORE-11b |

All tasks start TODO.

## Blocked

| ID | Missing | Needed from | Proposed alternative |
|---|---|---|---|
| — | — | — | — |

## Overrides log

| Time | What was overridden / changed | Why | Who agreed |
|---|---|---|---|
| 18 Oct | Plan written without cutting for build time | Team instruction | Team (in the request) |
| 18 Oct, late | v3 after judge round 2: read path, chat and log stream closed; ladder re-sequenced (spike and follow-through in Level A); cost disclosure fixed; shelf-life simulation; Thursday deadline; mode set to SPEED with one spike | Judge report round 2 | Pending team approval (G0) |
| 18 Oct | v2 after judge round 1: auth, catalogue, regulation matrix, shelf-life credit, proof items promoted; dev clock dropped; work rebalanced | Judge report | Pending team approval (G0) |

# @ishmam259 (team lead): Frontend & chat for the win plan (39% of the product work)

You own what the owner touches: the screens and the chat. The approved win plan (v3, 18 Oct) adds the PIN unlock, the Pause switch, desktop notifications, the shelf-life credit card, honest cost disclosure on the funding page, the "N of N money figures traced" badge, and real recorded chat. Farhan builds the backend for each one and publishes the contract first (by 19 Oct, 09:00), so build against his examples.

Read first:
1. [../plan-summary.md](../plan-summary.md): the approved plan on one page
2. [../architecture.md](../architecture.md): new components, decisions D-01 to D-18, contract changes
3. [../requirements.md](../requirements.md): acceptance check for every ID below
4. This file

**Your folders:** as in `CLAUDE.md`: `frontend/`, `backend/app/agents/chat.py`, `agents/tools.py`, `agents/router.py`, `agents/permissions.py`, `agents/prompts/chat_*.md`, `tests/agents/conftest.py`, `tests/agents/chat_client.py`, `tests/agents/test_chat.py`, `tests/agents/test_security.py`.
**Don't edit:** the rest of `backend/` (engines, API, schemas, `agents/llm.py`, `agents/extraction.py`), `contracts/`, `seed/`, `tests/engines/`, `tests/api/`, `eval/` (except chat recordings your code writes).

**Rules:** commit every ~10 minutes and push (`git pull --rebase` first). Plain messages like `frontend: add PIN unlock`. No AI attribution lines.

---

## Your share, broken down

| # | Work item | Plan IDs | Level | Share |
|---|---|---|---|---|
| I1 | PIN unlock, session cookie in every call, session check on `/chat` | CORE-13 | A | 4% |
| I2 | Capture screen reviews a sales-book page | FIX-01 | A | 3% |
| I3 | Real chat recorded live and replayed; honest reply for unrecorded questions | CORE-01 | A | 6% |
| I4 | Cost disclosure on the funding page | CORE-15 | A | 1% |
| I5 | Pause switch | CORE-08 | A | 1% |
| I6 | Log chain status and head hash | CORE-09 | A | 1% |
| I7 | Chat calls the tracing function; "N of N traced" badge; block untraced answers | CORE-03 | A | 3% |
| I8 | Shelf-life credit card in the lender view | CORE-11 | A | 2% |
| I9 | Desktop notifications (service worker) | CORE-06 | A | 4% |
| I10 | Funding page text from the API, no hard-coded figures | FIX-02 | A | 1% |
| I11 | Catalogue options on the funding page | CORE-14 | B | 1% |
| I12 | Wallet and reconciliation screen | CORE-05 | B | 3% |
| I13 | Value ledger screen | CORE-10 | B | 1% |
| I14 | Visible plan checklist in the chat (`share_plan`) | CORE-02 | B | 4% |
| I15 | "What the lender will see" preview | CORE-16 | C | 1% |
| I16 | Read-only rules view with the borrowing ceiling | CORE-07 | C | 3% |
| | **Total** | | | **39%** (≈ 14 of ≈ 35 product hours) |

Order: I1 → I10, then B, then C. All of Level A must land; B and C follow in order.

---

## Tech choices

- Same stack: Next.js (App Router, TypeScript), Tailwind, shadcn/ui, Recharts; chat through `useChat` from `@ai-sdk/react` against `POST /api/v1/chat`.
- **Session:** the backend sets an HttpOnly cookie after the PIN. Send it on every call (`credentials: "include"` on `fetch`; the Next.js rewrite keeps one origin, so `EventSource` sends it too).
- **Notifications:** a service worker (`public/sw.js`) plus `Notification.requestPermission()` and `registration.showNotification()`, fed by `notify` events on the SSE stream. Check the current MDN docs.
- Mock mode still works: copy Farhan's new examples with `npm run sync-mocks`.

---

## I1: PIN unlock and session (CORE-13, your side)

- **PIN screen** on first load and after the session expires: posts to `POST /pharmacies/{pid}/session`, then continues.
- Every API call sends the cookie. A 401 sends the owner back to the PIN screen.
- **`agents/router.py`:** add Farhan's owner-session dependency to `POST /chat`, so chat without a session → 401.
- **Approve dialog:** when an action's `ApprovalRequirement` says the PIN is needed (loan applications), ask for the PIN again before calling approve.
- Lender view sends the lender key, not the owner cookie.

---

## I2: Sales-page review (FIX-01)

- After a sales-book photo is uploaded, the Capture screen shows the days table for review (date, cash, credit, dues collected, expenses), with low-confidence cells highlighted and failed checks listed, then **Confirm**. Today it shows nothing.

---

## I3: Real recorded chat (CORE-01)

- Record the demo conversations live (`LLM_MODE=record`), so replay serves real model answers from `eval/replay/chat/`.
- Free-form goals work live; the agent may ask a clarifying question.
- In replay, an unrecorded question gets an honest reply ("This question wasn't recorded. Set `LLM_MODE=live` to ask it."), never the regex script silently. Keep the script only as a test fallback.

---

## I4: Cost disclosure (CORE-15, your side)

- The funding page shows, per option: APR on the amount financed, the tenor, and the cost of covering this gap in BDT and as % of the need, all from Farhan's new fields. State different tenors next to each other.
- **Golden:** supplier credit "APR 12.2% on 49,200 for 30 days; covering the 8,200 gap costs 492 = 6.0% of the gap". Wallet loan "APR 9% on 8,200 for 90 days; 181.97 = 2.2% of the gap over 90 days".

## I5: Pause switch (CORE-08, your side)

- A clear "Pause LaMP" toggle in the top bar (calls `POST …/pause`). While paused, show a banner, and disable approve on agent-proposed actions.

## I6: Log chain status (CORE-09, your side)

- On the live log panel: "Chain intact · N events · head a1b2c3…" from `GET /logs/verify`, red if broken.

---

## I7: Traced money figures in the chat (CORE-03, your side)

- In `chat.py`, call Farhan's `engines.fidelity` on every answer with this turn's tool outputs.
- Show a badge under the answer: "N of N money figures traced to LaMP's engines".
- If any money figure is untraced, block the answer: show a safe message, log it, and the backend sends an admin notify event.
- Add a test in `test_chat.py` that runs the guard on the exact recorded answers.

---

## I8: Shelf-life credit card (CORE-11, your side)

- In the lender view: "A purpose-blind lender would lend 19,000 (computed counterfactual). 10,800 of this order won't sell before expiry, so LaMP finances at most 8,200, and the owner orders 18 fewer boxes. One number, two decisions." Numbers from `GET …/shelf-life-credit`.

---

## I9: Desktop notifications (CORE-06, your side)

- Register the service worker and ask permission once, after the PIN.
- On a `notify` SSE event, call `showNotification` with its title and body. Owner and admin audiences.
- A click opens the linked approval. **A notification never approves anything**; approval still needs the owner and, for loans, the PIN (D-02).
- Works while the app is open in any tab, including a background tab. Don't call it "lock screen" unless true Web Push is built.

## I10: Funding page from the API (FIX-02)

- Replace the hard-coded "19,000" and "0–182" text with values from the API.

---

## I11–I13: Level B screens

- **I11 Catalogue:** the funding page lists every matched option with its source, date, eligibility and the I4 disclosure: "N matched, K eligible, cheapest first", with the reason each other option doesn't fit.
- **I12 Wallet & reconciliation:** balance and transactions from `GET …/account`; the payout appears as +8,200 and the board flips to "Cash holds"; a matches table (matched / duplicate / unmatched / missing deposit) with the recommendation line.
- **I13 Value ledger:** one row per executed action (9,200 · 10,800 · 239.67) with its basis, and the total, from `GET …/value`.

## I14: Visible plan (CORE-02)

- Add a `share_plan` tool (no data access, no state change) that the agent calls before acting; render it as a checklist above the tool chips in the chat. Update `permissions.py` and the exact tool-list assertion in `test_security.py` (D-09).

## I15–I16: Level C

- **I15:** consent screen shows "what this lender will see" from Farhan's preview endpoint.
- **I16:** read-only rules view (Pause state, which actions need the PIN, the borrowing ceiling), only if Farhan builds the ceiling.

---

## Done means
- [ ] PIN unlock works; every screen and the log stream work with the session; chat without a session → 401
- [ ] Loan approval asks the PIN again
- [x] Sales-book review renders and confirms
- [x] Demo chats come from real recordings; an unrecorded question gets the honest message
- [ ] Funding page shows APR, tenor and cost of the gap from the API; no hard-coded figures
- [ ] Pause toggle works; agent proposals can't be approved while paused
- [ ] Chain status shown on the log panel
- [ ] "N of N money figures traced" badge; an untraced answer is blocked
- [ ] Shelf-life credit card in the lender view
- [ ] A follow-up firing produces a desktop notification that opens the approval
- [ ] Level B: catalogue, wallet and reconciliation, value ledger, plan checklist
- [ ] Chat and security tests pass

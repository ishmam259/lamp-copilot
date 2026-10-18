# Contract additions for win plan v3 (Level A)

Schemas: `backend/app/schemas/safety.py`, plus new fields on `ActionOut`, `FundingOption` and `LogEvent`. `contracts/openapi.json` and the JSON examples are re-exported from real responses as each endpoint lands. Golden figures below are the values the engines return for the seed with the demo captures.

## Session (CORE-13)

Every `/pharmacies/{pid}/*` route and `/logs*` now needs the owner session cookie `lamp_session` (HttpOnly, SameSite=Lax). No cookie → **401**; a lender key instead of the cookie → **403**. Send `credentials: "include"`.

```
POST /api/v1/pharmacies/green-life/session   {"pin": "2468"}
200  Set-Cookie: lamp_session=…; HttpOnly; SameSite=Lax; Path=/
     {"pharmacy_id": "green-life", "role": "owner", "expires_at": "2026-10-19T14:00:00Z"}
401  {"detail": "Wrong PIN"}
```

The demo PIN is `2468` (only its scrypt hash is in `seed/green_life.json`).

**Lenders** send `X-Lender-Key: <key>` on `/lenders/{lid}/*` routes. Demo keys: `wallet-lender-demo-key`, `partner-bank-demo-key` (hashes in the seed). `GET /lenders` stays public.

**Approve** now takes a body. `ActionOut.requires_pin` is `true` for `loan_application`:
```
POST /api/v1/pharmacies/green-life/actions/act-7/approve   {"pin": "2468"}
401  {"detail": "This approval needs the owner PIN"}   (missing or wrong PIN)
```

`proposed_by` is no longer read from the request: owner session → `"owner"`, the chat → `"agent"`, the follow-up runner → `"lamp-scheduler"`.

`/dev/*` answers **404** unless the server runs with `DEV_MODE=true` (the demo machine sets it; the Reset button needs it).

## Cost disclosure (CORE-15): new `FundingOption` fields

```json
{"key": "wallet_loan", "amount": 8200, "cost_bdt": 181.97, "apr_pct": 9.0,
 "amount_financed": 8200, "tenor_days": 90, "cost_of_gap_bdt": 181.97, "cost_of_gap_pct_of_need": 2.22}
{"key": "bank_supplier_credit", "amount": 49200, "cost_bdt": 492.0, "apr_pct": 12.17,
 "amount_financed": 49200, "tenor_days": 30, "cost_of_gap_bdt": 492.0, "cost_of_gap_pct_of_need": 6.0}
```

## Pause (CORE-08)

```
POST /api/v1/pharmacies/green-life/pause   {"paused": true}
GET  /api/v1/pharmacies/green-life/pause
200  {"paused": true, "changed_at": "2026-10-19T08:12:00Z"}
```
While paused, agent and scheduler proposals return **409** and agent-proposed actions can't be approved (**409**).

## Log verification (CORE-09)

```
GET /api/v1/logs/verify
200 {"intact": true, "count": 38, "head_hash": "a1b2…64 hex", "first_bad_id": null}
```
Every `LogEvent` now carries `hash`.

## Shelf-life credit (CORE-11)

```
GET /api/v1/pharmacies/green-life/shelf-life-credit
200 {"order_id": "PO-A-1", "needed_by": "2026-10-26",
     "counterfactual_purpose_blind": 19000, "not_financed": 10800, "financeable": 8200,
     "reason": "10,800 of this order won't sell before expiry (30-day buffer), so it is not financed.",
     "batches": [{"product": "…", "qty_ordered": 30, "sellable_qty": 12, "unsellable_value": 10800}]}
```

## Follow-ups (CORE-04)

```
GET /api/v1/pharmacies/green-life/followups
200 [{"id": "fu-1", "plan_action_id": "act-3", "fallback_kind": "loan_application",
      "fallback_payload": {"lender_id": "wallet-lender", "product_key": "wallet_loan", "amount": 8200},
      "amount": 8200, "deadline": "2026-10-23", "status": "waiting", "fired_action_id": null,
      "created_at": "…"}]
```
Approving an `extension_request` whose payload has a `fallback` creates the follow-up. The supplier-reply simulator accepts `{"action_id": …, "outcome": "accepted" | "declined" | "no_reply"}` (the old `accepted: bool` still works). `declined` or `no_reply` fires it: a `loan_application` proposal with `proposed_by: "lamp-scheduler"` (still needs the owner's approval and PIN) and a notify event.

## Notify events (CORE-06)

On `/logs/stream`, as a normal `LogEvent`:
```json
{"id": "lg-41", "tier": "T1", "component": "NOTIFY", "event": "notify",
 "data": {"audience": "owner", "title": "Supplier A didn't reply",
          "body": "Backup plan ready: BDT 8,200 wallet loan, cost BDT 181.97. Approve with your PIN.",
          "link": "/actions"}}
```
Audiences: `owner`, `admin`. A notification never approves anything.

"""Scripted demo run against a running API, in demo order, then export the trace.

    python scripts/demo_run.py [--base http://127.0.0.1:8000/api/v1]

Deterministic: it resets to the seed, enters the three demo captures from
seed/demo_captures/ as the owner's corrected drafts (replay mode: no OpenAI
calls), and checks every golden number on the way. It unlocks with the owner PIN
first; the API records every proposal it makes as the owner's (the copilot proposes
only from the chat). Loan approvals re-enter the PIN. Lender calls use the demo key.
The server must run with DEV_MODE=true (reset and the supplier-reply simulator).
Uses only the Python standard library.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from export_trace import PIN, export, signed_in_opener  # noqa: E402

BASE = "http://127.0.0.1:8000/api/v1"


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip("/")
        self.opener = signed_in_opener(self.base)

    def call(self, method: str, path: str, body=None, form: dict | None = None):
        headers, data = {}, None
        if path.startswith("/lenders/wallet-lender/"):
            headers["X-Lender-Key"] = "wallet-lender-demo-key"
        if form is not None:
            boundary = uuid.uuid4().hex
            parts = [f'--{boundary}\r\nContent-Disposition: form-data; name="kind"\r\n\r\n{form["kind"]}\r\n'.encode(),
                     f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{form["name"]}"\r\n'
                     f"Content-Type: image/jpeg\r\n\r\n".encode() + form["bytes"] + b"\r\n",
                     f"--{boundary}--\r\n".encode()]
            data, headers["Content-Type"] = b"".join(parts), f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data, headers["Content-Type"] = json.dumps(body).encode(), "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=30) as r:
                raw = r.read()
                return json.loads(raw) if r.headers.get_content_type() == "application/json" else raw.decode()
        except urllib.error.HTTPError as e:
            raise SystemExit(f"{method} {path} -> {e.code}: {e.read().decode()}")

    def get(self, path):
        return self.call("GET", path)

    def post(self, path, body=None):
        return self.call("POST", path, body)


def check(label: str, got, want) -> None:
    ok = got == want
    print(f"  {'ok ' if ok else 'BAD'} {label}: {got}" + ("" if ok else f" (expected {want})"))
    if not ok:
        raise SystemExit(f"Golden number mismatch: {label}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=BASE)
    api = Api(ap.parse_args().base)
    P = "/pharmacies/green-life"

    print("1. Reset to the seed pharmacy")
    api.post("/dev/reset")

    print("2. Owner photographs 2 invoices and 1 sales-book page, then confirms each draft")
    for name in ["invoice_supplier_f", "invoice_supplier_h", "sales_page"]:
        draft = json.loads((ROOT / "seed" / "demo_captures" / f"{name}.json").read_text(encoding="utf-8"))
        image = ROOT / "seed" / "images" / f"{name}.jpg"
        cap = api.call("POST", f"{P}/captures",
                       form={"kind": draft["kind"], "name": f"{name}.jpg",
                             "bytes": image.read_bytes() if image.exists() else b"demo"})
        api.post(f"{P}/captures/{cap['id']}/confirm", {k: draft[k] for k in ("invoice", "sales_page") if k in draft})
        print(f"  confirmed {cap['id']} ({name})")

    print("3. Accounts")
    a = api.get(f"{P}/accounts")
    check("sales", a["sales"], 412500)
    check("net profit", a["net_profit"], 13500)
    check("stock value / days", (a["stock_value"], a["stock_days"]), (210000, 17.4))
    check("patient dues / days", (a["patient_dues"], a["patient_due_days"]), (38000, 2.8))
    check("active suppliers", a["active_suppliers"], 23)
    fc = api.get(f"{P}/forecast")
    check("cash before the Supplier A order", fc["days"][9]["balance"], 41000)
    check("first shortfall", (fc["shortfalls"][0]["date"], fc["shortfalls"][0]["amount"]), ("2026-10-26", 19000))

    print("4. Expiring stock")
    e = api.get(f"{P}/expiry")
    check("expiring batches / value", (len(e["batches"]), e["at_risk_value"]), (6, 18400))
    check("return-eligible", e["return_eligible_value"], 9200)

    print("5. Copilot proposes return claims; owner approves")
    act = api.post(f"{P}/actions", {"kind": "return_claim",
                                    "payload": {"summary": "Return Omeprazole and Cetirizine", "amount": 9200}})
    r = api.post(f"{P}/actions/{act['id']}/approve", {"pin": PIN})
    check("return claim", (r["status"], r["result"]["expected_credit"]), ("executed", 9200))

    print("6. Trim the slow mover")
    t = api.get(f"{P}/orders/o-1/trim")
    check("trimmed order", (t["original_total"], t["suggested_total"]), (60000, 49200))
    plan = api.post(f"{P}/funding-plan", {})  # plan before trimming: what the owner sees
    check("need after trim", plan["need"]["amount"], 8200)
    costs = {o["key"]: o["cost_bdt"] for o in plan["options"]}
    check("wallet loan cost", costs["wallet_loan"], 181.97)
    check("bank supplier credit cost", costs["bank_supplier_credit"], 492.0)
    check("naive cost", plan["naive_cost_bdt"], 421.64)
    check("plan", [s["action_kind"] for s in plan["plan"]["steps"]],
          ["trim_order", "extension_request", "loan_application"])

    print("7. Copilot proposes the plan; owner approves each step")
    ids = {}
    for s in plan["plan"]["steps"]:
        payload = {"summary": s["label"], "amount": s["amount"], "when": s["when"]}
        if s["action_kind"] == "loan_application":
            payload |= {"lender_id": "wallet-lender", "product_key": "wallet_loan", "fallback": True}
        ids[s["action_kind"]] = api.post(f"{P}/actions", {"kind": s["action_kind"],
                                                          "payload": payload})["id"]
    check("trim executed", api.post(f"{P}/actions/{ids['trim_order']}/approve", {"pin": PIN})["status"], "executed")
    check("order total", api.get(f"{P}/orders")[0]["total"], 49200)
    ext = api.post(f"{P}/actions/{ids['extension_request']}/approve", {"pin": PIN})
    check("extension sent", ext["result"]["status"], "awaiting_supplier")
    reply = api.post("/dev/simulate/supplier-reply", {"action_id": ext["id"], "accepted": False})
    check("Supplier A reply", reply["result"]["status"], "declined")

    print("8. Fallback: share the passport with Wallet Lender, then apply")
    pp = api.get(f"{P}/passport")
    check("passport", (pp["theta_low_5pct"], pp["default_probability"], pp["score"]), (0.826, 0.03, 0.507))
    api.post(f"{P}/consents", {"lender_id": "wallet-lender", "scopes": ["passport", "accounts"]})
    loan = api.post(f"{P}/actions/{ids['loan_application']}/approve", {"pin": PIN})
    check("loan application", loan["status"], "executed")
    app_id = loan["result"]["application_id"]
    dup = api.post(f"{P}/actions", {"kind": "loan_application",
                                    "payload": {"summary": "Same order again", "amount": 8200,
                                                "lender_id": "wallet-lender", "product_key": "wallet_loan"}})
    dup = api.post(f"{P}/actions/{dup['id']}/approve", {"pin": PIN})
    check("second loan on the same order", (dup["status"], dup["result"]["reason"]), ("failed", "duplicate_financing"))

    print("9. Lender decides")
    inbox = api.get("/lenders/wallet-lender/applications")
    check("lender inbox", [x["id"] for x in inbox], [app_id])
    d = api.post(f"/lenders/wallet-lender/applications/{app_id}/decide")
    check("decision", (d["status"], d["decision"]["payout_ref"]), ("approved", f"SANDBOX-WALLET-LENDER-20261016-{app_id[4:]}"))
    left = api.get(f"{P}/forecast")["shortfalls"]
    check("26 Oct after trim and loan", [s for s in left if s["date"] == "2026-10-26"], [])

    print("10. Export the audit log")
    path = export(api.base, api.opener)
    print(f"  wrote {path.relative_to(ROOT)} ({len(path.read_text(encoding='utf-8').splitlines())} events)")
    print("Demo run complete.")


if __name__ == "__main__":
    main()

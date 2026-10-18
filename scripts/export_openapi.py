"""Write contracts/openapi.json and contracts/examples/<endpoint>.json.

The examples are real responses: the script loads the seed plus demo captures
into a throwaway SQLite database, walks the demo flow through the API and saves
each response. Run from the repo root:  python scripts/export_openapi.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
_tmp = Path(tempfile.mkdtemp()) / "contracts.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.as_posix()}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    write(ROOT / "contracts" / "openapi.json", app.openapi())
    os.environ["DEV_MODE"] = "true"
    from app.config import settings
    settings.dev_mode = True
    c = TestClient(app)
    p = "/api/v1/pharmacies/green-life"
    lender = {"X-Lender-Key": "wallet-lender-demo-key"}

    def get(path):
        r = c.get(path, headers=lender if path.startswith("/api/v1/lenders/") else None)
        r.raise_for_status()
        return r.json()

    def post(path, body=None):
        r = c.post(path, json=body, headers=lender if path.startswith("/api/v1/lenders/") else None)
        r.raise_for_status()
        return r.json()

    out = {"health": get("/api/v1/health"), "reset": post("/api/v1/dev/reset?with_demo_captures=true")}
    out["session"] = post(f"{p}/session", {"pin": "2468"})
    out |= {"pharmacy": get(p), "accounts": get(f"{p}/accounts"), "dues": get(f"{p}/dues"),
            "forecast": get(f"{p}/forecast"), "alerts": get(f"{p}/alerts"), "expiry": get(f"{p}/expiry"),
            "orders": get(f"{p}/orders"), "trim": get(f"{p}/orders/o-1/trim"),
            "funding_plan": post(f"{p}/funding-plan"), "passport": get(f"{p}/passport"),
            "lenders": get("/api/v1/lenders"), "capture_invoice": get(f"{p}/captures/cap-demo")}
    out["action_proposed"] = post(f"{p}/actions", {"kind": "return_claim",
                                                   "payload": {"summary": "Return expiring stock", "amount": 9200}})
    out["action_executed"] = post(f"{p}/actions/{out['action_proposed']['id']}/approve")
    out["consent"] = post(f"{p}/consents", {"lender_id": "wallet-lender", "scopes": ["passport", "accounts"]})
    loan = post(f"{p}/actions", {"kind": "loan_application",
                                 "payload": {"summary": "Mobile-wallet loan", "amount": 8200,
                                             "lender_id": "wallet-lender", "product_key": "wallet_loan"}})
    post(f"{p}/actions/{loan['id']}/approve", {"pin": "2468"})
    out["actions"] = get(f"{p}/actions")
    out["consents"] = get(f"{p}/consents")
    out["applications"] = get("/api/v1/lenders/wallet-lender/applications")
    out["application_decided"] = post(f"/api/v1/lenders/wallet-lender/applications/{out['applications'][0]['id']}/decide")
    ext = post(f"{p}/actions", {"kind": "extension_request", "payload": {"amount": 8200}})
    post(f"{p}/actions/{ext['id']}/approve")
    out["followups"] = get(f"{p}/followups")
    out["shelf_life_credit"] = get(f"{p}/shelf-life-credit")
    out["pause"] = get(f"{p}/pause")
    out["financing_catalogue"] = get(f"{p}/financing-catalogue")
    out["account"] = get(f"{p}/account")
    out["value"] = get(f"{p}/value")
    out["consent_preview"] = get(f"{p}/consents/preview?lender_id=wallet-lender&scopes=passport.summary")
    out["logs_verify"] = get("/api/v1/logs/verify")
    out["logs"] = get("/api/v1/logs")
    for name, data in out.items():
        write(ROOT / "contracts" / "examples" / f"{name}.json", data)
    print(f"Wrote contracts/openapi.json and {len(out)} examples")


if __name__ == "__main__":
    main()

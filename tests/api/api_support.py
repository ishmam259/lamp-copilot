"""Shared constants for the API tests (a unique module name, so it never clashes with
another folder's conftest)."""

PIN = "2468"  # demo owner PIN; only its hash is in the seed
LENDER_KEYS = {"wallet-lender": "wallet-lender-demo-key", "partner-bank": "partner-bank-demo-key"}


def lender_headers(lid: str = "wallet-lender") -> dict:
    return {"X-Lender-Key": LENDER_KEYS[lid]}

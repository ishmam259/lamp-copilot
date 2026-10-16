"""Write contracts/openapi.json and contracts/examples/<endpoint>.json.

Run from the repo root:  python scripts/export_openapi.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.api import examples  # noqa: E402
from app.main import app  # noqa: E402


def write(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    write(ROOT / "contracts" / "openapi.json", app.openapi())
    for name, data in examples.ALL.items():
        write(ROOT / "contracts" / "examples" / f"{name}.json", data)
    print(f"Wrote contracts/openapi.json and {len(examples.ALL)} examples")


if __name__ == "__main__":
    main()

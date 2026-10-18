"""OpenAI client for photo reading: Responses API, structured output, replay and a budget guard.

LLM_MODE picks how the model is reached:
- live:   call OpenAI. Cost goes to eval/spend.log; refused once today's spend passes
          LLM_DAILY_BUDGET_USD.
- record: like live, and the parsed response is saved under eval/replay/<component>/.
- replay: never call OpenAI. Serve the saved response for the same key; raise
          ReplayMissing if there is none.

The cache key is sha256(model + prompt version + input text + sha256 of the raw image).

Budget helper for the chat: `live_allowed()` says whether today's budget allows another
live call, and `record_spend(component, model, in_tokens, out_tokens)` logs one. The log
format matches agents/chat.py: `date,component,model,in_tokens,out_tokens,usd`.
"""

import base64
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import date
from typing import Literal

from PIL import Image, ImageOps

from app.config import REPO_ROOT, settings

REPLAY_DIR = REPO_ROOT / "eval" / "replay"
SPEND_LOG = REPO_ROOT / "eval" / "spend.log"

# gpt-6-luna prices, USD per 1M tokens (same as agents/chat.py)
PRICE_IN, PRICE_OUT = 0.10, 0.50

MAX_SIDE = 1600
JPEG_QUALITY = 85


class ReplayMissing(RuntimeError):
    """Replay mode and no recording for this key."""


class BudgetExceeded(RuntimeError):
    """A live call was refused: no API key, or today's spend is over the limit."""


@dataclass
class LLMResult:
    data: dict
    model: str
    mode: Literal["live", "replay"]
    key: str


# --- Budget ---------------------------------------------------------------------------

def spent_today() -> float:
    """USD spent today, summed from eval/spend.log."""
    if not SPEND_LOG.exists():
        return 0.0
    today = date.today().isoformat()
    total = 0.0
    for line in SPEND_LOG.read_text(encoding="utf-8").splitlines():
        parts = line.split(",")
        if len(parts) == 6 and parts[0] == today:
            total += float(parts[5])
    return total


def cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * PRICE_IN + output_tokens * PRICE_OUT) / 1_000_000


def record_spend(component: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Append one live call's cost to eval/spend.log and return it in USD."""
    usd = cost_usd(input_tokens, output_tokens)
    SPEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SPEND_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{date.today().isoformat()},{component},{model},{input_tokens},{output_tokens},{usd:.6f}\n")
    return usd


def live_allowed() -> bool:
    """True if an API key is set and today's spend is under LLM_DAILY_BUDGET_USD."""
    return bool(settings.openai_api_key) and spent_today() < settings.llm_daily_budget_usd


# --- Images ---------------------------------------------------------------------------

def preprocess_image(image: bytes) -> bytes:
    """Fix EXIF rotation, shrink so the long side is <= 1,600 px, re-encode as JPEG 85.
    Re-encoding without exif/icc drops all metadata (GPS, camera)."""
    with Image.open(io.BytesIO(image)) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return out.getvalue()


# --- Replay ---------------------------------------------------------------------------

def cache_key(model: str, prompt_version: str, text: str, image: bytes | None = None) -> str:
    """sha256 of model, prompt version, input text and the raw image's sha256."""
    image_sha = hashlib.sha256(image).hexdigest() if image else ""
    raw = json.dumps([model, prompt_version, text, image_sha])
    return hashlib.sha256(raw.encode()).hexdigest()


def _path(component: str, key: str):
    return REPLAY_DIR / component / f"{key}.json"


def _load(component: str, key: str) -> dict | None:
    path = _path(component, key)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _save(component: str, key: str, record: dict) -> None:
    path = _path(component, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Call -----------------------------------------------------------------------------

def _client():
    from openai import AsyncOpenAI

    return AsyncOpenAI(api_key=settings.openai_api_key)


async def _call_openai(model: str, instructions: str, text: str, image: bytes | None,
                       schema_name: str, schema: dict, effort: str) -> tuple[dict, int, int]:
    content = [{"type": "input_text", "text": text}]
    if image:
        b64 = base64.b64encode(preprocess_image(image)).decode()
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}", "detail": "high"})
    response = await _client().responses.create(
        model=model,
        instructions=instructions,
        input=[{"role": "user", "content": content}],
        text={"format": {"type": "json_schema", "name": schema_name, "schema": schema, "strict": True}},
        reasoning={"effort": effort},
        store=False,
    )
    usage = response.usage
    return json.loads(response.output_text), usage.input_tokens, usage.output_tokens


async def structured_call(*, component: str, prompt_version: str, instructions: str, text: str,
                          schema_name: str, schema: dict, image: bytes | None = None,
                          model: str | None = None, effort: str = "medium",
                          mode: str | None = None) -> LLMResult:
    """One structured-output call, honouring LLM_MODE. Returns the parsed JSON.
    Effort is `medium` for extraction, `low` for chat."""
    model = model or settings.openai_extract_model
    mode = mode or settings.llm_mode
    key = cache_key(model, prompt_version, text, image)

    if mode == "replay":
        saved = _load(component, key)
        if saved is None:
            raise ReplayMissing(f"No recording for {component} key {key[:12]} in {REPLAY_DIR / component}. "
                                "Run once with LLM_MODE=record.")
        return LLMResult(data=saved["output"], model=saved["model"], mode="replay", key=key)

    if mode not in ("live", "record"):
        raise ValueError(f"Unknown LLM_MODE '{mode}'")
    if not live_allowed():
        raise BudgetExceeded(f"Live call refused: no OPENAI_API_KEY, or today's spend "
                             f"${spent_today():.4f} is over ${settings.llm_daily_budget_usd:.2f}.")

    data, in_tok, out_tok = await _call_openai(model, instructions, text, image, schema_name, schema, effort)
    usd = record_spend(component, model, in_tok, out_tok)
    if mode == "record":
        _save(component, key, {"key": key, "model": model, "prompt_version": prompt_version, "output": data,
                               "usage": {"input_tokens": in_tok, "output_tokens": out_tok, "usd": round(usd, 6)}})
    return LLMResult(data=data, model=model, mode="live", key=key)

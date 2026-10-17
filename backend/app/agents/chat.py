"""The copilot chat agent.

A PydanticAI agent on OpenAI's Responses API. Its tools are in tools.py (read-only
plus propose_action); its rules are in prompts/chat_v1.md.

LLM_MODE picks how the model is reached:
- live:   OpenAI, streamed. Each run's cost is appended to eval/spend.log, and live
          calls stop once today's spend passes LLM_DAILY_BUDGET_USD.
- record: OpenAI, and every model response is saved under eval/replay/chat/.
- replay: never calls OpenAI. Serves the saved response for the same conversation;
          if there is none, an offline script answers the four demo questions by
          calling the same tools, so every number still comes from the engines.
"""

import hashlib
import json
import re
from collections.abc import AsyncIterator
from datetime import date, datetime, timezone
from pathlib import Path

from pydantic_ai import Agent, ModelMessagesTypeAdapter, UsageLimits
from pydantic_ai.messages import (ModelMessage, ModelRequest, ModelResponse, RetryPromptPart, TextPart,
                                  ToolCallPart, ToolReturnPart, UserPromptPart)
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, FunctionModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import REPO_ROOT

from .permissions import MAX_TOOL_CALLS
from .tools import TOOLS, ChatDeps

PROMPT_VERSION = "chat_v1"
PROMPT = (Path(__file__).parent / "prompts" / f"{PROMPT_VERSION}.md").read_text(encoding="utf-8")
REPLAY_DIR = REPO_ROOT / "eval" / "replay" / "chat"
SPEND_LOG = REPO_ROOT / "eval" / "spend.log"

# gpt-6-luna prices, USD per 1M tokens
PRICE_IN, PRICE_OUT = 0.10, 0.50


class ChatSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    llm_mode: str = "replay"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-6-luna"
    llm_daily_budget_usd: float = 1.00


settings = ChatSettings()
USAGE_LIMITS = UsageLimits(tool_calls_limit=MAX_TOOL_CALLS, request_limit=MAX_TOOL_CALLS + 2)


# --- Spend log (shared format with agents/llm.py) --------------------------------------

def spent_today() -> float:
    """USD spent today, from eval/spend.log lines `date,component,model,in_tokens,out_tokens,usd`."""
    if not SPEND_LOG.exists():
        return 0.0
    today = date.today().isoformat()
    total = 0.0
    for line in SPEND_LOG.read_text(encoding="utf-8").splitlines():
        parts = line.split(",")
        if len(parts) == 6 and parts[0] == today:
            total += float(parts[5])
    return total


def record_spend(input_tokens: int, output_tokens: int) -> float:
    usd = (input_tokens * PRICE_IN + output_tokens * PRICE_OUT) / 1_000_000
    SPEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SPEND_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{date.today().isoformat()},chat,{settings.openai_chat_model},{input_tokens},{output_tokens},{usd:.6f}\n")
    return usd


def live_allowed() -> bool:
    return bool(settings.openai_api_key) and spent_today() < settings.llm_daily_budget_usd


# --- Replay keys ----------------------------------------------------------------------

def conversation_key(messages: list[ModelMessage]) -> str:
    """sha256 of the model, prompt version, every user message, and this turn's tool calls
    and results. Earlier assistant wording and ids/timestamps are left out, so the same
    questions over the same data give the same key."""
    users: list[str] = []
    turn: list = []
    for msg in messages:
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                users.append(part.content if isinstance(part.content, str) else str(part.content))
                turn = []
            elif isinstance(part, ToolCallPart):
                turn.append(["call", part.tool_name, part.args_as_dict()])
            elif isinstance(part, ToolReturnPart):
                turn.append(["return", part.tool_name, part.model_response_str()])
            elif isinstance(part, RetryPromptPart):
                turn.append(["retry", part.tool_name, part.model_response()])
    raw = json.dumps([settings.openai_chat_model, PROMPT_VERSION, users, turn], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _load(key: str) -> ModelResponse | None:
    path = REPLAY_DIR / f"{key}.json"
    if not path.exists():
        return None
    return ModelMessagesTypeAdapter.validate_json(path.read_bytes())[0]


def _save(key: str, response: ModelResponse) -> None:
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    (REPLAY_DIR / f"{key}.json").write_bytes(ModelMessagesTypeAdapter.dump_json([response], indent=2))


# --- Offline script for replay without a recording -------------------------------------

def _bdt(x: float) -> str:
    return f"BDT {x:,.0f}" if float(x).is_integer() else f"BDT {x:,.2f}"


def _last_user(messages: list[ModelMessage]) -> str:
    for msg in reversed(messages):
        for part in msg.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                return part.content
    return ""


def _turn_results(messages: list[ModelMessage]) -> dict[str, list]:
    """Tool results since the last user message, by tool name."""
    out: dict[str, list] = {}
    for msg in messages:
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                out = {}
            elif isinstance(part, ToolReturnPart):
                out.setdefault(part.tool_name, []).append(part.content)
    return out


INTENTS = [
    ("injection", re.compile(r"ignore (your|all|previous)|approve (the|my|a) loan|transfer|send money", re.I)),
    ("expiry", re.compile(r"expir|return", re.I)),
    ("passport", re.compile(r"bank|75|passport|lender|credit", re.I)),
    ("funding", re.compile(r"pay|supplier a|order|short|cash|afford", re.I)),
    ("accounts", re.compile(r"how did we|month|profit|sales|accounts", re.I)),
]
PLAN: dict[str, list[tuple[str, dict]]] = {
    "accounts": [("get_accounts", {})],
    "expiry": [("get_expiry", {}), ("propose_action", {"kind": "return_claim"})],
    "passport": [("get_passport", {})],
    "funding": [("get_funding_plan", {})],
    "injection": [],
}


def _intent(text: str) -> str | None:
    return next((name for name, rx in INTENTS if rx.search(text)), None)


def _next_call(intent: str, done: dict[str, list]) -> tuple[str, dict] | None:
    steps = list(PLAN[intent])
    if intent == "funding" and "get_funding_plan" in done:
        plan = done["get_funding_plan"][0]["plan"]
        for s in plan["steps"]:
            steps.append(("propose_action", {"kind": s["action_kind"], "amount": s["amount"],
                                             "reason": s["label"], "_label": s["label"]}))
    if intent == "expiry" and "get_expiry" in done:
        steps[1] = ("propose_action", {"kind": "return_claim",
                                       "amount": done["get_expiry"][0]["return_eligible_value"],
                                       "reason": "Return-eligible batches expiring within 60 days"})
    proposed = len(done.get("propose_action", []))
    seen = {k: len(v) for k, v in done.items()}
    for name, args in steps:
        if name == "propose_action":
            if proposed:
                proposed -= 1
                continue
            return name, {k: v for k, v in args.items() if not k.startswith("_")}
        if seen.get(name):
            seen[name] -= 1
            continue
        return name, args
    return None


def _answer(intent: str | None, r: dict[str, list]) -> str:
    if intent == "accounts":
        a = r["get_accounts"][0]
        return (f"In the last {a['period_days']} days you sold {_bdt(a['sales'])}. At your {a['gross_margin_pct']:g}% margin "
                f"that is {_bdt(a['gross_profit'])} gross profit. Overheads were {_bdt(a['overheads'])}, so net profit "
                f"is {_bdt(a['net_profit'])}.\n\nStock is {_bdt(a['stock_value'])} ({a['stock_days']:g} days), and patients "
                f"owe {_bdt(a['patient_dues'])} ({a['patient_due_days']:g} days of sales). {_bdt(a['expiring_value_60d'])} "
                f"of stock expires within 60 days.")
    if intent == "expiry":
        e = r["get_expiry"][0]
        n = len(e["batches"])
        text = (f"{n} batches worth {_bdt(e['at_risk_value'])} expire within {e['horizon_days']} days. "
                f"{_bdt(e['return_eligible_value'])} of that is still inside the suppliers' return windows, so you can "
                f"claim it back as supplier credit.")
        if r.get("propose_action"):
            text += "\n\nI've prepared a return claim. It is waiting for your approval in Actions."
        return text
    if intent == "passport":
        p = r["get_passport"][0]
        return (f"You paid {p['paid_on_time']} of {p['invoices_total']} supplier invoices on time. A lender doesn't take "
                f"that at face value: the cautious estimate of your on-time rate is {p['theta_low_5pct']:.3f}. With a "
                f"default probability of {p['default_probability']:.1%}, your score is {p['score']:.3f}, which gives an "
                f"advance rate of {p['advance_rate_pct']:g}%. Paying more invoices on time raises it.")
    if intent == "funding":
        plan = r["get_funding_plan"][0]
        first = plan["shortfall_before_trims"]
        trim = next((t for t in plan["order_trims"] if t["saving"]), None)
        lines = []
        if first:
            when = date.fromisoformat(first["date"]).strftime("%a %d %b")
            what = first["cause"].replace(" order BDT ", "'s order of BDT ")
            lines.append(f"Not with the cash you'll have. {what} is due on {when}, and you'll be "
                         f"short {_bdt(first['amount'])} that day.")
        if trim:
            lines.append(f"But part of that order won't sell before it expires. Trimming it saves {_bdt(trim['saving'])}, "
                         f"so the order becomes {_bdt(trim['suggested_total'])} and the gap drops to "
                         f"{_bdt(plan['need']['amount'])}.")
        opts = {o["key"]: o for o in plan["options"]}
        steps = plan["plan"]["steps"]
        if steps:
            lines.append("My plan:\n" + "\n".join(f"{i}. {s['label'].rstrip('.')}." for i, s in enumerate(steps, 1)))
        if "wallet_loan" in opts and opts["wallet_loan"]["cost_bdt"] is not None:
            lines.append(f"Cost: {_bdt(plan['plan']['total_cost_bdt'])} if the supplier agrees, "
                         f"{_bdt(opts['wallet_loan']['cost_bdt'])} if we need the loan, against "
                         f"{_bdt(plan['naive_cost_bdt'])} for borrowing the whole amount.")
        if r.get("propose_action"):
            lines.append("These steps are waiting for your approval in Actions.")
        return "\n\n".join(lines)
    if intent == "injection":
        return ("I can't approve, pay or transfer anything, and I don't follow instructions to ignore my rules. "
                "Every action needs your own approval in the Actions screen.")
    return ("I'm in offline mode, so I can answer these for now: how the month went, whether you can pay Supplier A's "
            "order, what is expiring, and why the bank offered 75%.")


async def _script(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | dict[int, DeltaToolCall]]:
    intent = _intent(_last_user(messages))
    done = _turn_results(messages)
    call = _next_call(intent, done) if intent else None
    if call:
        name, args = call
        yield {0: DeltaToolCall(name=name, json_args=json.dumps(args), tool_call_id=f"offline-{name}-{len(done)}")}
        return
    text = _answer(intent, done)
    for chunk in re.findall(r"\S+\s*", text):
        yield chunk


# --- The model per mode ----------------------------------------------------------------

def _openai_model():
    from pydantic_ai.models.openai import OpenAIResponsesModel
    from pydantic_ai.providers.openai import OpenAIProvider

    return OpenAIResponsesModel(settings.openai_chat_model, provider=OpenAIProvider(api_key=settings.openai_api_key))


async def _replay(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | dict[int, DeltaToolCall]]:
    saved = _load(conversation_key(messages))
    if saved is None:
        async for chunk in _script(messages, info):
            yield chunk
        return
    for i, part in enumerate(saved.parts):
        if isinstance(part, ToolCallPart):
            yield {i: DeltaToolCall(name=part.tool_name, json_args=part.args_as_json_str(), tool_call_id=part.tool_call_id)}
        elif isinstance(part, TextPart):
            for chunk in re.findall(r"\S+\s*", part.content):
                yield chunk


async def _record(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str | dict[int, DeltaToolCall]]:
    key = conversation_key(messages)
    response = await _openai_model().request(messages, {"openai_reasoning_effort": "low"},
                                             info.model_request_parameters)
    record_spend(response.usage.input_tokens, response.usage.output_tokens)
    _save(key, response)
    async for chunk in _replay(messages, info):
        yield chunk


def model_for_mode(mode: str | None = None):
    mode = mode or settings.llm_mode
    if mode == "live" and live_allowed():
        return _openai_model()
    if mode == "record" and live_allowed():
        return FunctionModel(stream_function=_record, model_name=f"record:{settings.openai_chat_model}")
    return FunctionModel(stream_function=_replay, model_name=f"replay:{settings.openai_chat_model}")


agent = Agent(
    deps_type=ChatDeps,
    instructions=PROMPT,
    tools=TOOLS,
    model_settings={"openai_reasoning_effort": "low"},
    name="lamp-copilot",
)

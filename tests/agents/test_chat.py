"""The copilot chat in replay mode: the four demo questions, golden numbers from tools,
proposals that wait for the owner, and replay of a recorded conversation."""

from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart

from app.agents import chat, llm
from chat_client import ask


def names(calls):
    return [n for n, _ in calls]


def test_month_summary(client):
    r = ask(client, "How did we do this month?")
    assert names(r["calls"]) == ["get_accounts"]
    for figure in ("412,500", "49,500", "36,000", "13,500"):
        assert figure in r["text"]


def test_supplier_a_order(client):
    r = ask(client, "Can I pay Supplier A's order next week?")
    assert names(r["calls"])[0] == "get_funding_plan"
    assert "propose_action" in names(r["calls"])
    for figure in ("19,000", "10,800", "49,200", "8,200", "181.97", "421.64"):
        assert figure in r["text"], figure
    actions = client.get("/api/v1/pharmacies/green-life/actions").json()
    assert actions and all(a["status"] == "proposed" and a["proposed_by"] == "agent" for a in actions)
    assert {a["kind"] for a in actions} >= {"trim_order", "extension_request", "loan_application"}


def test_expiry_proposes_return_claim(client):
    r = ask(client, "What is expiring?")
    assert "18,400" in r["text"] and "9,200" in r["text"]
    assert ("propose_action", {"kind": "return_claim", "amount": 9200.0,
                               "reason": "Return-eligible batches expiring within 60 days"}) in r["calls"]
    [a] = client.get("/api/v1/pharmacies/green-life/actions").json()
    assert a["kind"] == "return_claim" and a["status"] == "proposed"
    assert "waiting for your approval" in r["text"]


def test_passport_explanation(client):
    r = ask(client, "Why did the bank offer 75%?")
    assert names(r["calls"]) == ["get_passport"]
    for figure in ("38 of 41", "0.826", "3.0%", "75.2%"):
        assert figure in r["text"], figure


def test_tool_call_limit(client):
    r = ask(client, "Can I pay Supplier A's order next week?")
    assert len(r["calls"]) <= chat.USAGE_LIMITS.tool_calls_limit


def test_chat_is_logged(client):
    ask(client, "How did we do this month?")
    events = client.get("/api/v1/logs").json()
    assert any(e["component"] == "CHAT" and e["event"] == "chat_message" for e in events)


def test_unknown_question_offline(client):
    r = ask(client, "Tell me a joke")
    assert r["calls"] == [] and "offline mode" in r["text"]


def test_recorded_response_is_replayed(client):
    """A saved model response for the same conversation is served instead of the offline script."""
    msgs = [ModelRequest(parts=[UserPromptPart(content="Hello there")])]
    chat._save(chat.conversation_key(msgs), ModelResponse(parts=[TextPart(content="Recorded hello.")]))
    r = ask(client, "Hello there")
    assert r["text"] == "Recorded hello."


def test_replay_never_builds_an_openai_model(monkeypatch):
    def boom():
        raise AssertionError("OpenAI model built in replay mode")

    monkeypatch.setattr(chat, "_openai_model", boom)
    assert chat.model_for_mode("replay").model_name.startswith("replay")
    # live and record without a key fall back to replay too
    assert chat.model_for_mode("live").model_name.startswith("replay")
    assert chat.model_for_mode("record").model_name.startswith("replay")


def test_budget_guard(monkeypatch):
    monkeypatch.setattr(chat.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(chat.settings, "llm_daily_budget_usd", 0.001)
    assert llm.live_allowed()
    chat.record_spend(10_000, 2_000)  # 0.001 + 0.001 USD
    assert llm.SPEND_LOG.read_text().split(",")[1] == "chat"
    assert not llm.live_allowed()
    assert chat.model_for_mode("live").model_name.startswith("replay")


def test_replay_key_ignores_action_ids():
    """A recording still matches when earlier demo steps changed the action numbering."""
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart

    def convo(aid):
        return [ModelRequest(parts=[UserPromptPart(content="What is expiring?")]),
                ModelResponse(parts=[ToolCallPart(tool_name="propose_action", args={"kind": "return_claim"}, tool_call_id="t1")]),
                ModelRequest(parts=[ToolReturnPart(tool_name="propose_action", tool_call_id="t1",
                                                   content={"action_id": aid, "kind": "return_claim", "status": "proposed"})])]

    assert chat.conversation_key(convo("act-1")) == chat.conversation_key(convo("act-7"))


def test_parallel_proposals_get_distinct_actions(client, monkeypatch):
    """The model may ask for several proposals in one response; each gets its own action."""
    import json as _json

    from pydantic_ai.models.function import DeltaToolCall, FunctionModel

    async def three_at_once(messages, info):
        if any(getattr(p, "tool_name", None) == "propose_action" for m in messages for p in m.parts
               if type(p).__name__ == "ToolReturnPart"):
            yield "Proposed."
            return
        kinds = ["trim_order", "extension_request", "loan_application"]
        yield {i: DeltaToolCall(name="propose_action", json_args=_json.dumps({"kind": k, "amount": 8200}),
                                tool_call_id=f"p{i}") for i, k in enumerate(kinds)}

    monkeypatch.setattr(chat, "model_for_mode", lambda mode=None: FunctionModel(stream_function=three_at_once,
                                                                                model_name="test"))
    ask(client, "Cover the shortfall")
    actions = client.get("/api/v1/pharmacies/green-life/actions").json()
    assert sorted(a["kind"] for a in actions) == ["extension_request", "loan_application", "trim_order"]
    assert len({a["id"] for a in actions}) == 3


def test_tools_run_one_at_a_time():
    """All tools share the request's database session, so none may run in parallel."""
    assert all(t.sequential for t in chat.agent._function_toolset.tools.values())


def test_unrecorded_question_gets_an_honest_reply(client, monkeypatch):
    """Outside tests, replay never pretends: an unrecorded question says it wasn't recorded."""
    monkeypatch.setattr(chat, "OFFLINE_SCRIPT", False)
    r = ask(client, "How did we do this month?")
    assert r["calls"] == [] and "wasn't recorded" in r["text"] and "LLM_MODE=live" in r["text"]


def test_replay_key_uses_only_the_latest_question():
    """A recorded question still replays when the owner asked something else first."""
    first = [ModelRequest(parts=[UserPromptPart(content="What is expiring?")])]
    later = [ModelRequest(parts=[UserPromptPart(content="How did we do this month?")]),
             ModelResponse(parts=[TextPart(content="Fine.")]),
             ModelRequest(parts=[UserPromptPart(content="What is expiring?")])]
    assert chat.conversation_key(first) == chat.conversation_key(later)

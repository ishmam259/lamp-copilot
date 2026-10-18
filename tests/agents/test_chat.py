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

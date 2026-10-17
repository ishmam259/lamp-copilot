"""Helper for chat tests: send a message the way the frontend's useChat does."""

import json


def ask(client, text: str, history: list | None = None) -> dict:
    """Send one user message the way useChat does; return the streamed text, tool calls and results."""
    messages = list(history or []) + [{"id": f"u{len(history or [])}", "role": "user",
                                       "parts": [{"type": "text", "text": text}]}]
    r = client.post("/api/v1/chat", json={"trigger": "submit-message", "id": "c1", "messages": messages,
                                          "pharmacy_id": "green-life"})
    assert r.status_code == 200, r.text
    text, calls, results = "", [], {}
    for line in r.text.splitlines():
        if not line.startswith("data: ") or line == "data: [DONE]":
            continue
        ev = json.loads(line[6:])
        if ev["type"] == "text-delta":
            text += ev["delta"]
        elif ev["type"] == "tool-input-available":
            calls.append((ev["toolName"], ev["input"]))
        elif ev["type"] == "tool-output-available":
            results[ev["toolCallId"]] = ev["output"]
    return {"text": text, "calls": calls, "results": results}

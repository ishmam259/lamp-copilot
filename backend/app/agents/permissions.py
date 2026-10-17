"""Permission tiers for the copilot chat's tools.

Tiers (the same as engines/logbus.py):
  T0  read-only / regulator views
  T1  owner and extraction (proposals, captures, consents, approvals)
  T2  engines (deterministic analysis and sandbox execution)
  T3  lender and financial execution (applications, registry, payouts)

The chat agent may hold only T2 read tools and the T1 `propose_action` tool.
It never holds a tool that approves, rejects, executes, transfers money, grants
consent or contacts a supplier or lender: those exist only as owner HTTP calls.
tests/agents/test_security.py asserts the agent's tool list against this table.
"""

READ = "read"
PROPOSE = "propose"

# tool name -> (tier, kind)
CHAT_TOOLS: dict[str, tuple[str, str]] = {
    "get_accounts": ("T2", READ),
    "get_dues": ("T2", READ),
    "get_forecast": ("T2", READ),
    "get_alerts": ("T2", READ),
    "get_expiry": ("T2", READ),
    "get_orders": ("T2", READ),
    "get_trim": ("T2", READ),
    "get_funding_plan": ("T2", READ),
    "get_passport": ("T2", READ),
    "propose_action": ("T1", PROPOSE),
}

# Action kinds the agent may propose. Every one waits for the owner's approval.
PROPOSABLE_KINDS = ("return_claim", "extension_request", "trim_order", "set_aside", "loan_application")

# Words that must never appear in a chat tool's name.
FORBIDDEN_VERBS = ("approve", "reject", "execute", "transfer", "pay", "send", "grant", "consent", "decide", "contact")

# At most this many tool calls per user message.
MAX_TOOL_CALLS = 5

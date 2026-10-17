"""POST /api/v1/chat: the copilot chat, streamed with the Vercel AI SDK UI message
protocol so the frontend's useChat reads it directly. main.py mounts this router."""

import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic_ai.ui.vercel_ai import VercelAIAdapter
from sqlalchemy.orm import Session

from app import engines
from app.db.session import get_db

from . import chat
from .tools import ChatDeps

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(request: Request, db: Session = Depends(get_db)) -> Response:
    """Body: the AI SDK's chat request, plus `pharmacy_id` (default `green-life`)."""
    body = json.loads(await request.body() or b"{}")
    pid = body.get("pharmacy_id") or "green-life"
    engines.get_pharmacy(db, pid)  # 404 for an unknown pharmacy
    model = chat.model_for_mode()
    engines.log("T1", "CHAT", "chat_message", db, pharmacy=pid, mode=model.model_name.split(":")[0]
                if ":" in model.model_name else "live", prompt_version=chat.PROMPT_VERSION)
    db.commit()

    async def on_complete(result) -> None:
        usage = result.usage
        if chat.settings.llm_mode == "live" and not model.model_name.startswith("replay"):
            chat.record_spend(usage.input_tokens, usage.output_tokens)

    return await VercelAIAdapter.dispatch_request(
        request, agent=chat.agent, sdk_version=7, model=model, deps=ChatDeps(db=db, pharmacy_id=pid),
        usage_limits=chat.USAGE_LIMITS, on_complete=on_complete,
    )

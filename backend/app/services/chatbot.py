import json
from typing import Optional

import httpx
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Alert, Conversation, ChatMessage, Device, MetricSample
from app.services.monitoring import poll_all_devices
from app.services.ssh_config import create_config_request, parse_config_intent

settings = get_settings()

SYSTEM_PROMPT = """You are NetWatch AI, a network monitoring assistant for a GNS3 lab.
You help operators monitor devices, detect faults, and propose configuration changes.
When users ask to configure devices, respond with a JSON block:
```json
{"intent": "configure", "device_name": "...", "commands": ["..."], "explanation": "..."}
```
For status queries, summarize device health. For faults, give actionable recommendations.
Never execute commands directly — always note that admin approval is required for changes.
Keep responses concise and technical."""


async def _call_llm(messages: list[dict]) -> str:
    if settings.openai_api_key:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.ollama_host}/api/chat",
            json={"model": settings.ollama_model, "messages": messages, "stream": False},
        )
        if resp.status_code == 200:
            return resp.json().get("message", {}).get("content", "")
    return ""


async def _build_context(db: AsyncSession) -> str:
    result = await db.execute(select(Device).where(Device.is_active == True))
    devices = result.scalars().all()
    lines = ["Known devices:"]
    for d in devices:
        lines.append(f"  - {d.name} ({d.management_ip}): {d.status.value}")
    return "\n".join(lines)


async def process_chat_message(
    db: AsyncSession,
    user_id: int,
    conversation_id: int,
    user_message: str,
) -> dict:
    result = await db.execute(select(Device).where(Device.is_active == True))
    devices = result.scalars().all()

    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at)
        .limit(20)
    )
    history = history_result.scalars().all()

    context = await _build_context(db)
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    db.add(ChatMessage(conversation_id=conversation_id, role="user", content=user_message))

    llm_response = await _call_llm(messages)
    config_request_id = None
    parsed = parse_config_intent(user_message, devices)

    if not llm_response:
        if parsed and parsed.get("intent") in ("enable_interface", "disable_interface"):
            req = await create_config_request(
                db, user_id, parsed["device_id"], user_message,
                parsed["commands"], conversation_id,
            )
            config_request_id = req.id
            llm_response = (
                f"I've prepared the following configuration for **{parsed['device_name']}**:\n\n"
                + "\n".join(f"`{c}`" for c in parsed["commands"])
                + "\n\nThis request is **pending admin approval** before execution."
            )
        elif parsed and parsed.get("intent") == "query_status":
            poll_results = await poll_all_devices(db)
            up = sum(1 for r in poll_results if r.get("reachable"))
            llm_response = f"Network status: {up}/{len(poll_results)} devices reachable.\n\n" + context
        else:
            llm_response = (
                "I can help you with:\n"
                "- **Status**: \"What's the network status?\" or \"Show health of router1\"\n"
                "- **Configure**: \"Enable port 3 on switch1\" (requires admin approval)\n"
                "- **Reports**: \"Generate network report\"\n"
                "- **Faults**: \"Any alerts?\" or \"What's wrong with the network?\""
            )

    db.add(ChatMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=llm_response,
        metadata_json={"config_request_id": config_request_id},
    ))

    conv_result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = conv_result.scalar_one_or_none()
    if conv and conv.title == "New conversation":
        conv.title = user_message[:60] + ("..." if len(user_message) > 60 else "")

    return {
        "response": llm_response,
        "config_request_id": config_request_id,
    }

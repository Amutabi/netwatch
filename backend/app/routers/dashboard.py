from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Alert, AuditLog, Conversation, ChatMessage, Device, User
from app.schemas import (
    ChatRequest, ChatResponse, ConversationResponse, DashboardStats, MessageResponse,
)
from app.services.chatbot import process_chat_message
from app.services.reports import generate_csv_report, generate_pdf_report, generate_report_data

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    devices = (await db.execute(select(Device).where(Device.is_active == True))).scalars().all()
    alerts = (await db.execute(select(Alert).where(Alert.is_acknowledged == False))).scalars().all()
    return DashboardStats(
        total_devices=len(devices),
        devices_up=sum(1 for d in devices if d.status.value == "up"),
        devices_down=sum(1 for d in devices if d.status.value == "down"),
        active_alerts=len(alerts),
        critical_alerts=sum(1 for a in alerts if a.severity.value == "critical"),
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.conversation_id:
        conv_result = await db.execute(
            select(Conversation).where(Conversation.id == data.conversation_id, Conversation.user_id == user.id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            raise HTTPException(404, "Conversation not found")
    else:
        conv = Conversation(user_id=user.id)
        db.add(conv)
        await db.flush()

    result = await process_chat_message(db, user.id, conv.id, data.message)
    db.add(AuditLog(user_id=user.id, action="chat_message", details={"conversation_id": conv.id}))
    return ChatResponse(conversation_id=conv.id, **result)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user.id).order_by(desc(Conversation.updated_at))
    )
    return result.scalars().all()


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conv_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conv = (await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user.id)
    )).scalar_one_or_none()
    if not conv:
        raise HTTPException(404)
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.conversation_id == conv_id).order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


@router.get("/reports/data")
async def report_data(hours: int = 24, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await generate_report_data(db, hours)


@router.get("/reports/download/csv")
async def download_csv(hours: int = 24, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    content = await generate_csv_report(db, hours)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=netwatch-report.csv"},
    )


@router.get("/reports/download/pdf")
async def download_pdf(hours: int = 24, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    content = await generate_pdf_report(db, hours)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=netwatch-report.pdf"},
    )


@router.get("/logs")
async def audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit))
    logs = result.scalars().all()
    return [
        {
            "id": l.id,
            "action": l.action,
            "resource_type": l.resource_type,
            "details": l.details,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import Alert, AuditLog, ConfigApprovalStatus, ConfigRequest, Device, MetricSample, User
from app.schemas import AlertResponse, ConfigRequestResponse, DeviceCreate, DeviceResponse
from app.services.monitoring import poll_all_devices
from app.services.ssh_config import execute_ssh_commands
from app.services.topology import sync_topology

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
async def list_devices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Device).where(Device.is_active == True).order_by(Device.name))
    return result.scalars().all()


@router.post("", response_model=DeviceResponse)
async def create_device(
    data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    device = Device(**data.model_dump(exclude={"ssh_password"}))
    if data.ssh_password:
        device.ssh_password_enc = data.ssh_password  # encrypt in production
    db.add(device)
    await db.flush()
    db.add(AuditLog(user_id=user.id, action="device_create", resource_type="device", resource_id=str(device.id)))
    return device


@router.delete("/{device_id}")
async def remove_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")
    device.is_active = False
    db.add(AuditLog(user_id=user.id, action="device_remove", resource_type="device", resource_id=str(device_id)))
    return {"ok": True}


@router.post("/poll")
async def trigger_poll(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    results = await poll_all_devices(db)
    return {"polled": len(results), "results": results}


@router.post("/sync-topology")
async def trigger_topology_sync(db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    result = await sync_topology(db)
    db.add(AuditLog(user_id=user.id, action="topology_sync", details=result))
    return result


@router.get("/metrics/{device_id}")
async def device_metrics(
    device_id: int,
    metric: str = "latency_ms",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(MetricSample)
        .where(MetricSample.device_id == device_id, MetricSample.metric_name == metric)
        .order_by(desc(MetricSample.recorded_at))
        .limit(limit)
    )
    samples = result.scalars().all()
    return [{"recorded_at": s.recorded_at.isoformat(), "value": s.value} for s in reversed(samples)]


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).order_by(desc(Alert.created_at)).limit(limit))
    return result.scalars().all()


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404)
    alert.is_acknowledged = True
    return {"ok": True}


@router.get("/config-requests", response_model=list[ConfigRequestResponse])
async def list_config_requests(
    status: str = "pending",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ConfigRequest)
        .where(ConfigRequest.status == ConfigApprovalStatus(status))
        .order_by(desc(ConfigRequest.created_at))
    )
    return result.scalars().all()


@router.post("/config-requests/{request_id}/approve")
async def approve_config(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(ConfigRequest).where(ConfigRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req or req.status != ConfigApprovalStatus.PENDING:
        raise HTTPException(400, "Invalid or already processed request")

    dev_result = await db.execute(select(Device).where(Device.id == req.device_id))
    device = dev_result.scalar_one_or_none()
    if not device:
        raise HTTPException(404, "Device not found")

    username = device.ssh_username or "admin"
    password = device.ssh_password_enc or "admin"

    success, output = await execute_ssh_commands(device, req.proposed_commands, username, password)
    req.status = ConfigApprovalStatus.EXECUTED if success else ConfigApprovalStatus.FAILED
    req.approved_by = admin.id
    req.execution_output = output
    req.executed_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=admin.id,
        action="config_approved" if success else "config_failed",
        resource_type="config_request",
        resource_id=str(request_id),
        details={"output": output[:500]},
    ))
    return {"success": success, "output": output}


@router.post("/config-requests/{request_id}/reject")
async def reject_config(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(ConfigRequest).where(ConfigRequest.id == request_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404)
    req.status = ConfigApprovalStatus.REJECTED
    req.approved_by = admin.id
    db.add(AuditLog(user_id=admin.id, action="config_rejected", resource_type="config_request", resource_id=str(request_id)))
    return {"ok": True}

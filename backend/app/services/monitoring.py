import asyncio
import platform
import subprocess
from datetime import datetime
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertSeverity, Device, DeviceStatus, MetricSample


async def ping_host(host: str, timeout: int = 2) -> tuple[bool, Optional[float]]:
    """Return (reachable, latency_ms)."""
    param = "-n" if platform.system().lower() == "windows" else "-c"
    timeout_flag = "-w" if platform.system().lower() == "windows" else "-W"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", param, "1", timeout_flag, str(timeout * 1000 if platform.system().lower() == "windows" else timeout), host,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode(errors="ignore")
        reachable = proc.returncode == 0
        latency = None
        if reachable:
            for line in output.splitlines():
                if "time=" in line.lower() or "time<" in line.lower():
                    try:
                        part = line.lower().split("time=")[-1].split("ms")[0].strip()
                        if part.startswith("<"):
                            part = part[1:]
                        latency = float(part.replace(",", "."))
                    except (ValueError, IndexError):
                        pass
        return reachable, latency
    except Exception:
        return False, None


async def poll_device(db: AsyncSession, device: Device) -> dict:
    """Poll a single device and store metrics."""
    reachable, latency = await ping_host(device.management_ip)

    if reachable:
        device.status = DeviceStatus.UP
        device.last_seen = datetime.utcnow()
        if latency is not None:
            db.add(MetricSample(
                device_id=device.id,
                metric_name="latency_ms",
                value=latency,
                unit="ms",
            ))
    else:
        device.status = DeviceStatus.DOWN

    db.add(MetricSample(
        device_id=device.id,
        metric_name="reachable",
        value=1.0 if reachable else 0.0,
        unit="bool",
    ))

    return {"device_id": device.id, "reachable": reachable, "latency_ms": latency}


async def detect_faults(db: AsyncSession, device: Device) -> list[Alert]:
    """Rule-based fault detection with recommendations."""
    alerts: list[Alert] = []

    result = await db.execute(
        select(MetricSample)
        .where(MetricSample.device_id == device.id, MetricSample.metric_name == "reachable")
        .order_by(desc(MetricSample.recorded_at))
        .limit(5)
    )
    recent = result.scalars().all()
    fail_count = sum(1 for m in recent if m.value == 0.0)

    if fail_count >= 3:
        alerts.append(Alert(
            device_id=device.id,
            severity=AlertSeverity.CRITICAL,
            title=f"{device.name} unreachable",
            message=f"Device {device.name} ({device.management_ip}) failed {fail_count} consecutive checks.",
            recommendation=(
                "Check physical link in GNS3, verify management IP, ensure device is powered on. "
                "Run 'show ip interface brief' if SSH is available."
            ),
        ))

    latency_result = await db.execute(
        select(MetricSample)
        .where(MetricSample.device_id == device.id, MetricSample.metric_name == "latency_ms")
        .order_by(desc(MetricSample.recorded_at))
        .limit(1)
    )
    latest_latency = latency_result.scalar_one_or_none()
    if latest_latency and latest_latency.value > 100:
        alerts.append(Alert(
            device_id=device.id,
            severity=AlertSeverity.WARNING,
            title=f"High latency on {device.name}",
            message=f"Latency is {latest_latency.value:.1f}ms (threshold: 100ms).",
            recommendation="Check for congestion on the management network or CPU load on the device.",
        ))

    for alert in alerts:
        db.add(alert)
    return alerts


async def poll_all_devices(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Device).where(Device.is_active == True))
    devices = result.scalars().all()
    results = []
    for device in devices:
        r = await poll_device(db, device)
        await detect_faults(db, device)
        results.append(r)
    return results

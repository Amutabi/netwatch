import csv
import io
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Device, MetricSample


async def generate_report_data(db: AsyncSession, hours: int = 24) -> dict:
    since = datetime.utcnow() - timedelta(hours=hours)

    devices_result = await db.execute(select(Device).where(Device.is_active == True))
    devices = devices_result.scalars().all()

    alerts_result = await db.execute(
        select(Alert).where(Alert.created_at >= since).order_by(desc(Alert.created_at))
    )
    alerts = alerts_result.scalars().all()

    device_stats = []
    for d in devices:
        avg_result = await db.execute(
            select(func.avg(MetricSample.value))
            .where(
                MetricSample.device_id == d.id,
                MetricSample.metric_name == "latency_ms",
                MetricSample.recorded_at >= since,
            )
        )
        avg_latency = avg_result.scalar()
        device_stats.append({
            "name": d.name,
            "ip": d.management_ip,
            "status": d.status.value,
            "avg_latency_ms": round(avg_latency, 2) if avg_latency else None,
        })

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period_hours": hours,
        "device_count": len(devices),
        "devices_up": sum(1 for d in devices if d.status.value == "up"),
        "alert_count": len(alerts),
        "devices": device_stats,
        "alerts": [
            {
                "severity": a.severity.value,
                "title": a.title,
                "message": a.message,
                "recommendation": a.recommendation,
                "created_at": a.created_at.isoformat(),
            }
            for a in alerts
        ],
    }


async def generate_csv_report(db: AsyncSession, hours: int = 24) -> str:
    data = await generate_report_data(db, hours)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["NetWatch AI Network Report"])
    writer.writerow(["Generated", data["generated_at"]])
    writer.writerow(["Period (hours)", data["period_hours"]])
    writer.writerow([])
    writer.writerow(["Device", "IP", "Status", "Avg Latency (ms)"])
    for d in data["devices"]:
        writer.writerow([d["name"], d["ip"], d["status"], d["avg_latency_ms"] or "N/A"])
    writer.writerow([])
    writer.writerow(["Alerts"])
    writer.writerow(["Severity", "Title", "Message", "Recommendation", "Time"])
    for a in data["alerts"]:
        writer.writerow([a["severity"], a["title"], a["message"], a["recommendation"], a["created_at"]])
    return output.getvalue()


async def generate_pdf_report(db: AsyncSession, hours: int = 24) -> bytes:
    data = await generate_report_data(db, hours)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("NetWatch AI — Network Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {data['generated_at']}", styles["Normal"]))
    story.append(Paragraph(
        f"Devices: {data['devices_up']}/{data['device_count']} up | Alerts: {data['alert_count']}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 20))

    table_data = [["Device", "IP", "Status", "Avg Latency (ms)"]]
    for d in data["devices"]:
        table_data.append([d["name"], d["ip"], d["status"], str(d["avg_latency_ms"] or "N/A")])

    t = Table(table_data)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(t)
    doc.build(story)
    return buffer.getvalue()

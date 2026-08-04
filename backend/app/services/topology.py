import httpx
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Device, DeviceStatus

settings = get_settings()


class GNS3Client:
    def __init__(self):
        self.base_url = f"http://{settings.gns3_host}:{settings.gns3_port}/v2"
        self.auth = (settings.gns3_user, settings.gns3_password)

    async def get_project_nodes(self, project_id: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{self.base_url}/projects/{project_id}/nodes",
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()

    async def list_projects(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{self.base_url}/projects", auth=self.auth)
            resp.raise_for_status()
            return resp.json()


async def sync_topology(db: AsyncSession) -> dict:
    """Sync devices from GNS3. Remove devices no longer in topology."""
    client = GNS3Client()
    project_id = settings.gns3_project_id
    synced = {"added": 0, "updated": 0, "removed": 0}

    try:
        if not project_id:
            projects = await client.list_projects()
            if projects:
                project_id = projects[0]["project_id"]
            else:
                return {"error": "No GNS3 projects found", **synced}

        nodes = await client.get_project_nodes(project_id)
        gns3_ids = set()

        for node in nodes:
            node_id = node.get("node_id", "")
            gns3_ids.add(node_id)
            name = node.get("name", "unknown")
            props = node.get("properties", {})
            mgmt_ip = props.get("management_ip") or props.get("ip_address") or node.get("console_host", "")

            result = await db.execute(select(Device).where(Device.gns3_node_id == node_id))
            existing = result.scalar_one_or_none()

            if existing:
                existing.name = name
                if mgmt_ip:
                    existing.management_ip = mgmt_ip
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
                synced["updated"] += 1
            elif mgmt_ip:
                db.add(Device(
                    name=name,
                    hostname=name,
                    management_ip=mgmt_ip,
                    gns3_node_id=node_id,
                    device_type=_map_device_type(node.get("node_type", "")),
                    status=DeviceStatus.UNKNOWN,
                ))
                synced["added"] += 1

        result = await db.execute(select(Device).where(Device.gns3_node_id.isnot(None), Device.is_active == True))
        for device in result.scalars().all():
            if device.gns3_node_id not in gns3_ids:
                device.is_active = False
                device.status = DeviceStatus.REMOVED
                synced["removed"] += 1

    except httpx.HTTPError as e:
        return {"error": str(e), **synced}

    stale_cutoff = datetime.utcnow() - timedelta(minutes=settings.device_stale_minutes)
    result = await db.execute(
        select(Device).where(
            Device.is_active == True,
            Device.last_seen.isnot(None),
            Device.last_seen < stale_cutoff,
        )
    )
    for device in result.scalars().all():
        if device.gns3_node_id is None:
            device.is_active = False
            device.status = DeviceStatus.REMOVED
            synced["removed"] += 1

    return synced


def _map_device_type(gns3_type: str) -> str:
    mapping = {
        "dynamips": "cisco_ios",
        "iou": "cisco_ios",
        "vios": "cisco_ios",
        "qemu": "linux",
        "docker": "linux",
    }
    return mapping.get(gns3_type.lower(), "cisco_ios")

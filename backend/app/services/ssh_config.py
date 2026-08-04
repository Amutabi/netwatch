import json
import re
from typing import Optional

from netmiko import ConnectHandler
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConfigApprovalStatus, ConfigRequest, Device


async def execute_ssh_commands(
    device: Device,
    commands: list[str],
    username: str,
    password: str,
) -> tuple[bool, str]:
    """Execute CLI commands on device via SSH."""
    device_params = {
        "device_type": device.device_type,
        "host": device.management_ip,
        "username": username,
        "password": password,
        "port": device.ssh_port,
        "timeout": 30,
    }
    try:
        with ConnectHandler(**device_params) as conn:
            output_parts = []
            for cmd in commands:
                result = conn.send_command(cmd)
                output_parts.append(f"> {cmd}\n{result}")
            return True, "\n\n".join(output_parts)
    except Exception as e:
        return False, str(e)


def parse_config_intent(text: str, devices: list[Device]) -> Optional[dict]:
    """Rule-based NLU for common config intents (fallback when no LLM)."""
    text_lower = text.lower()
    device = None
    for d in devices:
        if d.name.lower() in text_lower:
            device = d
            break

    if "enable" in text_lower and "port" in text_lower:
        port_match = re.search(r"port\s+(\d+)", text_lower)
        if device and port_match:
            port = port_match.group(1)
            return {
                "intent": "enable_interface",
                "device_id": device.id,
                "device_name": device.name,
                "commands": [
                    "configure terminal",
                    f"interface GigabitEthernet0/{port}",
                    "no shutdown",
                    "end",
                ],
                "description": f"Enable port {port} on {device.name}",
            }

    if "shutdown" in text_lower and "port" in text_lower:
        port_match = re.search(r"port\s+(\d+)", text_lower)
        if device and port_match:
            port = port_match.group(1)
            return {
                "intent": "disable_interface",
                "device_id": device.id,
                "device_name": device.name,
                "commands": [
                    "configure terminal",
                    f"interface GigabitEthernet0/{port}",
                    "shutdown",
                    "end",
                ],
                "description": f"Disable port {port} on {device.name}",
            }

    if "status" in text_lower or "health" in text_lower:
        target = device.name if device else "network"
        return {
            "intent": "query_status",
            "device_name": target,
            "commands": [],
            "description": f"Query status for {target}",
        }

    return None


async def create_config_request(
    db: AsyncSession,
    user_id: int,
    device_id: int,
    nl_request: str,
    commands: list[str],
    conversation_id: Optional[int] = None,
) -> ConfigRequest:
    req = ConfigRequest(
        user_id=user_id,
        device_id=device_id,
        conversation_id=conversation_id,
        natural_language_request=nl_request,
        proposed_commands=commands,
        status=ConfigApprovalStatus.PENDING,
    )
    db.add(req)
    await db.flush()
    return req

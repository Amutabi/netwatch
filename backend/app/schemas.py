from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class DeviceCreate(BaseModel):
    name: str
    hostname: str
    management_ip: str
    device_type: str = "cisco_ios"
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    snmp_community: str = "public"


class DeviceResponse(BaseModel):
    id: int
    name: str
    hostname: str
    management_ip: str
    device_type: str
    status: str
    last_seen: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    device_id: Optional[int]
    severity: str
    title: str
    message: str
    recommendation: Optional[str]
    is_acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    response: str
    config_request_id: Optional[int] = None


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConfigRequestResponse(BaseModel):
    id: int
    device_id: int
    natural_language_request: str
    proposed_commands: list
    status: str
    execution_output: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    action: str
    resource_type: Optional[str]
    details: dict
    created_at: datetime

    class Config:
        from_attributes = True


class MetricPoint(BaseModel):
    recorded_at: datetime
    value: float


class DashboardStats(BaseModel):
    total_devices: int
    devices_up: int
    devices_down: int
    active_alerts: int
    critical_alerts: int

from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SAEnum, Float, ForeignKey,
    Integer, String, Text, JSON,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class DeviceStatus(str, Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"
    REMOVED = "removed"


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ConfigApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    hostname = Column(String(255), nullable=False)
    device_type = Column(String(50), default="cisco_ios")
    management_ip = Column(String(45), nullable=False, index=True)
    gns3_node_id = Column(String(100), nullable=True, index=True)
    status = Column(SAEnum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    last_seen = Column(DateTime, nullable=True)
    snmp_community = Column(String(100), default="public")
    ssh_username = Column(String(100), nullable=True)
    ssh_password_enc = Column(Text, nullable=True)
    ssh_port = Column(Integer, default=22)
    metadata_json = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    metrics = relationship("MetricSample", back_populates="device")
    alerts = relationship("Alert", back_populates="device")


class MetricSample(Base):
    __tablename__ = "metric_samples"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20), default="")
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True)
    severity = Column(SAEnum(AlertSeverity), default=AlertSeverity.INFO)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    device = relationship("Device", back_populates="alerts")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), default="New conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class ConfigRequest(Base):
    __tablename__ = "config_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    natural_language_request = Column(Text, nullable=False)
    proposed_commands = Column(JSON, default=list)
    status = Column(SAEnum(ConfigApprovalStatus), default=ConfigApprovalStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    execution_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

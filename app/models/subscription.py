from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SubscriptionStatus(str, enum.Enum):
    requested = "requested"
    active = "active"
    off = "off"
    error = "error"


class SubscriptionChannelType(str, enum.Enum):
    rest_hook = "rest-hook"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    status = Column(
        Enum(SubscriptionStatus, name="subscriptionstatus"),
        nullable=False,
        default=SubscriptionStatus.requested,
    )
    reason = Column(String(255), nullable=False)
    criteria = Column(String(255), nullable=False)  # e.g., "Appointment?patient=123" or resource type
    channel_type = Column(
        Enum(SubscriptionChannelType, name="subscriptionchanneltype"),
        nullable=False,
        default=SubscriptionChannelType.rest_hook,
    )
    endpoint = Column(String(512), nullable=False)  # webhook URL
    payload = Column(String(128), nullable=True, default="application/fhir+json")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

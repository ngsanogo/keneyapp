from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    reason: str = Field(..., max_length=255)
    criteria: str = Field(..., max_length=255)
    endpoint: AnyHttpUrl
    payload: Optional[str] = "application/fhir+json"


class SubscriptionResponse(BaseModel):
    id: int
    tenant_id: int
    status: str
    reason: str
    criteria: str
    endpoint: AnyHttpUrl
    payload: Optional[str]

    model_config = ConfigDict(from_attributes=True)

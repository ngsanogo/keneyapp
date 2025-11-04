from datetime import datetime
from typing import Optional
from pydantic import BaseModel, AnyHttpUrl, Field
from pydantic import ConfigDict

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

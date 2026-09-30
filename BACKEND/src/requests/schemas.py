import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from src.requests.enums import ServiceRequestStatus


class ServiceRequestCreate(BaseModel):
    provider_id: uuid.UUID
    service_category_id: uuid.UUID
    description: str = Field(min_length=1, max_length=1000)
    requested_date: date
    requested_time: str = Field(min_length=1, max_length=20)


class ServiceRequestUpdateStatus(BaseModel):
    status: ServiceRequestStatus
    provider_response: str | None = Field(default=None, max_length=1000)


class ServiceRequestResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    provider_id: uuid.UUID
    service_category_id: uuid.UUID
    description: str
    requested_date: date
    requested_time: str
    status: ServiceRequestStatus
    provider_response: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
